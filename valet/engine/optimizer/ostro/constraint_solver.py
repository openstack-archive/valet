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

from valet.engine.optimizer.app_manager.app_topology_base import VGroup, VM, LEVELS
from valet.engine.optimizer.ostro.openstack_filters import AggregateInstanceExtraSpecsFilter
from valet.engine.optimizer.ostro.openstack_filters import AvailabilityZoneFilter
from valet.engine.optimizer.ostro.openstack_filters import CoreFilter
from valet.engine.optimizer.ostro.openstack_filters import DiskFilter
from valet.engine.optimizer.ostro.openstack_filters import RamFilter


class ConstraintSolver(object):

    def __init__(self, _logger):
        self.logger = _logger

        self.openstack_AZ = AvailabilityZoneFilter(self.logger)
        self.openstack_AIES = AggregateInstanceExtraSpecsFilter(self.logger)
        self.openstack_R = RamFilter(self.logger)
        self.openstack_C = CoreFilter(self.logger)
        self.openstack_D = DiskFilter(self.logger)

        self.status = "success"

    def compute_candidate_list(self, _level, _n, _node_placements, _avail_resources, _avail_logical_groups):
        candidate_list = []

        ''' when replanning '''
        if _n.node.host is not None and len(_n.node.host) > 0:
            self.logger.debug("ConstraintSolver: reconsider with given candidates")
            for hk in _n.node.host:
                for ark, ar in _avail_resources.iteritems():
                    if hk == ark:
                        candidate_list.append(ar)
        else:
            for _, r in _avail_resources.iteritems():
                candidate_list.append(r)
        if len(candidate_list) == 0:
            self.status = "no candidate for node = " + _n.node.name
            self.logger.warn("ConstraintSolver: " + self.status)
            return candidate_list
        else:
            self.logger.debug("ConstraintSolver: num of candidates = " + str(len(candidate_list)))

        ''' availability zone constraint '''
        if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
            if (isinstance(_n.node, VM) and _n.node.availability_zone is not None) or \
               (isinstance(_n.node, VGroup) and len(_n.node.availability_zone_list) > 0):
                self._constrain_availability_zone(_level, _n, candidate_list)
                if len(candidate_list) == 0:
                    self.status = "violate availability zone constraint for node = " + _n.node.name
                    self.logger.error("ConstraintSolver: " + self.status)
                    return candidate_list
                else:
                    self.logger.debug("ConstraintSolver: done availability_zone constraint")

        ''' host aggregate constraint '''
        if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
            if len(_n.node.extra_specs_list) > 0:
                self._constrain_host_aggregates(_level, _n, candidate_list)
                if len(candidate_list) == 0:
                    self.status = "violate host aggregate constraint for node = " + _n.node.name
                    self.logger.error("ConstraintSolver: " + self.status)
                    return candidate_list
                else:
                    self.logger.debug("ConstraintSolver: done host_aggregate constraint")

        ''' cpu capacity constraint '''
        if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
            self._constrain_cpu_capacity(_level, _n, candidate_list)
            if len(candidate_list) == 0:
                self.status = "violate cpu capacity constraint for node = " + _n.node.name
                self.logger.error("ConstraintSolver: " + self.status)
                return candidate_list
            else:
                self.logger.debug("ConstraintSolver: done cpu capacity constraint")

        ''' memory capacity constraint '''
        if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
            self._constrain_mem_capacity(_level, _n, candidate_list)
            if len(candidate_list) == 0:
                self.status = "violate memory capacity constraint for node = " + _n.node.name
                self.logger.error("ConstraintSolver: " + self.status)
                return candidate_list
            else:
                self.logger.debug("ConstraintSolver: done memory capacity constraint")

        ''' local disk capacity constraint '''
        if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
            self._constrain_local_disk_capacity(_level, _n, candidate_list)
            if len(candidate_list) == 0:
                self.status = "violate local disk capacity constraint for node = " + _n.node.name
                self.logger.error("ConstraintSolver: " + self.status)
                return candidate_list
            else:
                self.logger.debug("ConstraintSolver: done local disk capacity constraint")

        ''' network bandwidth constraint '''
        self._constrain_nw_bandwidth_capacity(_level, _n, _node_placements, candidate_list)
        if len(candidate_list) == 0:
            self.status = "violate nw bandwidth capacity constraint for node = " + _n.node.name
            self.logger.error("ConstraintSolver: " + self.status)
            return candidate_list
        else:
            self.logger.debug("ConstraintSolver: done bandwidth capacity constraint")

        ''' diversity constraint '''
        if len(_n.node.diversity_groups) > 0:
            for _, diversity_id in _n.node.diversity_groups.iteritems():
                if diversity_id.split(":")[0] == _level:
                    if diversity_id in _avail_logical_groups.keys():
                        self._constrain_diversity_with_others(_level, diversity_id, candidate_list)
                        if len(candidate_list) == 0:
                            break
            if len(candidate_list) == 0:
                self.status = "violate diversity constraint for node = " + _n.node.name
                self.logger.error("ConstraintSolver: " + self.status)
                return candidate_list
            else:
                self._constrain_diversity(_level, _n, _node_placements, candidate_list)
                if len(candidate_list) == 0:
                    self.status = "violate diversity constraint for node = " + _n.node.name
                    self.logger.error("ConstraintSolver: " + self.status)
                    return candidate_list
                else:
                    self.logger.debug("ConstraintSolver: done diversity_group constraint")

        ''' exclusivity constraint '''
        exclusivities = self.get_exclusivities(_n.node.exclusivity_groups, _level)
        if len(exclusivities) > 1:
            self.status = "violate exclusivity constraint (more than one exclusivity) for node = " + _n.node.name
            self.logger.error("ConstraintSolver: " + self.status)
            return []
        else:
            if len(exclusivities) == 1:
                exclusivity_id = exclusivities[exclusivities.keys()[0]]
                if exclusivity_id.split(":")[0] == _level:
                    self._constrain_exclusivity(_level, exclusivity_id, candidate_list)
                    if len(candidate_list) == 0:
                        self.status = "violate exclusivity constraint for node = " + _n.node.name
                        self.logger.error("ConstraintSolver: " + self.status)
                        return candidate_list
                    else:
                        self.logger.debug("ConstraintSolver: done exclusivity_group constraint")
            else:
                self._constrain_non_exclusivity(_level, candidate_list)
                if len(candidate_list) == 0:
                    self.status = "violate non-exclusivity constraint for node = " + _n.node.name
                    self.logger.error("ConstraintSolver: " + self.status)
                    return candidate_list
                else:
                    self.logger.debug("ConstraintSolver: done non-exclusivity_group constraint")

        ''' affinity constraint '''
        affinity_id = _n.get_affinity_id()  # level:name, except name == "any"
        if affinity_id is not None:
            if affinity_id.split(":")[0] == _level:
                if affinity_id in _avail_logical_groups.keys():
                    self._constrain_affinity(_level, affinity_id, candidate_list)
                    if len(candidate_list) == 0:
                        self.status = "violate affinity constraint for node = " + _n.node.name
                        self.logger.error("ConstraintSolver: " + self.status)
                        return candidate_list
                    else:
                        self.logger.debug("ConstraintSolver: done affinity_group constraint")

        return candidate_list

    '''
    constraint modules
    '''

    def _constrain_affinity(self, _level, _affinity_id, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.exist_group(_level, _affinity_id, "AFF", r) is False:
                if r not in conflict_list:
                    conflict_list.append(r)

                    debug_resource_name = r.get_resource_name(_level)
                    self.logger.debug("ConstraintSolver: not exist affinity in resource = " + debug_resource_name)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def _constrain_diversity_with_others(self, _level, _diversity_id, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.exist_group(_level, _diversity_id, "DIV", r) is True:
                if r not in conflict_list:
                    conflict_list.append(r)

                    debug_resource_name = r.get_resource_name(_level)
                    self.logger.debug("ConstraintSolver: conflict diversity in resource = " + debug_resource_name)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def exist_group(self, _level, _id, _group_type, _candidate):
        match = False

        memberships = _candidate.get_memberships(_level)
        for lgk, lgr in memberships.iteritems():
            if lgr.group_type == _group_type and lgk == _id:
                match = True
                break

        return match

    def _constrain_diversity(self, _level, _n, _node_placements, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.conflict_diversity(_level, _n, _node_placements, r) is True:
                if r not in conflict_list:
                    conflict_list.append(r)

                    resource_name = r.get_resource_name(_level)
                    self.logger.debug("ConstraintSolver: conflict the diversity in resource = " + resource_name)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def conflict_diversity(self, _level, _n, _node_placements, _candidate):
        conflict = False

        for v in _node_placements.keys():
            diversity_level = _n.get_common_diversity(v.diversity_groups)
            if diversity_level != "ANY" and LEVELS.index(diversity_level) >= LEVELS.index(_level):
                if diversity_level == "host":
                    if _candidate.cluster_name == _node_placements[v].cluster_name and \
                       _candidate.rack_name == _node_placements[v].rack_name and  \
                       _candidate.host_name == _node_placements[v].host_name:
                        conflict = True
                        break
                elif diversity_level == "rack":
                    if _candidate.cluster_name == _node_placements[v].cluster_name and \
                       _candidate.rack_name == _node_placements[v].rack_name:
                        conflict = True
                        break
                elif diversity_level == "cluster":
                    if _candidate.cluster_name == _node_placements[v].cluster_name:
                        conflict = True
                        break

        return conflict

    def _constrain_non_exclusivity(self, _level, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.conflict_exclusivity(_level, r) is True:
                if r not in conflict_list:
                    conflict_list.append(r)

                    debug_resource_name = r.get_resource_name(_level)
                    self.logger.debug("ConstraintSolver: exclusivity defined in resource = " + debug_resource_name)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def conflict_exclusivity(self, _level, _candidate):
        conflict = False

        memberships = _candidate.get_memberships(_level)
        for mk in memberships.keys():
            if memberships[mk].group_type == "EX" and mk.split(":")[0] == _level:
                conflict = True

        return conflict

    def get_exclusivities(self, _exclusivity_groups, _level):
        exclusivities = {}

        for exk, level in _exclusivity_groups.iteritems():
            if level.split(":")[0] == _level:
                exclusivities[exk] = level

        return exclusivities

    def _constrain_exclusivity(self, _level, _exclusivity_id, _candidate_list):
        candidate_list = self._get_exclusive_candidates(_level, _exclusivity_id, _candidate_list)

        if len(candidate_list) == 0:
            candidate_list = self._get_hibernated_candidates(_level, _candidate_list)
            _candidate_list[:] = [x for x in _candidate_list if x in candidate_list]
        else:
            _candidate_list[:] = [x for x in _candidate_list if x in candidate_list]

    def _get_exclusive_candidates(self, _level, _exclusivity_id, _candidate_list):
        candidate_list = []

        for r in _candidate_list:
            if self.exist_group(_level, _exclusivity_id, "EX", r) is True:
                if r not in candidate_list:
                    candidate_list.append(r)
            else:
                debug_resource_name = r.get_resource_name(_level)
                self.logger.debug("ConstraintSolver: exclusivity not exist in resource = " + debug_resource_name)

        return candidate_list

    def _get_hibernated_candidates(self, _level, _candidate_list):
        candidate_list = []

        for r in _candidate_list:
            if self.check_hibernated(_level, r) is True:
                if r not in candidate_list:
                    candidate_list.append(r)
            else:
                debug_resource_name = r.get_resource_name(_level)
                self.logger.debug("ConstraintSolver: exclusivity not allowed in resource = " + debug_resource_name)

        return candidate_list

    def check_hibernated(self, _level, _candidate):
        match = False

        num_of_placed_vms = _candidate.get_num_of_placed_vms(_level)
        if num_of_placed_vms == 0:
            match = True

        return match

    def _constrain_host_aggregates(self, _level, _n, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.check_host_aggregates(_level, r, _n.node) is False:
                if r not in conflict_list:
                    conflict_list.append(r)

                    debug_resource_name = r.get_resource_name(_level)
                    self.logger.debug("ConstraintSolver: not meet aggregate in resource = " + debug_resource_name)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def check_host_aggregates(self, _level, _candidate, _v):
        return self.openstack_AIES.host_passes(_level, _candidate, _v)

    def _constrain_availability_zone(self, _level, _n, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.check_availability_zone(_level, r, _n.node) is False:
                if r not in conflict_list:
                    conflict_list.append(r)

                    debug_resource_name = r.get_resource_name(_level)
                    self.logger.debug("ConstraintSolver: not meet az in resource = " + debug_resource_name)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def check_availability_zone(self, _level, _candidate, _v):
        return self.openstack_AZ.host_passes(_level, _candidate, _v)

    def _constrain_cpu_capacity(self, _level, _n, _candidate_list):
        conflict_list = []

        for ch in _candidate_list:
            if self.check_cpu_capacity(_level, _n.node, ch) is False:
                conflict_list.append(ch)

                debug_resource_name = ch.get_resource_name(_level)
                self.logger.debug("ConstraintSolver: lack of cpu in " + debug_resource_name)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def check_cpu_capacity(self, _level, _v, _candidate):
        return self.openstack_C.host_passes(_level, _candidate, _v)

    def _constrain_mem_capacity(self, _level, _n, _candidate_list):
        conflict_list = []

        for ch in _candidate_list:
            if self.check_mem_capacity(_level, _n.node, ch) is False:
                conflict_list.append(ch)

                debug_resource_name = ch.get_resource_name(_level)
                self.logger.debug("ConstraintSolver: lack of mem in " + debug_resource_name)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def check_mem_capacity(self, _level, _v, _candidate):
        return self.openstack_R.host_passes(_level, _candidate, _v)

    def _constrain_local_disk_capacity(self, _level, _n, _candidate_list):
        conflict_list = []

        for ch in _candidate_list:
            if self.check_local_disk_capacity(_level, _n.node, ch) is False:
                conflict_list.append(ch)

                debug_resource_name = ch.get_resource_name(_level)
                self.logger.debug("ConstraintSolver: lack of local disk in " + debug_resource_name)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def check_local_disk_capacity(self, _level, _v, _candidate):
        return self.openstack_D.host_passes(_level, _candidate, _v)

    def _constrain_storage_capacity(self, _level, _n, _candidate_list):
        conflict_list = []

        for ch in _candidate_list:
            if self.check_storage_availability(_level, _n.node, ch) is False:
                conflict_list.append(ch)

                debug_resource_name = ch.get_resource_name(_level)
                avail_storages = ch.get_avail_storages(_level)
                avail_disks = []
                volume_classes = []
                volume_sizes = []
                if isinstance(_n.node, VGroup):
                    for vck in _n.node.volume_sizes.keys():
                        volume_classes.append(vck)
                        volume_sizes.append(_n.node.volume_sizes[vck])
                else:
                    volume_classes.append(_n.node.volume_class)
                    volume_sizes.append(_n.node.volume_size)

                for vc in volume_classes:
                    for _, s in avail_storages.iteritems():
                        if vc == "any" or s.storage_class == vc:
                            avail_disks.append(s.storage_avail_disk)

                self.logger.debug("ConstraintSolver: storage constrained in resource = " + debug_resource_name)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def check_storage_availability(self, _level, _v, _ch):
        available = False

        volume_sizes = []
        if isinstance(_v, VGroup):
            for vck in _v.volume_sizes.keys():
                volume_sizes.append((vck, _v.volume_sizes[vck]))
        else:
            volume_sizes.append((_v.volume_class, _v.volume_size))

        avail_storages = _ch.get_avail_storages(_level)
        for vc, vs in volume_sizes:
            for _, s in avail_storages.iteritems():
                if vc == "any" or s.storage_class == vc:
                    if s.storage_avail_disk >= vs:
                        available = True
                        break
                    else:
                        available = False
            if available is False:
                break

        return available

    def _constrain_nw_bandwidth_capacity(self, _level, _n, _node_placements, _candidate_list):
        conflict_list = []

        for cr in _candidate_list:
            if self.check_nw_bandwidth_availability(_level, _n, _node_placements, cr) is False:
                if cr not in conflict_list:
                    conflict_list.append(cr)

                    debug_resource_name = cr.get_resource_name(_level)
                    self.logger.debug("ConstraintSolver: bw constrained in resource = " + debug_resource_name)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def check_nw_bandwidth_availability(self, _level, _n, _node_placements, _cr):
        # NOTE: 3rd entry for special node requiring bandwidth of out-going from spine switch
        total_req_bandwidths = [0, 0, 0]

        link_list = _n.get_all_links()

        for vl in link_list:
            bandwidth = _n.get_bandwidth_of_link(vl)

            placement_level = None
            if vl.node in _node_placements.keys():  # vl.node is VM or Volume
                placement_level = _node_placements[vl.node].get_common_placement(_cr)
            else:  # in the open list
                placement_level = _n.get_common_diversity(vl.node.diversity_groups)
                if placement_level == "ANY":
                    implicit_diversity = self.get_implicit_diversity(_n.node, link_list, vl.node, _level)
                    if implicit_diversity[0] is not None:
                        placement_level = implicit_diversity[1]

            self.get_req_bandwidths(_level, placement_level, bandwidth, total_req_bandwidths)

        return self._check_nw_bandwidth_availability(_level, total_req_bandwidths, _cr)

    # to find any implicit diversity relation caused by the other links of _v
    # (i.e., intersection between _v and _target_v)
    def get_implicit_diversity(self, _v, _link_list, _target_v, _level):
        max_implicit_diversity = (None, 0)

        for vl in _link_list:
            diversity_level = _v.get_common_diversity(vl.node.diversity_groups)
            if diversity_level != "ANY" and LEVELS.index(diversity_level) >= LEVELS.index(_level):
                for dk, dl in vl.node.diversity_groups.iteritems():
                    if LEVELS.index(dl) > LEVELS.index(diversity_level):
                        if _target_v.uuid != vl.node.uuid:
                            if dk in _target_v.diversity_groups.keys():
                                if LEVELS.index(dl) > max_implicit_diversity[1]:
                                    max_implicit_diversity = (dk, dl)

        return max_implicit_diversity

    def get_req_bandwidths(self, _level, _placement_level, _bandwidth, _total_req_bandwidths):
        if _level == "cluster" or _level == "rack":
            if _placement_level == "cluster" or _placement_level == "rack":
                _total_req_bandwidths[1] += _bandwidth
        elif _level == "host":
            if _placement_level == "cluster" or _placement_level == "rack":
                _total_req_bandwidths[1] += _bandwidth
                _total_req_bandwidths[0] += _bandwidth
            elif _placement_level == "host":
                _total_req_bandwidths[0] += _bandwidth

    def _check_nw_bandwidth_availability(self, _level, _req_bandwidths, _candidate_resource):
        available = True

        if _level == "cluster":
            cluster_avail_bandwidths = []
            for _, sr in _candidate_resource.cluster_avail_switches.iteritems():
                cluster_avail_bandwidths.append(max(sr.avail_bandwidths))

            if max(cluster_avail_bandwidths) < _req_bandwidths[1]:
                available = False

        elif _level == "rack":
            rack_avail_bandwidths = []
            for _, sr in _candidate_resource.rack_avail_switches.iteritems():
                rack_avail_bandwidths.append(max(sr.avail_bandwidths))

            if max(rack_avail_bandwidths) < _req_bandwidths[1]:
                available = False

        elif _level == "host":
            host_avail_bandwidths = []
            for _, sr in _candidate_resource.host_avail_switches.iteritems():
                host_avail_bandwidths.append(max(sr.avail_bandwidths))

            if max(host_avail_bandwidths) < _req_bandwidths[0]:
                available = False

            rack_avail_bandwidths = []
            for _, sr in _candidate_resource.rack_avail_switches.iteritems():
                rack_avail_bandwidths.append(max(sr.avail_bandwidths))

            avail_bandwidth = min(max(host_avail_bandwidths), max(rack_avail_bandwidths))
            if avail_bandwidth < _req_bandwidths[1]:
                available = False

        return available
