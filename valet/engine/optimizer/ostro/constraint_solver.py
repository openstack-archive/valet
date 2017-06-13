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
from oslo_log import log

from valet.engine.optimizer.app_manager.app_topology_base import LEVELS
from valet.engine.optimizer.app_manager.app_topology_base import VGroup
from valet.engine.optimizer.app_manager.app_topology_base import VM
from valet.engine.optimizer.ostro.openstack_filters \
    import AggregateInstanceExtraSpecsFilter
from valet.engine.optimizer.ostro.openstack_filters \
    import AvailabilityZoneFilter
from valet.engine.optimizer.ostro.openstack_filters import CoreFilter
from valet.engine.optimizer.ostro.openstack_filters import DiskFilter
from valet.engine.optimizer.ostro.openstack_filters import RamFilter

LOG = log.getLogger(__name__)


class ConstraintSolver(object):
    """ConstraintSolver."""

    def __init__(self):
        """Initialization."""
        """Instantiate filters to help enforce constraints."""

        self.openstack_AZ = AvailabilityZoneFilter()
        self.openstack_AIES = AggregateInstanceExtraSpecsFilter()
        self.openstack_R = RamFilter()
        self.openstack_C = CoreFilter()
        self.openstack_D = DiskFilter()

        self.status = "success"

    def compute_candidate_list(self, _level, _n, _node_placements,
                               _avail_resources, _avail_logical_groups):
        """Compute candidate list for the given VGroup or VM."""
        candidate_list = []

        """When replanning."""
        if _n.node.host is not None and len(_n.node.host) > 0:
            for hk in _n.node.host:
                for ark, ar in _avail_resources.iteritems():
                    if hk == ark:
                        candidate_list.append(ar)
        else:
            for _, r in _avail_resources.iteritems():
                candidate_list.append(r)
        if len(candidate_list) == 0:
            self.status = "no candidate for node = " + _n.node.name
            LOG.warning(self.status)
            return candidate_list
        else:
            LOG.debug("ConstraintSolver: num of candidates = " +
                              str(len(candidate_list)))

        """Availability zone constraint."""
        if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
            if (isinstance(_n.node, VM) and _n.node.availability_zone
                is not None) or (isinstance(_n.node, VGroup) and
                                 len(_n.node.availability_zone_list) > 0):
                self._constrain_availability_zone(_level, _n, candidate_list)
                if len(candidate_list) == 0:
                    self.status = "violate availability zone constraint for " \
                                  "node = " + _n.node.name
                    LOG.error("ConstraintSolver: " + self.status)
                    return candidate_list

        """Host aggregate constraint."""
        if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
            if len(_n.node.extra_specs_list) > 0:
                self._constrain_host_aggregates(_level, _n, candidate_list)
                if len(candidate_list) == 0:
                    self.status = "violate host aggregate constraint for " \
                                  "node = " + _n.node.name
                    LOG.error("ConstraintSolver: " + self.status)
                    return candidate_list

        """CPU capacity constraint."""
        if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
            self._constrain_cpu_capacity(_level, _n, candidate_list)
            if len(candidate_list) == 0:
                self.status = "violate cpu capacity constraint for " \
                              "node = " + _n.node.name
                LOG.error("ConstraintSolver: " + self.status)
                return candidate_list

        """Memory capacity constraint."""
        if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
            self._constrain_mem_capacity(_level, _n, candidate_list)
            if len(candidate_list) == 0:
                self.status = "violate memory capacity constraint for " \
                              "node = " + _n.node.name
                LOG.error("ConstraintSolver: " + self.status)
                return candidate_list

        """Local disk capacity constraint."""
        if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
            self._constrain_local_disk_capacity(_level, _n, candidate_list)
            if len(candidate_list) == 0:
                self.status = "violate local disk capacity constraint for " \
                              "node = " + _n.node.name
                LOG.error("ConstraintSolver: " + self.status)
                return candidate_list

        """ diversity constraint """
        if len(_n.node.diversity_groups) > 0:
            for _, diversity_id in _n.node.diversity_groups.iteritems():
                if diversity_id.split(":")[0] == _level:
                    if diversity_id in _avail_logical_groups.keys():
                        self._constrain_diversity_with_others(_level,
                                                              diversity_id,
                                                              candidate_list)
                        if len(candidate_list) == 0:
                            break
            if len(candidate_list) == 0:
                self.status = "violate diversity constraint for " \
                              "node = " + _n.node.name
                LOG.error("ConstraintSolver: " + self.status)
                return candidate_list
            else:
                self._constrain_diversity(_level, _n, _node_placements,
                                          candidate_list)
                if len(candidate_list) == 0:
                    self.status = "violate diversity constraint for " \
                                  "node = " + _n.node.name
                    LOG.error("ConstraintSolver: " + self.status)
                    return candidate_list

        """Exclusivity constraint."""
        exclusivities = self.get_exclusivities(_n.node.exclusivity_groups,
                                               _level)
        if len(exclusivities) > 1:
            self.status = "violate exclusivity constraint (more than one " \
                          "exclusivity) for node = " + _n.node.name
            LOG.error("ConstraintSolver: " + self.status)
            return []
        else:
            if len(exclusivities) == 1:
                exclusivity_id = exclusivities[exclusivities.keys()[0]]
                if exclusivity_id.split(":")[0] == _level:
                    self._constrain_exclusivity(_level, exclusivity_id,
                                                candidate_list)
                    if len(candidate_list) == 0:
                        self.status = "violate exclusivity constraint for " \
                                      "node = " + _n.node.name
                        LOG.error("ConstraintSolver: " + self.status)
                        return candidate_list
            else:
                self._constrain_non_exclusivity(_level, candidate_list)
                if len(candidate_list) == 0:
                    self.status = "violate non-exclusivity constraint for " \
                                  "node = " + _n.node.name
                    LOG.error("ConstraintSolver: " + self.status)
                    return candidate_list

        """Affinity constraint."""
        affinity_id = _n.get_affinity_id()  # level:name, except name == "any"
        if affinity_id is not None:
            if affinity_id.split(":")[0] == _level:
                if affinity_id in _avail_logical_groups.keys():
                    self._constrain_affinity(_level, affinity_id,
                                             candidate_list)
                    if len(candidate_list) == 0:
                        self.status = "violate affinity constraint for " \
                                      "node = " + _n.node.name
                        LOG.error("ConstraintSolver: " + self.status)
                        return candidate_list

        return candidate_list

    """
    Constraint modules.
    """

    def _constrain_affinity(self, _level, _affinity_id, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.exist_group(_level, _affinity_id, "AFF", r) is False:
                if r not in conflict_list:
                    conflict_list.append(r)

        _candidate_list[:] = [
            c for c in _candidate_list if c not in conflict_list]

    def _constrain_diversity_with_others(self, _level, _diversity_id,
                                         _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.exist_group(_level, _diversity_id, "DIV", r) is True:
                if r not in conflict_list:
                    conflict_list.append(r)

        _candidate_list[:] = [
            c for c in _candidate_list if c not in conflict_list]

    def exist_group(self, _level, _id, _group_type, _candidate):
        """Check if group esists."""
        """Return True if there exists a group within the candidate's
         membership list that matches the provided id and group type.
        """
        match = False

        memberships = _candidate.get_memberships(_level)
        for lgk, lgr in memberships.iteritems():
            if lgr.group_type == _group_type and lgk == _id:
                match = True
                break

        return match

    def _constrain_diversity(self, _level, _n, _node_placements,
                             _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.conflict_diversity(_level, _n, _node_placements, r):
                if r not in conflict_list:
                    conflict_list.append(r)

        _candidate_list[:] = [
            c for c in _candidate_list if c not in conflict_list]

    def conflict_diversity(self, _level, _n, _node_placements, _candidate):
        """Return True if the candidate has a placement conflict."""
        conflict = False

        for v in _node_placements.keys():
            diversity_level = _n.get_common_diversity(v.diversity_groups)
            if diversity_level != "ANY" and \
                    LEVELS.index(diversity_level) >= \
                    LEVELS.index(_level):
                if diversity_level == "host":
                    if _candidate.cluster_name == \
                            _node_placements[v].cluster_name and \
                       _candidate.rack_name == \
                            _node_placements[v].rack_name and  \
                       _candidate.host_name == \
                            _node_placements[v].host_name:
                        conflict = True
                        break
                elif diversity_level == "rack":
                    if _candidate.cluster_name == \
                            _node_placements[v].cluster_name and \
                       _candidate.rack_name == _node_placements[v].rack_name:
                        conflict = True
                        break
                elif diversity_level == "cluster":
                    if _candidate.cluster_name == \
                            _node_placements[v].cluster_name:
                        conflict = True
                        break

        return conflict

    def _constrain_non_exclusivity(self, _level, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.conflict_exclusivity(_level, r) is True:
                if r not in conflict_list:
                    conflict_list.append(r)

        _candidate_list[:] = [
            c for c in _candidate_list if c not in conflict_list]

    def conflict_exclusivity(self, _level, _candidate):
        """Check for an exculsivity conflict."""
        """Check if the candidate contains an exclusivity group within its
        list of memberships."""
        conflict = False

        memberships = _candidate.get_memberships(_level)
        for mk in memberships.keys():
            if memberships[mk].group_type == "EX" and \
                    mk.split(":")[0] == _level:
                conflict = True

        return conflict

    def get_exclusivities(self, _exclusivity_groups, _level):
        """Return a list of filtered exclusivities."""
        """Extract and return only those exclusivities that exist at the
        specified level.
        """
        exclusivities = {}

        for exk, level in _exclusivity_groups.iteritems():
            if level.split(":")[0] == _level:
                exclusivities[exk] = level

        return exclusivities

    def _constrain_exclusivity(self, _level, _exclusivity_id, _candidate_list):
        candidate_list = self._get_exclusive_candidates(
            _level, _exclusivity_id, _candidate_list)

        if len(candidate_list) == 0:
            candidate_list = self._get_hibernated_candidates(_level,
                                                             _candidate_list)
            _candidate_list[:] = [x for x in _candidate_list
                                  if x in candidate_list]
        else:
            _candidate_list[:] = [x for x in _candidate_list
                                  if x in candidate_list]

    def _get_exclusive_candidates(self, _level, _exclusivity_id,
                                  _candidate_list):
        candidate_list = []

        for r in _candidate_list:
            if self.exist_group(_level, _exclusivity_id, "EX", r):
                if r not in candidate_list:
                    candidate_list.append(r)

        return candidate_list

    def _get_hibernated_candidates(self, _level, _candidate_list):
        candidate_list = []

        for r in _candidate_list:
            if self.check_hibernated(_level, r) is True:
                if r not in candidate_list:
                    candidate_list.append(r)

        return candidate_list

    def check_hibernated(self, _level, _candidate):
        """Check if the candidate is hibernated.

        Return True if the candidate has no placed VMs at the specified
        level.
        """
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

        _candidate_list[:] = [
            c for c in _candidate_list if c not in conflict_list]

    def check_host_aggregates(self, _level, _candidate, _v):
        """Check if candidate passes aggregate instance extra specs.

        Return true if the candidate passes the aggregate instance extra specs
        zone filter.
        """
        return self.openstack_AIES.host_passes(_level, _candidate, _v)

    def _constrain_availability_zone(self, _level, _n, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.check_availability_zone(_level, r, _n.node) is False:
                if r not in conflict_list:
                    conflict_list.append(r)

        _candidate_list[:] = [
            c for c in _candidate_list if c not in conflict_list]

    def check_availability_zone(self, _level, _candidate, _v):
        """Check if the candidate passes the availability zone filter."""
        return self.openstack_AZ.host_passes(_level, _candidate, _v)

    def _constrain_cpu_capacity(self, _level, _n, _candidate_list):
        conflict_list = []

        for ch in _candidate_list:
            if self.check_cpu_capacity(_level, _n.node, ch) is False:
                conflict_list.append(ch)

        _candidate_list[:] = [
            c for c in _candidate_list if c not in conflict_list]

    def check_cpu_capacity(self, _level, _v, _candidate):
        """Check if the candidate passes the core filter."""
        return self.openstack_C.host_passes(_level, _candidate, _v)

    def _constrain_mem_capacity(self, _level, _n, _candidate_list):
        conflict_list = []

        for ch in _candidate_list:
            if self.check_mem_capacity(_level, _n.node, ch) is False:
                conflict_list.append(ch)

        _candidate_list[:] = [
            c for c in _candidate_list if c not in conflict_list]

    def check_mem_capacity(self, _level, _v, _candidate):
        """Check if the candidate passes the RAM filter."""
        return self.openstack_R.host_passes(_level, _candidate, _v)

    def _constrain_local_disk_capacity(self, _level, _n, _candidate_list):
        conflict_list = []

        for ch in _candidate_list:
            if self.check_local_disk_capacity(_level, _n.node, ch) is False:
                conflict_list.append(ch)

        _candidate_list[:] = [
            c for c in _candidate_list if c not in conflict_list]

    def check_local_disk_capacity(self, _level, _v, _candidate):
        """Check if the candidate passes the disk filter."""
        return self.openstack_D.host_passes(_level, _candidate, _v)
