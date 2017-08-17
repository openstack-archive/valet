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

from valet.engine.resource_manager.resources.datacenter import Datacenter
from valet.engine.resource_manager.resources.group import Group
from valet.engine.resource_manager.resources.host_group import HostGroup
from valet.tests.base import Base


class TestHostGroup(Base):

    def setUp(self):
        super(TestHostGroup, self).setUp()

        self.host_group = HostGroup("test_host_group")

    def test_init_memberships(self):
        lg = Group("rack:test_group")
        lg.group_type = "EX"
        self.host_group.memberships[lg.name] = lg

        self.host_group.init_memberships()
        self.assertNotIn("rack:test_group", self.host_group.memberships.keys())

    def test_remove_membership(self):
        lg = Group("test_group")
        lg.group_type = "EX"
        self.host_group.memberships["test_group"] = lg

        result = self.host_group.remove_membership(lg)
        self.assertTrue(result)

        lg.vms_per_host["test_host_group"] = "foo"

        result = self.host_group.remove_membership(lg)
        self.assertFalse(result)

    def test_check_availability(self):
        self.host_group.status = "enabled"

        result = self.host_group.check_availability()
        self.assertTrue(result)

        self.host_group.status = "disabled"

        result = self.host_group.check_availability()
        self.assertFalse(result)

    def test_get_json_info(self):
        parent_datacenter = Datacenter("test_datacenter")
        self.host_group.parent_resource = parent_datacenter
        self.host_group.memberships = {
            "mem_key_1": "mem_value_1"
        }
        self.host_group.child_resources = {
            "child_key_1": "child_value_1"
        }
        membership_list = ["mem_key_1"]
        child_list = ["child_key_1"]

        expected = {
            "status": "enabled",
            "host_type": "rack",
            "membership_list": membership_list,
            "vCPUs": 0,
            "original_vCPUs": 0,
            "avail_vCPUs": 0,
            "mem": 0,
            "original_mem": 0,
            "avail_mem": 0,
            "local_disk": 0,
            "original_local_disk": 0,
            "avail_local_disk": 0,
            "parent": parent_datacenter.name,
            "children": child_list,
            "vm_list": [],
            "last_update": 0
        }

        result = self.host_group.get_json_info()
        self.assertEqual(expected, result)
