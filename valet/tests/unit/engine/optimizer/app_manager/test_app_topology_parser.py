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

from valet.engine.optimizer.app_manager.app_topology_base import VGroup
from valet.engine.optimizer.app_manager.app_topology_base import VM
from valet.engine.optimizer.app_manager.app_topology_parser import Parser
from valet.tests.base import Base


class TestAppTopologyParse(Base):

    def setUp(self):
        super(TestAppTopologyParse, self).setUp()

        self.parser = Parser(False)

    @mock.patch.object(Parser, '_set_topology')
    def test_set_topology_public(self, mock_set_topology):
        graph = {
            "version": "1.0",
            "stack_id": "test_stack",
            "application_name": "test_app",
            "action": "test",
            "locations": ["location1", "location2"],
            "resources": {
                "key1": "id_1"
            }
        }

        self.parser.set_topology(graph)
        mock_set_topology.assert_called_once_with(graph["resources"])
        self.assertEqual(graph["version"], self.parser.format_version)
        self.assertEqual(graph["stack_id"], self.parser.stack_id)
        self.assertEqual(graph["application_name"],
                         self.parser.application_name)
        self.assertEqual(graph["action"], self.parser.action)
        self.assertEqual(graph["locations"],
                         self.parser.candidate_list_map["key1"])

    @mock.patch.object(Parser, '_set_topology')
    def test_set_topology_public_none(self, mock_set_topology):
        graph = {
            "resources": "none"
        }
        self.parser.set_topology(graph)
        mock_set_topology.assert_called_once_with(graph["resources"])
        self.assertEqual("0.0", self.parser.format_version)
        self.assertEqual("none", self.parser.stack_id)
        self.assertEqual("none", self.parser.application_name)
        self.assertEqual("any", self.parser.action)

    @mock.patch.object(Parser, '_merge_diversity_groups')
    def test_set_topology_private_div_false(self, mock_merge_div):
        mock_merge_div.return_value = False
        result = self.parser._set_topology({})
        self.assertEqual(({}, {}), result)

    @mock.patch.object(Parser, '_merge_exclusivity_groups')
    @mock.patch.object(Parser, '_merge_diversity_groups')
    def test_set_topology_private_exc_false(self, mock_merge_div,
                                            mock_merge_exc):
        mock_merge_div.return_value = True
        mock_merge_exc.return_value = False

        result = self.parser._set_topology({})
        mock_merge_div.assert_called_once_with({}, {}, {})
        self.assertEqual(({}, {}), result)

    @mock.patch.object(Parser, '_merge_affinity_groups')
    @mock.patch.object(Parser, '_merge_exclusivity_groups')
    @mock.patch.object(Parser, '_merge_diversity_groups')
    def test_set_topology_private_aff_false(self, mock_merge_div,
                                            mock_merge_exc, mock_merge_aff):
        mock_merge_div.return_value = True
        mock_merge_exc.return_value = True
        mock_merge_aff.return_value = False

        result = self.parser._set_topology({})
        mock_merge_div.assert_called_once_with({}, {}, {})
        mock_merge_exc.assert_called_once_with({}, {}, {})
        self.assertEqual(({}, {}), result)

    @mock.patch.object(Parser, '_merge_affinity_groups')
    @mock.patch.object(Parser, '_merge_exclusivity_groups')
    @mock.patch.object(Parser, '_merge_diversity_groups')
    def test_set_topology_private_nova_type(self, mock_merge_div,
                                            mock_merge_exc, mock_merge_aff):
        mock_merge_div.return_value = True
        mock_merge_exc.return_value = True
        mock_merge_aff.return_value = True
        self.parser.stack_id = "test_id"
        vgroups = {}
        vms = {}

        elements = {
            "test_resource_vm": {
                "type": "OS::Nova::Server",
                "name": "foo",
                "properties": {
                    "flavor": "foo_flavor",
                    "availability_zone": "bar:zone:none"
                },
                "locations": ["loc_1", "loc2"]
            },
            "test_resource_vgroup_1": {
                "type": "ATT::Valet::GroupAssignment",
                "properties": {
                    "group_type": "affinity",
                    "group_name": "test_group_1",
                    "level": "host"
                }
            },
            "test_resource_vgroup_2": {
                "type": "ATT::Valet::GroupAssignment",
                "properties": {
                    "group_type": "diversity",
                    "group_name": "test_group_2",
                    "level": "host"
                }
            },
            "test_resource_vgroup_3": {
                "type": "ATT::Valet::GroupAssignment",
                "properties": {
                    "group_type": "exclusivity",
                    "group_name": "test_group_3",
                    "level": "host"
                }
            },
            "test_resource_vgroup_4": {
                "type": "OS::Cinder::Volume",
                "properties": {
                    "group_type": "exclusivity",
                    "group_name": "test_group_3",
                    "level": "host"
                }
            }
        }

        vg = VGroup(self.parser.stack_id, "test_resource_vgroup_1")
        vg.vgroup_type = "AFF"
        vg.name = "test_group_1"
        vg.level = "host"
        vgroups[vg.uuid] = vg

        vm = VM(self.parser.stack_id, "test_resource_vm")
        vm.name = "foo"
        vm.flavor_id = "foo_flavor"
        vm.availability_zone = "bar"
        vms[vm.uuid] = vm

        expected = (vgroups, vms)
        result_vgroups, result_vms = self.parser._set_topology(elements)

        mock_merge_div.assert_called_once()
        mock_merge_exc.assert_called_once()
        mock_merge_aff.assert_called_once()

        self.assertEqual(len(vgroups), len(result_vgroups))
        self.assertEqual(vgroups[vg.uuid].name, result_vgroups[vg.uuid].name)
        self.assertEqual(vms[vm.uuid].name, result_vms[vm.uuid].name)
