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


import filter_utils
from valet.engine.optimizer.app_manager.group import Group
from valet.engine.optimizer.app_manager.vm import VM


class AvailabilityZoneFilter(object):
    """ Filters Hosts by availability zone.

    Works with aggregate metadata availability zones, using the key
    'availability_zone'
    Note: in theory a compute node can be part of multiple availability_zones
    """

    def __init__(self):
        self.name = "availability-zone"

        self.status = None

    def init_condition(self):
        self.status = None

    def check_pre_condition(self, _level, _v, _node_placements, _avail_groups):
        if (isinstance(_v, VM) and _v.availability_zone is not None) or \
           (isinstance(_v, Group) and len(_v.availability_zone_list) > 0):
            return True
        else:
            return False

    def filter_candidates(self, _level, _v, _candidate_list):
        candidate_list = []

        for c in _candidate_list:
            if self._check_candidate(_level, _v, c):
                candidate_list.append(c)

        return candidate_list

    def _check_candidate(self, _level, _v, _candidate):
        az_request_list = []
        if isinstance(_v, VM):
            az_request_list.append(_v.availability_zone)
        else:
            for az in _v.availability_zone_list:
                az_request_list.append(az)

        if len(az_request_list) == 0:
            return True

        availability_zone_list = filter_utils.availability_zone_get_by_host(_level, _candidate)

        for azr in az_request_list:
            if azr not in availability_zone_list:
                return False

        return True
