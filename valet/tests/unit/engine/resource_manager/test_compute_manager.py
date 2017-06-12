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

from valet.engine.resource_manager.compute import Compute
from valet.engine.resource_manager.compute_manager import ComputeManager
from valet.engine.resource_manager.resource import Resource
from valet.tests.base import Base


class TestComputeManager(Base):

    def setUp(self):
        super(TestComputeManager, self).setUp()

        self.resource = Resource(mock.Mock(), mock.Mock())
        self.thread_id = uuid.uuid4().int
        self.thread_name = uuid.uuid4().hex
        self.data_lock = mock.Mock()
        self.config = mock.Mock()
        self.compute_manager = ComputeManager(self.thread_id, self.thread_name,
                                              self.resource, self.data_lock,
                                              self.config)

    # TODO(jakecarlson1): test run and _run

    @mock.patch.object(Resource, 'update_topology')
    @mock.patch.object(ComputeManager, '_check_host_update')
    @mock.patch.object(ComputeManager, '_check_logical_group_update')
    @mock.patch.object(ComputeManager, '_compute_avail_host_resources')
    @mock.patch.object(Compute, 'set_hosts')
    def test_set_hosts_failed(self, mock_set_hosts, mock_compute_host,
                              mock_check_lg, mock_check_host, mock_update_top):
        mock_set_hosts.return_value = "failed"

        result = self.compute_manager.set_hosts()
        mock_set_hosts.assert_called_once_with({}, {})
        mock_compute_host.assert_not_called()
        mock_check_lg.assert_not_called()
        mock_check_host.assert_not_called()
        self.assertFalse(result)

    @mock.patch.object(Resource, 'update_topology')
    @mock.patch.object(ComputeManager, '_check_host_update')
    @mock.patch.object(ComputeManager, '_check_logical_group_update')
    @mock.patch.object(ComputeManager, '_compute_avail_host_resources')
    @mock.patch.object(Compute, 'set_hosts')
    def test_set_hosts_updated(self, mock_set_hosts, mock_compute_host,
                               mock_check_lg, mock_check_host,
                               mock_update_top):
        mock_set_hosts.return_value = "success"
        mock_check_lg.return_value = True
        mock_check_host.return_value = True

        result = self.compute_manager.set_hosts()
        mock_set_hosts.assert_called_once_with({}, {})
        mock_compute_host.assert_called_once_with({})
        mock_check_lg.assert_called_once_with({})
        mock_check_host.assert_called_once_with({})
        mock_update_top.assert_called_once_with(store=False)
        self.assertTrue(result)

    @mock.patch.object(Resource, 'compute_avail_resources')
    def test_compute_avail_host_resources_empty(self, mock_compute_resource):
        mock_hosts = {}

        self.compute_manager._compute_avail_host_resources(mock_hosts)
        mock_compute_resource.assert_not_called()

    @mock.patch.object(Resource, 'compute_avail_resources')
    def test_compute_avail_host_resources_populated(self,
                                                    mock_compute_resource):
        mock_hosts = {
            'host1': 'valid1',
            'host2': 'valid2'
        }

        self.compute_manager._compute_avail_host_resources(mock_hosts)
        calls = [mock.call('host1', 'valid1'), mock.call('host2', 'valid2')]
        mock_compute_resource.assert_has_calls(calls, any_order=True)

    # TODO(jakecarlson1): test _check_logical_group_update,
    #           _check_logical_group_metadata_update, _check_host_update

    @mock.patch.object(ComputeManager, '_check_host_vms')
    @mock.patch.object(ComputeManager, '_check_host_memberships')
    @mock.patch.object(ComputeManager, '_check_host_resources')
    @mock.patch.object(ComputeManager, '_check_host_status')
    def test_check_host_config_update_false(self, mock_check_status,
                                            mock_check_resources,
                                            mock_check_memberships,
                                            mock_check_vms):
        mock_check_status.return_value = False
        mock_check_resources.return_value = False
        mock_check_memberships.return_value = False
        mock_check_vms.return_value = False

        result = self.compute_manager._check_host_config_update({}, {})
        mock_check_status.assert_called_once_with({}, {})
        mock_check_resources.assert_called_once_with({}, {})
        mock_check_memberships.assert_called_once_with({}, {})
        mock_check_vms.assert_called_once_with({}, {})
        self.assertFalse(result)

    @mock.patch.object(ComputeManager, '_check_host_vms')
    @mock.patch.object(ComputeManager, '_check_host_memberships')
    @mock.patch.object(ComputeManager, '_check_host_resources')
    @mock.patch.object(ComputeManager, '_check_host_status')
    def test_check_host_config_update_true(self, mock_check_status,
                                           mock_check_resources,
                                           mock_check_memberships,
                                           mock_check_vms):
        mock_check_status.return_value = True
        mock_check_resources.return_value = True
        mock_check_memberships.return_value = False
        mock_check_vms.return_value = False

        result = self.compute_manager._check_host_config_update({}, {})
        mock_check_status.assert_called_once_with({}, {})
        mock_check_resources.assert_called_once_with({}, {})
        mock_check_memberships.assert_called_once_with({}, {})
        mock_check_vms.assert_called_once_with({}, {})
        self.assertTrue(result)

    def test_check_host_status_updated(self):
        mock_host = mock.Mock()
        mock_host.name = uuid.uuid4().hex
        mock_host.status = "status1"
        mock_host.state = "state1"
        mock_rhost = mock.Mock()
        mock_rhost.name = uuid.uuid4().hex
        mock_rhost.tag = []
        mock_rhost.status = "status2"
        mock_rhost.state = "state2"

        result = self.compute_manager._check_host_status(mock_host, mock_rhost)
        self.assertIn("nova", mock_rhost.tag)
        self.assertEqual("status1", mock_rhost.status)
        self.assertEqual("state1", mock_rhost.state)
        self.assertTrue(result)

    def test_check_host_status_clean(self):
        mock_host = mock.Mock()
        mock_host.name = uuid.uuid4().hex
        mock_host.status = "status1"
        mock_host.state = "state1"
        mock_rhost = mock.Mock()
        mock_rhost.name = uuid.uuid4().hex
        mock_rhost.tag = ["nova"]
        mock_rhost.status = "status1"
        mock_rhost.state = "state1"

        result = self.compute_manager._check_host_status(mock_host, mock_rhost)
        self.assertFalse(result)

    def test_check_host_resources_updated(self):
        mock_host = mock.Mock()
        mock_host.name = uuid.uuid4().hex
        self._init_host(mock_host)
        mock_host.vCPUs = 1
        mock_host.mem_cap = 2
        mock_host.local_disk_cap = 3
        mock_rhost = mock.Mock()
        mock_rhost.name = uuid.uuid4().hex
        self._init_host(mock_rhost)

        result = self.compute_manager._check_host_resources(mock_host,
                                                            mock_rhost)
        self.assertEqual(mock_host.vCPUs, mock_rhost.vCPUs)
        self.assertEqual(mock_host.mem_cap, mock_rhost.mem_cap)
        self.assertEqual(mock_host.local_disk_cap, mock_rhost.local_disk_cap)
        self.assertTrue(result)

    def test_check_host_resources_clean(self):
        mock_host = mock.Mock()
        mock_host.name = uuid.uuid4().hex
        self._init_host(mock_host)
        mock_rhost = mock.Mock()
        mock_rhost.name = uuid.uuid4().hex
        self._init_host(mock_rhost)

        result = self.compute_manager._check_host_resources(mock_host,
                                                            mock_rhost)
        self.assertEqual(mock_host.vCPUs, mock_rhost.vCPUs)
        self.assertEqual(mock_host.mem_cap, mock_rhost.mem_cap)
        self.assertEqual(mock_host.local_disk_cap, mock_rhost.local_disk_cap)
        self.assertFalse(result)

    def _init_host(self, _host):
        _host.vCPUs = 0
        _host.original_vCPUs = 0
        _host.avail_vCPUs = 0
        _host.mem_cap = 0                 # MB
        _host.original_mem_cap = 0
        _host.avail_mem_cap = 0
        _host.local_disk_cap = 0          # GB, ephemeral
        _host.original_local_disk_cap = 0
        _host.avail_local_disk_cap = 0
        _host.vCPUs_used = 0
        _host.free_mem_mb = 0
        _host.free_disk_gb = 0
        _host.disk_available_least = 0
