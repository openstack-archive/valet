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
import search_helper

from oslo_log import log

from valet.engine.optimizer.app_manager.group import Group
from valet.engine.optimizer.app_manager.group import LEVEL
from valet.engine.optimizer.app_manager.vm import VM
from valet.engine.optimizer.ostro.avail_resources import AvailResources
from valet.engine.optimizer.ostro.constraint_solver import ConstraintSolver
from valet.engine.optimizer.ostro.resource import GroupResource
from valet.engine.optimizer.ostro.resource import Resource
from valet.engine.resource_manager.resources.datacenter import Datacenter

LOG = log.getLogger(__name__)


class Search(object):
    """Bin-packing approach in the hierachical datacenter layout."""

    def __init__(self):
        """Initialization."""

        # search inputs
        self.app_topology = None
        self.resource = None

        # snapshot of current resource status
        self.avail_hosts = {}
        self.avail_groups = {}

        # search results
        self.node_placements = {}
        self.planned_placements = {}
        self.num_of_hosts = 0

        # optimization criteria
        self.CPU_weight = -1
        self.mem_weight = -1
        self.local_disk_weight = -1

        self.constraint_solver = None

    def _init_search(self, _app_topology):
        """Init the search information and the output results."""

        self.app_topology = _app_topology
        self.resource = _app_topology.resource

        self.avail_hosts.clear()
        self.avail_groups.clear()

        self.node_placements.clear()
        self.planned_placements.clear()
        self.num_of_hosts = 0

        self.CPU_weight = -1
        self.mem_weight = -1
        self.local_disk_weight = -1

        self.constraint_solver = ConstraintSolver(LOG)

        self._create_avail_groups()
        self._create_avail_hosts()

        if len(self.app_topology.old_vm_map) > 0:
            self._adjust_resources()

        if self.app_topology.action == "migrate":
            self._set_no_migrated_list()

        self._set_resource_weights()

    def plan(self, _app_topology):
        """Determine placements of new app creation."""

        self._init_search(_app_topology)

        LOG.info("search")

        open_node_list = self._open_list(self.app_topology.vms, self.app_topology.groups)

        avail_resources = AvailResources(LEVEL[len(LEVEL) - 1])
        avail_resources.avail_hosts = self.avail_hosts
        avail_resources.set_next_level()   # NOTE(GJ): skip 'cluster' level

        return self._run_greedy(open_node_list, avail_resources, "plan")

    def re_plan(self, _app_topology):
        """Compute prior (pending) placements again due to

        change request (stack-update, migrate) and decision conflicts (so 'replan').

        Do not search for the confirmed placements.
        """

        self._init_search(_app_topology)

        LOG.info("first, search for old placements")

        if self._re_plan() is False:
            if self.app_topology.status == "success":
                self.app_topology.status = "cannot keep prior placements as they were"
            LOG.error(self.app_topology.status)
            return False

        LOG.info("second, search for new placements")

        open_node_list = self._open_list(self.app_topology.vms, self.app_topology.groups)

        for v, r in self.planned_placements.iteritems():
            self.node_placements[v] = r

        avail_resources = AvailResources(LEVEL[len(LEVEL) - 1])
        avail_resources.avail_hosts = self.avail_hosts
        avail_resources.set_next_level()   # NOTE(GJ): skip 'cluster' level

        return self._run_greedy(open_node_list, avail_resources, "plan")

    def _re_plan(self):
        """Check if the prior placements change."""

        node_list = self._open_planned_list(self.app_topology.vms, self.app_topology.groups)
        if len(node_list) == 0:
            return True

        avail_resources = AvailResources(LEVEL[len(LEVEL) - 1])
        avail_resources.avail_hosts = self.avail_hosts
        avail_resources.set_next_level()   # NOTE(GJ): skip 'cluster' level

        return self._run_greedy(node_list, avail_resources, "planned")

    def _open_list(self, _vms, _groups):
        """Extract all vms and groups of each level (cluster, rack, host)."""

        open_node_list = []

        for _, vm in _vms.iteritems():
            self._set_node_weight(vm)
            open_node_list.append(vm)

        for _, g in _groups.iteritems():
            self._set_node_weight(g)
            open_node_list.append(g)

        return open_node_list

    def _open_planned_list(self, _vms, _groups):
        """Get vms and groups that were already placed."""

        planned_node_list = []

        for vk, vm in _vms.iteritems():
            if vk in self.app_topology.planned_vm_map.keys():
                hk = self.app_topology.planned_vm_map[vk]
                if hk not in self.avail_hosts.keys():
                    # if prior host is not available
                    LOG.warning("host (" + hk + ") is not available")
                    continue
                if vm.host is None or vm.host == "none":
                    vm.host = hk
                self._set_node_weight(vm)
                planned_node_list.append(vm)

        for gk, g in _groups.iteritems():
            vm_list = []
            search_helper.get_child_vms(g, vm_list)
            for vk in vm_list:
                if vk in self.app_topology.planned_vm_map.keys():
                    hk = self.app_topology.planned_vm_map[vk]
                    if hk not in self.avail_hosts.keys():
                        # if prior host is not available
                        LOG.warning("host (" + hk + ") is not available")
                        continue
                    if g.host is None or g.host == "none":
                        resource_name = search_helper.get_resource_of_level(hk, g.level, self.avail_hosts)
                        if resource_name is None:
                            LOG.warning("host {} is not available".format(resource_name))
                            continue
                        g.host = resource_name
                    node = None
                    for n in planned_node_list:
                        if n.orch_id == g.orch_id:
                            node = n
                            break
                    if node is None:
                        self._set_node_weight(g)
                        planned_node_list.append(g)
                    break

        return planned_node_list

    def _set_no_migrated_list(self):
        migrated_vm_id = self.app_topology.candidate_list_map.keys()[0]

        if migrated_vm_id not in self.app_topology.vms.keys():
            group = search_helper.get_group_of_vm(migrated_vm_id,
                                                  self.app_topology.groups)
            if group is not None:
                vm_list = []
                search_helper.get_child_vms(group, vm_list)
                for vk in vm_list:
                    if vk in self.app_topology.planned_vm_map.keys():
                        del self.app_topology.planned_vm_map[vk]
            else:
                LOG.error("migrated " + migrated_vm_id + " is missing")

    def _create_avail_hosts(self):
        """Create all available hosts."""

        for hk, host in self.resource.hosts.iteritems():
            if host.check_availability() is False:
                LOG.debug("Search: host (" + host.name +
                          ") not available at this time")
                continue

            r = Resource()
            r.host_name = hk

            for mk in host.memberships.keys():
                if mk in self.avail_groups.keys():
                    r.host_memberships[mk] = self.avail_groups[mk]

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
                    if mk in self.avail_groups.keys():
                        r.rack_memberships[mk] = self.avail_groups[mk]

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
                        if mk in self.avail_groups.keys():
                            r.cluster_memberships[mk] = self.avail_groups[mk]

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

    def _create_avail_groups(self):
        """Collect all available groups.

        Group type is affinity, diversity, exclusivity, AZ, host-aggregate.
        """

        for lgk, lg in self.resource.groups.iteritems():
            if lg.status != "enabled" or \
               (lg.group_type in ("AFF", "EX", "DIV") and len(lg.vm_list) == 0):
                LOG.warning("group (" + lg.name + ") disabled")
                continue

            lgr = GroupResource()
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
                        for vm_info in host.vm_list:
                            if lg.exist_vm(uuid=vm_info["uuid"]):
                                lgr.num_of_placed_vms -= 1
                        if hk in lgr.num_of_placed_vms_per_host.keys():
                            del lgr.num_of_placed_vms_per_host[hk]
                elif hk in self.resource.host_groups.keys():
                    host_group = self.resource.host_groups[hk]
                    if host_group.check_availability() is False:
                        for vm_info in host_group.vm_list:
                            if lg.exist_vm(uuid=vm_info["uuid"]):
                                lgr.num_of_placed_vms -= 1
                        if hk in lgr.num_of_placed_vms_per_host.keys():
                            del lgr.num_of_placed_vms_per_host[hk]

            self.avail_groups[lgk] = lgr

    def _adjust_resources(self):
        """Deduct all prior placements before search."""

        for v_id, vm_alloc in self.app_topology.old_vm_map.iteritems():
            if vm_alloc["host"] not in self.avail_hosts.keys():
                continue

            r = self.avail_hosts[vm_alloc["host"]]
            r.host_num_of_placed_vms -= 1
            r.host_avail_vCPUs += vm_alloc["vcpus"]
            r.host_avail_mem += vm_alloc["mem"]
            r.host_avail_local_disk += vm_alloc["local_volume"]
            if r.host_num_of_placed_vms == 0:
                self.num_of_hosts -= 1

            for _, rr in self.avail_hosts.iteritems():
                if rr.rack_name != "any" and rr.rack_name == r.rack_name:
                    rr.rack_num_of_placed_vms -= 1
                    rr.rack_avail_vCPUs += vm_alloc["vcpus"]
                    rr.rack_avail_mem += vm_alloc["mem"]
                    rr.rack_avail_local_disk += vm_alloc["local_volume"]

            for _, cr in self.avail_hosts.iteritems():
                if cr.cluster_name != "any" and \
                        cr.cluster_name == r.cluster_name:
                    cr.cluster_num_of_placed_vms -= 1
                    cr.cluster_avail_vCPUs += vm_alloc["vcpus"]
                    cr.cluster_avail_mem += vm_alloc["mem"]
                    cr.cluster_avail_local_disk += vm_alloc["local_volume"]

            for lgk in r.host_memberships.keys():
                if lgk not in self.avail_groups.keys():
                    continue

                lg = self.resource.groups[lgk]
                if lg.exist_vm(orch_id=v_id):
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

                    if lgr.group_type == "EX" or \
                       lgr.group_type == "AFF" or \
                       lgr.group_type == "DIV":
                        if lgr.num_of_placed_vms == 0:
                            del self.avail_groups[lgk]

            for lgk in r.rack_memberships.keys():
                if lgk not in self.avail_groups.keys():
                    continue

                lg = self.resource.groups[lgk]
                if lg.group_type == "EX" or \
                   lg.group_type == "AFF" or \
                   lg.group_type == "DIV":
                    if lgk.split(":")[0] == "rack":
                        if lg.exist_vm(orch_id=v_id):
                            lgr = r.rack_memberships[lgk]
                            lgr.num_of_placed_vms -= 1

                            if r.rack_name in lgr.num_of_placed_vms_per_host.keys():
                                lgr.num_of_placed_vms_per_host[r.rack_name] -= 1
                                if lgr.num_of_placed_vms_per_host[r.rack_name] == 0:
                                    del lgr.num_of_placed_vms_per_host[r.rack_name]
                                    for _, rr in self.avail_hosts.iteritems():
                                        if rr.rack_name != "any" and \
                                                rr.rack_name == \
                                                r.rack_name:
                                            del rr.rack_memberships[lgk]

                            if lgr.num_of_placed_vms == 0:
                                del self.avail_groups[lgk]

            for lgk in r.cluster_memberships.keys():
                if lgk not in self.avail_groups.keys():
                    continue

                lg = self.resource.groups[lgk]
                if lg.group_type == "EX" or \
                   lg.group_type == "AFF" or \
                   lg.group_type == "DIV":
                    if lgk.split(":")[0] == "cluster":
                        if lg.exist_vm(orch_id=v_id) is True:
                            lgr = r.cluster_memberships[lgk]
                            lgr.num_of_placed_vms -= 1

                            if r.cluster_name in lgr.num_of_placed_vms_per_host.keys():
                                lgr.num_of_placed_vms_per_host[r.cluster_name] -= 1
                                if lgr.num_of_placed_vms_per_host[r.cluster_name] == 0:
                                    del lgr.num_of_placed_vms_per_host[r.cluster_name]
                                    for _, cr in self.avail_hosts.iteritems():
                                        if cr.cluster_name != "any" and \
                                                cr.cluster_name == \
                                                r.cluster_name:
                                            del cr.cluster_memberships[lgk]

                            if lgr.num_of_placed_vms == 0:
                                del self.avail_groups[lgk]

    def _set_resource_weights(self):
        """Compute weight of each resource type."""
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

    def _set_node_weight(self, _v):
        """Compute each vm's weight."""
        _v.sort_base = -1
        _v.sort_base = self.CPU_weight * _v.vCPU_weight
        _v.sort_base += self.mem_weight * _v.mem_weight
        _v.sort_base += self.local_disk_weight * _v.local_volume_weight

    def _set_compute_sort_base(self, _level, _candidate_list):
        """Compute the weight of each candidate host."""
        for c in _candidate_list:
            CPU_ratio = -1
            mem_ratio = -1
            ldisk_ratio = -1

            cpu_available = float(self.resource.CPU_avail)
            mem_available = float(self.resource.mem_avail)
            dsk_available = float(self.resource.local_disk_avail)

            if _level == "cluster":
                CPU_ratio = float(c.cluster_avail_vCPUs) / cpu_available
                mem_ratio = float(c.cluster_avail_mem) / mem_available
                ldisk_ratio = float(c.cluster_avail_local_disk) / dsk_available
            elif _level == "rack":
                CPU_ratio = float(c.rack_avail_vCPUs) / cpu_available
                mem_ratio = float(c.rack_avail_mem) / mem_available
                ldisk_ratio = float(c.rack_avail_local_disk) / dsk_available
            elif _level == "host":
                CPU_ratio = float(c.host_avail_vCPUs) / cpu_available
                mem_ratio = float(c.host_avail_mem) / mem_available
                ldisk_ratio = float(c.host_avail_local_disk) / dsk_available
            c.sort_base = (1.0 - self.CPU_weight) * CPU_ratio + \
                          (1.0 - self.mem_weight) * mem_ratio + \
                          (1.0 - self.local_disk_weight) * ldisk_ratio

    def _run_greedy(self, _open_node_list, _avail_resources, _mode):
        """Search placements with greedy algorithm."""

        LOG.debug("level = " + _avail_resources.level)
        for n in _open_node_list:
            LOG.debug("current open node = " + n.orch_id)

        _open_node_list.sort(
            key=operator.attrgetter("sort_base"), reverse=True)

        while len(_open_node_list) > 0:
            n = _open_node_list.pop(0)

            LOG.debug("node = " + n.orch_id)

            best_resource = None
            if _mode == "plan":
                best_resource = self._get_best_resource(n, _avail_resources,
                                                        _mode)
            else:
                best_resource = self._get_best_resource_for_planned(n, _avail_resources, _mode)

            if best_resource is None:
                LOG.error("fail placement decision")
                return False
            else:
                self._deduct_resources(_avail_resources.level,
                                       best_resource, n)
                if _mode == "plan":
                    self._close_node_placement(_avail_resources.level,
                                               best_resource, n)
                else:
                    self._close_planned_placement(_avail_resources.level,
                                                  best_resource, n)

        return True

    def _get_best_resource_for_planned(self, _n, _avail_resources, _mode):
        """Check if the given placement is still held.

        For update case, perform constraint solvings to see any placement violation.
        """

        resource_of_level = search_helper.get_node_resource_of_level(_n, _avail_resources.level, self.avail_hosts)
        _avail_resources.set_candidate(resource_of_level)

        if len(_avail_resources.candidates) == 0:
            if self.app_topology.status == "success":
                self.app_topology.status = "no available resource"
            LOG.error(self.app_topology.status)
            return None

        for ck in _avail_resources.candidates.keys():
            LOG.debug("candidate = " + ck)

        if self.app_topology.action == "update":
            candidate_list = self.constraint_solver.get_candidate_list(_n, self.planned_placements, _avail_resources, self.avail_groups)
            if len(candidate_list) == 0:
                if self.app_topology.status == "success":
                    self.app_topology.status = self.constraint_solver.status
                return None

        best_resource = None
        if _avail_resources.level == "host" and isinstance(_n, VM):
            best_resource = copy.deepcopy(_avail_resources.candidates[resource_of_level])
            best_resource.level = "host"
        else:
            # Get the next open_node_list and level
            (vms, groups) = search_helper.get_next_placements(_n, _avail_resources.level)
            open_node_list = self._open_planned_list(vms, groups)

            avail_resources = AvailResources(_avail_resources.level)
            avail_resources.set_next_avail_hosts(_avail_resources.avail_hosts, resource_of_level)
            avail_resources.set_next_level()

            # Recursive call
            if self._run_greedy(open_node_list, avail_resources, _mode) is True:
                best_resource = copy.deepcopy(_avail_resources.candidates[resource_of_level])
                best_resource.level = _avail_resources.level

        return best_resource

    def _get_best_resource(self, _n, _avail_resources, _mode):
        """Determine the best placement for given vm or affinity group."""

        candidate_list = []
        planned_resource = None

        # if this is already planned one
        if _n in self.planned_placements.keys():
            planned_resource = _avail_resources.get_candidate(self.planned_placements[_n])
            candidate_list.append(planned_resource)

        else:
            resource_list = []

            if len(self.app_topology.candidate_list_map) > 0:
                vm_id = self.app_topology.candidate_list_map.keys()[0]
                candidate_host_list = self.app_topology.candidate_list_map[vm_id]

                if (isinstance(_n, VM) and vm_id == _n.orch_id) or \
                   (isinstance(_n, Group) and search_helper.check_vm_grouping(_n, vm_id) is True):
                    for hk in candidate_host_list:
                        resource_name = search_helper.get_resource_of_level(hk, _avail_resources.level, self.avail_hosts)
                        if resource_name is not None:
                            if resource_name not in resource_list:
                                resource_list.append(resource_name)
                        else:
                            LOG.warning("cannot find candidate resource while replanning")
                    for rk in resource_list:
                        _avail_resources.set_candidate(rk)

            if len(resource_list) == 0:
                _avail_resources.set_candidates()

            candidate_list = self.constraint_solver.get_candidate_list(_n, self.node_placements, _avail_resources, self.avail_groups)

        if len(candidate_list) == 0:
            if self.app_topology.status == "success":
                if self.constraint_solver.status != "success":
                    self.app_topology.status = self.constraint_solver.status
                else:
                    self.app_topology.status = "fail to get candidate hosts"
            return None

        if len(candidate_list) > 1:
            self._set_compute_sort_base(_avail_resources.level, candidate_list)
            candidate_list.sort(key=operator.attrgetter("sort_base"))

        best_resource = None
        if _avail_resources.level == "host" and isinstance(_n, VM):
            best_resource = copy.deepcopy(candidate_list[0])
            best_resource.level = "host"
        else:
            while len(candidate_list) > 0:
                cr = candidate_list.pop(0)

                (vms, groups) = search_helper.get_next_placements(_n, _avail_resources.level)
                open_node_list = self._open_list(vms, groups)

                avail_resources = AvailResources(_avail_resources.level)
                resource_name = cr.get_resource_name(_avail_resources.level)
                LOG.debug("try " + resource_name)

                avail_resources.set_next_avail_hosts(_avail_resources.avail_hosts, resource_name)
                avail_resources.set_next_level()

                # Recursive call
                if self._run_greedy(open_node_list, avail_resources,
                                    _mode) is True:
                    best_resource = copy.deepcopy(cr)
                    best_resource.level = _avail_resources.level
                    break
                else:
                    if planned_resource is None:
                        LOG.warning("rollback candidate = " + resource_name)
                        self._rollback_resources(_n)
                        self._rollback_node_placement(_n)
                        if len(candidate_list) > 0 and \
                           self.app_topology.status != "success":
                            self.app_topology.status = "success"
                    else:
                        break

        if best_resource is None and len(candidate_list) == 0:
            if self.app_topology.status == "success":
                self.app_topology.status = "no available hosts"
            LOG.warning(self.app_topology.status)

        return best_resource

    def _deduct_resources(self, _level, _best, _n):
        """Reflect new placement in host resources and groups."""

        if _n in self.planned_placements.keys() or \
           _n in self.node_placements.keys():
            return

        exclusivities = _n.get_exclusivities(_level)
        exclusivity_id = None
        if len(exclusivities) == 1:
            exclusivity_id = exclusivities[exclusivities.keys()[0]]
        if exclusivity_id is not None:
            self._add_exclusivity(_level, _best, exclusivity_id)

        if isinstance(_n, Group):
            affinity_id = _n.get_affinity_id()
            if affinity_id is not None and affinity_id.split(":")[1] != "any":
                self._add_affinity(_level, _best, affinity_id)

        if len(_n.diversity_groups) > 0:
            for _, diversity_id in _n.diversity_groups.iteritems():
                if diversity_id.split(":")[1] != "any":
                    self._add_diversity(_level, _best, diversity_id)

        if isinstance(_n, VM) and _level == "host":
            self._deduct_vm_resources(_best, _n)

    def _add_exclusivity(self, _level, _best, _exclusivity_id):
        """Add new exclusivity group."""

        LOG.info("find exclusivity (" + _exclusivity_id + ")")

        lgr = None
        if _exclusivity_id not in self.avail_groups.keys():
            lgr = GroupResource()
            lgr.name = _exclusivity_id
            lgr.group_type = "EX"
            self.avail_groups[lgr.name] = lgr
        else:
            lgr = self.avail_groups[_exclusivity_id]

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
        """Add new affinity group."""

        LOG.info("find affinity (" + _affinity_id + ")")

        lgr = None
        if _affinity_id not in self.avail_groups.keys():
            lgr = GroupResource()
            lgr.name = _affinity_id
            lgr.group_type = "AFF"
            self.avail_groups[lgr.name] = lgr
        else:
            lgr = self.avail_groups[_affinity_id]

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

    def _add_diversity(self, _level, _best, _diversity_id):
        """Add new diversity group."""

        LOG.info("find diversity (" + _diversity_id + ")")

        lgr = None
        if _diversity_id not in self.avail_groups.keys():
            lgr = GroupResource()
            lgr.name = _diversity_id
            lgr.group_type = "DIV"
            self.avail_groups[lgr.name] = lgr
        else:
            lgr = self.avail_groups[_diversity_id]

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
        """Reflect the reduced amount of resources in the chosen host."""

        chosen_host = self.avail_hosts[_best.host_name]
        chosen_host.host_avail_vCPUs -= _n.vCPUs
        chosen_host.host_avail_mem -= _n.mem
        chosen_host.host_avail_local_disk -= _n.local_volume_size

        if chosen_host.host_num_of_placed_vms == 0:
            self.num_of_hosts += 1
        chosen_host.host_num_of_placed_vms += 1

        for _, np in self.avail_hosts.iteritems():
            if chosen_host.rack_name != "any" and \
               np.rack_name == chosen_host.rack_name:
                np.rack_avail_vCPUs -= _n.vCPUs
                np.rack_avail_mem -= _n.mem
                np.rack_avail_local_disk -= _n.local_volume_size
                np.rack_num_of_placed_vms += 1
            if chosen_host.cluster_name != "any" and \
               np.cluster_name == chosen_host.cluster_name:
                np.cluster_avail_vCPUs -= _n.vCPUs
                np.cluster_avail_mem -= _n.mem
                np.cluster_avail_local_disk -= _n.local_volume_size
                np.cluster_num_of_placed_vms += 1

    def _close_node_placement(self, _level, _best, _v):
        """Record the final placement decision."""
        if _v not in self.node_placements.keys() and \
           _v not in self.planned_placements.keys():
            if _level == "host" or isinstance(_v, Group):
                self.node_placements[_v] = _best

    def _close_planned_placement(self, _level, _best, _v):
        """Set the decision for planned vm or group."""
        if _v not in self.planned_placements.keys():
            if _level == "host" or isinstance(_v, Group):
                self.planned_placements[_v] = _best

    def _rollback_resources(self, _v):
        """Rollback the placement."""

        if isinstance(_v, VM):
            self._rollback_vm_resources(_v)
        elif isinstance(_v, Group):
            for _, v in _v.subgroups.iteritems():
                self._rollback_resources(v)

        if _v in self.node_placements.keys():
            chosen_host = self.avail_hosts[self.node_placements[_v].host_name]
            level = self.node_placements[_v].level

            if isinstance(_v, Group):
                affinity_id = _v.level + ":" + _v.name
                if _v.name != "any":
                    self._remove_affinity(chosen_host, affinity_id, level)

            exclusivities = _v.get_exclusivities(level)
            if len(exclusivities) == 1:
                exclusivity_id = exclusivities[exclusivities.keys()[0]]
                self._remove_exclusivity(chosen_host, exclusivity_id, level)

            if len(_v.diversity_groups) > 0:
                for _, diversity_id in _v.diversity_groups.iteritems():
                    if diversity_id.split(":")[1] != "any":
                        self._remove_diversity(chosen_host,
                                               diversity_id,
                                               level)

    def _remove_exclusivity(self, _chosen_host, _exclusivity_id, _level):
        """Remove the exclusivity group."""

        if _exclusivity_id.split(":")[0] == _level:
            lgr = self.avail_groups[_exclusivity_id]

            host_name = _chosen_host.get_resource_name(_level)
            lgr.num_of_placed_vms -= 1
            lgr.num_of_placed_vms_per_host[host_name] -= 1

            if lgr.num_of_placed_vms_per_host[host_name] == 0:
                del lgr.num_of_placed_vms_per_host[host_name]

            if lgr.num_of_placed_vms == 0:
                del self.avail_groups[_exclusivity_id]

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
        """Remove affinity group."""

        if _affinity_id.split(":")[0] == _level:
            lgr = self.avail_groups[_affinity_id]

            host_name = _chosen_host.get_resource_name(_level)
            lgr.num_of_placed_vms -= 1
            lgr.num_of_placed_vms_per_host[host_name] -= 1

            if lgr.num_of_placed_vms_per_host[host_name] == 0:
                del lgr.num_of_placed_vms_per_host[host_name]

            if lgr.num_of_placed_vms == 0:
                del self.avail_groups[_affinity_id]

            exist_affinity = True
            if _affinity_id not in self.avail_groups.keys():
                exist_affinity = False
            else:
                lgr = self.avail_groups[_affinity_id]
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

    def _remove_diversity(self, _chosen_host, _diversity_id, _level):
        """Remove diversity group."""

        if _diversity_id.split(":")[0] == _level:
            lgr = self.avail_groups[_diversity_id]

            host_name = _chosen_host.get_resource_name(_level)
            lgr.num_of_placed_vms -= 1
            lgr.num_of_placed_vms_per_host[host_name] -= 1

            if lgr.num_of_placed_vms_per_host[host_name] == 0:
                del lgr.num_of_placed_vms_per_host[host_name]

            if lgr.num_of_placed_vms == 0:
                del self.avail_groups[_diversity_id]

            exist_diversity = True
            if _diversity_id not in self.avail_groups.keys():
                exist_diversity = False
            else:
                lgr = self.avail_groups[_diversity_id]
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

    def _rollback_vm_resources(self, _v):
        """Return back the amount of resources to host."""

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
        """Remove placement decisions."""
        if _v in self.node_placements.keys():
            del self.node_placements[_v]
        if isinstance(_v, Group):
            for _, sg in _v.subgroups.iteritems():
                self._rollback_node_placement(sg)
