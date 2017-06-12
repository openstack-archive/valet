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


class TestDatacenter(Base):

    def setUp(self):
        super(TestDatacenter, self).setUp()

        self.datacenter = Datacenter(uuid.uuid4().hex)

        self.vCPUs = "test_vcpus"
        self.original_vCPUs = "test_original_vcpus"
        self.avail_vCPUs = "test_avail_vcpus"
        self.mem_cap = "test_mem_cap"
        self.original_mem_cap = "test_original_mem_cap"
        self.avail_mem_cap = "test_avail_mem_cap"
        self.local_disk_cap = "test_local_disk_cap"
        self.original_local_disk_cap = "test_original_local_disk_cap"
        self.avail_local_disk_cap = "test_avail_local_disk_cap"

    def test_datacenter_get_json_info_empty(self):
        self._init_instance(self.datacenter)
        expected = {
            'status': 'enabled',
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

    def test_datacenter_get_json_info_populated(self):
        self._init_instance(self.datacenter)
        self.datacenter.memberships = {
            "mem1": "is_valid",
            "mem2": "is_valid"
        }
        self.datacenter.resources = {
            "resrc1": "is_valid",
            "resrc2": "is_valid"
        }
        expected = {
            'status': 'enabled',
            'name': self.datacenter.name,
            'region_code_list': [],
            'membership_list': ['mem1', 'mem2'],
            'vCPUs': self.vCPUs,
            'original_vCPUs': self.original_vCPUs,
            'avail_vCPUs': self.avail_vCPUs,
            'mem': self.mem_cap,
            'original_mem': self.original_mem_cap,
            'avail_mem': self.avail_mem_cap,
            'local_disk': self.local_disk_cap,
            'original_local_disk': self.original_local_disk_cap,
            'avail_local_disk': self.avail_local_disk_cap,
            'children': ['resrc1', 'resrc2'],
            'vm_list': [],
            'last_update': 0
        }

        result = self.datacenter.get_json_info()
        result['membership_list'] = sorted(result['membership_list'])
        result['children'] = sorted(result['children'])
        self.assertEqual(expected, result)

    def _init_instance(self, item):
        item.vCPUs = self.vCPUs
        item.original_vCPUs = self.original_vCPUs
        item.avail_vCPUs = self.avail_vCPUs
        item.mem_cap = self.mem_cap
        item.original_mem_cap = self.original_mem_cap
        item.avail_mem_cap = self.avail_mem_cap
        item.local_disk_cap = self.local_disk_cap
        item.original_local_disk_cap = self.original_local_disk_cap
        item.avail_local_disk_cap = self.avail_local_disk_cap


class TestHostGroup(Base):

    def setUp(self):
        super(TestHostGroup, self).setUp()

        self.hostgroup = HostGroup(uuid.uuid4().int)

        self.vCPUs = "test_vcpus"
        self.original_vCPUs = "test_original_vcpus"
        self.avail_vCPUs = "test_avail_vcpus"
        self.mem_cap = "test_mem_cap"
        self.original_mem_cap = "test_original_mem_cap"
        self.avail_mem_cap = "test_avail_mem_cap"
        self.local_disk_cap = "test_local_disk_cap"
        self.original_local_disk_cap = "test_original_local_disk_cap"
        self.avail_local_disk_cap = "test_avail_local_disk_cap"

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

    def test_hostgroup_remove_membership_self_in_vms(self):
        mock_logical_group = LogicalGroup("rack:foo")
        mock_logical_group.group_type = "EX"
        mock_logical_group.vms_per_host = {
            "rack:foo": "is_valid"
        }
        self.hostgroup.memberships = {
            "rack:foo": mock_logical_group
        }

        result = self.hostgroup.remove_membership(mock_logical_group)
        self.assertEqual({}, self.hostgroup.memberships)
        self.assertTrue(result)

    def test_hostgroup_check_availability_enabled(self):
        self.hostgroup.status = "enabled"

        result = self.hostgroup.check_availability()
        self.assertTrue(result)

    def test_hostgroup_check_availability_not_enabled(self):
        self.hostgroup.status = "disabled"

        result = self.hostgroup.check_availability()
        self.assertFalse(result)

    def test_hostgroup_get_json_info_empty(self):
        self._init_instance(self.hostgroup)
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

    def test_hostgroup_get_json_info_populated(self):
        self._init_instance(self.hostgroup)
        self.hostgroup.memberships = {
            "mem1": "is_valid",
            "mem2": "is_valid"
        }
        self.hostgroup.child_resources = {
            "child1": "is_valid",
            "child2": "is_valid"
        }
        self.hostgroup.parent_resource = mock.Mock()
        self.hostgroup.parent_resource.name = "foo"
        expected = {
            'status': "enabled",
            'host_type': "rack",
            'membership_list': ['mem1', 'mem2'],
            'vCPUs': self.vCPUs,
            'original_vCPUs': self.original_vCPUs,
            'avail_vCPUs': self.avail_vCPUs,
            'mem': self.mem_cap,
            'original_mem': self.original_mem_cap,
            'avail_mem': self.avail_mem_cap,
            'local_disk': self.local_disk_cap,
            'original_local_disk': self.original_local_disk_cap,
            'avail_local_disk': self.avail_local_disk_cap,
            'parent': 'foo',
            'children': ['child1', 'child2'],
            'vm_list': [],
            'last_update': 0
        }

        result = self.hostgroup.get_json_info()
        result['membership_list'] = sorted(result['membership_list'])
        result['children'] = sorted(result['children'])
        self.assertEqual(expected, result)

    def test_hostgroup_get_json_info_has_parent(self):
        self._init_instance(self.hostgroup)
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

    def _init_instance(self, item):
        item.vCPUs = self.vCPUs
        item.original_vCPUs = self.original_vCPUs
        item.avail_vCPUs = self.avail_vCPUs
        item.mem_cap = self.mem_cap
        item.original_mem_cap = self.original_mem_cap
        item.avail_mem_cap = self.avail_mem_cap
        item.local_disk_cap = self.local_disk_cap
        item.original_local_disk_cap = self.original_local_disk_cap
        item.avail_local_disk_cap = self.avail_local_disk_cap


class TestHost(Base):

    def setUp(self):
        super(TestHost, self).setUp()

        self.host = Host(uuid.uuid4().hex)

        self.vCPUs = "test_vcpus"
        self.original_vCPUs = "test_original_vcpus"
        self.avail_vCPUs = "test_avail_vcpus"
        self.mem_cap = "test_mem_cap"
        self.original_mem_cap = "test_original_mem_cap"
        self.avail_mem_cap = "test_avail_mem_cap"
        self.local_disk_cap = "test_local_disk_cap"
        self.original_local_disk_cap = "test_original_local_disk_cap"
        self.avail_local_disk_cap = "test_avail_local_disk_cap"

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
        self.host.original_vCPUs = 40
        self.host.vCPUs_used = 20

        self.host.compute_avail_vCPUs(3, 0)
        self.assertEqual(120, self.host.vCPUs)
        self.assertEqual(100, self.host.avail_vCPUs)

    def test_host_compute_avail_mem(self):
        self.host.original_mem_cap = 40
        self.host.free_mem_mb = 20

        self.host.compute_avail_mem(3, 0)
        self.assertEqual(120, self.host.mem_cap)
        self.assertEqual(100, self.host.avail_mem_cap)

    def test_host_compute_avail_disk_least_gt_zero(self):
        self.host.original_local_disk_cap = 40
        self.host.free_disk_gb = 64
        self.host.disk_available_least = 20

        self.host.compute_avail_disk(3, 0)
        self.assertEqual(120, self.host.local_disk_cap)
        self.assertEqual(100, self.host.avail_local_disk_cap)

    def test_host_compute_avail_disk_least_eq_zero(self):
        self.host.original_local_disk_cap = 40
        self.host.free_disk_gb = 20
        self.host.disk_available_least = 0

        self.host.compute_avail_disk(3, 0)
        self.assertEqual(120, self.host.local_disk_cap)
        self.assertEqual(100, self.host.avail_local_disk_cap)

    def test_host_get_json_info_empty(self):
        self._init_instance(self.host)
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

    def test_host_get_json_info_populated(self):
        self._init_instance(self.host)
        self.host.host_group = mock.Mock()
        self.host.host_group.name = "foo"
        self.host.memberships = {
            'mem1': 'is_valid',
            'mem2': 'is_valid'
        }
        expected = {
            'tag': [],
            'status': "enabled",
            'state': "up",
            'membership_list': ['mem1', 'mem2'],
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
        result['membership_list'] = sorted(result['membership_list'])
        self.assertEqual(expected, result)

    def _init_instance(self, item):
        item.vCPUs = self.vCPUs
        item.original_vCPUs = self.original_vCPUs
        item.avail_vCPUs = self.avail_vCPUs
        item.mem_cap = self.mem_cap
        item.original_mem_cap = self.original_mem_cap
        item.avail_mem_cap = self.avail_mem_cap
        item.local_disk_cap = self.local_disk_cap
        item.original_local_disk_cap = self.original_local_disk_cap
        item.avail_local_disk_cap = self.avail_local_disk_cap


class TestLogicalGroup(Base):

    def setUp(self):
        super(TestLogicalGroup, self).setUp()

        self.logicalgroup = LogicalGroup(uuid.uuid4().hex)

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

    @mock.patch.object(LogicalGroup, '_check_group_type')
    @mock.patch.object(LogicalGroup, 'exist_vm_by_h_uuid')
    def test_add_vm_by_h_uuid_vm_exists(self, mock_exist_by_h_uuid,
                                        mock_check_group):
        mock_exist_by_h_uuid.return_value = True
        mock_vm_id = uuid.uuid4().hex
        mock_host_id = uuid.uuid4().hex

        result = self.logicalgroup.add_vm_by_h_uuid(mock_vm_id, mock_host_id)
        mock_check_group.assert_not_called()
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


class TestFlavor(Base):

    def setUp(self):
        super(TestFlavor, self).setUp()

        self.flavor = Flavor(uuid.uuid4().hex)

        self.vCPUs = "test_vcpus"
        self.mem_cap = "test_mem_cap"

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
