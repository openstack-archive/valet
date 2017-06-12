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
import time
import uuid

from valet.engine.optimizer.db_connect.music_handler import MusicHandler
from valet.engine.resource_manager.resource import Resource
from valet.engine.resource_manager.resource_base import Host
from valet.engine.resource_manager.resource_base import HostGroup
from valet.engine.resource_manager.resource_base import LogicalGroup
from valet.tests.base import Base


class TestResource(Base):

    def setUp(self):
        super(TestResource, self).setUp()

        self.config = mock.Mock()
        self.db = MusicHandler(self.config)
        self.resource = Resource(self.db, self.config)

    # TODO(jakecarlson1): test bootstrap_from_db

    @mock.patch.object(Resource, 'store_topology_updates')
    @mock.patch.object(Resource, '_update_compute_avail')
    @mock.patch.object(Resource, '_update_topology')
    def test_update_topology_false(self, mock_update_topology,
                                   mock_update_compute, mock_store_update):
        result = self.resource.update_topology(False)
        mock_update_topology.assert_called_once_with()
        mock_update_compute.assert_called_once_with()
        mock_store_update.assert_not_called()
        self.assertTrue(result)

    @mock.patch.object(Resource, 'store_topology_updates')
    @mock.patch.object(Resource, '_update_compute_avail')
    @mock.patch.object(Resource, '_update_topology')
    def test_update_topology_true(self, mock_update_topology,
                                  mock_update_compute, mock_store_update):
        mock_store_update.return_value = "test_val"

        result = self.resource.update_topology(True)
        mock_update_topology.assert_called_once_with()
        mock_update_compute.assert_called_once_with()
        mock_store_update.assert_called_once_with()
        self.assertEqual("test_val", result)

    # TODO(jakecarlson1): test _update_topology, _update_host_group_topology,
    #           _update_datacenter_topology, store_topology_updates,

    @mock.patch.object(Resource, 'update_cluster_resource')
    @mock.patch.object(time, 'time')
    def test_update_rack_resource_rack_not_none_is_instance(self, mock_time,
                                                            mock_update):
        mock_host = mock.Mock()
        mock_host.host_group = HostGroup(uuid.uuid4().int)
        mock_time.return_value = 60

        self.resource.update_rack_resource(mock_host)
        mock_update.assert_called_once_with(mock_host.host_group)
        self.assertEqual(60, mock_host.host_group.last_update)

    @mock.patch.object(time, 'time')
    def test_update_cluster_resource_rack_not_none_is_instance(self,
                                                               mock_time):
        mock_host = mock.Mock()
        mock_host.parent_resource = HostGroup(uuid.uuid4().int)
        mock_time.return_value = 60

        self.resource.update_cluster_resource(mock_host)
        self.assertEqual(60, self.resource.datacenter.last_update)

    def test_add_vm_to_host(self):
        host_name = uuid.uuid4().hex
        vm_id = (0, uuid.uuid4().int, 0)
        mock_host = Host(host_name)
        self.resource.hosts = {
            host_name: mock_host
        }
        vcpus = 2
        mem = 4
        ldisk = 8

        self.resource.add_vm_to_host(host_name, vm_id, vcpus, mem, ldisk)
        self.assertIn(vm_id, mock_host.vm_list)
        self.assertEqual(mock_host.avail_vCPUs, -2)
        self.assertEqual(mock_host.avail_mem_cap, -4)
        self.assertEqual(mock_host.avail_local_disk_cap, -8)
        self.assertEqual(mock_host.vCPUs_used, 2)
        self.assertEqual(mock_host.free_mem_mb, -4)
        self.assertEqual(mock_host.free_disk_gb, -8)
        self.assertEqual(mock_host.disk_available_least, -8)

    def test_remove_vm_by_h_uuid_from_host(self):
        host_name = uuid.uuid4().hex
        vm_id = (uuid.uuid4().int, uuid.uuid4().int, 0)
        mock_host = Host(host_name)
        self.resource.hosts = {
            host_name: mock_host
        }
        mock_host.vm_list.append(vm_id)
        vcpus = 2
        mem = 4
        ldisk = 8

        self.resource.remove_vm_by_h_uuid_from_host(host_name, vm_id[0], vcpus,
                                                    mem, ldisk)
        self.assertNotIn(vm_id, mock_host.vm_list)
        self.assertEqual(mock_host.avail_vCPUs, 2)
        self.assertEqual(mock_host.avail_mem_cap, 4)
        self.assertEqual(mock_host.avail_local_disk_cap, 8)
        self.assertEqual(mock_host.vCPUs_used, -2)
        self.assertEqual(mock_host.free_mem_mb, 4)
        self.assertEqual(mock_host.free_disk_gb, 8)
        self.assertEqual(mock_host.disk_available_least, 8)

    def test_remove_vm_by_uuid_from_host(self):
        host_name = uuid.uuid4().hex
        vm_id = (0, uuid.uuid4().int, uuid.uuid4().int)
        mock_host = Host(host_name)
        self.resource.hosts = {
            host_name: mock_host
        }
        mock_host.vm_list.append(vm_id)
        vcpus = 2
        mem = 4
        ldisk = 8

        self.resource.remove_vm_by_uuid_from_host(host_name, vm_id[2], vcpus,
                                                  mem, ldisk)
        self.assertNotIn(vm_id, mock_host.vm_list)
        self.assertEqual(mock_host.avail_vCPUs, 2)
        self.assertEqual(mock_host.avail_mem_cap, 4)
        self.assertEqual(mock_host.avail_local_disk_cap, 8)
        self.assertEqual(mock_host.vCPUs_used, -2)
        self.assertEqual(mock_host.free_mem_mb, 4)
        self.assertEqual(mock_host.free_disk_gb, 8)
        self.assertEqual(mock_host.disk_available_least, 8)

    @mock.patch.object(Resource, 'compute_avail_resources')
    def test_update_host_resources_same_status(self, mock_resource):
        host_name = uuid.uuid4().hex
        mock_host = Host(host_name)
        self.resource.hosts = {
            host_name: mock_host
        }
        mock_host.status = "enabled"

        result = self.resource.update_host_resources(host_name, "enabled", 0,
                                                     0, 0, 0, 0, 0, 0)
        mock_resource.assert_not_called()
        self.assertFalse(result)

    @mock.patch.object(Resource, 'compute_avail_resources')
    def test_update_host_resources_diff_status(self, mock_resource):
        host_name = uuid.uuid4().hex
        mock_host = Host(host_name)
        self.resource.hosts = {
            host_name: mock_host
        }
        mock_host.status = "enabled"

        result = self.resource.update_host_resources(host_name, "disabled", 0,
                                                     0, 0, 0, 0, 0, 0)
        mock_resource.assert_called_once_with(host_name, mock_host)
        self.assertTrue(result)

    @mock.patch.object(Resource, 'update_rack_resource')
    @mock.patch.object(time, 'time')
    def test_update_host_time(self, mock_time, mock_resource):
        host_name = uuid.uuid4().hex
        mock_host = Host(host_name)
        self.resource.hosts = {
            host_name: mock_host
        }
        mock_time.return_value = 60

        self.resource.update_host_time(host_name)
        self.assertEqual(mock_host.last_update, 60)
        mock_resource.assert_called_once_with(mock_host)

    @mock.patch.object(Resource, 'update_cluster_resource')
    def test_add_logical_group_hn_in_hosts_no_lg(self, mock_resource):
        host_name = uuid.uuid4().hex
        mock_host = Host(host_name)
        self.resource.hosts = {
            host_name: mock_host
        }
        lg_name = "foo"
        lg_type = "bar"

        self.resource.add_logical_group(host_name, lg_name, lg_type)
        self.assertEqual(self.resource.logical_groups[lg_name].
                         group_type, lg_type)
        self.assertEqual(self.resource.logical_groups[lg_name],
                         mock_host.memberships[lg_name])
        mock_resource.assert_not_called()

    @mock.patch.object(Resource, 'update_cluster_resource')
    def test_add_logical_group_hn_not_in_hosts_no_lg(self, mock_resource):
        host_name = uuid.uuid4().hex
        mock_host_group = HostGroup(host_name)
        self.resource.host_groups = {
            host_name: mock_host_group
        }
        lg_name = "foo"
        lg_type = "bar"

        self.resource.add_logical_group(host_name, lg_name, lg_type)
        self.assertEqual(self.resource.logical_groups[lg_name].
                         group_type, lg_type)
        self.assertEqual(self.resource.logical_groups[lg_name],
                         mock_host_group.memberships[lg_name])
        mock_resource.assert_called_once_with(mock_host_group)

    @mock.patch.object(time, 'time')
    @mock.patch.object(LogicalGroup, 'add_vm_by_h_uuid')
    def test_add_vm_to_logical_groups_is_host(self, mock_lg, mock_time):
        mock_host = Host(uuid.uuid4().hex)
        mock_host.host_group = HostGroup(uuid.uuid4().hex)
        mock_host.host_group.parent_resource = None
        mock_logical_group = LogicalGroup(uuid.uuid4().hex)
        mock_lg.return_value = True
        mock_host.memberships = {
            "lg": mock_logical_group
        }
        self.resource.logical_groups = {
            "lg": mock_logical_group
        }
        logical_groups = ["lg"]
        mock_time.return_value = 60

        self.resource.add_vm_to_logical_groups(mock_host, "foo",
                                               logical_groups)
        mock_lg.assert_called_once_with("foo", mock_host.name)
        self.assertEqual(mock_logical_group.last_update, 60)

    @mock.patch.object(time, 'time')
    @mock.patch.object(LogicalGroup, 'add_vm_by_h_uuid')
    @mock.patch.object(Resource, '_check_group_type')
    def test_add_vm_to_logical_groups_is_host_group(self, mock_check_group,
                                                    mock_lg, mock_time):
        mock_host_group = HostGroup(uuid.uuid4().hex)
        mock_host_group.host_type = "lg"
        mock_host_group.parent_resource = None
        mock_logical_group = LogicalGroup(uuid.uuid4().hex)
        mock_logical_group.group_type = "bar"
        mock_lg.return_value = True
        mock_host_group.memberships = {
            "lg": mock_logical_group
        }
        self.resource.logical_groups = {
            "lg": mock_logical_group
        }
        logical_groups = ["lg"]
        mock_time.return_value = 60

        self.resource.add_vm_to_logical_groups(mock_host_group, "foo",
                                               logical_groups)
        mock_check_group.assert_called_once_with(mock_logical_group.group_type)
        mock_lg.assert_called_once_with("foo", mock_host_group.name)
        self.assertEqual(mock_logical_group.last_update, 60)

    # TODO(jakecarlson1): test remove_vm_by_uuid_from_logical_groups,
    #           remove_vm_by_uuid_from_logical_groups,
    #           clean_none_vms_from_logical_groups

    @mock.patch.object(time, 'time')
    @mock.patch.object(LogicalGroup, 'update_uuid')
    def test_update_uuid_in_logical_groups_is_host(self, mock_lg, mock_time):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_host = Host(uuid.uuid4().hex)
        mock_host.host_group = HostGroup(uuid.uuid4().hex)
        mock_logical_group = LogicalGroup(uuid.uuid4().hex)
        mock_lg.return_value = True
        mock_host.memberships = {
            "lg": mock_logical_group
        }
        self.resource.logical_groups = {
            "lg": mock_logical_group
        }
        mock_time.return_value = 60

        self.resource.update_uuid_in_logical_groups(mock_h_uuid, mock_uuid,
                                                    mock_host)
        mock_lg.assert_called_once_with(mock_h_uuid, mock_uuid, mock_host.name)
        self.assertEqual(mock_logical_group.last_update, 60)

    @mock.patch.object(time, 'time')
    @mock.patch.object(LogicalGroup, 'update_uuid')
    @mock.patch.object(Resource, '_check_group_type')
    def test_update_uuid_in_logical_groups_is_host_group(self,
                                                         mock_check_group,
                                                         mock_lg, mock_time):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_host_group = HostGroup(uuid.uuid4().hex)
        mock_host_group.host_type = "lg"
        mock_host_group.parent_resource = None
        mock_logical_group = LogicalGroup(uuid.uuid4().hex)
        mock_logical_group.group_type = "bar"
        mock_lg.return_value = True
        mock_host_group.memberships = {
            "lg": mock_logical_group
        }
        self.resource.logical_groups = {
            "lg": mock_logical_group
        }
        mock_time.return_value = 60

        self.resource.update_uuid_in_logical_groups(mock_h_uuid, mock_uuid,
                                                    mock_host_group)
        mock_check_group.assert_called_once_with(mock_logical_group.group_type)
        mock_lg.assert_called_once_with(mock_h_uuid, mock_uuid,
                                        mock_host_group.name)
        self.assertEqual(mock_logical_group.last_update, 60)

    @mock.patch.object(time, 'time')
    @mock.patch.object(LogicalGroup, 'update_h_uuid')
    def test_update_h_uuid_in_logical_groups_is_host(self, mock_lg, mock_time):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_host = Host(uuid.uuid4().hex)
        mock_host.host_group = HostGroup(uuid.uuid4().hex)
        mock_logical_group = LogicalGroup(uuid.uuid4().hex)
        mock_lg.return_value = True
        mock_host.memberships = {
            "lg": mock_logical_group
        }
        self.resource.logical_groups = {
            "lg": mock_logical_group
        }
        mock_time.return_value = 60

        self.resource.update_h_uuid_in_logical_groups(mock_h_uuid, mock_uuid,
                                                      mock_host)
        mock_lg.assert_called_once_with(mock_h_uuid, mock_uuid, mock_host.name)
        self.assertEqual(mock_logical_group.last_update, 60)

    @mock.patch.object(time, 'time')
    @mock.patch.object(LogicalGroup, 'update_h_uuid')
    @mock.patch.object(Resource, '_check_group_type')
    def test_update_h_uuid_in_logical_groups_is_host_group(self,
                                                           mock_check_group,
                                                           mock_lg, mock_time):
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_host_group = HostGroup(uuid.uuid4().hex)
        mock_host_group.host_type = "lg"
        mock_host_group.parent_resource = None
        mock_logical_group = LogicalGroup(uuid.uuid4().hex)
        mock_logical_group.group_type = "bar"
        mock_lg.return_value = True
        mock_host_group.memberships = {
            "lg": mock_logical_group
        }
        self.resource.logical_groups = {
            "lg": mock_logical_group
        }
        mock_time.return_value = 60

        self.resource.update_h_uuid_in_logical_groups(mock_h_uuid, mock_uuid,
                                                      mock_host_group)
        mock_check_group.assert_called_once_with(mock_logical_group.group_type)
        mock_lg.assert_called_once_with(mock_h_uuid, mock_uuid,
                                        mock_host_group.name)
        self.assertEqual(mock_logical_group.last_update, 60)

    # TODO(jakecarlson1): compute_avail_resources, get_flavor
