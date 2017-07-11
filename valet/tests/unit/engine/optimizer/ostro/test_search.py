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

from valet.engine.optimizer.app_manager.app_topology import AppTopology
from valet.engine.optimizer.ostro.search import Search
from valet.engine.resource_manager.resource import Resource
from valet.engine.resource_manager.resource_base import Datacenter
from valet.engine.resource_manager.resource_base import Host
from valet.engine.resource_manager.resource_base import HostGroup
from valet.engine.resource_manager.resource_base import LogicalGroup
from valet.tests.base import Base


class TestSearch(Base):
    """Unit tests for valet.engine.optimizer.ostro.search."""

    def setUp(self):
        """Setup Test Search Class."""
        super(TestSearch, self).setUp()

        self.resource = Resource(mock.Mock(), mock.Mock())
        self.app_topology = AppTopology(self.resource)
        self.search = Search()
        self.search.resource = self.resource
        self.search.app_topology = self.app_topology

    def test_copy_resource_status(self):
        """Test Copy Resource Status."""
        self.search.copy_resource_status(mock.MagicMock())

    @mock.patch.object(Search, '_get_vgroup_of_vm')
    def test_set_no_migrated_list_candidate_not_in_vms(self, mock_get_vgroup):
        self.search.app_topology.candidate_list_map = {
            'candidate1': 'is_valid'
        }
        self.search.app_topology.vm = {}
        self.search.app_topology.vgroups = []
        mock_get_vgroup.return_value = None

        self.search._set_no_migrated_list()
        mock_get_vgroup.assert_called_once_with('candidate1', [])

    @mock.patch.object(Search, '_get_child_vms')
    @mock.patch.object(Search, '_get_vgroup_of_vm')
    def test_set_no_migrated_list_candidate_in_vms(self, mock_get_vgroup,
                                                   mock_children):
        self.search.app_topology.candidate_list_map = {
            'candidate1': 'is_valid'
        }
        self.search.app_topology.vm = {
            'candidate1': 'is_valid'
        }
        self.search.app_topology.vgroups = []
        mock_get_vgroup.return_value = 'test_val'

        self.search._set_no_migrated_list()
        mock_get_vgroup.assert_called_once_with('candidate1', [])
        mock_children.assert_called_once_with('test_val', [], 'candidate1')

    @mock.patch.object(Host, 'check_availability')
    def test_create_avail_hosts_is_datacenter(self, mock_check_avail):
        mock_check_avail.return_value = True
        mock_host = Host(uuid.uuid4().hex)
        mock_host.host_group = Datacenter(uuid.uuid4().hex)
        mock_host.memberships = {
            'parent1': 'is_valid'
        }
        mock_host.vm_list = ['testvm1']
        self.search.avail_logical_groups = {
            'parent1': 'is_valid'
        }
        self.search.resource.hosts = {
            'host1': mock_host
        }
        self.search.num_of_hosts = 1

        self.search._create_avail_hosts()
        result_resource = self.search.avail_hosts['host1']
        self.assertEqual(2, self.search.num_of_hosts)
        self.assertEqual("any", result_resource.rack_name)
        self.assertEqual("any", result_resource.cluster_name)
        self.assertEqual(1, result_resource.host_num_of_placed_vms)
        self.assertIn("parent1", result_resource.host_memberships)

    @mock.patch.object(Host, 'check_availability')
    def test_create_avail_hosts_cluster_is_datacenter(self, mock_check_avail):
        mock_check_avail.return_value = True
        mock_host = Host(uuid.uuid4().hex)
        mock_host.host_group = HostGroup(uuid.uuid4().hex)
        mock_host.memberships = {
            'parent1': 'is_valid'
        }
        mock_host.vm_list = ['testvm1']
        mock_host.host_group.memberships = {
            'parent2': 'is_valid'
        }
        mock_host.host_group.vm_list = ['testvm2']
        mock_host.host_group.parent_resource = Datacenter(uuid.uuid4().hex)
        self.search.avail_logical_groups = {
            'parent1': 'is_valid',
            'parent2': 'is_valid'
        }
        self.search.resource.hosts = {
            'host1': mock_host
        }
        self.search.num_of_hosts = 1

        self.search._create_avail_hosts()
        result_resource = self.search.avail_hosts['host1']
        self.assertEqual(2, self.search.num_of_hosts)
        self.assertEqual(mock_host.host_group.name, result_resource.rack_name)
        self.assertEqual("any", result_resource.cluster_name)
        self.assertEqual(1, result_resource.host_num_of_placed_vms)
        self.assertEqual(1, result_resource.rack_num_of_placed_vms)
        self.assertIn("parent1", result_resource.host_memberships)
        self.assertIn("parent2", result_resource.rack_memberships)

    @mock.patch.object(Host, 'check_availability')
    def test_create_avail_hosts_cluster_is_not_datacenter(self,
                                                          mock_check_avail):
        mock_check_avail.return_value = True
        mock_host = Host(uuid.uuid4().hex)
        mock_host.host_group = HostGroup(uuid.uuid4().hex)
        mock_host.memberships = {
            'parent1': 'is_valid'
        }
        mock_host.vm_list = ['testvm1']
        mock_host.host_group.memberships = {
            'parent2': 'is_valid'
        }
        mock_host.host_group.vm_list = ['testvm2']
        mock_host.host_group.parent_resource = HostGroup(uuid.uuid4().hex)
        mock_host.host_group.parent_resource.memberships = {
            'parent3': 'is_valid'
        }
        mock_host.host_group.parent_resource.vm_list = ['testvm3']
        self.search.avail_logical_groups = {
            'parent1': 'is_valid',
            'parent2': 'is_valid',
            'parent3': 'is_valid'
        }
        self.search.resource.hosts = {
            'host1': mock_host
        }
        self.search.num_of_hosts = 1

        self.search._create_avail_hosts()
        result_resource = self.search.avail_hosts['host1']
        self.assertEqual(2, self.search.num_of_hosts)
        self.assertEqual(mock_host.host_group.name, result_resource.rack_name)
        self.assertEqual(mock_host.host_group.parent_resource.name,
                         result_resource.cluster_name)
        self.assertEqual(1, result_resource.host_num_of_placed_vms)
        self.assertEqual(1, result_resource.rack_num_of_placed_vms)
        self.assertEqual(1, result_resource.cluster_num_of_placed_vms)
        self.assertIn("parent1", result_resource.host_memberships)
        self.assertIn("parent2", result_resource.rack_memberships)
        self.assertIn("parent3", result_resource.cluster_memberships)

    @mock.patch.object(LogicalGroup, 'exist_vm_by_uuid')
    @mock.patch.object(HostGroup, 'check_availability')
    @mock.patch.object(Host, 'check_availability')
    def test_create_avail_logical_groups_in_hosts_and_lg(self, mock_host_check,
                                                         mock_group_check,
                                                         mock_lg):
        mock_host_check.return_value = False
        mock_group_check.return_value = True
        mock_lg.return_value = True
        mock_uuid = uuid.uuid4().hex
        mock_h_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        mock_logical_group = LogicalGroup(uuid.uuid4().hex)
        mock_logical_group.group_type = 'test_type'
        mock_logical_group.metadata = {
            'key1': 'val1',
            'key2': 'val2'
        }
        mock_logical_group.vm_list = [mock_vm_id]
        mock_logical_group.vms_per_host = {
            'host1': [mock_vm_id]
        }
        mock_host = Host(uuid.uuid4().hex)
        mock_host.vm_list = [mock_vm_id]
        self.search.resource.logical_groups = {
            'lg1': mock_logical_group
        }
        self.search.resource.hosts = {
            'host1': mock_host
        }

        self.search._create_avail_logical_groups()
        result_lg = self.search.avail_logical_groups['lg1']
        mock_host_check.assert_called_once_with()
        mock_lg.assert_called_once_with(mock_uuid)
        self.assertEqual('lg1', result_lg.name)
        self.assertEqual(0, result_lg.num_of_placed_vms)
        self.assertEqual('test_type', result_lg.group_type)
        self.assertNotIn('lg1', result_lg.num_of_placed_vms_per_host)

    @mock.patch.object(LogicalGroup, 'exist_vm_by_uuid')
    @mock.patch.object(HostGroup, 'check_availability')
    @mock.patch.object(Host, 'check_availability')
    def test_create_avail_logical_groups_in_hostgroup_and_lg(self,
                                                             mock_host_check,
                                                             mock_group_check,
                                                             mock_lg):
        mock_host_check.return_value = True
        mock_group_check.return_value = False
        mock_lg.return_value = True
        mock_uuid = uuid.uuid4().hex
        mock_h_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        mock_logical_group = LogicalGroup(uuid.uuid4().hex)
        mock_logical_group.group_type = 'test_type'
        mock_logical_group.metadata = {
            'key1': 'val1',
            'key2': 'val2'
        }
        mock_logical_group.vm_list = [mock_vm_id]
        mock_logical_group.vms_per_host = {
            'hostgroup1': [mock_vm_id]
        }
        mock_host_group = HostGroup(uuid.uuid4().hex)
        mock_host_group.vm_list = [mock_vm_id]
        self.search.resource.logical_groups = {
            'lg1': mock_logical_group
        }
        self.search.resource.host_groups = {
            'hostgroup1': mock_host_group
        }

        self.search._create_avail_logical_groups()
        result_lg = self.search.avail_logical_groups['lg1']
        mock_group_check.assert_called_once_with()
        mock_lg.assert_called_once_with(mock_uuid)
        self.assertEqual('lg1', result_lg.name)
        self.assertEqual(0, result_lg.num_of_placed_vms)
        self.assertEqual('test_type', result_lg.group_type)
        self.assertNotIn('lg1', result_lg.num_of_placed_vms_per_host)

    # TODO(jakecarlson1): test _adjust_resources

    def test_compute_resource_weights(self):
        self.search.app_topology.optimization_priority = [
            ("cpu", 0.2),
            ("mem", 0.3),
            ("lvol", 0.5)
        ]

        self.search._compute_resource_weights()
        self.assertEqual(0.2, self.search.CPU_weight)
        self.assertEqual(0.3, self.search.mem_weight)
        self.assertEqual(0.5, self.search.local_disk_weight)

    def test_set_compute_sort_base_cluster(self):
        self.search.CPU_weight = 0
        self.search.mem_weight = 0
        self.search.local_disk_weight = 0
        self.search.resource.CPU_avail = 1
        self.search.resource.mem_avail = 1
        self.search.resource.local_disk_avail = 1
        mock_candidate = mock.Mock()
        mock_candidate.cluster_avail_vCPUs = 2
        mock_candidate.cluster_avail_mem = 3
        mock_candidate.cluster_avail_local_disk = 5

        self.search._set_compute_sort_base("cluster", [mock_candidate])
        self.assertEqual(10, mock_candidate.sort_base)

    def test_set_compute_sort_base_rack(self):
        self.search.CPU_weight = 0
        self.search.mem_weight = 0
        self.search.local_disk_weight = 0
        self.search.resource.CPU_avail = 1
        self.search.resource.mem_avail = 1
        self.search.resource.local_disk_avail = 1
        mock_candidate = mock.Mock()
        mock_candidate.rack_avail_vCPUs = 2
        mock_candidate.rack_avail_mem = 3
        mock_candidate.rack_avail_local_disk = 5

        self.search._set_compute_sort_base("rack", [mock_candidate])
        self.assertEqual(10, mock_candidate.sort_base)

    def test_set_compute_sort_base_host(self):
        self.search.CPU_weight = 0
        self.search.mem_weight = 0
        self.search.local_disk_weight = 0
        self.search.resource.CPU_avail = 1
        self.search.resource.mem_avail = 1
        self.search.resource.local_disk_avail = 1
        mock_candidate = mock.Mock()
        mock_candidate.host_avail_vCPUs = 2
        mock_candidate.host_avail_mem = 3
        mock_candidate.host_avail_local_disk = 5

        self.search._set_compute_sort_base("host", [mock_candidate])
        self.assertEqual(10, mock_candidate.sort_base)

    # @mock.patch.object(Host, 'get_resource_name')
    # def test_add_exclusivity_host(self, mock_get_res):
    #     mock_get_res.return_value = "host1"
    #     mock_exclusivity_id = "host:" + uuid.uuid4().hex
    #     mock_logical_group = LogicalGroupResource()
    #     mock_logical_group.num_of_placed_vms_per_host = {
    #         'host1': 0
    #     }
    #     self.search.avail_logical_groups = {
    #         mock_exclusivity_id: mock_logical_group
    #     }
    #     mock_host = Host(uuid.uuid4().hex)
    #     mock_host.host_name = "host1"
    #     mock_host.rack_name = "testrack1"
    #     mock_host.host_memberships = {

    #     }
    #     self.search.avail_hosts = {
    #         'host1': mock_host
    #     }

    # TODO(jakecarlson1): test _add_affinity and _add_diversities ...
