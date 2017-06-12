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

from valet.engine.resource_manager.resource import Resource
from valet.engine.resource_manager.resource_base import Host
from valet.engine.resource_manager.resource_base import HostGroup
from valet.engine.resource_manager.topology import Topology
from valet.engine.resource_manager.topology_manager import TopologyManager
from valet.tests.base import Base


class TestTopologyManger(Base):

    def setUp(self):
        super(TestTopologyManger, self).setUp()

        id = uuid.uuid4().int
        name = uuid.uuid4().hex

        self.resource = Resource(mock.Mock(), mock.Mock())
        self.data_lock = mock.Mock()
        self.config = mock.Mock()
        self.manager = TopologyManager(id, name, self.resource, self.data_lock,
                                       self.config)

    # TODO(jakecarlson1): test run and _run methods

    # @mock.patch.object(TopologyManager, '_run')
    # def test_run_trigger_freq_gt_zero(self, mock_run):
    #     self.manager.config.topology_trigger_freq = 1

    @mock.patch.object(Topology, 'set_topology')
    def test_set_topology_status_not_success(self, mock_set_topology):
        mock_set_topology.return_value = "failed"

        result = self.manager.set_topology()
        self.assertFalse(result)

    @mock.patch.object(Resource, 'update_topology')
    @mock.patch.object(TopologyManager, '_check_update')
    @mock.patch.object(Topology, 'set_topology')
    def test_set_topology_status_success_update_true(self, mock_set_topology,
                                                     mock_check_update,
                                                     mock_resource):
        mock_set_topology.return_value = "success"
        mock_check_update.return_value = True
        self.manager.config.datacenter_name = "foo"

        result = self.manager.set_topology()
        self.data_lock.acquire.assert_called_once()
        mock_check_update.asert_called_once()
        mock_resource.assert_called_once_with(store=False)
        self.data_lock.release.assert_called_once()
        self.assertTrue(result)

    @mock.patch.object(Resource, 'update_topology')
    @mock.patch.object(TopologyManager, '_check_update')
    @mock.patch.object(Topology, 'set_topology')
    def test_set_topology_status_success_update_false(self, mock_set_topology,
                                                      mock_check_update,
                                                      mock_resource):
        mock_set_topology.return_value = "success"
        mock_check_update.return_value = False

        result = self.manager.set_topology()
        self.data_lock.acquire.assert_called_once()
        mock_check_update.assert_called_once()
        mock_resource.assert_not_called()
        self.data_lock.release.assert_called_once()
        self.assertTrue(result)

    # TODO(jakecarlson1): test _check_update method

    def test_create_new_host(self):
        name = uuid.uuid4().hex
        mock_host = Host(name)

        result = self.manager._create_new_host(mock_host)
        mock_host.tag.append("infra")
        self.assertEqual(result.name, mock_host.name)
        self.assertEqual(result.tag, mock_host.tag)

    def test_create_new_host_group(self):
        id = uuid.uuid4().int
        mock_host_group = HostGroup(id)
        mock_host_group.host_type = "type"

        result = self.manager._create_new_host_group(mock_host_group)
        self.assertEqual(result.name, mock_host_group.name)
        self.assertEqual(result.host_type, mock_host_group.host_type)

    def test_check_host_update_rhost_no_infra_name_match_host(self):
        mock_host = mock.Mock()
        mock_host.name = uuid.uuid4().hex
        mock_host.host_group.name = "foo"
        mock_rhost = mock.Mock()
        mock_rhost.name = uuid.uuid4().hex
        mock_rhost.host_group.name = "foo"
        mock_rhost.tag = ["bar"]

        result = self.manager._check_host_update(mock_host, mock_rhost)
        self.assertIn("infra", mock_rhost.tag)
        self.assertTrue(result)

    def test_check_host_update_rhost_infra_name_match_host(self):
        mock_host = mock.Mock()
        mock_host.name = uuid.uuid4().hex
        mock_host.host_group.name = "foo"
        mock_rhost = mock.Mock()
        mock_rhost.name = uuid.uuid4().hex
        mock_rhost.host_group.name = "foo"
        mock_rhost.tag = ["bar", "infra"]

        result = self.manager._check_host_update(mock_host, mock_rhost)
        self.assertFalse(result)

    def test_check_host_update_rhost_no_infra_host_group_name_in_keys(self):
        mock_host = mock.Mock()
        mock_host.name = uuid.uuid4().hex
        mock_host.host_group.name = "foo"
        mock_rhost = mock.Mock()
        mock_rhost.name = uuid.uuid4().hex
        mock_rhost.host_group = None
        mock_rhost.tag = ["bar"]
        self.manager.resource.host_groups = {
            "foo": "val"
        }

        result = self.manager._check_host_update(mock_host, mock_rhost)
        self.assertIn("infra", mock_rhost.tag)
        self.assertEqual(mock_rhost.host_group, "val")
        self.assertTrue(result)

    def test_check_host_update_rhost_infra_host_group_name_in_keys(self):
        mock_host = mock.Mock()
        mock_host.name = uuid.uuid4().hex
        mock_host.host_group.name = "foo"
        mock_rhost = mock.Mock()
        mock_rhost.name = uuid.uuid4().hex
        mock_rhost.host_group = None
        mock_rhost.tag = ["bar", "infra"]
        self.manager.resource.host_groups = {
            "foo": "val"
        }

        result = self.manager._check_host_update(mock_host, mock_rhost)
        self.assertIn("infra", mock_rhost.tag)
        self.assertEqual(mock_rhost.host_group, "val")
        self.assertTrue(result)

    def test_check_host_update_rhost_no_infra_no_host_group_name_in_keys(self):
        mock_host = mock.Mock()
        mock_host.name = uuid.uuid4().hex
        mock_host.host_group.name = "foo"
        mock_rhost = mock.Mock()
        mock_rhost.name = uuid.uuid4().hex
        mock_rhost.host_group = None
        mock_rhost.tag = ["bar"]
        self.manager.resource.host_groups = {}

        result = self.manager._check_host_update(mock_host, mock_rhost)
        self.assertIn("infra", mock_rhost.tag)
        self.assertEqual(mock_rhost.host_group,
                         self.manager.resource.datacenter)
        self.assertTrue(result)

    def test_check_host_update_rhost_infra_no_host_group_name_in_keys(self):
        mock_host = mock.Mock()
        mock_host.name = uuid.uuid4().hex
        mock_host.host_group.name = "foo"
        mock_rhost = mock.Mock()
        mock_rhost.name = uuid.uuid4().hex
        mock_rhost.host_group = None
        mock_rhost.tag = ["bar", "infra"]
        self.manager.resource.host_groups = {}

        result = self.manager._check_host_update(mock_host, mock_rhost)
        self.assertIn("infra", mock_rhost.tag)
        self.assertEqual(mock_rhost.host_group,
                         self.manager.resource.datacenter)
        self.assertTrue(result)

    # TODO(jakecarlson1): test _check_host_group_update and
    #           _check_datacenter_update
