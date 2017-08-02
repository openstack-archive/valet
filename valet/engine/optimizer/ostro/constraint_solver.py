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

from valet.engine.optimizer.ostro.filters.aggregate_instance_filter \
    import AggregateInstanceExtraSpecsFilter
from valet.engine.optimizer.ostro.filters.az_filter \
    import AvailabilityZoneFilter
from valet.engine.optimizer.ostro.filters.cpu_filter import CPUFilter
from valet.engine.optimizer.ostro.filters.disk_filter import DiskFilter
from valet.engine.optimizer.ostro.filters.diversity_filter \
    import DiversityFilter
from valet.engine.optimizer.ostro.filters.mem_filter import MemFilter
from valet.engine.optimizer.ostro.filters.named_affinity_filter \
    import NamedAffinityFilter
from valet.engine.optimizer.ostro.filters.named_diversity_filter \
    import NamedDiversityFilter
from valet.engine.optimizer.ostro.filters.named_exclusivity_filter \
    import NamedExclusivityFilter
from valet.engine.optimizer.ostro.filters.no_exclusivity_filter \
    import NoExclusivityFilter

LOG = log.getLogger(__name__)


class ConstraintSolver(object):
    """Solver to filter out candidate hosts."""

    def __init__(self):
        """Instantiate filters to help enforce constraints."""

        self.filter_list = []

        self.filter_list.append(NamedAffinityFilter())
        self.filter_list.append(NamedDiversityFilter())
        self.filter_list.append(DiversityFilter())
        self.filter_list.append(NamedExclusivityFilter())
        self.filter_list.append(NoExclusivityFilter())
        self.filter_list.append(AvailabilityZoneFilter())
        self.filter_list.append(AggregateInstanceExtraSpecsFilter())
        self.filter_list.append(CPUFilter())
        self.filter_list.append(MemFilter())
        self.filter_list.append(DiskFilter())

        self.status = "success"

    def get_candidate_list(self, _n, _node_placements, _avail_resources,
                           _avail_groups):
        """Filter candidate hosts using a list of filters."""

        level = _avail_resources.level

        candidate_list = []
        for _, r in _avail_resources.candidates.iteritems():
            candidate_list.append(r)

        if len(candidate_list) == 0:
            self.status = "no candidate for node = " + _n.orch_id
            LOG.warn(self.status)
            return candidate_list

        LOG.debug("num of candidates = " + str(len(candidate_list)))

        for f in self.filter_list:
            f.init_condition()

            if not f.check_pre_condition(level, _n, _node_placements,
                                         _avail_groups):
                if f.status is not None:
                    self.status = f.status
                    LOG.error(self.status)
                    return []
                continue

            candidate_list = f.filter_candidates(level, _n, candidate_list)

            if len(candidate_list) == 0:
                self.status = "violate {} constraint for node {} ".format(f.name, _n.orch_id)
                LOG.error(self.status)
                return []

            LOG.debug("pass " + f.name + " with num of candidates = " + str(len(candidate_list)))

        return candidate_list
