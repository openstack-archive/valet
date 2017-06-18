#
# Copyright 2014-2017 AT&T Intellectual Property
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import copy
import operator

from oslo_log import log

from valet.engine.optimizer.app_manager.app_topology_base import LEVELS
from valet.engine.optimizer.app_manager.app_topology_base import VGroup
from valet.engine.optimizer.app_manager.app_topology_base import VM
from valet.engine.optimizer.ostro.constraint_solver import ConstraintSolver
from valet.engine.optimizer.ostro.search_base import LogicalGroupResource
from valet.engine.optimizer.ostro.search_base import Node
from valet.engine.optimizer.ostro.search_base import Resource
from valet.engine.resource_manager.resource_base import Datacenter

LOG = log.getLogger(__name__)


class Search(object):
    '''A bin-packing with maximal consolidation approach '''

    def __init__(self):
        """Initialization."""

        # search inputs
        self.resource = None
        self.app_topology = None

        # snapshot of current resource status
        self.avail_hosts = {}
        self.avail_logical_groups = {}

        # search results
        self.node_placements = {}
        self.num_of_hosts = 0

        # for replan
        self.planned_placements = {}

        # optimization criteria
        self.CPU_weight = -1
        self.mem_weight = -1
        self.local_disk_weight = -1

        self.constraint_solver = None

        self.status = "success"

    def _init_placements(self):
        self.avail_hosts.clear()
        self.avail_logical_groups.clear()

        self.node_placements.clear()
        self.num_of_hosts = 0

        self.planned_placements.clear()

        self.CPU_weight = -1
        self.mem_weight = -1
        self.local_disk_weight = -1

    def copy_resource_status(self, _resource):
        """Copy the resource status."""
        self._init_placements()

        self.resource = _resource

        self._create_avail_logical_groups()
        self._create_avail_hosts()

    def place_nodes(self, _app_topology, _resource):
        """Place nodes."""
        """Copy the resource status and utilize the constraint solver
        to place nodes based on the app topology."""
        self._init_placements()

        self.app_topology = _app_topology

        # ping request
        if self.app_topology.optimization_priority is None:
            return True

        self.resource = _resource

        self.constraint_solver = ConstraintSolver()

        LOG.info("start search")

        self._create_avail_logical_groups()
        self._create_avail_hosts()

        self._compute_resource_weights()

        init_level = LEVELS[len(LEVELS) - 1]
        (open_node_list, level) = self._open_list(self.app_topology.vms,
                                                  self.app_topology.vgroups,
                                                  init_level)

        # start from 'rack' level
        return self._run_greedy(open_node_list, level, self.avail_hosts)

    def re_place_nodes(self, _app_topology, _resource):
        """Re-place nodes."""
        """Copy the resource status and utilize the constraint solver
        to re-place nodes based on the app topology."""
        self._init_placements()

        self.app_topology = _app_topology
        self.resource = _resource

        self.constraint_solver = ConstraintSolver()

        LOG.info("start search for replan")

        self._create_avail_logical_groups()
        self._create_avail_hosts()

        if len(self.app_topology.old_vm_map) > 0:
            self._adjust_resources()

        self._compute_resource_weights()

        LOG.info("first, place already-planned nodes")

        # reconsider all vms to be migrated together
        if len(_app_topology.exclusion_list_map) > 0:
            self._set_no_migrated_list()

        if self._place_planned_nodes() is False:
            self.status = "cannot replan VMs that was planned"
            LOG.error(self.status)
            return False

        LOG.info("second, re-place not-planned nodes")

        init_level = LEVELS[len(LEVELS) - 1]
        (open_node_list, level) = self._open_list(self.app_topology.vms,
                                                  self.app_topology.vgroups,
                                                  init_level)
        if open_node_list is None:
            LOG.error("fail to replan")
            return False

        for v, ah in self.planned_placements.iteritems():
            self.node_placements[v] = ah

        return self._run_greedy(open_node_list, level, self.avail_hosts)

    def _set_no_migrated_list(self):
        migrated_vm_id = self.app_topology.candidate_list_map.keys()[0]

        if migrated_vm_id not in self.app_topology.vms.keys():
            vgroup = self._get_vgroup_of_vm(migrated_vm_id,
                                            self.app_topology.vgroups)
            if vgroup is not None:
                vm_list = []
                self._get_child_vms(vgroup, vm_list, migrated_vm_id)
                for vk in vm_list:
                    if vk in self.app_topology.planned_vm_map.keys():
                        del self.app_topology.planned_vm_map[vk]
            else:
                LOG.error("Search: migrated " + migrated_vm_id +
                          " is missing while replan")

    def _get_child_vms(self, _g, _vm_list, _e_vmk):
        for sgk, sg in _g.subvgroups.iteritems():
            if isinstance(sg, VM):
                if sgk != _e_vmk:
                    _vm_list.append(sgk)
            else:
                self._get_child_vms(sg, _vm_list, _e_vmk)

    def _place_planned_nodes(self):
        init_level = LEVELS[len(LEVELS) - 1]
        (planned_node_list, level) = self._open_planned_list(
            self.app_topology.vms, self.app_topology.vgroups, init_level)
        if len(planned_node_list) == 0:
            return True

        return self._run_greedy_as_planned(planned_node_list, level,
                                           self.avail_hosts)

    def _open_planned_list(self, _vms, _vgroups, _current_level):
        planned_node_list = []
        next_level = None

        for vmk, hk in self.app_topology.planned_vm_map.iteritems():
            if vmk in _vms.keys():
                vm = _vms[vmk]
                if vm.host is None:
                    vm.host = []
                if hk not in vm.host:
                    vm.host.append(hk)
                n = Node()
                n.node = vm
                n.sort_base = self._set_virtual_capacity_based_sort(vm)
                planned_node_list.append(n)
            else:
                vgroup = self._get_vgroup_of_vm(vmk, _vgroups)
                if vgroup is not None:
                    if vgroup.host is None:
                        vgroup.host = []
                    host_name = self._get_host_of_vgroup(hk, vgroup.level)
                    if host_name is None:
                        LOG.warning("Search: host does not exist while "
                                    "replan with vgroup")
                    else:
                        if host_name not in vgroup.host:
                            vgroup.host.append(host_name)
                        node = None
                        for n in planned_node_list:
                            if n.node.uuid == vgroup.uuid:
                                node = n
                                break
                        if node is None:
                            n = Node()
                            n.node = vgroup
                            n.sort_base = \
                                self._set_virtual_capacity_based_sort(vgroup)
                            planned_node_list.append(n)

        current_level_index = LEVELS.index(_current_level)
        next_level_index = current_level_index - 1
        if next_level_index < 0:
            next_level = LEVELS[0]
        else:
            next_level = LEVELS[next_level_index]

        return (planned_node_list, next_level)

    def _get_vgroup_of_vm(self, _vmk, _vgroups):
        vgroup = None

        for _, g in _vgroups.iteritems():
            if self._check_vm_grouping(g, _vmk) is True:
                vgroup = g
                break

        return vgroup

    def _check_vm_grouping(self, _g, _vmk):
        exist = False

        for sgk, sg in _g.subvgroups.iteritems():
            if isinstance(sg, VM):
                if sgk == _vmk:
                    exist = True
                    break
            elif isinstance(sg, VGroup):
                if self._check_vm_grouping(sg, _vmk) is True:
                    exist = True
                    break

        return exist

    def _get_host_of_vgroup(self, _host, _level):
        host = None

        if _level == "host":
            host = _host
        elif _level == "rack":
            if _host in self.avail_hosts.keys():
                host = self.avail_hosts[_host].rack_name
        elif _level == "cluster":
            if _host in self.avail_hosts.keys():
                host = self.avail_hosts[_host].cluster_name

        return host

    def _run_greedy_as_planned(self, _node_list, _level, _avail_hosts):
        avail_resources = {}
        if _level == "cluster":
            for _, h in _avail_hosts.iteritems():
                if h.cluster_name not in avail_resources.keys():
                    avail_resources[h.cluster_name] = h
        elif _level == "rack":
            for _, h in _avail_hosts.iteritems():
                if h.rack_name not in avail_resources.keys():
                    avail_resources[h.rack_name] = h
        elif _level == "host":
            avail_resources = _avail_hosts

        _node_list.sort(key=operator.attrgetter("sort_base"), reverse=True)

        while len(_node_list) > 0:
            n = _node_list.pop(0)

            best_resource = self._get_best_resource_for_planned(
                n, _level, avail_resources)
            if best_resource is not None:
                self._deduct_reservation(_level, best_resource, n)
                self._close_planned_placement(_level, best_resource, n.node)
            else:
                LOG.error("fail to place already-planned VMs")
                return False

        return True

    def _get_best_resource_for_planned(self, _n, _level, _avail_resources):
        best_resource = None

        if _level == "host" and isinstance(_n.node, VM):
            best_resource = copy.deepcopy(_avail_resources[_n.node.host[0]])
            best_resource.level = "host"
        else:
            vms = {}
            vgroups = {}
            if isinstance(_n.node, VGroup):
                if LEVELS.index(_n.node.level) < LEVELS.index(_level):
                    vgroups[_n.node.uuid] = _n.node
                else:
                    for _, sg in _n.node.subvgroups.iteritems():
                        if isinstance(sg, VM):
                            vms[sg.uuid] = sg
                        elif isinstance(sg, VGroup):
                            vgroups[sg.uuid] = sg
            else:
                vms[_n.node.uuid] = _n.node

            (planned_node_list, level) = self._open_planned_list(
                vms, vgroups, _level)

            host_name = self._get_host_of_level(_n, _level)
            if host_name is None:
                LOG.warning("cannot find host while replanning")
                return None

            avail_hosts = {}
            for hk, h in self.avail_hosts.iteritems():
                if _level == "cluster":
                    if h.cluster_name == host_name:
                        avail_hosts[hk] = h
                elif _level == "rack":
                    if h.rack_name == host_name:
                        avail_hosts[hk] = h
                elif _level == "host":
                    if h.host_name == host_name:
                        avail_hosts[hk] = h

            if self._run_greedy_as_planned(planned_node_list, level,
                                           avail_hosts) is True:
                best_resource = copy.deepcopy(_avail_resources[host_name])
                best_resource.level = _level

        return best_resource

    def _get_host_of_level(self, _n, _level):
        host_name = None

        if isinstance(_n.node, VM):
            host_name = self._get_host_of_vgroup(_n.node.host[0], _level)
        elif isinstance(_n.node, VGroup):
            if _n.node.level == "host":
                host_name = self._get_host_of_vgroup(_n.node.host[0], _level)
            elif _n.node.level == "rack":
                if _level == "rack":
                    host_name = _n.node.host[0]
                elif _level == "cluster":
                    for _, ah in self.avail_hosts.iteritems():
                        if ah.rack_name == _n.node.host[0]:
                            host_name = ah.cluster_name
                            break
            elif _n.node.level == "cluster":
                if _level == "cluster":
                    host_name = _n.node.host[0]

        return host_name

    def _close_planned_placement(self, _level, _best, _v):
        if _v not in self.planned_placements.keys():
            if _level == "host" or isinstance(_v, VGroup):
                self.planned_placements[_v] = _best

    def _create_avail_hosts(self):
        for hk, host in self.resource.hosts.iteritems():

            if host.check_availability() is False:
                LOG.debug("Search: host (" + host.name +
                          ") not available at this time")
                continue

            r = Resource()
            r.host_name = hk

            for mk in host.memberships.keys():
                if mk in self.avail_logical_groups.keys():
                    r.host_memberships[mk] = self.avail_logical_groups[mk]

            r.host_vCPUs = host.original_vCPUs
            r.host_avail_vCPUs = host.avail_vCPUs
            r.host_mem = host.original_mem_cap
            r.host_avail_mem = host.avail_mem_cap
            r.host_local_disk = host.original_local_disk_cap
            r.host_avail_local_disk = host.avail_local_disk_cap

            r.host_num_of_placed_vms = len(host.vm_list)

            rack = host.host_group
            if isinstance(rack, Datacenter):
                r.rack_name = "any"
                r.cluster_name = "any"
            else:
                if rack.status != "enabled":
                    continue

                r.rack_name = rack.name

                for mk in rack.memberships.keys():
                    if mk in self.avail_logical_groups.keys():
                        r.rack_memberships[mk] = self.avail_logical_groups[mk]

                r.rack_vCPUs = rack.original_vCPUs
                r.rack_avail_vCPUs = rack.avail_vCPUs
                r.rack_mem = rack.original_mem_cap
                r.rack_avail_mem = rack.avail_mem_cap
                r.rack_local_disk = rack.original_local_disk_cap
                r.rack_avail_local_disk = rack.avail_local_disk_cap

                r.rack_num_of_placed_vms = len(rack.vm_list)

                cluster = rack.parent_resource
                if isinstance(cluster, Datacenter):
                    r.cluster_name = "any"
                else:
                    if cluster.status != "enabled":
                        continue

                    r.cluster_name = cluster.name

                    for mk in cluster.memberships.keys():
                        if mk in self.avail_logical_groups.keys():
                            r.cluster_memberships[mk] = \
                                self.avail_logical_groups[mk]

                    r.cluster_vCPUs = cluster.original_vCPUs
                    r.cluster_avail_vCPUs = cluster.avail_vCPUs
                    r.cluster_mem = cluster.original_mem_cap
                    r.cluster_avail_mem = cluster.avail_mem_cap
                    r.cluster_local_disk = cluster.original_local_disk_cap
                    r.cluster_avail_local_disk = cluster.avail_local_disk_cap

                    r.cluster_num_of_placed_vms = len(cluster.vm_list)

            if r.host_num_of_placed_vms > 0:
                self.num_of_hosts += 1

            self.avail_hosts[hk] = r

    def _create_avail_logical_groups(self):
        for lgk, lg in self.resource.logical_groups.iteritems():

            if lg.status != "enabled":
                LOG.warning("group (" + lg.name + ") disabled")
                continue

            lgr = LogicalGroupResource()
            lgr.name = lgk
            lgr.group_type = lg.group_type

            for mk, mv in lg.metadata.iteritems():
                lgr.metadata[mk] = mv

            lgr.num_of_placed_vms = len(lg.vm_list)
            for hk in lg.vms_per_host.keys():
                lgr.num_of_placed_vms_per_host[hk] = len(lg.vms_per_host[hk])

            for hk in lg.vms_per_host.keys():
                if hk in self.resource.hosts.keys():
                    host = self.resource.hosts[hk]
                    if host.check_availability() is False:
                        for vm_id in host.vm_list:
                            if lg.exist_vm_by_uuid(vm_id[2]) is True:
                                lgr.num_of_placed_vms -= 1
                        if hk in lgr.num_of_placed_vms_per_host.keys():
                            del lgr.num_of_placed_vms_per_host[hk]
                elif hk in self.resource.host_groups.keys():
                    host_group = self.resource.host_groups[hk]
                    if host_group.check_availability() is False:
                        for vm_id in host_group.vm_list:
                            if lg.exist_vm_by_uuid(vm_id[2]) is True:
                                lgr.num_of_placed_vms -= 1
                        if hk in lgr.num_of_placed_vms_per_host.keys():
                            del lgr.num_of_placed_vms_per_host[hk]

            self.avail_logical_groups[lgk] = lgr

    def _adjust_resources(self):
        for h_uuid, info in self.app_topology.old_vm_map.iteritems():
            # info = (host, cpu, mem, disk)
            if info[0] not in self.avail_hosts.keys():
                continue

            r = self.avail_hosts[info[0]]

            r.host_num_of_placed_vms -= 1
            r.host_avail_vCPUs += info[1]
            r.host_avail_mem += info[2]
            r.host_avail_local_disk += info[3]

            if r.host_num_of_placed_vms == 0:
                self.num_of_hosts -= 1

            for _, rr in self.avail_hosts.iteritems():
                if rr.rack_name != "any" and rr.rack_name == r.rack_name:
                    rr.rack_num_of_placed_vms -= 1
                    rr.rack_avail_vCPUs += info[1]
                    rr.rack_avail_mem += info[2]
                    rr.rack_avail_local_disk += info[3]

            for _, cr in self.avail_hosts.iteritems():
                if cr.cluster_name != "any" and \
                        cr.cluster_name == r.cluster_name:
                    cr.cluster_num_of_placed_vms -= 1
                    cr.cluster_avail_vCPUs += info[1]
                    cr.cluster_avail_mem += info[2]
                    cr.cluster_avail_local_disk += info[3]

            for lgk in r.host_memberships.keys():
                if lgk not in self.avail_logical_groups.keys():
                    continue
                if lgk not in self.resource.logical_groups.keys():
                    continue
                lg = self.resource.logical_groups[lgk]
                if lg.exist_vm_by_h_uuid(h_uuid) is True:
                    lgr = r.host_memberships[lgk]
                    lgr.num_of_placed_vms -= 1
                    if r.host_name in lgr.num_of_placed_vms_per_host.keys():
                        num_placed_vm = lgr.num_of_placed_vms_per_host
                        lgr.num_of_placed_vms_per_host[r.host_name] -= 1
                        if lgr.group_type == "EX" or \
                                lgr.group_type == "AFF" or \
                                lgr.group_type == "DIV":
                            if num_placed_vm[r.host_name] == 0:
                                del lgr.num_of_placed_vms_per_host[r.host_name]
                                del r.host_memberships[lgk]
                    if lgr.group_type == "EX" or lgr.group_type == "AFF" or \
                            lgr.group_type == "DIV":
                        if lgr.num_of_placed_vms == 0:
                            del self.avail_logical_groups[lgk]

            for lgk in r.rack_memberships.keys():
                if lgk not in self.avail_logical_groups.keys():
                    continue
                if lgk not in self.resource.logical_groups.keys():
                    continue
                lg = self.resource.logical_groups[lgk]
                if lg.group_type == "EX" or lg.group_type == "AFF" or \
                        lg.group_type == "DIV":
                    if lgk.split(":")[0] == "rack":
                        if lg.exist_vm_by_h_uuid(h_uuid) is True:
                            lgr = r.rack_memberships[lgk]
                            lgr.num_of_placed_vms -= 1
                            vms_placed = lgr.num_of_placed_vms_per_host
                            if r.rack_name in vms_placed.keys():
                                vms_placed[r.rack_name] -= 1
                                if vms_placed[r.rack_name] == 0:
                                    del vms_placed[r.rack_name]
                                    for _, rr in self.avail_hosts.iteritems():
                                        if rr.rack_name != "any" and \
                                                rr.rack_name == \
                                                r.rack_name:
                                            del rr.rack_memberships[lgk]
                            if lgr.num_of_placed_vms == 0:
                                del self.avail_logical_groups[lgk]

            for lgk in r.cluster_memberships.keys():
                if lgk not in self.avail_logical_groups.keys():
                    continue
                if lgk not in self.resource.logical_groups.keys():
                    continue
                lg = self.resource.logical_groups[lgk]
                if lg.group_type == "EX" or lg.group_type == "AFF" or \
                        lg.group_type == "DIV":
                    if lgk.split(":")[0] == "cluster":
                        if lg.exist_vm_by_h_uuid(h_uuid) is True:
                            lgr = r.cluster_memberships[lgk]
                            lgr.num_of_placed_vms -= 1
                            if r.cluster_name in \
                                    lgr.num_of_placed_vms_per_host.keys():
                                lgr.num_of_placed_vms_per_host[
                                    r.cluster_name
                                ] -= 1
                                if lgr.num_of_placed_vms_per_host[
                                    r.cluster_name
                                ] == 0:
                                    del lgr.num_of_placed_vms_per_host[
                                        r.cluster_name
                                    ]
                                    for _, cr in self.avail_hosts.iteritems():
                                        if cr.cluster_name != "any" and \
                                                cr.cluster_name == \
                                                r.cluster_name:
                                            del cr.cluster_memberships[lgk]
                            if lgr.num_of_placed_vms == 0:
                                del self.avail_logical_groups[lgk]

    def _compute_resource_weights(self):
        denominator = 0.0
        for (t, w) in self.app_topology.optimization_priority:
            denominator += w

        for (t, w) in self.app_topology.optimization_priority:
            if t == "cpu":
                self.CPU_weight = float(w / denominator)
            elif t == "mem":
                self.mem_weight = float(w / denominator)
            elif t == "lvol":
                self.local_disk_weight = float(w / denominator)

    def _open_list(self, _vms, _vgroups, _current_level):
        open_node_list = []
        next_level = None

        for _, vm in _vms.iteritems():
            n = Node()
            n.node = vm
            n.sort_base = self._set_virtual_capacity_based_sort(vm)
            open_node_list.append(n)

        for _, g in _vgroups.iteritems():
            n = Node()
            n.node = g
            n.sort_base = self._set_virtual_capacity_based_sort(g)
            open_node_list.append(n)

        current_level_index = LEVELS.index(_current_level)
        next_level_index = current_level_index - 1
        if next_level_index < 0:
            next_level = LEVELS[0]
        else:
            next_level = LEVELS[next_level_index]

        return (open_node_list, next_level)

    def _set_virtual_capacity_based_sort(self, _v):
        sort_base = -1

        sort_base = self.CPU_weight * _v.vCPU_weight
        sort_base += self.mem_weight * _v.mem_weight
        sort_base += self.local_disk_weight * _v.local_volume_weight

        return sort_base

    def _run_greedy(self, _open_node_list, _level, _avail_hosts):
        success = True

        avail_resources = {}
        if _level == "cluster":
            for _, h in _avail_hosts.iteritems():
                if h.cluster_name not in avail_resources.keys():
                    avail_resources[h.cluster_name] = h
        elif _level == "rack":
            for _, h in _avail_hosts.iteritems():
                if h.rack_name not in avail_resources.keys():
                    avail_resources[h.rack_name] = h
        elif _level == "host":
            avail_resources = _avail_hosts

        _open_node_list.sort(
            key=operator.attrgetter("sort_base"), reverse=True)

        while len(_open_node_list) > 0:
            n = _open_node_list.pop(0)

            best_resource = self._get_best_resource(n, _level, avail_resources)
            if best_resource is None:
                success = False
                break

            if n.node not in self.planned_placements.keys():
                # for VM under host level only
                self._deduct_reservation(_level, best_resource, n)
                # close all types of nodes under any level, but VM
                # with above host level
                self._close_node_placement(_level, best_resource, n.node)

        return success

    def _get_best_resource(self, _n, _level, _avail_resources):
        # already planned vgroup
        planned_host = None
        if _n.node in self.planned_placements.keys():
            copied_host = self.planned_placements[_n.node]
            if _level == "host":
                planned_host = _avail_resources[copied_host.host_name]
            elif _level == "rack":
                planned_host = _avail_resources[copied_host.rack_name]
            elif _level == "cluster":
                planned_host = _avail_resources[copied_host.cluster_name]
        else:
            if len(self.app_topology.candidate_list_map) > 0:
                conflicted_vm_uuid = \
                    self.app_topology.candidate_list_map.keys()[0]
                candidate_name_list = \
                    self.app_topology.candidate_list_map[conflicted_vm_uuid]
                if (isinstance(_n.node, VM) and
                        conflicted_vm_uuid == _n.node.uuid) or \
                   (isinstance(_n.node, VGroup) and
                        self._check_vm_grouping(
                            _n.node, conflicted_vm_uuid) is True):
                    host_list = []
                    for hk in candidate_name_list:
                        host_name = self._get_host_of_vgroup(hk, _level)
                        if host_name is not None:
                            if host_name not in host_list:
                                host_list.append(host_name)
                        else:
                            LOG.warning("Search: cannot find candidate "
                                        "host while replanning")
                    _n.node.host = host_list

        candidate_list = []
        if planned_host is not None:
            candidate_list.append(planned_host)
        else:
            candidate_list = self.constraint_solver.compute_candidate_list(
                _level, _n, self.node_placements, _avail_resources,
                self.avail_logical_groups)
        if len(candidate_list) == 0:
            self.status = self.constraint_solver.status
            return None

        self._set_compute_sort_base(_level, candidate_list)
        candidate_list.sort(key=operator.attrgetter("sort_base"))

        best_resource = None
        if _level == "host" and isinstance(_n.node, VM):
            best_resource = copy.deepcopy(candidate_list[0])
            best_resource.level = "host"
        else:
            while len(candidate_list) > 0:
                cr = candidate_list.pop(0)

                vms = {}
                vgroups = {}
                if isinstance(_n.node, VGroup):
                    if LEVELS.index(_n.node.level) < LEVELS.index(_level):
                        vgroups[_n.node.uuid] = _n.node
                    else:
                        for _, sg in _n.node.subvgroups.iteritems():
                            if isinstance(sg, VM):
                                vms[sg.uuid] = sg
                            elif isinstance(sg, VGroup):
                                vgroups[sg.uuid] = sg
                else:
                    vms[_n.node.uuid] = _n.node

                (open_node_list, level) = self._open_list(vms, vgroups, _level)
                if open_node_list is None:
                    break

                avail_hosts = {}
                for hk, h in self.avail_hosts.iteritems():
                    if _level == "cluster":
                        if h.cluster_name == cr.cluster_name:
                            avail_hosts[hk] = h
                    elif _level == "rack":
                        if h.rack_name == cr.rack_name:
                            avail_hosts[hk] = h
                    elif _level == "host":
                        if h.host_name == cr.host_name:
                            avail_hosts[hk] = h

                # recursive call
                if self._run_greedy(open_node_list, level, avail_hosts):
                    best_resource = copy.deepcopy(cr)
                    best_resource.level = _level
                    break
                else:
                    debug_candidate_name = cr.get_resource_name(_level)
                    msg = "rollback of candidate resource = {0}"
                    LOG.warning(msg.format(debug_candidate_name))

                    if planned_host is None:
                        # recursively rollback deductions of all
                        # child VMs of _n
                        self._rollback_reservation(_n.node)
                        # recursively rollback closing
                        self._rollback_node_placement(_n.node)
                    else:
                        break

        if best_resource is None and len(candidate_list) == 0:
            self.status = "no available hosts"
            LOG.warning(self.status)

        return best_resource

    def _set_compute_sort_base(self, _level, _candidate_list):
        for c in _candidate_list:
            CPU_ratio = -1
            mem_ratio = -1
            local_disk_ratio = -1
            if _level == "cluster":
                CPU_ratio = float(c.cluster_avail_vCPUs) / \
                    float(self.resource.CPU_avail)
                mem_ratio = float(c.cluster_avail_mem) / \
                    float(self.resource.mem_avail)
                local_disk_ratio = float(c.cluster_avail_local_disk) / \
                    float(self.resource.local_disk_avail)
            elif _level == "rack":
                CPU_ratio = float(c.rack_avail_vCPUs) / \
                    float(self.resource.CPU_avail)
                mem_ratio = float(c.rack_avail_mem) / \
                    float(self.resource.mem_avail)
                local_disk_ratio = float(c.rack_avail_local_disk) / \
                    float(self.resource.local_disk_avail)
            elif _level == "host":
                CPU_ratio = float(c.host_avail_vCPUs) / \
                    float(self.resource.CPU_avail)
                mem_ratio = float(c.host_avail_mem) / \
                    float(self.resource.mem_avail)
                local_disk_ratio = float(c.host_avail_local_disk) / \
                    float(self.resource.local_disk_avail)
            c.sort_base = (1.0 - self.CPU_weight) * CPU_ratio + \
                          (1.0 - self.mem_weight) * mem_ratio + \
                          (1.0 - self.local_disk_weight) * local_disk_ratio

    """
    Deduction modules.
    """
    def _deduct_reservation(self, _level, _best, _n):
        exclusivities = self.constraint_solver.get_exclusivities(
            _n.node.exclusivity_groups, _level)
        exclusivity_id = None
        if len(exclusivities) == 1:
            exclusivity_id = exclusivities[exclusivities.keys()[0]]
        if exclusivity_id is not None:
            self._add_exclusivity(_level, _best, exclusivity_id)

        affinity_id = _n.get_affinity_id()
        if affinity_id is not None and affinity_id.split(":")[1] != "any":
            self._add_affinity(_level, _best, affinity_id)

        if len(_n.node.diversity_groups) > 0:
            for _, diversity_id in _n.node.diversity_groups.iteritems():
                if diversity_id.split(":")[1] != "any":
                    self._add_diversities(_level, _best, diversity_id)

        if isinstance(_n.node, VM) and _level == "host":
            self._deduct_vm_resources(_best, _n)

    def _add_exclusivity(self, _level, _best, _exclusivity_id):
        lgr = None
        if _exclusivity_id not in self.avail_logical_groups.keys():
            lgr = LogicalGroupResource()
            lgr.name = _exclusivity_id
            lgr.group_type = "EX"
            self.avail_logical_groups[lgr.name] = lgr

            LOG.info(
                "Search: add new exclusivity (%s)" % _exclusivity_id)

        else:
            lgr = self.avail_logical_groups[_exclusivity_id]

        if _exclusivity_id.split(":")[0] == _level:
            lgr.num_of_placed_vms += 1

            host_name = _best.get_resource_name(_level)
            if host_name not in lgr.num_of_placed_vms_per_host.keys():
                lgr.num_of_placed_vms_per_host[host_name] = 0
            lgr.num_of_placed_vms_per_host[host_name] += 1

            chosen_host = self.avail_hosts[_best.host_name]
            if _level == "host":
                if _exclusivity_id not in chosen_host.host_memberships.keys():
                    chosen_host.host_memberships[_exclusivity_id] = lgr
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.rack_name != "any" and \
                            np.rack_name == chosen_host.rack_name:
                        if _exclusivity_id not in np.rack_memberships.keys():
                            np.rack_memberships[_exclusivity_id] = lgr
                    if chosen_host.cluster_name != "any" and \
                            np.cluster_name == chosen_host.cluster_name:
                        if (_exclusivity_id not in
                                np.cluster_memberships.keys()):
                            np.cluster_memberships[_exclusivity_id] = lgr
            elif _level == "rack":
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.rack_name != "any" and \
                            np.rack_name == chosen_host.rack_name:
                        if _exclusivity_id not in np.rack_memberships.keys():
                            np.rack_memberships[_exclusivity_id] = lgr
                    if chosen_host.cluster_name != "any" and \
                            np.cluster_name == chosen_host.cluster_name:
                        if (_exclusivity_id not in
                                np.cluster_memberships.keys()):
                            np.cluster_memberships[_exclusivity_id] = lgr
            elif _level == "cluster":
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.cluster_name != "any" and \
                            np.cluster_name == chosen_host.cluster_name:
                        if (_exclusivity_id not in
                                np.cluster_memberships.keys()):
                            np.cluster_memberships[_exclusivity_id] = lgr

    def _add_affinity(self, _level, _best, _affinity_id):
        lgr = None
        if _affinity_id not in self.avail_logical_groups.keys():
            lgr = LogicalGroupResource()
            lgr.name = _affinity_id
            lgr.group_type = "AFF"
            self.avail_logical_groups[lgr.name] = lgr

            LOG.info("add new affinity (" + _affinity_id + ")")
        else:
            lgr = self.avail_logical_groups[_affinity_id]

        if _affinity_id.split(":")[0] == _level:
            lgr.num_of_placed_vms += 1

            host_name = _best.get_resource_name(_level)
            if host_name not in lgr.num_of_placed_vms_per_host.keys():
                lgr.num_of_placed_vms_per_host[host_name] = 0
            lgr.num_of_placed_vms_per_host[host_name] += 1

            chosen_host = self.avail_hosts[_best.host_name]
            if _level == "host":
                if _affinity_id not in chosen_host.host_memberships.keys():
                    chosen_host.host_memberships[_affinity_id] = lgr
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.rack_name != "any" and \
                            np.rack_name == chosen_host.rack_name:
                        if _affinity_id not in np.rack_memberships.keys():
                            np.rack_memberships[_affinity_id] = lgr
                    if chosen_host.cluster_name != "any" and \
                            np.cluster_name == chosen_host.cluster_name:
                        if _affinity_id not in np.cluster_memberships.keys():
                            np.cluster_memberships[_affinity_id] = lgr
            elif _level == "rack":
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.rack_name != "any" and \
                            np.rack_name == chosen_host.rack_name:
                        if _affinity_id not in np.rack_memberships.keys():
                            np.rack_memberships[_affinity_id] = lgr
                    if chosen_host.cluster_name != "any" and \
                            np.cluster_name == chosen_host.cluster_name:
                        if _affinity_id not in np.cluster_memberships.keys():
                            np.cluster_memberships[_affinity_id] = lgr
            elif _level == "cluster":
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.cluster_name != "any" and \
                            np.cluster_name == chosen_host.cluster_name:
                        if _affinity_id not in np.cluster_memberships.keys():
                            np.cluster_memberships[_affinity_id] = lgr

    def _add_diversities(self, _level, _best, _diversity_id):
        lgr = None
        if _diversity_id not in self.avail_logical_groups.keys():
            lgr = LogicalGroupResource()
            lgr.name = _diversity_id
            lgr.group_type = "DIV"
            self.avail_logical_groups[lgr.name] = lgr

            LOG.info(
                "Search: add new diversity (%s)", _diversity_id)
        else:
            lgr = self.avail_logical_groups[_diversity_id]

        if _diversity_id.split(":")[0] == _level:
            lgr.num_of_placed_vms += 1

            host_name = _best.get_resource_name(_level)
            if host_name not in lgr.num_of_placed_vms_per_host.keys():
                lgr.num_of_placed_vms_per_host[host_name] = 0
            lgr.num_of_placed_vms_per_host[host_name] += 1

            chosen_host = self.avail_hosts[_best.host_name]
            if _level == "host":
                if _diversity_id not in chosen_host.host_memberships.keys():
                    chosen_host.host_memberships[_diversity_id] = lgr
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.rack_name != "any" and \
                            np.rack_name == chosen_host.rack_name:
                        if _diversity_id not in np.rack_memberships.keys():
                            np.rack_memberships[_diversity_id] = lgr
                    if chosen_host.cluster_name != "any" and \
                            np.cluster_name == chosen_host.cluster_name:
                        if _diversity_id not in np.cluster_memberships.keys():
                            np.cluster_memberships[_diversity_id] = lgr
            elif _level == "rack":
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.rack_name != "any" and \
                            np.rack_name == chosen_host.rack_name:
                        if _diversity_id not in np.rack_memberships.keys():
                            np.rack_memberships[_diversity_id] = lgr
                    if chosen_host.cluster_name != "any" and \
                            np.cluster_name == chosen_host.cluster_name:
                        if _diversity_id not in np.cluster_memberships.keys():
                            np.cluster_memberships[_diversity_id] = lgr
            elif _level == "cluster":
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.cluster_name != "any" and \
                            np.cluster_name == chosen_host.cluster_name:
                        if _diversity_id not in np.cluster_memberships.keys():
                            np.cluster_memberships[_diversity_id] = lgr

    def _deduct_vm_resources(self, _best, _n):
        chosen_host = self.avail_hosts[_best.host_name]
        chosen_host.host_avail_vCPUs -= _n.node.vCPUs
        chosen_host.host_avail_mem -= _n.node.mem
        chosen_host.host_avail_local_disk -= _n.node.local_volume_size

        if chosen_host.host_num_of_placed_vms == 0:
            self.num_of_hosts += 1
        chosen_host.host_num_of_placed_vms += 1

        for _, np in self.avail_hosts.iteritems():
            if chosen_host.rack_name != "any" and \
                    np.rack_name == chosen_host.rack_name:
                np.rack_avail_vCPUs -= _n.node.vCPUs
                np.rack_avail_mem -= _n.node.mem
                np.rack_avail_local_disk -= _n.node.local_volume_size
                np.rack_num_of_placed_vms += 1
            if chosen_host.cluster_name != "any" and \
                    np.cluster_name == chosen_host.cluster_name:
                np.cluster_avail_vCPUs -= _n.node.vCPUs
                np.cluster_avail_mem -= _n.node.mem
                np.cluster_avail_local_disk -= _n.node.local_volume_size
                np.cluster_num_of_placed_vms += 1

    def _close_node_placement(self, _level, _best, _v):
        if _v not in self.node_placements.keys():
            if _level == "host" or isinstance(_v, VGroup):
                self.node_placements[_v] = _best

    """
    Rollback modules.
    """

    def _rollback_reservation(self, _v):
        if isinstance(_v, VM):
            self._rollback_vm_reservation(_v)

        elif isinstance(_v, VGroup):
            for _, v in _v.subvgroups.iteritems():
                self._rollback_reservation(v)

        if _v in self.node_placements.keys():
            chosen_host = self.avail_hosts[self.node_placements[_v].host_name]
            level = self.node_placements[_v].level

            if isinstance(_v, VGroup):
                affinity_id = _v.level + ":" + _v.name
                if _v.name != "any":
                    self._remove_affinity(chosen_host, affinity_id, level)

            exclusivities = self.constraint_solver.get_exclusivities(
                _v.exclusivity_groups, level)
            if len(exclusivities) == 1:
                exclusivity_id = exclusivities[exclusivities.keys()[0]]
                self._remove_exclusivity(chosen_host, exclusivity_id, level)

            if len(_v.diversity_groups) > 0:
                for _, diversity_id in _v.diversity_groups.iteritems():
                    if diversity_id.split(":")[1] != "any":
                        self._remove_diversities(
                            chosen_host, diversity_id, level)

    def _remove_exclusivity(self, _chosen_host, _exclusivity_id, _level):
        if _exclusivity_id.split(":")[0] == _level:
            lgr = self.avail_logical_groups[_exclusivity_id]

            host_name = _chosen_host.get_resource_name(_level)
            lgr.num_of_placed_vms -= 1
            lgr.num_of_placed_vms_per_host[host_name] -= 1

            if lgr.num_of_placed_vms_per_host[host_name] == 0:
                del lgr.num_of_placed_vms_per_host[host_name]

            if lgr.num_of_placed_vms == 0:
                del self.avail_logical_groups[_exclusivity_id]

            if _level == "host":
                if _chosen_host.host_num_of_placed_vms == 0 and \
                   _exclusivity_id in _chosen_host.host_memberships.keys():
                    del _chosen_host.host_memberships[_exclusivity_id]

                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.rack_name != "any" and \
                                np.rack_name == _chosen_host.rack_name:
                            if _exclusivity_id in np.rack_memberships.keys():
                                del np.rack_memberships[_exclusivity_id]
                        if _chosen_host.cluster_name != "any" and \
                                np.cluster_name == \
                                _chosen_host.cluster_name:
                            if (_exclusivity_id in
                                    np.cluster_memberships.keys()):
                                del np.cluster_memberships[_exclusivity_id]

            elif _level == "rack":
                if _chosen_host.rack_num_of_placed_vms == 0:
                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.rack_name != "any" and \
                                np.rack_name == _chosen_host.rack_name:
                            if _exclusivity_id in np.rack_memberships.keys():
                                del np.rack_memberships[_exclusivity_id]
                        if _chosen_host.cluster_name != "any" and \
                                np.cluster_name == \
                                _chosen_host.cluster_name:
                            if (_exclusivity_id in
                                    np.cluster_memberships.keys()):
                                del np.cluster_memberships[_exclusivity_id]

            elif _level == "cluster":
                if _chosen_host.cluster_num_of_placed_vms == 0:
                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.cluster_name != "any" and \
                                np.cluster_name == \
                                _chosen_host.cluster_name:
                            if (_exclusivity_id in
                                    np.cluster_memberships.keys()):
                                del np.cluster_memberships[_exclusivity_id]

    def _remove_affinity(self, _chosen_host, _affinity_id, _level):
        if _affinity_id.split(":")[0] == _level:
            lgr = self.avail_logical_groups[_affinity_id]

            host_name = _chosen_host.get_resource_name(_level)
            lgr.num_of_placed_vms -= 1
            lgr.num_of_placed_vms_per_host[host_name] -= 1

            if lgr.num_of_placed_vms_per_host[host_name] == 0:
                del lgr.num_of_placed_vms_per_host[host_name]

            if lgr.num_of_placed_vms == 0:
                del self.avail_logical_groups[_affinity_id]

            exist_affinity = True
            if _affinity_id not in self.avail_logical_groups.keys():
                exist_affinity = False
            else:
                lgr = self.avail_logical_groups[_affinity_id]
                host_name = _chosen_host.get_resource_name(_level)
                if host_name not in lgr.num_of_placed_vms_per_host.keys():
                    exist_affinity = False

            if _level == "host":
                if exist_affinity is False and _affinity_id \
                        in _chosen_host.host_memberships.keys():
                    del _chosen_host.host_memberships[_affinity_id]

                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.rack_name != "any" and \
                                np.rack_name == _chosen_host.rack_name:
                            if _affinity_id in np.rack_memberships.keys():
                                del np.rack_memberships[_affinity_id]
                        if _chosen_host.cluster_name != "any" and \
                                np.cluster_name == \
                                _chosen_host.cluster_name:
                            if _affinity_id in np.cluster_memberships.keys():
                                del np.cluster_memberships[_affinity_id]

            elif _level == "rack":
                if exist_affinity is False:
                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.rack_name != "any" and \
                                np.rack_name == _chosen_host.rack_name:
                            if _affinity_id in np.rack_memberships.keys():
                                del np.rack_memberships[_affinity_id]
                        if _chosen_host.cluster_name != "any" and \
                                np.cluster_name == \
                                _chosen_host.cluster_name:
                            if _affinity_id in np.cluster_memberships.keys():
                                del np.cluster_memberships[_affinity_id]

            elif _level == "cluster":
                if exist_affinity is False:
                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.cluster_name != "any" and \
                                np.cluster_name == \
                                _chosen_host.cluster_name:
                            if _affinity_id in np.cluster_memberships.keys():
                                del np.cluster_memberships[_affinity_id]

    def _remove_diversities(self, _chosen_host, _diversity_id, _level):
        if _diversity_id.split(":")[0] == _level:
            lgr = self.avail_logical_groups[_diversity_id]

            host_name = _chosen_host.get_resource_name(_level)
            lgr.num_of_placed_vms -= 1
            lgr.num_of_placed_vms_per_host[host_name] -= 1

            if lgr.num_of_placed_vms_per_host[host_name] == 0:
                del lgr.num_of_placed_vms_per_host[host_name]

            if lgr.num_of_placed_vms == 0:
                del self.avail_logical_groups[_diversity_id]

            exist_diversity = True
            if _diversity_id not in self.avail_logical_groups.keys():
                exist_diversity = False
            else:
                lgr = self.avail_logical_groups[_diversity_id]
                host_name = _chosen_host.get_resource_name(_level)
                if host_name not in lgr.num_of_placed_vms_per_host.keys():
                    exist_diversity = False

            if _level == "host":
                if exist_diversity is False and _diversity_id \
                        in _chosen_host.host_memberships.keys():
                    del _chosen_host.host_memberships[_diversity_id]

                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.rack_name != "any" and \
                                np.rack_name == _chosen_host.rack_name:
                            if _diversity_id in np.rack_memberships.keys():
                                del np.rack_memberships[_diversity_id]
                        if _chosen_host.cluster_name != "any" and \
                                np.cluster_name == \
                                _chosen_host.cluster_name:
                            if _diversity_id in np.cluster_memberships.keys():
                                del np.cluster_memberships[_diversity_id]

            elif _level == "rack":
                if exist_diversity is False:
                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.rack_name != "any" and \
                                np.rack_name == _chosen_host.rack_name:
                            if _diversity_id in np.rack_memberships.keys():
                                del np.rack_memberships[_diversity_id]
                        if _chosen_host.cluster_name != "any" and \
                                np.cluster_name == \
                                _chosen_host.cluster_name:
                            if _diversity_id in np.cluster_memberships.keys():
                                del np.cluster_memberships[_diversity_id]

            elif _level == "cluster":
                if exist_diversity is False:
                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.cluster_name != "any" and \
                                np.cluster_name == \
                                _chosen_host.cluster_name:
                            if _diversity_id in np.cluster_memberships.keys():
                                del np.cluster_memberships[_diversity_id]

    def _rollback_vm_reservation(self, _v):
        if _v in self.node_placements.keys():
            chosen_host = self.avail_hosts[self.node_placements[_v].host_name]
            chosen_host.host_avail_vCPUs += _v.vCPUs
            chosen_host.host_avail_mem += _v.mem
            chosen_host.host_avail_local_disk += _v.local_volume_size

            chosen_host.host_num_of_placed_vms -= 1
            if chosen_host.host_num_of_placed_vms == 0:
                self.num_of_hosts -= 1

            for _, np in self.avail_hosts.iteritems():
                if chosen_host.rack_name != "any" and \
                        np.rack_name == chosen_host.rack_name:
                    np.rack_avail_vCPUs += _v.vCPUs
                    np.rack_avail_mem += _v.mem
                    np.rack_avail_local_disk += _v.local_volume_size
                    np.rack_num_of_placed_vms -= 1
                if chosen_host.cluster_name != "any" and \
                        np.cluster_name == chosen_host.cluster_name:
                    np.cluster_avail_vCPUs += _v.vCPUs
                    np.cluster_avail_mem += _v.mem
                    np.cluster_avail_local_disk += _v.local_volume_size
                    np.cluster_num_of_placed_vms -= 1

    def _rollback_node_placement(self, _v):
        if _v in self.node_placements.keys():
            del self.node_placements[_v]

        if isinstance(_v, VGroup):
            for _, sg in _v.subvgroups.iteritems():
                self._rollback_node_placement(sg)
