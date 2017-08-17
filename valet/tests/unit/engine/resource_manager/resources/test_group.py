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

from valet.engine.resource_manager.resources.group import Group
from valet.tests.base import Base


class TestGroup(Base):

    def setUp(self):
        super(TestGroup, self).setUp()

        self.group = Group("test_group")

    def test_exist_vm(self):
        self.group.vm_list.append({
            "orch_id": "foo",
            "uuid": "bar"
        })

        result = self.group.exist_vm()
        self.assertFalse(result)

        result = self.group.exist_vm("foo", "none")
        self.assertTrue(result)

        result = self.group.exist_vm("none", "bar")
        self.assertTrue(result)

    def test_exist_vm_in_host(self):
        self.group.vms_per_host["test_key"] = [{
            "orch_id": "foo",
            "uuid": "bar"
        }]

        result = self.group.exist_vm_in_host("bad_key")
        self.assertFalse(result)

        result = self.group.exist_vm_in_host("test_key", "foo", "none")
        self.assertTrue(True)

        result = self.group.exist_vm_in_host("test_key", None, "bar")
        self.assertTrue(result)

    def test_update_uuid(self):
        self.group.vm_list = [{
            "orch_id": "foo",
            "uuid": "bar"
        }]
        self.group.vms_per_host["test_key"] = [{
            "orch_id": "alpha",
            "uuid": "beta"
        }]

        result = self.group.update_uuid("not_foo", "not_bar", "test_host")
        self.assertFalse(result)

        result = self.group.update_uuid("foo", "bar_update", "test_host")
        self.assertTrue(result)

        result = self.group.update_uuid("alpha", "omega", "test_key")
        self.assertTrue(result)

    def test_update_orch_id(self):
        self.group.vm_list = [{
            "orch_id": "foo",
            "uuid": "bar"
        }]
        self.group.vms_per_host["test_key"] = [{
            "orch_id": "alpha",
            "uuid": "beta"
        }]

        result = self.group.update_orch_id("not_foo", "not_bar", "test_host")
        self.assertFalse(result)

        result = self.group.update_orch_id("foo_update", "bar", "test_host")
        self.assertTrue(result)

        result = self.group.update_orch_id("omega", "beta", "test_key")
        self.assertTrue(result)

    @mock.patch.object(Group, 'remove_vm_from_host')
    @mock.patch.object(Group, 'exist_vm_in_host')
    @mock.patch.object(Group, '_remove_vm')
    @mock.patch.object(Group, 'exist_vm')
    def test_add_vm(self, mock_exist, mock_remove,
                    mock_exist_host, mock_remove_host):
        mock_exist.return_value = True
        mock_exist_host.return_value = True
        test_vm_info = {
            "orch_id": "foo",
            "uuid": "bar"
        }
        self.group.group_type = "AFF"

        result = self.group.add_vm(test_vm_info, "test_host")
        self.assertTrue(result)
        mock_remove.assert_called_once_with(orch_id="foo", uuid="bar")
        mock_remove_host.assert_called_once_with("test_host", orch_id="foo", uuid="bar")
