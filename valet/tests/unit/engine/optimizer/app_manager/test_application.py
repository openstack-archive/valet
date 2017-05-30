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

from valet.engine.optimizer.app_manager.app_topology_base import VGroup
from valet.engine.optimizer.app_manager.app_topology_base import VM
from valet.engine.optimizer.app_manager.application import App
from valet.tests.base import Base


class TestApplication(Base):

    def setUp(self):
        super(TestApplication, self).setUp()

        self.app = App("test_id", "test_name", "test_action")

    def test_add_vm(self):
        vm = VM("app_uuid", "uuid")

        self.app.add_vm(vm, "test_host", "test_status")
        self.assertEqual(vm, self.app.vms[vm.uuid])

    def test_add_vgroup(self):
        vgroup = VGroup("app_uuid", "uuid")

        self.app.add_vgroup(vgroup, "test_host")
        self.assertEqual(vgroup, self.app.vgroups[vgroup.uuid])

    def test_get_json_info(self):
        request_type = "test_action"
        timestamp_scheduled = "test_timestamp"
        app_id = "test_stack_id"
        app_name = "test_app_name"

        self.app.request_type = request_type
        self.app.timestamp_scheduled = timestamp_scheduled
        self.app.app_id = app_id
        self.app.app_name = app_name

        test_json = {
            'action': request_type,
            'timestamp': timestamp_scheduled,
            'stack_id': app_id,
            'name': app_name,
            'VMs': {},
            'VGroups': {}
        }

        result = self.app.get_json_info()
        self.assertEqual(test_json, result)
