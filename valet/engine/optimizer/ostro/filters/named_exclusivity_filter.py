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


class NamedExclusivityFilter(object):

    def __init__(self):
        self.name = "named-exclusivity"

        self.exclusivity_id = None

        self.status = None

    def init_condition(self):
        self.exclusivity_id = None
        self.status = None

    def check_pre_condition(self, _level, _v, _node_placements, _avail_groups):
        exclusivities = _v.get_exclusivities(_level)

        if len(exclusivities) > 1:
            self.status = "multiple exclusivities for node = " + _v.orch_id
            return False

        if len(exclusivities) == 1:
            exclusivity_id = exclusivities[exclusivities.keys()[0]]

            # NOTE(gjung): possibly miss host that is claimed for the named exclusivity
            if exclusivity_id.split(":")[0] == _level:
                self.exclusivity_id = exclusivity_id

        if self.exclusivity_id is not None:
            return True
        else:
            return False

    def filter_candidates(self, _level, _v, _candidate_list):
        candidate_list = []

        candidate_list = self._get_candidates(_level, _candidate_list)

        return candidate_list

    def _get_candidates(self, _level, _candidate_list):
        candidate_list = []

        for c in _candidate_list:
            if self._check_exclusive_candidate(_level, c) is True or \
               self._check_empty(_level, c) is True:
                candidate_list.append(c)

        return candidate_list

    def _check_exclusive_candidate(self, _level, _candidate):
        # NOTE(gjung): possibly miss host that is claimed for the named exclusivity
        memberships = _candidate.get_memberships(_level)

        for lgk, lgr in memberships.iteritems():
            if lgr.group_type == "EX" and lgk == self.exclusivity_id:
                return True

        return False

    def _check_empty(self, _level, _candidate):
        num_of_placed_vms = _candidate.get_num_of_placed_vms(_level)

        if num_of_placed_vms == 0:
            return True

        return False
