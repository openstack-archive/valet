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

from valet.engine.resource_manager.resources.group import Group
from valet.engine.resource_manager.resources.host import Host
from valet.tests.base import Base


class TestHost(Base):

    def setUp(self):
        super(TestHost, self).setUp()

        self.test_host = Host("test_host")

    def test_clean_memberships(self):
        lg = Group("test_group")
        self.test_host.memberships["test_mem"] = lg

        result = self.test_host.clean_memberships()
        self.assertTrue(result)

        lg.vms_per_host["test_host"] = "foo"
        self.test_host.memberships["test_mem"] = lg

        result = self.test_host.clean_memberships()
        self.assertFalse(result)

    def test_remove_membership(self):
        lg = Group("test_group")
        lg.group_type = "EX"
        self.test_host.memberships["test_group"] = lg

        result = self.test_host.remove_membership(lg)
        self.assertTrue(result)

        lg.vms_per_host["test_host"] = "foo"

        result = self.test_host.remove_membership(lg)
        self.assertFalse(result)

    def test_check_availability(self):
        self.test_host.status = "enabled"
        self.test_host.state = "up"
        self.test_host.tag.append("nova")
        self.test_host.tag.append("infra")

        result = self.test_host.check_availability()
        self.assertTrue(result)

        self.test_host.status = "disabled"

        result = self.test_host.check_availability()
        self.assertFalse(result)

    def test_get_vm_info(self):
        self.test_host.vm_list.append({
            "orch_id": "foo",
            "uuid": "bar"
        })

        result = self.test_host.get_vm_info()
        self.assertIsNone(result)

        result = self.test_host.get_vm_info("none", "bar")
        self.assertEqual(self.test_host.vm_list[0], result)

        result = self.test_host.get_vm_info("foo", "none")
        self.assertEqual(self.test_host.vm_list[0], result)

    def test_get_uuid(self):
        self.test_host.vm_list.append({
            "orch_id": "foo",
            "uuid": "bar"
        })

        result = self.test_host.get_uuid("none")
        self.assertIsNone(result)

        result = self.test_host.get_uuid("foo")
        self.assertEqual("bar", result)

    def test_exist_vm(self):
        self.test_host.vm_list.append({
            "orch_id": "foo",
            "uuid": "bar"
        })

        result = self.test_host.exist_vm()
        self.assertFalse(result)

        result = self.test_host.exist_vm("foo", "none")
        self.assertTrue(result)

        result = self.test_host.exist_vm("none", "bar")
        self.assertTrue(result)

    def test_remove_vm(self):
        self.test_host.vm_list.append({
            "orch_id": "foo",
            "uuid": "bar"
        })

        result = self.test_host.remove_vm()
        self.assertFalse(result)

        result = self.test_host.remove_vm("foo", "none")
        self.assertTrue(result)
        self.assertEqual([], self.test_host.vm_list)

        self.test_host.vm_list.append({
            "orch_id": "foo",
            "uuid": "bar"
        })

        result = self.test_host.remove_vm("none", "bar")
        self.assertTrue(result)
        self.assertEqual([], self.test_host.vm_list)

    def test_update_uuid(self):
        self.test_host.vm_list.append({
            "orch_id": "foo",
            "uuid": "bar"
        })

        result = self.test_host.update_uuid("none", "fake")
        self.assertFalse(result)

        result = self.test_host.update_uuid("foo", "new_uuid")
        self.assertTrue(result)
        self.assertEqual("new_uuid", self.test_host.vm_list[0]["uuid"])

    def test_update_orch_id(self):
        self.test_host.vm_list.append({
            "orch_id": "foo",
            "uuid": "bar"
        })

        result = self.test_host.update_orch_id("none", "fake")
        self.assertFalse(result)

        result = self.test_host.update_orch_id("new_orch", "bar")
        self.assertTrue(result)
        self.assertEqual("new_orch", self.test_host.vm_list[0]["orch_id"])
