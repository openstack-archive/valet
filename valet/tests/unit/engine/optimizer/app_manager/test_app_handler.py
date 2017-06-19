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
import uuid

from valet.engine.optimizer.app_manager.app_handler import AppHandler
from valet.engine.optimizer.app_manager.app_handler import AppHistory
from valet.engine.optimizer.app_manager.application import App
from valet.engine.optimizer.db_connect.music_handler import MusicHandler
from valet.tests.base import Base


class TestAppHandler(Base):

    def setUp(self):
        super(TestAppHandler, self).setUp()

        rstr = uuid.uuid4().hex

        self.config = mock.Mock()
        self.db = MusicHandler(self.config)
        self.app = AppHandler(rstr, self.db, self.config)

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
        self.assertEqual(result, None)

        mock_get_app_info.return_value = {}

        result = self.app._regenerate_app_topology(None, None, None, None)
        self.assertEqual(result, None)
