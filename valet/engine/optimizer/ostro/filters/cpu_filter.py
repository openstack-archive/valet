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


class CPUFilter(object):

    def __init__(self):
        self.name = "cpu"

        self.status = None

    def init_condition(self):
        self.status = None

    def check_pre_condition(self, _level, _v, _node_placements, _avail_groups):
        return True

    def filter_candidates(self, _level, _v, _candidate_list):
        candidate_list = []

        for c in _candidate_list:
            if self._check_candidate(_level, _v, c):
                candidate_list.append(c)

        return candidate_list

    def _check_candidate(self, _level, _v, _candidate):
        """Return True if host has sufficient CPU cores."""

        (vCPUs, avail_vCPUs) = _candidate.get_vCPUs(_level)

        instance_vCPUs = _v.vCPUs

        # Do not allow an instance to overcommit against itself, only against other instances.
        if instance_vCPUs > vCPUs:
            return False

        if avail_vCPUs < instance_vCPUs:
            return False

        return True
