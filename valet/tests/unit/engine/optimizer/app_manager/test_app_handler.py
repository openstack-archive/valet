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

from valet.engine.optimizer.app_manager.app_handler import AppHandler
from valet.engine.optimizer.app_manager.app_handler import AppHistory
from valet.engine.optimizer.app_manager.app_topology import AppTopology
from valet.engine.optimizer.app_manager.application import App
from valet.engine.optimizer.db_connect.music_handler import MusicHandler
from valet.engine.resource_manager.resource import Resource
from valet.tests.base import Base


class TestAppHandler(Base):

    def setUp(self):
        super(TestAppHandler, self).setUp()

        self.config = mock.Mock()
        self.db = MusicHandler(self.config)
        self.rsrc = Resource(self.db, self.config)
        self.app = AppHandler(self.rsrc, self.db, self.config)

    def test_check_history_no_action(self):
        mock_app = {
            "stack_id": "foo",
            "action": "bar",
        }

        result = self.app.check_history(mock_app)
        self.assertEqual(result, (None, None))

    def test_check_history_create(self):
        app_history_mock = AppHistory("none")
        mock_app = {
            "stack_id": "foo",
            "action": "create",
        }
        mock_key = "foo:create:none"

        app_history_mock.decision_key = mock_key
        app_history_mock.result = "bar"
        self.app.decision_history[mock_key] = app_history_mock

        result = self.app.check_history(mock_app)
        self.assertEqual(result, (mock_key, "bar"))

        self.app.decision_history = {}
        result = self.app.check_history(mock_app)
        self.assertEqual(result, (mock_key, None))

    def test_check_history_replan(self):
        app_history_mock = AppHistory("none")
        mock_app = {
            "stack_id": "foo",
            "action": "replan",
            "orchestration_id": "bar",
        }
        mock_key = "foo:replan:bar"

        app_history_mock.decision_key = mock_key
        app_history_mock.result = "result"
        self.app.decision_history[mock_key] = app_history_mock

        result = self.app.check_history(mock_app)
        self.assertEqual(result, (mock_key, "result"))

        self.app.decision_history = {}
        result = self.app.check_history(mock_app)
        self.assertEqual(result, (mock_key, None))

    @mock.patch.object(AppHandler, '_clean_decision_history')
    def test_put_history_create(self, mock_clean):
        key = "foo:create:bar"
        mock_app_history = AppHistory(key)
        mock_app_history.result = "result"

        self.app.max_decision_history = 0

        self.app.put_history(key, "result")
        self.assertEqual(self.app.decision_history[key].result, "result")
        self.assertEqual(self.app.decision_history[key].decision_key, key)
        mock_clean.assert_called_once_with()

    @mock.patch.object(AppHandler, '_clean_decision_history')
    def test_put_history_replan(self, mock_clean):
        key = "foo:replan:bar"
        mock_app_history = AppHistory(key)
        mock_app_history.result = "result"

        self.app.max_decision_history = 0

        self.app.put_history(key, "result")
        self.assertEqual(self.app.decision_history[key].result, "result")
        self.assertEqual(self.app.decision_history[key].decision_key, key)

    def test_clean_decision_history(self):
        self.app.min_decision_history = 0
        app_history_one = AppHistory("keyone")
        app_history_two = AppHistory("keytwo")
        app_history_one.timestamp = 1
        app_history_two.timestamp = 2
        self.app.decision_history = {
            "keyone": app_history_one,
            "keytwo": app_history_two,
        }

        self.app._clean_decision_history()
        self.assertEqual(len(self.app.decision_history),
                         self.app.min_decision_history)

    @mock.patch.object(AppHandler, '_regenerate_app_topology')
    def test_add_app_reapp_none_replan(self, mock_regen_app):
        mock_regen_app.return_value = None

        app_data = {
            "stack_id": "test_id",
            "application_name": "test_name",
            "action": "replan"
        }

        result = self.app.add_app(app_data)
        self.assertIsNone(result)
        self.assertIsNone(self.app.apps["test_id"])

    @mock.patch.object(AppTopology, 'set_app_topology')
    @mock.patch.object(AppHandler, '_regenerate_app_topology')
    def test_add_app_id_none_migrate(self, mock_regen_app, mock_set_topology):
        mock_regen_app.return_value = "mock_re_app"
        mock_set_topology.return_value = None

        app_data = {
            "action": "migrate"
        }

        result = self.app.add_app(app_data)
        self.assertIsNone(result)
        self.assertIsNone(self.app.apps["none"])

    @mock.patch.object(AppTopology, 'set_app_topology')
    def test_add_app_id_none_create(self, mock_set_topology):
        mock_set_topology.return_value = None

        app_data = {
            "stack_id": "test_id",
            "application_name": "test_name",
            "action": "create"
        }

        result = self.app.add_app(app_data)
        self.assertIsNone(result)
        self.assertIsNone(self.app.apps["test_id"])

    @mock.patch.object(AppTopology, 'set_app_topology')
    def test_add_app_success(self, mock_set_topology):
        mock_set_topology.return_value = "test_app_id"

        app_data = {
            "stack_id": "test_id",
            "application_name": "test_name",
            "action": "create"
        }

        result = self.app.add_app(app_data)
        self.assertIsInstance(result, AppTopology)

    @mock.patch.object(MusicHandler, 'add_app')
    @mock.patch.object(App, 'get_json_info')
    def test_store_app_placement_true(self, mock_get_json, mock_add_app):
        mock_get_json.return_value = "info"
        mock_add_app.return_value = True
        test_app = App("test_id", "test_name", "test_action")

        self.app.apps = {"foo": test_app}
        result = self.app._store_app_placements()
        mock_get_json.assert_called_once_with()
        mock_add_app.assert_called_once_with("foo", "info")
        self.assertTrue(result)

    @mock.patch.object(MusicHandler, 'add_app')
    @mock.patch.object(App, 'get_json_info')
    def test_store_app_placement_false(self, mock_get_json, mock_add_app):
        mock_get_json.return_value = "info"
        mock_add_app.return_value = False
        test_app = App("test_id", "test_name", "test_action")

        self.app.apps = {"foo": test_app}
        result = self.app._store_app_placements()
        mock_get_json.assert_called_once_with()
        mock_add_app.assert_called_once_with("foo", "info")
        self.assertFalse(result)

    @mock.patch.object(MusicHandler, 'add_app')
    def test_remove_placement(self, mock_add_app):
        mock_add_app.return_value = True

        self.app.apps = {"foo": "bar"}
        self.app.remove_placement()
        mock_add_app.assert_called_once_with("foo", None)

    @mock.patch.object(MusicHandler, 'get_vm_info')
    def test_get_vm_info(self, mock_get_vm_info):
        vm_info = {'vm_info': 'exists'}
        mock_get_vm_info.return_value = {'vm_info': 'exists'}
        result = self.app.get_vm_info('foo', 'bar', 'test')
        self.assertEqual(result, vm_info)

    def test_get_vm_info_none(self):
        mock_vm_info = {}

        result = self.app.get_vm_info(None, None, None)
        self.assertEqual(result, mock_vm_info)

        result = self.app.get_vm_info('none', 'none', None)
        self.assertEqual(result, mock_vm_info)

        result = self.app.get_vm_info('none', 'foo', None)
        self.assertEqual(result, mock_vm_info)

        result = self.app.get_vm_info('foo', None, None)
        self.assertEqual(result, mock_vm_info)

    @mock.patch.object(MusicHandler, 'update_vm_info')
    def test_update_vm_info(self, mock_db):
        mock_db.return_value = False
        result = self.app.update_vm_info("foo", "bar")
        mock_db.assert_called_once_with("foo", "bar")
        self.assertFalse(result)

    def test_update_vm_info_uuids_none(self):
        result = self.app.update_vm_info(None, None)
        self.assertTrue(result)

        result = self.app.update_vm_info('none', 'none')
        self.assertTrue(result)

        result = self.app.update_vm_info('none', 'foo')
        self.assertTrue(result)

        result = self.app.update_vm_info('foo', None)
        self.assertTrue(result)

    @mock.patch.object(MusicHandler, 'get_app_info')
    def test_regenerate_app_topology_none(self, mock_get_app_info):
        mock_get_app_info.return_value = None

        result = self.app._regenerate_app_topology(None, None, None, None)
        self.assertIsNone(result)

        mock_get_app_info.return_value = {}

        result = self.app._regenerate_app_topology(None, None, None, None)
        self.assertIsNone(result)

    @mock.patch.object(MusicHandler, 'get_app_info')
    def test_regenerate_app_topology(self, mock_get_app_info):
        old_app_mock = {
            "VMs": {
                "vm_1": {
                    "name": "test_name",
                    "flavor": "tiny",
                    "availability_zones": "test_zone",
                    "host": "foo",
                    "cpus": "test_cpus",
                    "mem": "test_mem",
                    "local_volume": "test_lv",
                    "status": "replanned",
                    "diversity_groups": {
                        "div_group_1": "level_1:vm1div",
                        "div_group_2": "level_2:vm1div"
                    },
                    "exclusivity_groups": {
                        "ex_group_1": "level_1:vm1ex",
                        "ex_group_2": "level_2:vm1ex"
                    }
                }
            },
            "VGroups": {
                "vg_1": {
                    "name": "test_group",
                    "level": "test_level",
                    "subvgroup_list": ["sg_1", "sg_2"],
                    "diversity_groups": {
                        "key1": "level1:vg1div",
                        "key2": "level2:vg1div"
                    },
                    "exclusivity_groups": {
                        "key1": "level1:vg1ex",
                        "key2": "level2:vg1ex"
                    }
                }
            }
        }
        mock_get_app_info.return_value = old_app_mock

        mock_app = {
            "orchestration_id": "vm_1",
            "locations": "location_list"
        }
        app_topology = AppTopology(Resource(self.db, self.config))

        result = self.app._regenerate_app_topology("mock_stack_id", mock_app,
                                                   app_topology, "replan")

        expected = {
            'action': 'create',
            'resources': {
                'div_group_1': {
                    'properties': {
                        'group_name': 'vm1div',
                        'group_type': 'diversity',
                        'level': 'level_1',
                        'resources': ['vm_1']
                    },
                    'type': 'ATT::Valet::GroupAssignment'
                },
                'div_group_2': {
                    'properties': {
                        'group_name': 'vm1div',
                        'group_type': 'diversity',
                        'level': 'level_2',
                        'resources': ['vm_1']
                    },
                    'type': 'ATT::Valet::GroupAssignment'
                },
                'ex_group_1': {
                    'properties': {
                        'group_name': 'vm1ex',
                        'group_type': 'exclusivity',
                        'level': 'level_1',
                        'resources': ['vm_1']
                    },
                    'type': 'ATT::Valet::GroupAssignment'
                },
                'ex_group_2': {
                    'properties': {
                        'group_name': 'vm1ex',
                        'group_type': 'exclusivity',
                        'level': 'level_2',
                        'resources': ['vm_1']
                    },
                    'type': 'ATT::Valet::GroupAssignment'
                },
                'key1': {
                    'properties': {
                        'group_name': 'vg1ex',
                        'group_type': 'exclusivity',
                        'level': 'level1',
                        'resources': ['vg_1']
                    },
                    'type': 'ATT::Valet::GroupAssignment'
                },
                'key2': {
                    'properties': {
                        'group_name': 'vg1ex',
                        'group_type': 'exclusivity',
                        'level': 'level2',
                        'resources': ['vg_1']
                    },
                    'type': 'ATT::Valet::GroupAssignment'
                },
                'vg_1': {
                    'properties': {
                        'group_name': 'test_group',
                        'group_type': 'affinity',
                        'level': 'test_level',
                        'resources': ['sg_1', 'sg_2']
                    },
                    'type': 'ATT::Valet::GroupAssignment'
                },
                'vm_1': {
                    'name': 'test_name',
                    'properties': {
                        'availability_zone': 'test_zone',
                        'flavor': 'tiny'
                    },
                    'type': 'OS::Nova::Server'
                }
            },
            'stack_id': 'mock_stack_id'
        }

        self.assertEqual(expected, result)
