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

import uuid

from valet.engine.optimizer.app_manager.app_topology_base import VGroup
from valet.engine.optimizer.app_manager.app_topology_base import VM
from valet.tests.base import Base


class TestAppTopologyBase(Base):

    def setUp(self):
        super(TestAppTopologyBase, self).setUp()

        rstr = uuid.uuid4().hex
        self.vgroup = VGroup(rstr, rstr)
        self.vm = VM(rstr, rstr)

        self.name = "test_name"
        self.status = "test_status"
        self.vgroup_type = "test_type"
        self.level = "test_level"
        self.survgroup = VM("app_uuid", "uuid")
        self.subvgroup_list = []
        self.diversity_groups = "div_groups"
        self.exclusivity_groups = "ex_groups"
        self.extra_specs_list = "specs_list"
        self.cpus = "test_vcpus"
        self.mem = "test_mem"
        self.local_volume = "test_local_volume"
        self.cpu_weight = "test_cpu_weight"
        self.mem_weight = "test_mem_weight"
        self.local_volume_weight = "weight"
        self.host = "test_host"
        self.flavor = "test_flavor"

    def test_get_json_info_vgroup_none(self):
        self.vgroup.name = self.name
        self.vgroup.status = self.status
        self.vgroup.vgroup_type = self.vgroup_type
        self.vgroup.level = self.level
        self.vgroup.survgroup = None
        self.vgroup.subvgroups = {}
        self.vgroup.diversity_groups = self.diversity_groups
        self.vgroup.exclusivity_groups = self.exclusivity_groups
        self.vgroup.availability_zone_list = None
        self.vgroup.extra_specs_list = self.extra_specs_list
        self.vgroup.vCPUs = self.cpus
        self.vgroup.mem = self.mem
        self.vgroup.local_volume_size = self.local_volume
        self.vgroup.vCPU_weight = self.cpu_weight
        self.vgroup.mem_weight = self.mem_weight
        self.vgroup.local_volume_weight = self.local_volume_weight
        self.vgroup.host = self.host

        vgroup_test_info = {
            'name': self.name,
            'status': self.status,
            'vgroup_type': self.vgroup_type,
            'level': self.level,
            'survgroup': 'none',
            'subvgroup_list': [],
            'diversity_groups': self.diversity_groups,
            'exclusivity_groups': self.exclusivity_groups,
            'availability_zones': None,
            'extra_specs_list': self.extra_specs_list,
            'cpus': self.cpus,
            'mem': self.mem,
            'local_volume': self.local_volume,
            'cpu_weight': self.cpu_weight,
            'mem_weight': self.mem_weight,
            'local_volume_weight': self.local_volume_weight,
            'host': self.host
        }

        result = self.vgroup.get_json_info()
        self.assertEqual(vgroup_test_info, result)

    def test_get_json_info_vgroup(self):
        self.vgroup.name = self.name
        self.vgroup.status = self.status
        self.vgroup.vgroup_type = self.vgroup_type
        self.vgroup.level = self.level
        self.vgroup.survgroup = self.survgroup
        self.vgroup.subvgroups = {}
        self.vgroup.diversity_groups = self.diversity_groups
        self.vgroup.exclusivity_groups = self.exclusivity_groups
        self.vgroup.availability_zone_list = None
        self.vgroup.extra_specs_list = self.extra_specs_list
        self.vgroup.vCPUs = self.cpus
        self.vgroup.mem = self.mem
        self.vgroup.local_volume_size = self.local_volume
        self.vgroup.vCPU_weight = self.cpu_weight
        self.vgroup.mem_weight = self.mem_weight
        self.vgroup.local_volume_weight = self.local_volume_weight
        self.vgroup.host = self.host

        vgroup_test_info = {
            'name': self.name,
            'status': self.status,
            'vgroup_type': self.vgroup_type,
            'level': self.level,
            'survgroup': self.survgroup.uuid,
            'subvgroup_list': [],
            'diversity_groups': self.diversity_groups,
            'exclusivity_groups': self.exclusivity_groups,
            'availability_zones': None,
            'extra_specs_list': self.extra_specs_list,
            'cpus': self.cpus,
            'mem': self.mem,
            'local_volume': self.local_volume,
            'cpu_weight': self.cpu_weight,
            'mem_weight': self.mem_weight,
            'local_volume_weight': self.local_volume_weight,
            'host': self.host
        }

        result = self.vgroup.get_json_info()
        self.assertEqual(vgroup_test_info, result)

    def test_get_json_info_vm_none(self):
        self.vm.name = self.name
        self.vm.status = self.status
        self.vm.survgroup = None
        self.vm.diversity_groups = self.diversity_groups
        self.vm.exclusivity_groups = self.exclusivity_groups
        self.vm.availability_zone = None
        self.vm.extra_specs_list = self.extra_specs_list
        self.vm.flavor = self.flavor
        self.vm.vCPUs = self.cpus
        self.vm.mem = self.mem
        self.vm.local_volume_size = self.local_volume
        self.vm.vCPU_weight = self.cpu_weight
        self.vm.mem_weight = self.mem_weight
        self.vm.local_volume_weight = self.local_volume_weight
        self.vm.host = self.host

        vm_test_info = {
            'name': self.name,
            'status': self.status,
            'survgroup': 'none',
            'diversity_groups': self.diversity_groups,
            'exclusivity_groups': self.exclusivity_groups,
            'availability_zones': "none",
            'extra_specs_list': self.extra_specs_list,
            'flavor': self.flavor,
            'cpus': self.cpus,
            'mem': self.mem,
            'local_volume': self.local_volume,
            'cpu_weight': self.cpu_weight,
            'mem_weight': self.mem_weight,
            'local_volume_weight': self.local_volume_weight,
            'host': self.host
        }

        result = self.vm.get_json_info()
        self.assertEqual(vm_test_info, result)

    def test_get_json_info_vm(self):
        self.vm.name = self.name
        self.vm.status = self.status
        self.vm.survgroup = self.survgroup
        self.vm.diversity_groups = self.diversity_groups
        self.vm.exclusivity_groups = self.exclusivity_groups
        self.vm.availability_zone = "az_exist"
        self.vm.extra_specs_list = self.extra_specs_list
        self.vm.flavor = self.flavor
        self.vm.vCPUs = self.cpus
        self.vm.mem = self.mem
        self.vm.local_volume_size = self.local_volume
        self.vm.vCPU_weight = self.cpu_weight
        self.vm.mem_weight = self.mem_weight
        self.vm.local_volume_weight = self.local_volume_weight
        self.vm.host = self.host

        vm_test_info = {
            'name': self.name,
            'status': self.status,
            'survgroup': 'uuid',
            'diversity_groups': self.diversity_groups,
            'exclusivity_groups': self.exclusivity_groups,
            'availability_zones': 'az_exist',
            'extra_specs_list': self.extra_specs_list,
            'flavor': self.flavor,
            'cpus': self.cpus,
            'mem': self.mem,
            'local_volume': self.local_volume,
            'cpu_weight': self.cpu_weight,
            'mem_weight': self.mem_weight,
            'local_volume_weight': self.local_volume_weight,
            'host': self.host
        }

        result = self.vm.get_json_info()
        self.assertEqual(vm_test_info, result)
