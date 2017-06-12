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

from valet.engine.resource_manager.resource_base import Datacenter
from valet.engine.resource_manager.resource_base import Flavor
from valet.engine.resource_manager.resource_base import Host
from valet.engine.resource_manager.resource_base import HostGroup
from valet.engine.resource_manager.resource_base import LogicalGroup
from valet.tests.base import Base


class TestResourceBase(Base):

    def setUp(self):
        super(TestResourceBase, self).setUp()

        self.datacenter = Datacenter(uuid.uuid4().hex)
        self.hostgroup = HostGroup(uuid.uuid4().int)
        self.host = Host(uuid.uuid4().hex)
        self.logicalgroup = LogicalGroup(uuid.uuid4().hex)
        self.flavor = Flavor(uuid.uuid4().hex)

        self.vCPUs = "test_vcpus"
        self.original_vCPUs = "test_original_vcpus"
        self.avail_vCPUs = "test_avail_vcpus"
        self.mem_cap = "test_mem_cap"
        self.original_mem_cap = "test_original_mem_cap"
        self.avail_mem_cap = "test_avail_mem_cap"
        self.local_disk_cap = "test_local_disk_cap"
        self.original_local_disk_cap = "test_original_local_disk_cap"
        self.avail_local_disk_cap = "test_avail_local_disk_cap"

    def test_datacenter_init_resources(self):
        self.datacenter.vCPUs = self.vCPUs
        self.datacenter.original_vCPUs = self.original_vCPUs
        self.datacenter.avail_vCPUs = self.avail_vCPUs
        self.datacenter.mem_cap = self.mem_cap
        self.datacenter.original_mem_cap = self.original_mem_cap
        self.datacenter.avail_mem_cap = self.avail_mem_cap
        self.datacenter.local_disk_cap = self.local_disk_cap
        self.datacenter.original_local_disk_cap = self.original_local_disk_cap
        self.datacenter.avail_local_disk_cap = self.avail_local_disk_cap

        self.datacenter.init_resources()
        self.assertEqual(self.datacenter.vCPUs, 0)
        self.assertEqual(self.datacenter.original_vCPUs, 0)
        self.assertEqual(self.datacenter.avail_vCPUs, 0)
        self.assertEqual(self.datacenter.mem_cap, 0)
        self.assertEqual(self.datacenter.original_mem_cap, 0)
        self.assertEqual(self.datacenter.avail_mem_cap, 0)
        self.assertEqual(self.datacenter.local_disk_cap, 0)
        self.assertEqual(self.datacenter.original_local_disk_cap, 0)
        self.assertEqual(self.datacenter.avail_local_disk_cap, 0)

    def test_datacenter_get_json_info(self):
        self.datacenter.vCPUs = self.vCPUs
        self.datacenter.original_vCPUs = self.original_vCPUs
        self.datacenter.avail_vCPUs = self.avail_vCPUs
        self.datacenter.mem_cap = self.mem_cap
        self.datacenter.original_mem_cap = self.original_mem_cap
        self.datacenter.avail_mem_cap = self.avail_mem_cap
        self.datacenter.local_disk_cap = self.local_disk_cap
        self.datacenter.original_local_disk_cap = self.original_local_disk_cap
        self.datacenter.avail_local_disk_cap = self.avail_local_disk_cap
        expected = {
            'status': "enabled",
            'name': self.datacenter.name,
            'region_code_list': [],
            'membership_list': [],
            'vCPUs': self.vCPUs,
            'original_vCPUs': self.original_vCPUs,
            'avail_vCPUs': self.avail_vCPUs,
            'mem': self.mem_cap,
            'original_mem': self.original_mem_cap,
            'avail_mem': self.avail_mem_cap,
            'local_disk': self.local_disk_cap,
            'original_local_disk': self.original_local_disk_cap,
            'avail_local_disk': self.avail_local_disk_cap,
            'children': [],
            'vm_list': [],
            'last_update': 0
        }

        result = self.datacenter.get_json_info()
        self.assertEqual(expected, result)

    def test_hostgroup_init_resources(self):
        self.hostgroup.vCPUs = self.vCPUs
        self.hostgroup.original_vCPUs = self.original_vCPUs
        self.hostgroup.avail_vCPUs = self.avail_vCPUs
        self.hostgroup.mem_cap = self.mem_cap
        self.hostgroup.original_mem_cap = self.original_mem_cap
        self.hostgroup.avail_mem_cap = self.avail_mem_cap
        self.hostgroup.local_disk_cap = self.local_disk_cap
        self.hostgroup.original_local_disk_cap = self.original_local_disk_cap
        self.hostgroup.avail_local_disk_cap = self.avail_local_disk_cap

        self.hostgroup.init_resources()
        self.assertEqual(self.hostgroup.vCPUs, 0)
        self.assertEqual(self.hostgroup.original_vCPUs, 0)
        self.assertEqual(self.hostgroup.avail_vCPUs, 0)
        self.assertEqual(self.hostgroup.mem_cap, 0)
        self.assertEqual(self.hostgroup.original_mem_cap, 0)
        self.assertEqual(self.hostgroup.avail_mem_cap, 0)
        self.assertEqual(self.hostgroup.local_disk_cap, 0)
        self.assertEqual(self.hostgroup.original_local_disk_cap, 0)
        self.assertEqual(self.hostgroup.avail_local_disk_cap, 0)

    def test_hostgroup_init_memberships_level_lt_host_level(self):
        mock_logical_group = LogicalGroup("rack:foo")
        mock_logical_group.group_type = "EX"
        self.hostgroup.host_type = "cluster"
        self.hostgroup.memberships = {
            "lg": mock_logical_group
        }

        self.hostgroup.init_memberships()
        self.assertEqual(self.hostgroup.memberships, {})

    def test_hostgroup_init_memberships_host_not_in_vms(self):
        mock_logical_group = LogicalGroup("rack:foo")
        mock_logical_group.group_type = "EX"
        self.hostgroup.host_type = "host"
        self.hostgroup.memberships = {
            "lg": mock_logical_group
        }

        self.hostgroup.init_memberships()
        self.assertEqual(self.hostgroup.memberships, {})

    def test_hostgroup_init_memberships_host_in_vms(self):
        mock_logical_group = LogicalGroup("rack:foo")
        mock_logical_group.group_type = "EX"
        mock_logical_group.vms_per_host = {
            self.hostgroup.name: "is_valid"
        }
        self.hostgroup.host_type = "host"
        self.hostgroup.memberships = {
            "lg": mock_logical_group
        }

        self.hostgroup.init_memberships()
        self.assertEqual(self.hostgroup.memberships, {"lg":
                         mock_logical_group})

    def test_hostgroup_init_memperships_no_group_type(self):
        mock_logical_group = LogicalGroup("rack:foo")
        self.hostgroup.host_type = "host"
        self.hostgroup.memberships = {
            "lg": mock_logical_group
        }

        self.hostgroup.init_memberships()
        self.assertEqual(self.hostgroup.memberships, {})

    def test_hostgroup_remove_membership_host_not_in_vms(self):
        mock_logical_group = LogicalGroup("rack:foo")
        mock_logical_group.group_type = "EX"
        self.hostgroup.memberships = {
            "rack:foo": mock_logical_group
        }

        result = self.hostgroup.remove_membership(mock_logical_group)
        self.assertEqual(self.hostgroup.memberships, {})
        self.assertTrue(result)

    def test_hostgroup_remove_membership_host_in_vms(self):
        mock_logical_group = LogicalGroup("rack:foo")
        mock_logical_group.group_type = "EX"
        mock_logical_group.vms_per_host = {
            self.hostgroup.name: "is_valid"
        }
        self.hostgroup.memberships = {
            "rack:foo": mock_logical_group
        }

        result = self.hostgroup.remove_membership(mock_logical_group)
        self.assertEqual(self.hostgroup.memberships, {"rack:foo":
                         mock_logical_group})
        self.assertFalse(result)

    def test_hostgroup_remove_membership_no_group_type(self):
        mock_logical_group = LogicalGroup("rack:foo")
        self.hostgroup.memberships = {
            "rack:foo": mock_logical_group
        }

        result = self.hostgroup.remove_membership(mock_logical_group)
        self.assertEqual(self.hostgroup.memberships, {"rack:foo":
                         mock_logical_group})
        self.assertFalse(result)

    def test_hostgroup_check_availability_enabled(self):
        self.hostgroup.status = "enabled"

        result = self.hostgroup.check_availability()
        self.assertTrue(result)

    def test_hostgroup_check_availability_not_enabled(self):
        self.hostgroup.status = "disabled"

        result = self.hostgroup.check_availability()
        self.assertFalse(result)

    def test_hostgroup_get_json_info_no_parent(self):
        self.hostgroup.vCPUs = self.vCPUs
        self.hostgroup.original_vCPUs = self.original_vCPUs
        self.hostgroup.avail_vCPUs = self.avail_vCPUs
        self.hostgroup.mem_cap = self.mem_cap
        self.hostgroup.original_mem_cap = self.original_mem_cap
        self.hostgroup.avail_mem_cap = self.avail_mem_cap
        self.hostgroup.local_disk_cap = self.local_disk_cap
        self.hostgroup.original_local_disk_cap = self.original_local_disk_cap
        self.hostgroup.avail_local_disk_cap = self.avail_local_disk_cap
        expected = {
            'status': "enabled",
            'host_type': "rack",
            'membership_list': [],
            'vCPUs': self.vCPUs,
            'original_vCPUs': self.original_vCPUs,
            'avail_vCPUs': self.avail_vCPUs,
            'mem': self.mem_cap,
            'original_mem': self.original_mem_cap,
            'avail_mem': self.avail_mem_cap,
            'local_disk': self.local_disk_cap,
            'original_local_disk': self.original_local_disk_cap,
            'avail_local_disk': self.avail_local_disk_cap,
            'parent': None,
            'children': [],
            'vm_list': [],
            'last_update': 0
        }

        result = self.hostgroup.get_json_info()
        self.assertEqual(expected, result)

    def test_hostgroup_get_json_info_has_parent(self):
        self.hostgroup.vCPUs = self.vCPUs
        self.hostgroup.original_vCPUs = self.original_vCPUs
        self.hostgroup.avail_vCPUs = self.avail_vCPUs
        self.hostgroup.mem_cap = self.mem_cap
        self.hostgroup.original_mem_cap = self.original_mem_cap
        self.hostgroup.avail_mem_cap = self.avail_mem_cap
        self.hostgroup.local_disk_cap = self.local_disk_cap
        self.hostgroup.original_local_disk_cap = self.original_local_disk_cap
        self.hostgroup.avail_local_disk_cap = self.avail_local_disk_cap
        self.hostgroup.parent_resource = mock.Mock()
        self.hostgroup.parent_resource.name = "foo"
        expected = {
            'status': "enabled",
            'host_type': "rack",
            'membership_list': [],
            'vCPUs': self.vCPUs,
            'original_vCPUs': self.original_vCPUs,
            'avail_vCPUs': self.avail_vCPUs,
            'mem': self.mem_cap,
            'original_mem': self.original_mem_cap,
            'avail_mem': self.avail_mem_cap,
            'local_disk': self.local_disk_cap,
            'original_local_disk': self.original_local_disk_cap,
            'avail_local_disk': self.avail_local_disk_cap,
            'parent': "foo",
            'children': [],
            'vm_list': [],
            'last_update': 0
        }

        result = self.hostgroup.get_json_info()
        self.assertEqual(expected, result)

    def test_host_clean_memberships_name_in_vms(self):
        mock_logical_group = LogicalGroup("rack:foo")
        mock_logical_group.vms_per_host = {
            self.host.name: 'is_valid'
        }
        self.host.memberships = {
            "rack:foo": mock_logical_group
        }

        result = self.host.clean_memberships()
        self.assertEqual(self.host.memberships, {"rack:foo":
                         mock_logical_group})
        self.assertFalse(result)

    def test_host_clean_memberships_name_not_in_vms(self):
        mock_logical_group = LogicalGroup("rack:foo")
        self.host.memberships = {
            "rack:foo": mock_logical_group
        }

        result = self.host.clean_memberships()
        self.assertEqual(self.host.memberships, {})
        self.assertTrue(result)

    def test_host_remove_membership_host_not_in_vms(self):
        mock_logical_group = LogicalGroup("rack:foo")
        mock_logical_group.group_type = "EX"
        self.host.memberships = {
            "rack:foo": mock_logical_group
        }

        result = self.host.remove_membership(mock_logical_group)
        self.assertEqual(self.host.memberships, {})
        self.assertTrue(result)

    def test_host_remove_membership_host_in_vms(self):
        mock_logical_group = LogicalGroup("rack:foo")
        mock_logical_group.group_type = "EX"
        mock_logical_group.vms_per_host = {
            self.host.name: "is_valid"
        }
        self.host.memberships = {
            "rack:foo": mock_logical_group
        }

        result = self.host.remove_membership(mock_logical_group)
        self.assertEqual(self.host.memberships, {"rack:foo":
                         mock_logical_group})
        self.assertFalse(result)

    def test_host_remove_membership_no_group_type(self):
        mock_logical_group = LogicalGroup("rack:foo")
        self.host.memberships = {
            "rack:foo": mock_logical_group
        }

        result = self.host.remove_membership(mock_logical_group)
        self.assertEqual(self.host.memberships, {"rack:foo":
                         mock_logical_group})
        self.assertFalse(result)

    def test_host_check_availability_enabled(self):
        self.host.status = "enabled"
        self.host.state = "up"
        self.host.tag = ["nova", "infra"]

        result = self.host.check_availability()
        self.assertTrue(result)

    def test_host_check_availability_disabled(self):
        self.host.status = "disabled"

        result = self.host.check_availability()
        self.assertFalse(result)

    def test_host_get_uuid_has_vm_id(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        self.host.vm_list = [mock_vm_id]

        result = self.host.get_uuid(mock_h_uuid)
        self.assertEqual(mock_uuid, result)

    def test_host_get_uuid_no_vm_id(self):
        self.host.vm_list = []

        result = self.host.get_uuid(uuid.uuid4().hex)
        self.assertEqual(None, result)

    def test_host_exist_vm_by_h_uuid_has_vm_id(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        self.host.vm_list = [mock_vm_id]

        result = self.host.exist_vm_by_h_uuid(mock_h_uuid)
        self.assertTrue(result)

    def test_host_exist_vm_by_h_uuid_no_vm_id(self):
        self.host.vm_list = []

        result = self.host.exist_vm_by_h_uuid(uuid.uuid4().hex)
        self.assertFalse(result)

    def test_host_exist_vm_by_uuid_has_vm_id(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        self.host.vm_list = [mock_vm_id]

        result = self.host.exist_vm_by_uuid(mock_uuid)
        self.assertTrue(result)

    def test_host_exist_vm_by_uuid_no_vm_id(self):
        self.host.vm_list = []

        result = self.host.exist_vm_by_uuid(uuid.uuid4().hex)
        self.assertFalse(result)

    def test_host_remove_vm_by_h_uuid_has_vm_id(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        self.host.vm_list = [mock_vm_id]

        result = self.host.remove_vm_by_h_uuid(mock_h_uuid)
        self.assertNotIn(mock_vm_id, self.host.vm_list)
        self.assertTrue(result)

    def test_host_remove_vm_by_h_uuid_no_vm_id(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        self.host.vm_list = []

        result = self.host.remove_vm_by_h_uuid(mock_h_uuid)
        self.assertNotIn(mock_vm_id, self.host.vm_list)
        self.assertFalse(result)

    def test_host_remove_vm_by_uuid_has_vm_id(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        self.host.vm_list = [mock_vm_id]

        result = self.host.remove_vm_by_uuid(mock_uuid)
        self.assertNotIn(mock_vm_id, self.host.vm_list)
        self.assertTrue(result)

    def test_host_remove_vm_by_uuid_no_vm_id(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        self.host.vm_list = []

        result = self.host.remove_vm_by_uuid(mock_uuid)
        self.assertNotIn(mock_vm_id, self.host.vm_list)
        self.assertFalse(result)

    def test_host_update_uuid_has_vm_id(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        self.host.vm_list = [mock_vm_id]
        mock_new_uuid = uuid.uuid4().hex

        result = self.host.update_uuid(mock_h_uuid, mock_new_uuid)
        self.assertIn((mock_h_uuid, 0, mock_new_uuid), self.host.vm_list)
        self.assertTrue(result)

    def test_host_update_uuid_no_vm_id(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        self.host.vm_list = []

        result = self.host.update_uuid(mock_h_uuid, mock_uuid)
        self.assertNotIn(mock_vm_id, self.host.vm_list)
        self.assertFalse(result)

    def test_host_update_h_uuid_has_vm_id(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        self.host.vm_list = [mock_vm_id]
        mock_new_h_uuid = uuid.uuid4().hex

        result = self.host.update_h_uuid(mock_new_h_uuid, mock_uuid)
        self.assertIn((mock_new_h_uuid, 0, mock_uuid), self.host.vm_list)
        self.assertTrue(result)

    def test_host_update_h_uuid_no_vm_id(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        self.host.vm_list = []

        result = self.host.update_h_uuid(mock_h_uuid, mock_uuid)
        self.assertNotIn(mock_vm_id, self.host.vm_list)
        self.assertFalse(result)

    def test_host_compute_avail_vCPUs(self):
        self.host.vCPUs = 8
        self.host.original_vCPUs = 16
        self.host.vCPUs_used = 4

        self.host.compute_avail_vCPUs(0.5, 0.2)
        self.assertAlmostEqual(6.4, self.host.vCPUs, places=7)
        self.assertAlmostEqual(2.4, self.host.avail_vCPUs, places=7)

    def test_host_compute_avail_mem(self):
        self.host.original_mem_cap = 64
        self.host.free_mem_mb = 16

        self.host.compute_avail_mem(0.5, 0.2)
        self.assertAlmostEqual(25.6, self.host.mem_cap, places=7)
        self.assertAlmostEqual(-22.4, self.host.avail_mem_cap, places=7)

    def test_host_compute_avail_disk_least_gt_zero(self):
        self.host.original_local_disk_cap = 256
        self.host.free_disk_gb = 64
        self.host.disk_available_least = 8

        self.host.compute_avail_disk(0.5, 0.2)
        self.assertAlmostEqual(102.4, self.host.local_disk_cap, places=7)
        self.assertAlmostEqual(-145.6, self.host.avail_local_disk_cap,
                               places=7)

    def test_host_compute_avail_disk_least_eq_zero(self):
        self.host.original_local_disk_cap = 256
        self.host.free_disk_gb = 64
        self.host.disk_available_least = 0

        self.host.compute_avail_disk(0.5, 0.2)
        self.assertAlmostEqual(102.4, self.host.local_disk_cap, places=7)
        self.assertAlmostEqual(-89.6, self.host.avail_local_disk_cap,
                               places=7)

    def test_host_get_json_info_has_parent(self):
        self.host.vCPUs = self.vCPUs
        self.host.original_vCPUs = self.original_vCPUs
        self.host.avail_vCPUs = self.avail_vCPUs
        self.host.mem_cap = self.mem_cap
        self.host.original_mem_cap = self.original_mem_cap
        self.host.avail_mem_cap = self.avail_mem_cap
        self.host.local_disk_cap = self.local_disk_cap
        self.host.original_local_disk_cap = self.original_local_disk_cap
        self.host.avail_local_disk_cap = self.avail_local_disk_cap
        self.host.host_group = mock.Mock()
        self.host.host_group.name = "foo"
        expected = {
            'tag': [],
            'status': "enabled",
            'state': "up",
            'membership_list': [],
            'vCPUs': self.vCPUs,
            'original_vCPUs': self.original_vCPUs,
            'avail_vCPUs': self.avail_vCPUs,
            'mem': self.mem_cap,
            'original_mem': self.original_mem_cap,
            'avail_mem': self.avail_mem_cap,
            'local_disk': self.local_disk_cap,
            'original_local_disk': self.original_local_disk_cap,
            'avail_local_disk': self.avail_local_disk_cap,
            'vCPUs_used': 0,
            'free_mem_mb': 0,
            'free_disk_gb': 0,
            'disk_available_least': 0,
            'parent': "foo",
            'vm_list': [],
            'last_update': 0
        }

        result = self.host.get_json_info()
        self.assertEqual(expected, result)

    def test_logicalgroup_exist_vm_by_h_uuid_has_vm_id(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        self.logicalgroup.vm_list = [mock_vm_id]

        result = self.logicalgroup.exist_vm_by_h_uuid(mock_h_uuid)
        self.assertTrue(result)

    def test_logicalgroup_exist_vm_by_h_uui_no_vm_id(self):
        self.logicalgroup.vm_list = []

        result = self.logicalgroup.exist_vm_by_h_uuid(uuid.uuid4().hex)
        self.assertFalse(result)

    def test_logicalgroup_exist_vm_by_uuid_has_vm_id(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        self.logicalgroup.vm_list = [mock_vm_id]

        result = self.logicalgroup.exist_vm_by_uuid(mock_uuid)
        self.assertTrue(result)

    def test_logicalgroup_exist_vm_by_uuid_no_vm_id(self):
        self.logicalgroup.vm_list = []

        result = self.logicalgroup.exist_vm_by_uuid(uuid.uuid4().hex)
        self.assertFalse(result)

    def test_logicalgroup_update_uuid_has_vm_id_and_host(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, mock_host_id, mock_uuid)
        self.logicalgroup.vm_list = [mock_vm_id]
        self.logicalgroup.vms_per_host = {
            mock_host_id: [
                mock_vm_id
            ]
        }
        mock_new_uuid = uuid.uuid4().hex

        result = self.logicalgroup.update_uuid(mock_h_uuid, mock_new_uuid,
                                               mock_host_id)
        self.assertIn((mock_h_uuid, mock_host_id, mock_new_uuid),
                      self.logicalgroup.vms_per_host[mock_host_id])
        self.assertIn((mock_h_uuid, mock_host_id, mock_new_uuid),
                      self.logicalgroup.vm_list)
        self.assertTrue(result)

    def test_logicalgroup_update_uuid_no_vm_id_or_host(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        self.logicalgroup.vm_list = []
        self.logicalgroup.vms_per_host = {}

        result = self.logicalgroup.update_uuid(mock_h_uuid, mock_uuid,
                                               mock_host_id)
        self.assertEqual([], self.logicalgroup.vm_list)
        self.assertFalse(result)

    def test_logicalgroup_update_uuid_no_vm_id_has_host(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, mock_host_id, mock_uuid)
        self.logicalgroup.vm_list = []
        self.logicalgroup.vms_per_host = {
            mock_host_id: [
                mock_vm_id
            ]
        }

        result = self.logicalgroup.update_uuid(mock_h_uuid, mock_uuid,
                                               mock_host_id)
        self.assertIn((mock_h_uuid, "none", mock_uuid),
                      self.logicalgroup.vm_list)
        self.assertIn((mock_h_uuid, "none", mock_uuid),
                      self.logicalgroup.vms_per_host[mock_host_id])
        self.assertTrue(result)

    def test_logicalgroup_update_h_uuid_has_vm_id_and_host(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, mock_host_id, mock_uuid)
        self.logicalgroup.vm_list = [mock_vm_id]
        self.logicalgroup.vms_per_host = {
            mock_host_id: [
                mock_vm_id
            ]
        }
        mock_new_h_uuid = uuid.uuid4().hex

        result = self.logicalgroup.update_h_uuid(mock_new_h_uuid, mock_uuid,
                                                 mock_host_id)
        self.assertIn((mock_new_h_uuid, mock_host_id, mock_uuid),
                      self.logicalgroup.vms_per_host[mock_host_id])
        self.assertIn((mock_new_h_uuid, mock_host_id, mock_uuid),
                      self.logicalgroup.vm_list)
        self.assertTrue(result)

    def test_logicalgroup_update_h_uuid_no_vm_id_or_host(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        self.logicalgroup.vm_list = []
        self.logicalgroup.vms_per_host = {}

        result = self.logicalgroup.update_h_uuid(mock_h_uuid, mock_uuid,
                                                 mock_host_id)
        self.assertEqual([], self.logicalgroup.vm_list)
        self.assertFalse(result)

    def test_logicalgroup_update_h_uuid_no_vm_id_has_host(self):
        mock_h_uuid = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, mock_host_id, mock_uuid)
        self.logicalgroup.vm_list = []
        self.logicalgroup.vms_per_host = {
            mock_host_id: [
                mock_vm_id
            ]
        }

        result = self.logicalgroup.update_h_uuid(mock_h_uuid, mock_uuid,
                                                 mock_host_id)
        self.assertIn((mock_h_uuid, "none", mock_uuid),
                      self.logicalgroup.vm_list)
        self.assertIn((mock_h_uuid, "none", mock_uuid),
                      self.logicalgroup.vms_per_host[mock_host_id])
        self.assertTrue(result)

    @mock.patch.object(LogicalGroup, '_check_group_type')
    @mock.patch.object(LogicalGroup, 'exist_vm_by_h_uuid')
    def test_add_vm_by_h_uuid_new_vm_host_absent(self,
                                                 mock_exist_by_h_uuid,
                                                 mock_check_group):
        mock_exist_by_h_uuid.return_value = False
        mock_check_group.return_value = True
        mock_vm_id = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex
        self.logicalgroup.vms_per_host = {}

        result = self.logicalgroup.add_vm_by_h_uuid(mock_vm_id, mock_host_id)
        self.assertIn(mock_vm_id, self.logicalgroup.vm_list)
        self.assertIn(mock_vm_id, self.logicalgroup.vms_per_host[mock_host_id])
        self.assertTrue(result)

    @mock.patch.object(LogicalGroup, '_check_group_type')
    @mock.patch.object(LogicalGroup, 'exist_vm_by_h_uuid')
    def test_add_vm_by_h_uuid_new_vm_host_present(self,
                                                  mock_exist_by_h_uuid,
                                                  mock_check_group):
        mock_exist_by_h_uuid.return_value = False
        mock_check_group.return_value = True
        mock_vm_id = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex
        self.logicalgroup.vms_per_host = {
            mock_host_id: []
        }

        result = self.logicalgroup.add_vm_by_h_uuid(mock_vm_id, mock_host_id)
        self.assertIn(mock_vm_id, self.logicalgroup.vm_list)
        self.assertIn(mock_vm_id, self.logicalgroup.vms_per_host[mock_host_id])
        self.assertTrue(result)

    @mock.patch.object(LogicalGroup, 'exist_vm_by_h_uuid')
    def test_add_vm_by_h_uuid_vm_exists(self, mock_exist_by_h_uuid):
        mock_exist_by_h_uuid.return_value = True
        mock_vm_id = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex

        result = self.logicalgroup.add_vm_by_h_uuid(mock_vm_id, mock_host_id)
        self.assertNotIn(mock_vm_id, self.logicalgroup.vm_list)
        self.assertFalse(result)

    @mock.patch.object(LogicalGroup, '_check_group_type')
    def test_remove_vm_by_h_uuid_has_vm_remove_host(self,
                                                    mock_check_group):
        mock_check_group.return_value = True
        mock_h_uuid = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, mock_host_id, mock_uuid)
        self.logicalgroup.vm_list = [mock_vm_id]
        self.logicalgroup.vms_per_host = {
            mock_host_id: [mock_vm_id]
        }

        result = self.logicalgroup.remove_vm_by_h_uuid(mock_h_uuid,
                                                       mock_host_id)
        self.assertEqual([], self.logicalgroup.vm_list)
        self.assertEqual({}, self.logicalgroup.vms_per_host)
        self.assertTrue(result)

    @mock.patch.object(LogicalGroup, '_check_group_type')
    def test_remove_vm_by_h_uuid_has_vm_keep_host(self,
                                                  mock_check_group):
        mock_check_group.return_value = False
        mock_h_uuid = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, mock_host_id, mock_uuid)
        self.logicalgroup.vm_list = [mock_vm_id]
        self.logicalgroup.vms_per_host = {
            mock_host_id: [mock_vm_id]
        }

        result = self.logicalgroup.remove_vm_by_h_uuid(mock_h_uuid,
                                                       mock_host_id)
        self.assertEqual([], self.logicalgroup.vm_list)
        self.assertEqual([], self.logicalgroup.vms_per_host[mock_host_id])
        self.assertTrue(result)

    @mock.patch.object(LogicalGroup, '_check_group_type')
    def test_remove_vm_by_h_uuid_no_vms_or_hosts(self,
                                                 mock_check_group):
        mock_check_group.return_value = True
        mock_h_uuid = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex
        self.logicalgroup.vm_list = []
        self.logicalgroup.vms_per_host = {}

        result = self.logicalgroup.remove_vm_by_h_uuid(mock_h_uuid,
                                                       mock_host_id)
        self.assertEqual([], self.logicalgroup.vm_list)
        self.assertEqual({}, self.logicalgroup.vms_per_host)
        self.assertFalse(result)

    @mock.patch.object(LogicalGroup, '_check_group_type')
    def test_remove_vm_by_uuid_has_vm_remove_host(self,
                                                  mock_check_group):
        mock_check_group.return_value = True
        mock_h_uuid = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, mock_host_id, mock_uuid)
        self.logicalgroup.vm_list = [mock_vm_id]
        self.logicalgroup.vms_per_host = {
            mock_host_id: [mock_vm_id]
        }

        result = self.logicalgroup.remove_vm_by_uuid(mock_uuid, mock_host_id)
        self.assertEqual([], self.logicalgroup.vm_list)
        self.assertEqual({}, self.logicalgroup.vms_per_host)
        self.assertTrue(result)

    @mock.patch.object(LogicalGroup, '_check_group_type')
    def test_remove_vm_by_uuid_has_vm_keep_host(self,
                                                mock_check_group):
        mock_check_group.return_value = False
        mock_h_uuid = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, mock_host_id, mock_uuid)
        self.logicalgroup.vm_list = [mock_vm_id]
        self.logicalgroup.vms_per_host = {
            mock_host_id: [mock_vm_id]
        }

        result = self.logicalgroup.remove_vm_by_uuid(mock_uuid, mock_host_id)
        self.assertEqual([], self.logicalgroup.vm_list)
        self.assertEqual([], self.logicalgroup.vms_per_host[mock_host_id])
        self.assertTrue(result)

    @mock.patch.object(LogicalGroup, '_check_group_type')
    def test_remove_vm_by_uuid_no_vms_or_hosts(self,
                                               mock_check_group):
        mock_check_group.return_value = True
        mock_host_id = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        self.logicalgroup.vm_list = []
        self.logicalgroup.vms_per_host = {}

        result = self.logicalgroup.remove_vm_by_uuid(mock_uuid, mock_host_id)
        self.assertEqual([], self.logicalgroup.vm_list)
        self.assertEqual({}, self.logicalgroup.vms_per_host)
        self.assertFalse(result)

    @mock.patch.object(LogicalGroup, '_check_group_type')
    def test_clean_none_vms_has_mixed_vms(self,
                                          mock_check_group):
        mock_check_group.return_value = True
        mock_host_id = uuid.uuid4().hex
        mock_vm_with_uuid = (uuid.uuid4().hex, mock_host_id, uuid.uuid4().hex)
        mock_vm_with_none = (uuid.uuid4().hex, mock_host_id, "none")
        self.logicalgroup.vm_list = [
            mock_vm_with_uuid, mock_vm_with_none
        ]
        self.logicalgroup.vms_per_host = {
            mock_host_id: [
                mock_vm_with_uuid, mock_vm_with_none
            ]
        }

        result = self.logicalgroup.clean_none_vms(mock_host_id)
        self.assertEqual([mock_vm_with_uuid], self.logicalgroup.vm_list)
        self.assertEqual([mock_vm_with_uuid],
                         self.logicalgroup.vms_per_host[mock_host_id])
        self.assertTrue(result)

    @mock.patch.object(LogicalGroup, '_check_group_type')
    def test_clean_none_vms_has_only_none_vms(self,
                                              mock_check_group):
        mock_check_group.return_value = True
        mock_host_id = uuid.uuid4().hex
        mock_vm_with_none = (uuid.uuid4().hex, mock_host_id, "none")
        self.logicalgroup.vm_list = [
            mock_vm_with_none
        ]
        self.logicalgroup.vms_per_host = {
            mock_host_id: [
                mock_vm_with_none
            ]
        }

        result = self.logicalgroup.clean_none_vms(mock_host_id)
        self.assertEqual([], self.logicalgroup.vm_list)
        self.assertEqual({}, self.logicalgroup.vms_per_host)
        self.assertTrue(result)

    @mock.patch.object(LogicalGroup, '_check_group_type')
    def test_clean_none_vms_has_only_valid_vms(self,
                                               mock_check_group):
        mock_check_group.return_value = True
        mock_host_id = uuid.uuid4().hex
        mock_vm_with_uuid = (uuid.uuid4().hex, mock_host_id, uuid.uuid4().hex)
        self.logicalgroup.vm_list = [
            mock_vm_with_uuid
        ]
        self.logicalgroup.vms_per_host = {
            mock_host_id: [
                mock_vm_with_uuid
            ]
        }

        result = self.logicalgroup.clean_none_vms(mock_host_id)
        self.assertEqual([mock_vm_with_uuid], self.logicalgroup.vm_list)
        self.assertEqual([mock_vm_with_uuid],
                         self.logicalgroup.vms_per_host[mock_host_id])
        self.assertFalse(result)

    def test_logicalgroup_get_json_info(self):
        self.logicalgroup.status = "enabled"
        self.logicalgroup.group_type = "AGGR"
        self.logicalgroup.metadata = {}
        self.logicalgroup.vm_list = []
        self.logicalgroup.vms_per_host = {}
        self.logicalgroup.last_update = 0
        expected = {
            'status': "enabled",
            'group_type': "AGGR",
            'metadata': {},
            'vm_list': [],
            'vms_per_host': {},
            'last_update': 0
        }

        result = self.logicalgroup.get_json_info()
        self.assertEqual(expected, result)

    def test_flavor_get_json_info(self):
        self.flavor.status = "enabled"
        self.flavor.flavor_id = "test_id"
        self.flavor.vCPUs = self.vCPUs
        self.flavor.mem_cap = self.mem_cap
        self.flavor.disk_cap = 64
        self.flavor.extra_specs = {}
        self.flavor.last_update = 0
        expected = {
            'status': "enabled",
            'flavor_id': "test_id",
            'vCPUs': self.vCPUs,
            'mem': self.mem_cap,
            'disk': 64,
            'extra_specs': {},
            'last_update': 0
        }

        result = self.flavor.get_json_info()
        self.assertEqual(expected, result)
