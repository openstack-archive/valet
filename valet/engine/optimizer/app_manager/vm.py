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

from valet.engine.optimizer.app_manager.group import LEVEL


class VM(object):

    def __init__(self, _app_id, _orch_id):
        self.app_id = _app_id
        self.orch_id = _orch_id
        self.uuid = None               # permanent physical uuid
        self.name = None

        self.surgroup = None          # Group where this vm belongs to

        self.diversity_groups = {}
        self.exclusivity_groups = {}

        self.availability_zone = None
        self.extra_specs_list = []

        self.flavor = None
        self.image = None
        self.vCPUs = 0
        self.mem = 0                  # MB
        self.local_volume_size = 0    # GB

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

        availability_zone = None
        if self.availability_zone is None:
            availability_zone = "none"
        else:
            availability_zone = self.availability_zone

        uuid = None
        if self.uuid is not None and self.uuid != "none":
            uuid = self.uuid
        else:
            uuid = "none"

        return {'name': self.name,
                'uuid': uuid,
                'surgroup': surgroup_id,
                'diversity_groups': self.diversity_groups,
                'exclusivity_groups': self.exclusivity_groups,
                'availability_zones': availability_zone,
                'extra_specs_list': self.extra_specs_list,
                'flavor': self.flavor,
                'image': self.image,
                'cpus': self.vCPUs,
                'mem': self.mem,
                'local_volume': self.local_volume_size,
                'cpu_weight': self.vCPU_weight,
                'mem_weight': self.mem_weight,
                'local_volume_weight': self.local_volume_weight,
                'host': self.host}
