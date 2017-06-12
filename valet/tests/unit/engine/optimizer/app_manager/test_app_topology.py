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

import mock

from valet.engine.optimizer.app_manager.app_topology import AppTopology
from valet.engine.optimizer.app_manager.app_topology_base import VGroup
from valet.engine.optimizer.app_manager.app_topology_base import VM
from valet.engine.optimizer.app_manager.app_topology_parser import Parser
from valet.engine.optimizer.db_connect.music_handler import MusicHandler
from valet.engine.resource_manager.resource import Resource
from valet.tests.base import Base


class TestAppTopology(Base):

    def setUp(self):
        super(TestAppTopology, self).setUp()

        self.logger = mock.Mock()
        self.config = mock.Mock()
        self.db = MusicHandler(self.config, self.logger)
        self.resource = Resource(self.db, self.config, self.logger)
        self.app_topology = AppTopology(self.resource, self.logger)

    @mock.patch.object(Parser, 'set_topology')
    def test_set_app_topology(self, mock_set_topology):
        self.app_topology.parser = Parser("test_high_level", self.logger)
        return

    @mock.patch.object(Parser, 'set_topology')
    def test_set_app_topology_none(self, mock_set_topology):
        self.app_topology.parser = Parser("test_high_level", self.logger)
        mock_set_topology.return_value = ({}, {})

        result = self.app_topology.set_app_topology("app_graph")
        self.assertEqual(None, result)

    @mock.patch.object(AppTopology, '_set_vgroup_weight')
    @mock.patch.object(AppTopology, '_set_vgroup_resource')
    @mock.patch.object(AppTopology, '_set_vm_weight')
    def test_set_weight(self, mock_vm_weight,
                        mock_vg_resource, mock_vg_weight):
        test_group = 'foo'
        test_vm = 'bar'
        self.app_topology.vgroups = {
            'test_group': test_group
        }
        self.app_topology.vms = {
            'test_vm': test_vm
        }
        self.app_topology.set_weight()
        calls = [mock.call(test_vm), mock.call(test_group)]
        mock_vm_weight.assert_has_calls(calls)
        mock_vg_resource.assert_called_once_with(test_group)
        mock_vg_weight.assert_called_once_with(test_group)

    def test_set_vm_weight_vgroup(self):
        vgroup = VGroup("mock_app", "mock_uuid")
        vm = VM("vm_app_uuid", "vm_uuid")

        vm.vCPUs = 4
        self.app_topology.resource.CPU_avail = 2
        vCPU_weight = vm.vCPUs / self.app_topology.resource.CPU_avail

        vm.mem = 6
        self.app_topology.resource.mem_avail = 2
        mem_weight = vm.mem / self.app_topology.resource.mem_avail

        vm.local_volume_size = 8
        self.app_topology.resource.local_disk_avail = 4
        local_volume_weight = vm.local_volume_size / \
            self.app_topology.resource.local_disk_avail

        vgroup.subvgroups = {"foo": vm}
        self.app_topology._set_vm_weight(vgroup)

        self.assertEqual(vCPU_weight, vm.vCPU_weight)
        self.assertEqual(mem_weight, vm.mem_weight)
        self.assertEqual(local_volume_weight, vm.local_volume_weight)

    def test_set_vgroup_resource_vm(self):
        vm = VM("app_uuid", "vm_uuid")
        result = self.app_topology._set_vgroup_resource(vm)
        self.assertEqual(None, result)

    def test_set_optimization_priority_none(self):
        self.app_topology.vgroups = {
            "foo": "bar"
        }
        self.app_topology.vms = {
            "foo": "bar"
        }
        self.app_topology.resource.CPU_avail = 1
        self.app_topology.total_CPU = 10

        self.app_topology.resource.mem_avail = 1
        self.app_topology.total_mem = 4

        self.app_topology.resource.local_disk_avail = 2
        self.app_topology.total_local_vol = 10

        opt = [("cpu", 10.0),
               ("lvol", 5.0),
               ("mem", 4.0)]

        self.app_topology.set_optimization_priority()
        self.assertEqual(opt, self.app_topology.optimization_priority)
