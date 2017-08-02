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

LEVEL = ["host", "rack", "cluster"]


class Group(object):

    def __init__(self, _app_id, _orch_id):
        self.app_id = _app_id          # stack_id
        self.orch_id = _orch_id        # consistent and permanent key
        self.name = None

        self.group_type = "AFF"
        self.level = None              # host, rack, or cluster

        self.surgroup = None          # where this group belong to
        self.subgroups = {}           # child groups

        self.diversity_groups = {}     # cumulative diversity/exclusivity group
        self.exclusivity_groups = {}   # over this level. key=name, value=level

        self.availability_zone_list = []
        self.extra_specs_list = []     # cumulative extra_specs

        self.vCPUs = 0
        self.mem = 0                   # MB
        self.local_volume_size = 0     # GB

        self.vCPU_weight = -1
        self.mem_weight = -1
        self.local_volume_weight = -1

        self.host = None

        self.sort_base = -1

    def get_common_diversity(self, _diversity_groups):
        common_level = "ANY"

        for dk in self.diversity_groups.keys():
            if dk in _diversity_groups.keys():
                level = self.diversity_groups[dk].split(":")[0]
                if common_level != "ANY":
                    if LEVEL.index(level) > LEVEL.index(common_level):
                        common_level = level
                else:
                    common_level = level

        return common_level

    def get_affinity_id(self):
        aff_id = None

        if self.group_type == "AFF" and self.name != "any":
            aff_id = self.level + ":" + self.name

        return aff_id

    def get_exclusivities(self, _level):
        exclusivities = {}

        for exk, level in self.exclusivity_groups.iteritems():
            if level.split(":")[0] == _level:
                exclusivities[exk] = level

        return exclusivities

    def get_json_info(self):
        surgroup_id = None
        if self.surgroup is None:
            surgroup_id = "none"
        else:
            surgroup_id = self.surgroup.orch_id

        subgroup_list = []
        for vk in self.subgroups.keys():
            subgroup_list.append(vk)

        return {'name': self.name,
                'group_type': self.group_type,
                'level': self.level,
                'surgroup': surgroup_id,
                'subgroup_list': subgroup_list,
                'diversity_groups': self.diversity_groups,
                'exclusivity_groups': self.exclusivity_groups,
                'availability_zones': self.availability_zone_list,
                'extra_specs_list': self.extra_specs_list,
                'cpus': self.vCPUs,
                'mem': self.mem,
                'local_volume': self.local_volume_size,
                'cpu_weight': self.vCPU_weight,
                'mem_weight': self.mem_weight,
                'local_volume_weight': self.local_volume_weight,
                'host': self.host}
