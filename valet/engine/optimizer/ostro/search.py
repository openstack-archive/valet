#!/bin/python

# Modified: Sep. 27, 2016

import copy
import operator

from valet.engine.optimizer.app_manager.app_topology_base import VGroup, VM, Volume, LEVELS
from valet.engine.optimizer.ostro.constraint_solver import ConstraintSolver
from valet.engine.optimizer.ostro.search_base import compute_reservation
from valet.engine.optimizer.ostro.search_base import Node, Resource, LogicalGroupResource
from valet.engine.optimizer.ostro.search_base import SwitchResource, StorageResource
from valet.engine.resource_manager.resource_base import Datacenter


class Search(object):

    def __init__(self, _logger):
        self.logger = _logger

        ''' search inputs '''
        self.resource = None
        self.app_topology = None

        ''' snapshot of current resource status '''
        self.avail_hosts = {}
        self.avail_logical_groups = {}
        self.avail_storage_hosts = {}
        self.avail_switches = {}

        ''' search results '''
        self.node_placements = {}
        self.bandwidth_usage = 0
        self.num_of_hosts = 0

        ''' for replan '''
        self.planned_placements = {}

        ''' optimization criteria '''
        self.nw_bandwidth_weight = -1
        self.CPU_weight = -1
        self.mem_weight = -1
        self.local_disk_weight = -1
        self.disk_weight = -1

        self.constraint_solver = None

        self.status = "success"

    def _init_placements(self):
        self.avail_hosts.clear()
        self.avail_logical_groups.clear()
        self.avail_storage_hosts.clear()
        self.avail_switches.clear()

        self.node_placements.clear()
        self.bandwidth_usage = 0
        self.num_of_hosts = 0

        self.planned_placements.clear()

        self.nw_bandwidth_weight = -1
        self.CPU_weight = -1
        self.mem_weight = -1
        self.local_disk_weight = -1
        self.disk_weight = -1

    def copy_resource_status(self, _resource):
        self._init_placements()

        self.resource = _resource

        self._create_avail_logical_groups()
        self._create_avail_storage_hosts()
        self._create_avail_switches()
        self._create_avail_hosts()

    def place_nodes(self, _app_topology, _resource):
        self._init_placements()

        self.app_topology = _app_topology

        ''' ping request '''
        if self.app_topology.optimization_priority is None:
            return True

        self.resource = _resource

        self.constraint_solver = ConstraintSolver(self.logger)

        self.logger.info("Search: start search")

        self._create_avail_logical_groups()
        self._create_avail_storage_hosts()
        self._create_avail_switches()
        self._create_avail_hosts()

        self._compute_resource_weights()

        init_level = LEVELS[len(LEVELS) - 1]
        (open_node_list, level) = self._open_list(self.app_topology.vms,
                                                  self.app_topology.volumes,
                                                  self.app_topology.vgroups,
                                                  init_level)

        ''' start from 'rack' level '''

        return self._run_greedy(open_node_list, level, self.avail_hosts)

    def re_place_nodes(self, _app_topology, _resource):
        self._init_placements()

        self.app_topology = _app_topology
        self.resource = _resource

        self.constraint_solver = ConstraintSolver(self.logger)

        self.logger.info("Search: start search for replan")

        self._create_avail_logical_groups()
        self._create_avail_storage_hosts()
        self._create_avail_switches()
        self._create_avail_hosts()

        if len(self.app_topology.old_vm_map) > 0:
            self._adjust_resources()
            self.logger.debug("Search: adjust resources by deducting prior placements")

        self._compute_resource_weights()

        self.logger.debug("Search: first, place already-planned nodes")

        ''' reconsider all vms to be migrated together '''
        if len(_app_topology.exclusion_list_map) > 0:
            self._set_no_migrated_list()

        if self._place_planned_nodes() is False:
            self.status = "cannot replan VMs that was planned"
            self.logger.error("Search: " + self.status)
            return False

        self.logger.debug("Search: second, re-place not-planned nodes")

        init_level = LEVELS[len(LEVELS) - 1]
        (open_node_list, level) = self._open_list(self.app_topology.vms,
                                                  self.app_topology.volumes,
                                                  self.app_topology.vgroups,
                                                  init_level)
        if open_node_list is None:
            self.logger.error("Search: fail to replan")
            return False

        for v, ah in self.planned_placements.iteritems():
            self.node_placements[v] = ah

        return self._run_greedy(open_node_list, level, self.avail_hosts)

    def _set_no_migrated_list(self):
        migrated_vm_id = self.app_topology.candidate_list_map.keys()[0]

        if migrated_vm_id not in self.app_topology.vms.keys():
            vgroup = self._get_vgroup_of_vm(migrated_vm_id, self.app_topology.vgroups)
            if vgroup is not None:
                vm_list = []
                self._get_child_vms(vgroup, vm_list, migrated_vm_id)
                for vk in vm_list:
                    if vk in self.app_topology.planned_vm_map.keys():
                        del self.app_topology.planned_vm_map[vk]
            else:
                self.logger.error("Search: migrated " + migrated_vm_id + " is missing while replan")

    def _get_child_vms(self, _g, _vm_list, _e_vmk):
        for sgk, sg in _g.subvgroups.iteritems():
            if isinstance(sg, VM):
                if sgk != _e_vmk:
                    _vm_list.append(sgk)
            else:
                self._get_child_vms(sg, _vm_list, _e_vmk)

    def _place_planned_nodes(self):
        init_level = LEVELS[len(LEVELS) - 1]
        (planned_node_list, level) = self._open_planned_list(self.app_topology.vms,
                                                             self.app_topology.volumes,
                                                             self.app_topology.vgroups,
                                                             init_level)
        if len(planned_node_list) == 0:
            return True

        return self._run_greedy_as_planned(planned_node_list, level, self.avail_hosts)

    def _open_planned_list(self, _vms, _volumes, _vgroups, _current_level):
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

            # NOTE: volumes skip

            else:
                vgroup = self._get_vgroup_of_vm(vmk, _vgroups)
                if vgroup is not None:
                    if vgroup.host is None:
                        vgroup.host = []
                    host_name = self._get_host_of_vgroup(hk, vgroup.level)
                    if host_name is None:
                        self.logger.error("Search: host does not exist while replan with vgroup")
                    else:
                        # if len(vgroup.host) == 0:
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
                            n.sort_base = self._set_virtual_capacity_based_sort(vgroup)
                            planned_node_list.append(n)
                # else:
                #     self.logger.warn("Search: " + vmk + " is missing while replan")

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
        self.logger.debug("Search: level = " + _level)
        for on in _node_list:
            self.logger.debug("    node = {}, value = {}".format(on.node.name, on.sort_base))

        while len(_node_list) > 0:
            n = _node_list.pop(0)
            self.logger.debug("Search: level = " + _level + ", placing node = " + n.node.name)

            best_resource = self._get_best_resource_for_planned(n, _level, avail_resources)
            if best_resource is not None:
                debug_best_resource = best_resource.get_resource_name(_level)
                # elif isinstance(n.node, Volume):
                # debug_best_resource = best_resource.host_name + "@" + best_resource.storage.storage_name
                self.logger.debug("Search: best resource = " + debug_best_resource + " for node = " + n.node.name)

                self._deduct_reservation(_level, best_resource, n)
                self._close_planned_placement(_level, best_resource, n.node)
            else:
                self.logger.error("Search: fail to place already-planned VMs")
                return False

        return True

    def _get_best_resource_for_planned(self, _n, _level, _avail_resources):
        best_resource = None

        if _level == "host" and (isinstance(_n.node, VM) or isinstance(_n.node, Volume)):
            best_resource = copy.deepcopy(_avail_resources[_n.node.host[0]])
            best_resource.level = "host"
            # storage set
        else:
            vms = {}
            volumes = {}
            vgroups = {}
            if isinstance(_n.node, VGroup):
                if LEVELS.index(_n.node.level) < LEVELS.index(_level):
                    vgroups[_n.node.uuid] = _n.node
                else:
                    for _, sg in _n.node.subvgroups.iteritems():
                        if isinstance(sg, VM):
                            vms[sg.uuid] = sg
                        elif isinstance(sg, Volume):
                            volumes[sg.uuid] = sg
                        elif isinstance(sg, VGroup):
                            vgroups[sg.uuid] = sg
            else:
                if isinstance(_n.node, VM):
                    vms[_n.node.uuid] = _n.node
                elif isinstance(_n.node, Volume):
                    volumes[_n.node.uuid] = _n.node

            (planned_node_list, level) = self._open_planned_list(vms, volumes, vgroups, _level)

            host_name = self._get_host_of_level(_n, _level)
            if host_name is None:
                self.logger.warn("Search: cannot find host while replanning")
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

            if self._run_greedy_as_planned(planned_node_list, level, avail_hosts) is True:
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
                self.logger.debug("Search: host (" + host.name + ") not available at this time")
                continue

            r = Resource()
            r.host_name = hk

            for mk in host.memberships.keys():
                if mk in self.avail_logical_groups.keys():
                    r.host_memberships[mk] = self.avail_logical_groups[mk]

            for sk in host.storages.keys():
                if sk in self.avail_storage_hosts.keys():
                    r.host_avail_storages[sk] = self.avail_storage_hosts[sk]

            for sk in host.switches.keys():
                if sk in self.avail_switches.keys():
                    r.host_avail_switches[sk] = self.avail_switches[sk]

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

                for rsk in rack.storages.keys():
                    if rsk in self.avail_storage_hosts.keys():
                        r.rack_avail_storages[rsk] = self.avail_storage_hosts[rsk]

                for rsk in rack.switches.keys():
                    if rsk in self.avail_switches.keys():
                        r.rack_avail_switches[rsk] = self.avail_switches[rsk]

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
                            r.cluster_memberships[mk] = self.avail_logical_groups[mk]

                    for csk in cluster.storages.keys():
                        if csk in self.avail_storage_hosts.keys():
                            r.cluster_avail_storages[csk] = self.avail_storage_hosts[csk]

                    for csk in cluster.switches.keys():
                        if csk in self.avail_switches.keys():
                            r.cluster_avail_switches[csk] = self.avail_switches[csk]

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
                self.logger.debug("Search: group (" + lg.name + ") disabled")
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
        for h_uuid, info in self.app_topology.old_vm_map.iteritems():   # info = (host, cpu, mem, disk)
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
                if cr.cluster_name != "any" and cr.cluster_name == r.cluster_name:
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
                        lgr.num_of_placed_vms_per_host[r.host_name] -= 1
                        if lgr.group_type == "EX" or lgr.group_type == "AFF" or lgr.group_type == "DIV":
                            if lgr.num_of_placed_vms_per_host[r.host_name] == 0:
                                del lgr.num_of_placed_vms_per_host[r.host_name]
                                del r.host_memberships[lgk]
                    if lgr.group_type == "EX" or lgr.group_type == "AFF" or lgr.group_type == "DIV":
                        if lgr.num_of_placed_vms == 0:
                            del self.avail_logical_groups[lgk]

            for lgk in r.rack_memberships.keys():
                if lgk not in self.avail_logical_groups.keys():
                    continue
                if lgk not in self.resource.logical_groups.keys():
                    continue
                lg = self.resource.logical_groups[lgk]
                if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                    if lgk.split(":")[0] == "rack":
                        if lg.exist_vm_by_h_uuid(h_uuid) is True:
                            lgr = r.rack_memberships[lgk]
                            lgr.num_of_placed_vms -= 1
                            if r.rack_name in lgr.num_of_placed_vms_per_host.keys():
                                lgr.num_of_placed_vms_per_host[r.rack_name] -= 1
                                if lgr.num_of_placed_vms_per_host[r.rack_name] == 0:
                                    del lgr.num_of_placed_vms_per_host[r.rack_name]
                                    for _, rr in self.avail_hosts.iteritems():
                                        if rr.rack_name != "any" and rr.rack_name == r.rack_name:
                                            del rr.rack_memberships[lgk]
                            if lgr.num_of_placed_vms == 0:
                                del self.avail_logical_groups[lgk]

            for lgk in r.cluster_memberships.keys():
                if lgk not in self.avail_logical_groups.keys():
                    continue
                if lgk not in self.resource.logical_groups.keys():
                    continue
                lg = self.resource.logical_groups[lgk]
                if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                    if lgk.split(":")[0] == "cluster":
                        if lg.exist_vm_by_h_uuid(h_uuid) is True:
                            lgr = r.cluster_memberships[lgk]
                            lgr.num_of_placed_vms -= 1
                            if r.cluster_name in lgr.num_of_placed_vms_per_host.keys():
                                lgr.num_of_placed_vms_per_host[r.cluster_name] -= 1
                                if lgr.num_of_placed_vms_per_host[r.cluster_name] == 0:
                                    del lgr.num_of_placed_vms_per_host[r.cluster_name]
                                    for _, cr in self.avail_hosts.iteritems():
                                        if cr.cluster_name != "any" and cr.cluster_name == r.cluster_name:
                                            del cr.cluster_memberships[lgk]
                            if lgr.num_of_placed_vms == 0:
                                del self.avail_logical_groups[lgk]

    def _create_avail_storage_hosts(self):
        for _, sh in self.resource.storage_hosts.iteritems():

            if sh.status != "enabled":
                continue

            sr = StorageResource()
            sr.storage_name = sh.name
            sr.storage_class = sh.storage_class
            sr.storage_avail_disk = sh.avail_disk_cap

            self.avail_storage_hosts[sr.storage_name] = sr

    def _create_avail_switches(self):
        for sk, s in self.resource.switches.iteritems():

            if s.status != "enabled":
                continue

            sr = SwitchResource()
            sr.switch_name = s.name
            sr.switch_type = s.switch_type

            for _, ul in s.up_links.iteritems():
                sr.avail_bandwidths.append(ul.avail_nw_bandwidth)

            # NOTE: peer_links?

            self.avail_switches[sk] = sr

    def _compute_resource_weights(self):
        denominator = 0.0
        for (t, w) in self.app_topology.optimization_priority:
            denominator += w

        for (t, w) in self.app_topology.optimization_priority:
            if t == "bw":
                self.nw_bandwidth_weight = float(w / denominator)
            elif t == "cpu":
                self.CPU_weight = float(w / denominator)
            elif t == "mem":
                self.mem_weight = float(w / denominator)
            elif t == "lvol":
                self.local_disk_weight = float(w / denominator)
            elif t == "vol":
                self.disk_weight = float(w / denominator)

        self.logger.debug("Search: placement priority weights")
        for (r, w) in self.app_topology.optimization_priority:
            if r == "bw":
                self.logger.debug("    nw weight = " + str(self.nw_bandwidth_weight))
            elif r == "cpu":
                self.logger.debug("    cpu weight = " + str(self.CPU_weight))
            elif r == "mem":
                self.logger.debug("    mem weight = " + str(self.mem_weight))
            elif r == "lvol":
                self.logger.debug("    local disk weight = " + str(self.local_disk_weight))
            elif r == "vol":
                self.logger.debug("    disk weight = " + str(self.disk_weight))

    def _open_list(self, _vms, _volumes, _vgroups, _current_level):
        open_node_list = []
        next_level = None

        for _, vm in _vms.iteritems():
            n = Node()
            n.node = vm
            n.sort_base = self._set_virtual_capacity_based_sort(vm)
            open_node_list.append(n)

        # volume handling

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

        if isinstance(_v, Volume):
            sort_base = self.disk_weight * _v.volume_weight
            sort_base += self.nw_bandwidth_weight * _v.bandwidth_weight
        elif isinstance(_v, VM):
            sort_base = self.nw_bandwidth_weight * _v.bandwidth_weight
            sort_base += self.CPU_weight * _v.vCPU_weight
            sort_base += self.mem_weight * _v.mem_weight
            sort_base += self.local_disk_weight * _v.local_volume_weight
        elif isinstance(_v, VGroup):
            sort_base = self.nw_bandwidth_weight * _v.bandwidth_weight
            sort_base += self.CPU_weight * _v.vCPU_weight
            sort_base += self.mem_weight * _v.mem_weight
            sort_base += self.local_disk_weight * _v.local_volume_weight
            sort_base += self.disk_weight * _v.volume_weight

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

        _open_node_list.sort(key=operator.attrgetter("sort_base"), reverse=True)

        self.logger.debug("Search: the order of open node list in level = " + _level)
        for on in _open_node_list:
            self.logger.debug("    node = {}, value = {}".format(on.node.name, on.sort_base))

        while len(_open_node_list) > 0:
            n = _open_node_list.pop(0)
            self.logger.debug("Search: level = " + _level + ", node = " + n.node.name)

            best_resource = self._get_best_resource(n, _level, avail_resources)
            if best_resource is None:
                success = False
                break

            debug_best_resource = best_resource.get_resource_name(_level)
            # if isinstance(n.node, Volume):
            #     debug_best_resource = debug_best_resource + "@" + best_resource.storage.storage_name
            self.logger.debug("Search: best resource = " + debug_best_resource + " for node = " + n.node.name)

            if n.node not in self.planned_placements.keys():
                ''' for VM or Volume under host level only '''
                self._deduct_reservation(_level, best_resource, n)
                ''' close all types of nodes under any level, but VM or Volume with above host level '''
                self._close_node_placement(_level, best_resource, n.node)
            else:
                self.logger.debug("Search: node (" + n.node.name + ") is already deducted")

        return success

    def _get_best_resource(self, _n, _level, _avail_resources):
        ''' already planned vgroup '''
        planned_host = None
        if _n.node in self.planned_placements.keys():
            self.logger.debug("Search: already determined node = " + _n.node.name)
            copied_host = self.planned_placements[_n.node]
            if _level == "host":
                planned_host = _avail_resources[copied_host.host_name]
            elif _level == "rack":
                planned_host = _avail_resources[copied_host.rack_name]
            elif _level == "cluster":
                planned_host = _avail_resources[copied_host.cluster_name]

        else:
            if len(self.app_topology.candidate_list_map) > 0:
                conflicted_vm_uuid = self.app_topology.candidate_list_map.keys()[0]
                candidate_name_list = self.app_topology.candidate_list_map[conflicted_vm_uuid]
                if (isinstance(_n.node, VM) and conflicted_vm_uuid == _n.node.uuid) or \
                   (isinstance(_n.node, VGroup) and self._check_vm_grouping(_n.node, conflicted_vm_uuid) is True):
                    host_list = []
                    for hk in candidate_name_list:
                        host_name = self._get_host_of_vgroup(hk, _level)
                        if host_name is not None:
                            if host_name not in host_list:
                                host_list.append(host_name)
                        else:
                            self.logger.warn("Search: cannot find candidate host while replanning")
                    _n.node.host = host_list

        candidate_list = []
        if planned_host is not None:
            candidate_list.append(planned_host)
        else:
            candidate_list = self.constraint_solver.compute_candidate_list(_level, _n,
                                                                           self.node_placements,
                                                                           _avail_resources,
                                                                           self.avail_logical_groups)
        if len(candidate_list) == 0:
            self.status = self.constraint_solver.status
            return None

        self.logger.debug("Search: candidate list")
        for c in candidate_list:
            self.logger.debug("    candidate = " + c.get_resource_name(_level))

        (target, _) = self.app_topology.optimization_priority[0]
        top_candidate_list = None

        if target == "bw":
            constrained_list = []
            for cr in candidate_list:
                cr.sort_base = self._estimate_max_bandwidth(_level, _n, cr)
                if cr.sort_base == -1:
                    constrained_list.append(cr)

            for c in constrained_list:
                if c in candidate_list:
                    candidate_list.remove(c)

            if len(candidate_list) == 0:
                self.status = "no available network bandwidth left, for node = " + _n.node.name
                self.logger.error("Search: " + self.status)
                return None

            candidate_list.sort(key=operator.attrgetter("sort_base"))
            top_candidate_list = self._sort_highest_consolidation(_n, _level, candidate_list)
        else:
            if target == "vol":
                if isinstance(_n.node, VGroup) or isinstance(_n.node, Volume):
                    volume_class = None
                    if isinstance(_n.node, Volume):
                        volume_class = _n.node.volume_class
                    else:
                        max_size = 0
                        for vck in _n.node.volume_sizes.keys():
                            if _n.node.volume_sizes[vck] > max_size:
                                max_size = _n.node.volume_sizes[vck]
                                volume_class = vck

                    self._set_disk_sort_base(_level, candidate_list, volume_class)
                    candidate_list.sort(key=operator.attrgetter("sort_base"), reverse=True)
                else:
                    self._set_compute_sort_base(_level, candidate_list)
                    candidate_list.sort(key=operator.attrgetter("sort_base"))
            else:
                if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
                    self._set_compute_sort_base(_level, candidate_list)
                    candidate_list.sort(key=operator.attrgetter("sort_base"))
                else:
                    self._set_disk_sort_base(_level, candidate_list, _n.node.volume_class)
                    candidate_list.sort(key=operator.attrgetter("sort_base"), reverse=True)

            top_candidate_list = self._sort_lowest_bandwidth_usage(_n, _level, candidate_list)

            if len(top_candidate_list) == 0:
                self.status = "no available network bandwidth left"
                self.logger.error("Search: " + self.status)
                return None

        best_resource = None
        if _level == "host" and (isinstance(_n.node, VM) or isinstance(_n.node, Volume)):
            best_resource = copy.deepcopy(top_candidate_list[0])
            best_resource.level = "host"
            if isinstance(_n.node, Volume):
                self._set_best_storage(_n, best_resource)
        else:
            while True:

                while len(top_candidate_list) > 0:
                    cr = top_candidate_list.pop(0)

                    self.logger.debug("Search: try candidate = " + cr.get_resource_name(_level))

                    vms = {}
                    volumes = {}
                    vgroups = {}
                    if isinstance(_n.node, VGroup):
                        if LEVELS.index(_n.node.level) < LEVELS.index(_level):
                            vgroups[_n.node.uuid] = _n.node
                        else:
                            for _, sg in _n.node.subvgroups.iteritems():
                                if isinstance(sg, VM):
                                    vms[sg.uuid] = sg
                                elif isinstance(sg, Volume):
                                    volumes[sg.uuid] = sg
                                elif isinstance(sg, VGroup):
                                    vgroups[sg.uuid] = sg
                    else:
                        if isinstance(_n.node, VM):
                            vms[_n.node.uuid] = _n.node
                        elif isinstance(_n.node, Volume):
                            volumes[_n.node.uuid] = _n.node

                    (open_node_list, level) = self._open_list(vms, volumes, vgroups, _level)
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

                    ''' recursive call '''
                    if self._run_greedy(open_node_list, level, avail_hosts) is True:
                        best_resource = copy.deepcopy(cr)
                        best_resource.level = _level
                        break
                    else:
                        debug_candidate_name = cr.get_resource_name(_level)
                        self.logger.debug("Search: rollback of candidate resource = " + debug_candidate_name)

                        if planned_host is None:
                            ''' recursively rollback deductions of all child VMs and Volumes of _n '''
                            self._rollback_reservation(_n.node)
                            ''' recursively rollback closing '''
                            self._rollback_node_placement(_n.node)
                        else:
                            break

                ''' after explore top candidate list for _n '''
                if best_resource is not None:
                    break
                else:
                    if len(candidate_list) == 0:
                        self.status = "no available hosts"
                        self.logger.warn("Search: " + self.status)
                        break
                    else:
                        if target == "bw":
                            top_candidate_list = self._sort_highest_consolidation(_n, _level, candidate_list)
                        else:
                            top_candidate_list = self._sort_lowest_bandwidth_usage(_n, _level, candidate_list)
                            if len(top_candidate_list) == 0:
                                self.status = "no available network bandwidth left"
                                self.logger.warn("Search: " + self.status)
                                break

        return best_resource

    def _set_best_storage(self, _n, _resource):
        max_storage_size = 0
        for sk in _resource.host_avail_storages.keys():
            s = self.avail_storage_hosts[sk]
            if _n.node.volume_class == "any" or s.storage_class == _n.node.volume_class:
                if s.storage_avail_disk > max_storage_size:
                    max_storage_size = s.storage_avail_disk
                    _resource.storage = s

    def _sort_lowest_bandwidth_usage(self, _n, _level, _candidate_list):
        while True:
            top_candidate_list = []
            best_usage = _candidate_list[0].sort_base

            rm_list = []
            for ch in _candidate_list:
                if ch.sort_base == best_usage:
                    top_candidate_list.append(ch)
                    rm_list.append(ch)
                else:
                    break
            _candidate_list[:] = [c for c in _candidate_list if c not in rm_list]

            constrained_list = []
            for c in top_candidate_list:
                c.sort_base = self._estimate_max_bandwidth(_level, _n, c)
                if c.sort_base == -1:
                    constrained_list.append(c)

            for c in constrained_list:
                if c in top_candidate_list:
                    top_candidate_list.remove(c)

            if len(top_candidate_list) > 0:
                top_candidate_list.sort(key=operator.attrgetter("sort_base"))
                break

            if len(_candidate_list) == 0:
                break

        return top_candidate_list

    def _sort_highest_consolidation(self, _n, _level, _candidate_list):
        top_candidate_list = []
        best_bandwidth_usage = _candidate_list[0].sort_base

        rm_list = []
        for ch in _candidate_list:
            if ch.sort_base == best_bandwidth_usage:
                top_candidate_list.append(ch)
                rm_list.append(ch)
            else:
                break
        _candidate_list[:] = [c for c in _candidate_list if c not in rm_list]

        target = None
        for (t, _) in self.app_topology.optimization_priority:
            if t != "bw":
                target = t
                break

        if target == "vol":
            if isinstance(_n.node, VGroup) or isinstance(_n.node, Volume):
                volume_class = None
                if isinstance(_n.node, Volume):
                    volume_class = _n.node.volume_class
                else:
                    max_size = 0
                    for vck in _n.node.volume_sizes.keys():
                        if _n.node.volume_sizes[vck] > max_size:
                            max_size = _n.node.volume_sizes[vck]
                            volume_class = vck
                self._set_disk_sort_base(_level, top_candidate_list, volume_class)
                top_candidate_list.sort(key=operator.attrgetter("sort_base"), reverse=True)
            else:
                self._set_compute_sort_base(_level, top_candidate_list)
                top_candidate_list.sort(key=operator.attrgetter("sort_base"))
        else:
            if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
                self._set_compute_sort_base(_level, top_candidate_list)
                top_candidate_list.sort(key=operator.attrgetter("sort_base"))
            else:
                self._set_disk_sort_base(_level, top_candidate_list, _n.node.volume_class)
                top_candidate_list.sort(key=operator.attrgetter("sort_base"), reverse=True)

        return top_candidate_list

    def _set_disk_sort_base(self, _level, _candidate_list, _class):
        for c in _candidate_list:
            avail_storages = {}
            if _level == "cluster":
                for sk in c.cluster_avail_storages.keys():
                    s = c.cluster_avail_storages[sk]
                    if _class == "any" or s.storage_class == _class:
                        avail_storages[sk] = s
            elif _level == "rack":
                for sk in c.rack_avail_storages.keys():
                    s = c.rack_avail_storages[sk]
                    if _class == "any" or s.storage_class == _class:
                        avail_storages[sk] = s
            elif _level == "host":
                for sk in c.host_avail_storages.keys():
                    s = c.host_avail_storages[sk]
                    if _class == "any" or s.storage_class == _class:
                        avail_storages[sk] = s

            current_max = 0
            for sk in avail_storages.keys():
                s = avail_storages[sk]
                if s.storage_avail_disk > current_max:
                    current_max = s.storage_avail_disk

            c.sort_base = current_max

    def _set_compute_sort_base(self, _level, _candidate_list):
        for c in _candidate_list:
            CPU_ratio = -1
            mem_ratio = -1
            local_disk_ratio = -1
            if _level == "cluster":
                CPU_ratio = float(c.cluster_avail_vCPUs) / float(self.resource.CPU_avail)
                mem_ratio = float(c.cluster_avail_mem) / float(self.resource.mem_avail)
                local_disk_ratio = float(c.cluster_avail_local_disk) / float(self.resource.local_disk_avail)
            elif _level == "rack":
                CPU_ratio = float(c.rack_avail_vCPUs) / float(self.resource.CPU_avail)
                mem_ratio = float(c.rack_avail_mem) / float(self.resource.mem_avail)
                local_disk_ratio = float(c.rack_avail_local_disk) / float(self.resource.local_disk_avail)
            elif _level == "host":
                CPU_ratio = float(c.host_avail_vCPUs) / float(self.resource.CPU_avail)
                mem_ratio = float(c.host_avail_mem) / float(self.resource.mem_avail)
                local_disk_ratio = float(c.host_avail_local_disk) / float(self.resource.local_disk_avail)
            c.sort_base = (1.0 - self.CPU_weight) * CPU_ratio + \
                          (1.0 - self.mem_weight) * mem_ratio + \
                          (1.0 - self.local_disk_weight) * local_disk_ratio

    def _estimate_max_bandwidth(self, _level, _n, _candidate):
        nw_bandwidth_penalty = self._estimate_nw_bandwidth_penalty(_level, _n, _candidate)

        if nw_bandwidth_penalty >= 0:
            return nw_bandwidth_penalty
        else:
            return -1

    def _estimate_nw_bandwidth_penalty(self, _level, _n, _candidate):
        sort_base = 0  # Set bandwidth usage penalty by placement

        # To check the bandwidth constraint at the last moment
        # 3rd entry to be used for special node communicating beyond datacenter or zone
        req_bandwidths = [0, 0, 0]

        link_list = _n.get_all_links()

        placed_link_list = []
        for vl in link_list:
            for v in self.node_placements.keys():
                if v.uuid == vl.node.uuid:
                    placed_link_list.append(vl)

                    bandwidth = _n.get_bandwidth_of_link(vl)
                    placement_level = _candidate.get_common_placement(self.node_placements[v])
                    if placement_level != "ANY" and LEVELS.index(placement_level) >= LEVELS.index(_level):
                        sort_base += compute_reservation(_level, placement_level, bandwidth)
                        self.constraint_solver.get_req_bandwidths(_level,
                                                                  placement_level,
                                                                  bandwidth,
                                                                  req_bandwidths)

        candidate = copy.deepcopy(_candidate)

        exclusivity_ids = self.constraint_solver.get_exclusivities(_n.node.exclusivity_groups, _level)
        exclusivity_id = None
        if len(exclusivity_ids) > 0:
            exclusivity_id = exclusivity_ids[exclusivity_ids.keys()[0]]
        temp_exclusivity_insert = False
        if exclusivity_id is not None:
            if exclusivity_id not in self.avail_logical_groups.keys():
                temp_lgr = LogicalGroupResource()
                temp_lgr.name = exclusivity_id
                temp_lgr.group_type = "EX"

                self.avail_logical_groups[exclusivity_id] = temp_lgr
                temp_exclusivity_insert = True

            self._add_exclusivity_to_candidate(_level, candidate, exclusivity_id)

        affinity_id = _n.get_affinity_id()
        temp_affinity_insert = False
        if affinity_id is not None:
            if affinity_id not in self.avail_logical_groups.keys():
                temp_lgr = LogicalGroupResource()
                temp_lgr.name = affinity_id
                temp_lgr.group_type = "AFF"

                self.avail_logical_groups[affinity_id] = temp_lgr
                temp_affinity_insert = True

            self._add_affinity_to_candidate(_level, candidate, affinity_id)

        self._deduct_reservation_from_candidate(candidate, _n, req_bandwidths, _level)

        handled_vgroups = {}
        for vl in link_list:
            if vl in placed_link_list:
                continue

            bandwidth = _n.get_bandwidth_of_link(vl)

            diversity_level = _n.get_common_diversity(vl.node.diversity_groups)
            if diversity_level == "ANY":
                implicit_diversity = self.constraint_solver.get_implicit_diversity(_n.node,
                                                                                   link_list,
                                                                                   vl.node,
                                                                                   _level)
                if implicit_diversity[0] is not None:
                    diversity_level = implicit_diversity[1]
            if diversity_level == "ANY" or LEVELS.index(diversity_level) < LEVELS.index(_level):
                vg = self._get_top_vgroup(vl.node, _level)
                if vg.uuid not in handled_vgroups.keys():
                    handled_vgroups[vg.uuid] = vg

                    temp_n = Node()
                    temp_n.node = vg
                    temp_req_bandwidths = [0, 0, 0]
                    self.constraint_solver.get_req_bandwidths(_level, _level, bandwidth, temp_req_bandwidths)

                    if self._check_availability(_level, temp_n, candidate) is True:
                        self._deduct_reservation_from_candidate(candidate, temp_n, temp_req_bandwidths, _level)
                    else:
                        sort_base += compute_reservation(_level, _level, bandwidth)
                        req_bandwidths[0] += temp_req_bandwidths[0]
                        req_bandwidths[1] += temp_req_bandwidths[1]
                        req_bandwidths[2] += temp_req_bandwidths[2]
            else:
                self.constraint_solver.get_req_bandwidths(_level, diversity_level, bandwidth, req_bandwidths)
                sort_base += compute_reservation(_level, diversity_level, bandwidth)

        if self.constraint_solver._check_nw_bandwidth_availability(_level, req_bandwidths, _candidate) is False:
            sort_base = -1

        if temp_exclusivity_insert is True:
            del self.avail_logical_groups[exclusivity_id]

        if temp_affinity_insert is True:
            del self.avail_logical_groups[affinity_id]

        return sort_base

    def _add_exclusivity_to_candidate(self, _level, _candidate, _exclusivity_id):
        lgr = self.avail_logical_groups[_exclusivity_id]

        if _level == "host":
            if _exclusivity_id not in _candidate.host_memberships.keys():
                _candidate.host_memberships[_exclusivity_id] = lgr
            if _exclusivity_id not in _candidate.rack_memberships.keys():
                _candidate.rack_memberships[_exclusivity_id] = lgr
            if _exclusivity_id not in _candidate.cluster_memberships.keys():
                _candidate.cluster_memberships[_exclusivity_id] = lgr
        elif _level == "rack":
            if _exclusivity_id not in _candidate.rack_memberships.keys():
                _candidate.rack_memberships[_exclusivity_id] = lgr
            if _exclusivity_id not in _candidate.cluster_memberships.keys():
                _candidate.cluster_memberships[_exclusivity_id] = lgr
        elif _level == "cluster":
            if _exclusivity_id not in _candidate.cluster_memberships.keys():
                _candidate.cluster_memberships[_exclusivity_id] = lgr

    def _add_affinity_to_candidate(self, _level, _candidate, _affinity_id):
        lgr = self.avail_logical_groups[_affinity_id]

        if _level == "host":
            if _affinity_id not in _candidate.host_memberships.keys():
                _candidate.host_memberships[_affinity_id] = lgr
            if _affinity_id not in _candidate.rack_memberships.keys():
                _candidate.rack_memberships[_affinity_id] = lgr
            if _affinity_id not in _candidate.cluster_memberships.keys():
                _candidate.cluster_memberships[_affinity_id] = lgr
        elif _level == "rack":
            if _affinity_id not in _candidate.rack_memberships.keys():
                _candidate.rack_memberships[_affinity_id] = lgr
            if _affinity_id not in _candidate.cluster_memberships.keys():
                _candidate.cluster_memberships[_affinity_id] = lgr
        elif _level == "cluster":
            if _affinity_id not in _candidate.cluster_memberships.keys():
                _candidate.cluster_memberships[_affinity_id] = lgr

    def _get_top_vgroup(self, _v, _level):
        vg = _v.survgroup

        if vg is None:
            return _v

        if LEVELS.index(vg.level) > LEVELS.index(_level):
            return _v

        return self._get_top_vgroup(vg, _level)

    def _check_availability(self, _level, _n, _candidate):
        if isinstance(_n.node, VM):
            if self.constraint_solver.check_cpu_capacity(_level, _n.node, _candidate) is False:
                return False
            if self.constraint_solver.check_mem_capacity(_level, _n.node, _candidate) is False:
                return False
            if self.constraint_solver.check_local_disk_capacity(_level, _n.node, _candidate) is False:
                return False
        elif isinstance(_n.node, Volume):
            if self.constraint_solver.check_storage_availability(_level, _n.node, _candidate) is False:
                return False
        else:
            if self.constraint_solver.check_cpu_capacity(_level, _n.node, _candidate) is False or \
               self.constraint_solver.check_mem_capacity(_level, _n.node, _candidate) is False or \
               self.constraint_solver.check_local_disk_capacity(_level, _n.node, _candidate) is False or \
               self.constraint_solver.check_storage_availability(_level, _n.node, _candidate) is False:
                return False

        if self.constraint_solver.check_nw_bandwidth_availability(_level, _n,
                                                                  self.node_placements,
                                                                  _candidate) is False:
            return False

        if isinstance(_n.node, VM):
            if len(_n.node.extra_specs_list) > 0:
                if self.constraint_solver.check_host_aggregates(_level, _candidate, _n.node) is False:
                    return False

        if isinstance(_n.node, VM):
            if _n.node.availability_zone is not None:
                if self.constraint_solver.check_availability_zone(_level, _candidate, _n.node) is False:
                    return False

        if self.constraint_solver.conflict_diversity(_level, _n, self.node_placements, _candidate) is True:
            return False

        exclusivities = self.constraint_solver.get_exclusivities(_n.node.exclusivity_groups, _level)
        if len(exclusivities) == 1:
            exc_id = exclusivities[exclusivities.keys()[0]]
            if self.constraint_solver.exist_group(_level, exc_id, "EX", _candidate) is False:
                return False
        elif len(exclusivities) < 1:
            if self.constraint_solver.conflict_exclusivity(_level, _candidate):
                return False

        aff_id = _n.get_affinity_id()
        if aff_id is not None:
            if aff_id in self.avail_logical_groups.keys():
                if self.constraint_solver.exist_group(_level, aff_id, "AFF", _candidate) is False:
                    return False

        return True

    def _deduct_reservation_from_candidate(self, _candidate, _n, _rsrv, _level):
        if isinstance(_n.node, VM) or isinstance(_n.node, VGroup):
            self._deduct_candidate_vm_reservation(_level, _n.node, _candidate)

        if isinstance(_n.node, Volume) or isinstance(_n.node, VGroup):
            self._deduct_candidate_volume_reservation(_level, _n.node, _candidate)

        self._deduct_candidate_nw_reservation(_candidate, _rsrv)

    def _deduct_candidate_vm_reservation(self, _level, _v, _candidate):
        is_vm_included = False
        if isinstance(_v, VM):
            is_vm_included = True
        elif isinstance(_v, VGroup):
            is_vm_included = self._check_vm_included(_v)

        if _level == "cluster":
            _candidate.cluster_avail_vCPUs -= _v.vCPUs
            _candidate.cluster_avail_mem -= _v.mem
            _candidate.cluster_avail_local_disk -= _v.local_volume_size
            if is_vm_included is True:
                _candidate.cluster_num_of_placed_vms += 1
        elif _level == "rack":
            _candidate.cluster_avail_vCPUs -= _v.vCPUs
            _candidate.cluster_avail_mem -= _v.mem
            _candidate.cluster_avail_local_disk -= _v.local_volume_size
            if is_vm_included is True:
                _candidate.cluster_num_of_placed_vms += 1
            _candidate.rack_avail_vCPUs -= _v.vCPUs
            _candidate.rack_avail_mem -= _v.mem
            _candidate.rack_avail_local_disk -= _v.local_volume_size
            if is_vm_included is True:
                _candidate.rack_num_of_placed_vms += 1
        elif _level == "host":
            _candidate.cluster_avail_vCPUs -= _v.vCPUs
            _candidate.cluster_avail_mem -= _v.mem
            _candidate.cluster_avail_local_disk -= _v.local_volume_size
            if is_vm_included is True:
                _candidate.cluster_num_of_placed_vms += 1
            _candidate.rack_avail_vCPUs -= _v.vCPUs
            _candidate.rack_avail_mem -= _v.mem
            _candidate.rack_avail_local_disk -= _v.local_volume_size
            if is_vm_included is True:
                _candidate.rack_num_of_placed_vms += 1
            _candidate.host_avail_vCPUs -= _v.vCPUs
            _candidate.host_avail_mem -= _v.mem
            _candidate.host_avail_local_disk -= _v.local_volume_size
            if is_vm_included is True:
                _candidate.host_num_of_placed_vms += 1

    def _check_vm_included(self, _v):
        is_vm_included = False

        for _, sv in _v.subvgroups.iteritems():
            if isinstance(sv, VM):
                is_vm_included = True
                break
            elif isinstance(sv, VGroup):
                is_vm_included = self._check_vm_included(sv)
                if is_vm_included is True:
                    break

        return is_vm_included

    def _deduct_candidate_volume_reservation(self, _level, _v, _candidate):
        volume_sizes = []
        if isinstance(_v, VGroup):
            for vck in _v.volume_sizes.keys():
                volume_sizes.append((vck, _v.volume_sizes[vck]))
        else:
            volume_sizes.append((_v.volume_class, _v.volume_size))

        for (vc, vs) in volume_sizes:
            max_size = 0
            selected_storage = None
            if _level == "cluster":
                for sk in _candidate.cluster_avail_storages.keys():
                    s = _candidate.cluster_avail_storages[sk]
                    if vc == "any" or s.storage_class == vc:
                        if s.storage_avail_disk > max_size:
                            max_size = s.storage_avail_disk
                            selected_storage = s
                selected_storage.storage_avail_disk -= vs
            elif _level == "rack":
                for sk in _candidate.rack_avail_storages.keys():
                    s = _candidate.rack_avail_storages[sk]
                    if vc == "any" or s.storage_class == vc:
                        if s.storage_avail_disk > max_size:
                            max_size = s.storage_avail_disk
                            selected_storage = s
                selected_storage.storage_avail_disk -= vs
            elif _level == "host":
                for sk in _candidate.host_avail_storages.keys():
                    s = _candidate.host_avail_storages[sk]
                    if vc == "any" or s.storage_class == vc:
                        if s.storage_avail_disk > max_size:
                            max_size = s.storage_avail_disk
                            selected_storage = s
                selected_storage.storage_avail_disk -= vs

    def _deduct_candidate_nw_reservation(self, _candidate, _rsrv):
        for srk in _candidate.host_avail_switches.keys():
            sr = _candidate.host_avail_switches[srk]
            sr.avail_bandwidths = [bw - _rsrv[0] for bw in sr.avail_bandwidths]

        for srk in _candidate.rack_avail_switches.keys():
            sr = _candidate.rack_avail_switches[srk]
            sr.avail_bandwidths = [bw - _rsrv[1] for bw in sr.avail_bandwidths]

        for srk in _candidate.cluster_avail_switches.keys():
            sr = _candidate.cluster_avail_switches[srk]
            if sr.switch_type == "spine":
                sr.avail_bandwidths = [bw - _rsrv[2] for bw in sr.avail_bandwidths]

    '''
    deduction modules
    '''

    def _deduct_reservation(self, _level, _best, _n):
        exclusivities = self.constraint_solver.get_exclusivities(_n.node.exclusivity_groups, _level)
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
        elif isinstance(_n.node, Volume) and _level == "host":
            self._deduct_volume_resources(_best, _n)

    def _add_exclusivity(self, _level, _best, _exclusivity_id):
        lgr = None
        if _exclusivity_id not in self.avail_logical_groups.keys():
            lgr = LogicalGroupResource()
            lgr.name = _exclusivity_id
            lgr.group_type = "EX"
            self.avail_logical_groups[lgr.name] = lgr

            self.logger.debug("Search: add new exclusivity (" + _exclusivity_id + ")")
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
                    if chosen_host.rack_name != "any" and np.rack_name == chosen_host.rack_name:
                        if _exclusivity_id not in np.rack_memberships.keys():
                            np.rack_memberships[_exclusivity_id] = lgr
                    if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                        if _exclusivity_id not in np.cluster_memberships.keys():
                            np.cluster_memberships[_exclusivity_id] = lgr
            elif _level == "rack":
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.rack_name != "any" and np.rack_name == chosen_host.rack_name:
                        if _exclusivity_id not in np.rack_memberships.keys():
                            np.rack_memberships[_exclusivity_id] = lgr
                    if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                        if _exclusivity_id not in np.cluster_memberships.keys():
                            np.cluster_memberships[_exclusivity_id] = lgr
            elif _level == "cluster":
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                        if _exclusivity_id not in np.cluster_memberships.keys():
                            np.cluster_memberships[_exclusivity_id] = lgr

    def _add_affinity(self, _level, _best, _affinity_id):
        lgr = None
        if _affinity_id not in self.avail_logical_groups.keys():
            lgr = LogicalGroupResource()
            lgr.name = _affinity_id
            lgr.group_type = "AFF"
            self.avail_logical_groups[lgr.name] = lgr

            self.logger.debug("Search: add new affinity (" + _affinity_id + ")")
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
                    if chosen_host.rack_name != "any" and np.rack_name == chosen_host.rack_name:
                        if _affinity_id not in np.rack_memberships.keys():
                            np.rack_memberships[_affinity_id] = lgr
                    if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                        if _affinity_id not in np.cluster_memberships.keys():
                            np.cluster_memberships[_affinity_id] = lgr
            elif _level == "rack":
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.rack_name != "any" and np.rack_name == chosen_host.rack_name:
                        if _affinity_id not in np.rack_memberships.keys():
                            np.rack_memberships[_affinity_id] = lgr
                    if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                        if _affinity_id not in np.cluster_memberships.keys():
                            np.cluster_memberships[_affinity_id] = lgr
            elif _level == "cluster":
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                        if _affinity_id not in np.cluster_memberships.keys():
                            np.cluster_memberships[_affinity_id] = lgr

    def _add_diversities(self, _level, _best, _diversity_id):
        lgr = None
        if _diversity_id not in self.avail_logical_groups.keys():
            lgr = LogicalGroupResource()
            lgr.name = _diversity_id
            lgr.group_type = "DIV"
            self.avail_logical_groups[lgr.name] = lgr

            self.logger.debug("Search: add new diversity (" + _diversity_id + ")")
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
                    if chosen_host.rack_name != "any" and np.rack_name == chosen_host.rack_name:
                        if _diversity_id not in np.rack_memberships.keys():
                            np.rack_memberships[_diversity_id] = lgr
                    if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                        if _diversity_id not in np.cluster_memberships.keys():
                            np.cluster_memberships[_diversity_id] = lgr
            elif _level == "rack":
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.rack_name != "any" and np.rack_name == chosen_host.rack_name:
                        if _diversity_id not in np.rack_memberships.keys():
                            np.rack_memberships[_diversity_id] = lgr
                    if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                        if _diversity_id not in np.cluster_memberships.keys():
                            np.cluster_memberships[_diversity_id] = lgr
            elif _level == "cluster":
                for _, np in self.avail_hosts.iteritems():
                    if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
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
            if chosen_host.rack_name != "any" and np.rack_name == chosen_host.rack_name:
                np.rack_avail_vCPUs -= _n.node.vCPUs
                np.rack_avail_mem -= _n.node.mem
                np.rack_avail_local_disk -= _n.node.local_volume_size
                np.rack_num_of_placed_vms += 1
            if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                np.cluster_avail_vCPUs -= _n.node.vCPUs
                np.cluster_avail_mem -= _n.node.mem
                np.cluster_avail_local_disk -= _n.node.local_volume_size
                np.cluster_num_of_placed_vms += 1

        for vml in _n.node.vm_list:
            if vml.node in self.node_placements.keys():
                cn = self.avail_hosts[self.node_placements[vml.node].host_name]
                placement_level = cn.get_common_placement(chosen_host)
                bandwidth = vml.nw_bandwidth
                self.bandwidth_usage += self._deduct_nw_reservation(placement_level, chosen_host, cn, bandwidth)

        for voll in _n.node.volume_list:
            if voll.node in self.node_placements.keys():
                cn = self.avail_hosts[self.node_placements[voll.node].host_name]
                placement_level = cn.get_common_placement(chosen_host)
                bandwidth = voll.io_bandwidth
                self.bandwidth_usage += self._deduct_nw_reservation(placement_level, chosen_host, cn, bandwidth)

    def _deduct_volume_resources(self, _best, _n):
        storage_host = self.avail_storage_hosts[_best.storage.storage_name]
        storage_host.storage_avail_disk -= _n.node.volume_size

        chosen_host = self.avail_hosts[_best.host_name]

        for vml in _n.node.vm_list:
            if vml.node in self.node_placements.keys():
                cn = self.avail_hosts[self.node_placements[vml.node].host_name]
                placement_level = cn.get_common_placement(chosen_host)
                bandwidth = vml.io_bandwidth
                self.bandwidth_usage += self._deduct_nw_reservation(placement_level, chosen_host, cn, bandwidth)

    def _deduct_nw_reservation(self, _placement_level, _host1, _host2, _rsrv):
        nw_reservation = compute_reservation("host", _placement_level, _rsrv)

        if _placement_level == "host":
            for _, sr in _host1.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]
            for _, sr in _host2.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]
        elif _placement_level == "rack":
            for _, sr in _host1.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]
            for _, sr in _host2.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]

            for _, sr in _host1.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]
            for _, sr in _host2.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]
        elif _placement_level == "cluster":
            for _, sr in _host1.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]
            for _, sr in _host2.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]

            for _, sr in _host1.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]
            for _, sr in _host2.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]

            for _, sr in _host1.cluster_avail_switches.iteritems():
                if sr.switch_type == "spine":
                    sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]
            for _, sr in _host2.cluster_avail_switches.iteritems():
                if sr.switch_type == "spine":
                    sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]

        return nw_reservation

    def _close_node_placement(self, _level, _best, _v):
        if _v not in self.node_placements.keys():
            if _level == "host" or isinstance(_v, VGroup):
                self.node_placements[_v] = _best

    '''
    rollback modules
    '''

    def _rollback_reservation(self, _v):
        if isinstance(_v, VM):
            self._rollback_vm_reservation(_v)

        elif isinstance(_v, Volume):
            self._rollback_volume_reservation(_v)

        elif isinstance(_v, VGroup):
            for _, v in _v.subvgroups.iteritems():
                self._rollback_reservation(v)

        if _v in self.node_placements.keys():
            self.logger.debug("Search: node (" + _v.name + ") rollbacked")

            chosen_host = self.avail_hosts[self.node_placements[_v].host_name]
            level = self.node_placements[_v].level

            if isinstance(_v, VGroup):
                affinity_id = _v.level + ":" + _v.name
                if _v.name != "any":
                    self._remove_affinity(chosen_host, affinity_id, level)

            exclusivities = self.constraint_solver.get_exclusivities(_v.exclusivity_groups, level)
            if len(exclusivities) == 1:
                exclusivity_id = exclusivities[exclusivities.keys()[0]]
                self._remove_exclusivity(chosen_host, exclusivity_id, level)

            if len(_v.diversity_groups) > 0:
                for _, diversity_id in _v.diversity_groups.iteritems():
                    if diversity_id.split(":")[1] != "any":
                        self._remove_diversities(chosen_host, diversity_id, level)

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
                        if _chosen_host.rack_name != "any" and np.rack_name == _chosen_host.rack_name:
                            if _exclusivity_id in np.rack_memberships.keys():
                                del np.rack_memberships[_exclusivity_id]
                        if _chosen_host.cluster_name != "any" and np.cluster_name == _chosen_host.cluster_name:
                            if _exclusivity_id in np.cluster_memberships.keys():
                                del np.cluster_memberships[_exclusivity_id]

            elif _level == "rack":
                if _chosen_host.rack_num_of_placed_vms == 0:
                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.rack_name != "any" and np.rack_name == _chosen_host.rack_name:
                            if _exclusivity_id in np.rack_memberships.keys():
                                del np.rack_memberships[_exclusivity_id]
                        if _chosen_host.cluster_name != "any" and np.cluster_name == _chosen_host.cluster_name:
                            if _exclusivity_id in np.cluster_memberships.keys():
                                del np.cluster_memberships[_exclusivity_id]

            elif _level == "cluster":
                if _chosen_host.cluster_num_of_placed_vms == 0:
                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.cluster_name != "any" and np.cluster_name == _chosen_host.cluster_name:
                            if _exclusivity_id in np.cluster_memberships.keys():
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
                if exist_affinity is False and _affinity_id in _chosen_host.host_memberships.keys():
                    del _chosen_host.host_memberships[_affinity_id]

                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.rack_name != "any" and np.rack_name == _chosen_host.rack_name:
                            if _affinity_id in np.rack_memberships.keys():
                                del np.rack_memberships[_affinity_id]
                        if _chosen_host.cluster_name != "any" and np.cluster_name == _chosen_host.cluster_name:
                            if _affinity_id in np.cluster_memberships.keys():
                                del np.cluster_memberships[_affinity_id]

            elif _level == "rack":
                if exist_affinity is False:
                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.rack_name != "any" and np.rack_name == _chosen_host.rack_name:
                            if _affinity_id in np.rack_memberships.keys():
                                del np.rack_memberships[_affinity_id]
                        if _chosen_host.cluster_name != "any" and np.cluster_name == _chosen_host.cluster_name:
                            if _affinity_id in np.cluster_memberships.keys():
                                del np.cluster_memberships[_affinity_id]

            elif _level == "cluster":
                if exist_affinity is False:
                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.cluster_name != "any" and np.cluster_name == _chosen_host.cluster_name:
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
                if exist_diversity is False and _diversity_id in _chosen_host.host_memberships.keys():
                    del _chosen_host.host_memberships[_diversity_id]

                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.rack_name != "any" and np.rack_name == _chosen_host.rack_name:
                            if _diversity_id in np.rack_memberships.keys():
                                del np.rack_memberships[_diversity_id]
                        if _chosen_host.cluster_name != "any" and np.cluster_name == _chosen_host.cluster_name:
                            if _diversity_id in np.cluster_memberships.keys():
                                del np.cluster_memberships[_diversity_id]

            elif _level == "rack":
                if exist_diversity is False:
                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.rack_name != "any" and np.rack_name == _chosen_host.rack_name:
                            if _diversity_id in np.rack_memberships.keys():
                                del np.rack_memberships[_diversity_id]
                        if _chosen_host.cluster_name != "any" and np.cluster_name == _chosen_host.cluster_name:
                            if _diversity_id in np.cluster_memberships.keys():
                                del np.cluster_memberships[_diversity_id]

            elif _level == "cluster":
                if exist_diversity is False:
                    for _, np in self.avail_hosts.iteritems():
                        if _chosen_host.cluster_name != "any" and np.cluster_name == _chosen_host.cluster_name:
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
                if chosen_host.rack_name != "any" and np.rack_name == chosen_host.rack_name:
                    np.rack_avail_vCPUs += _v.vCPUs
                    np.rack_avail_mem += _v.mem
                    np.rack_avail_local_disk += _v.local_volume_size
                    np.rack_num_of_placed_vms -= 1
                if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                    np.cluster_avail_vCPUs += _v.vCPUs
                    np.cluster_avail_mem += _v.mem
                    np.cluster_avail_local_disk += _v.local_volume_size
                    np.cluster_num_of_placed_vms -= 1

            for vml in _v.vm_list:
                if vml.node in self.node_placements.keys():
                    cn = self.avail_hosts[self.node_placements[vml.node].host_name]
                    level = cn.get_common_placement(chosen_host)
                    bandwidth = vml.nw_bandwidth
                    self.bandwidth_usage -= self._rollback_nw_reservation(level, chosen_host, cn, bandwidth)

            for voll in _v.volume_list:
                if voll.node in self.node_placements.keys():
                    cn = self.avail_hosts[self.node_placements[voll.node].host_name]
                    level = cn.get_common_placement(chosen_host)
                    bandwidth = voll.io_bandwidth
                    self.bandwidth_usage -= self._rollback_nw_reservation(level, chosen_host, cn, bandwidth)

    def _rollback_volume_reservation(self, _v):
        if _v in self.node_placements.keys():
            cs = self.node_placements[_v]
            storage_host = self.avail_storage_hosts[cs.storage.storage_name]
            storage_host.storage_avail_disk += _v.volume_size

            chosen_host = self.avail_hosts[self.node_placements[_v].host_name]

            for vml in _v.vm_list:
                if vml.node in self.node_placements.keys():
                    cn = self.avail_hosts[self.node_placements[vml.node].host_name]
                    level = cn.get_common_placement(chosen_host)
                    bandwidth = vml.io_bandwidth
                    self.bandwidth_usage -= self._rollback_nw_reservation(level, chosen_host, cn, bandwidth)

    def _rollback_nw_reservation(self, _level, _host1, _host2, _rsrv):
        nw_reservation = compute_reservation("host", _level, _rsrv)

        if _level == "host":
            for _, sr in _host1.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
            for _, sr in _host2.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
        elif _level == "rack":
            for _, sr in _host1.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
            for _, sr in _host2.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]

            for _, sr in _host1.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
            for _, sr in _host2.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
        elif _level == "cluster":
            for _, sr in _host1.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
            for _, sr in _host2.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]

            for _, sr in _host1.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
            for _, sr in _host2.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]

            for _, sr in _host1.cluster_avail_switches.iteritems():
                if sr.switch_type == "spine":
                    sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
            for _, sr in _host2.cluster_avail_switches.iteritems():
                if sr.switch_type == "spine":
                    sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]

        return nw_reservation

    def _rollback_node_placement(self, _v):
        if _v in self.node_placements.keys():
            del self.node_placements[_v]
            self.logger.debug("Search: node (" + _v.name + ") removed from placement")

        if isinstance(_v, VGroup):
            for _, sg in _v.subvgroups.iteritems():
                self._rollback_node_placement(sg)
