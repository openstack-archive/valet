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
from valet.engine.optimizer.ostro.ostro import Ostro
# from valet.engine.optimizer.ostro_server.configuration import Config
from valet.engine.resource_manager.compute_manager import ComputeManager
from valet.engine.resource_manager.resource import Resource
from valet.engine.resource_manager.resource_base import LogicalGroup
from valet.engine.resource_manager.topology_manager import TopologyManager
from valet.tests.base import Base


class TestOstro(Base):
    """Unit tests for valet.engine.optimizer.ostro.ostro."""

    def setUp(self):
        """Setup Test Ostro Class."""
        super(TestOstro, self).setUp()

        # self.config = Config("/valet/tests/unit/engine/"+
        #                      "optimizer/ostro/empty.cfg")
        self.ostro = Ostro(mock.Mock())

    @mock.patch.object(time, 'sleep')
    def test_stop_ostro_t_dead(self, mock_time):
        mock_thread = mock.Mock()
        mock_thread.is_alive.return_value = False
        self.ostro.thread_list.append(mock_thread)

        self.ostro.stop_ostro()
        self.assertNotIn(mock_thread, self.ostro.thread_list)
        mock_time.assert_called_once_with(1)

    @mock.patch.object(Resource, 'update_topology')
    @mock.patch.object(Ostro, '_set_topology')
    @mock.patch.object(Ostro, '_set_hosts')
    @mock.patch.object(Ostro, '_set_flavors')
    @mock.patch.object(MusicHandler, 'get_resource_status')
    def test_bootstrap_db_fail(self, mock_db, mock_hosts, mock_flavors,
                               mock_topology, mock_update):
        mock_db.return_value = None
        self.ostro.resource.datacenter.name = 'test_name'

        result = self.ostro.bootstrap()
        self.assertFalse(result)
        mock_db.assert_called_once_with('test_name')
        mock_hosts.assert_not_called()
        mock_flavors.assert_not_called()
        mock_topology.assert_not_called()
        mock_update.assert_not_called()

    @mock.patch.object(Resource, 'update_topology')
    @mock.patch.object(Ostro, '_set_topology')
    @mock.patch.object(Ostro, '_set_flavors')
    @mock.patch.object(Ostro, '_set_hosts')
    @mock.patch.object(Resource, 'bootstrap_from_db')
    @mock.patch.object(MusicHandler, 'get_resource_status')
    def test_bootstrap_one_resource(self, mock_db, mock_bootstrap, mock_hosts,
                                    mock_flavors, mock_topology, mock_update):
        mock_db.return_value = ['test_status']
        mock_bootstrap.return_value = True
        mock_hosts.return_value = True
        mock_flavors.return_value = True
        mock_topology.return_value = True
        self.ostro.resource.datacenter.name = 'test_name'

        result = self.ostro.bootstrap()
        self.assertTrue(result)
        mock_db.assert_called_once_with('test_name')
        mock_bootstrap.assert_called_once_with(['test_status'])
        mock_hosts.assert_called_once_with()
        mock_flavors.assert_called_once_with()
        mock_topology.assert_called_once_with()
        mock_update.assert_called_once_with()

    @mock.patch.object(Resource, 'update_topology')
    @mock.patch.object(Ostro, '_set_topology')
    @mock.patch.object(Ostro, '_set_flavors')
    @mock.patch.object(Ostro, '_set_hosts')
    @mock.patch.object(MusicHandler, 'get_resource_status')
    def test_bootstrap_hosts_fail(self, mock_db, mock_hosts, mock_flavors,
                                  mock_topology, mock_update):
        mock_db.return_value = []
        mock_hosts.return_value = False
        mock_flavors.return_value = True
        mock_topology.return_value = True
        self.ostro.resource.datacenter.name = 'test_name'

        result = self.ostro.bootstrap()
        self.assertFalse(result)
        mock_db.assert_called_once_with('test_name')
        mock_hosts.assert_called_once_with()
        mock_flavors.assert_not_called()
        mock_topology.assert_not_called()
        mock_update.assert_not_called()

    @mock.patch.object(Resource, 'update_topology')
    @mock.patch.object(Ostro, '_set_topology')
    @mock.patch.object(Ostro, '_set_flavors')
    @mock.patch.object(Ostro, '_set_hosts')
    @mock.patch.object(MusicHandler, 'get_resource_status')
    def test_bootstrap_flavors_fail(self, mock_db, mock_hosts, mock_flavors,
                                    mock_topology, mock_update):
        mock_db.return_value = []
        mock_hosts.return_value = True
        mock_flavors.return_value = False
        mock_topology.return_value = True
        self.ostro.resource.datacenter.name = 'test_name'

        result = self.ostro.bootstrap()
        self.assertFalse(result)
        mock_db.assert_called_once_with('test_name')
        mock_hosts.assert_called_once_with()
        mock_flavors.assert_called_once_with()
        mock_topology.assert_not_called()
        mock_update.assert_not_called()

    @mock.patch.object(Resource, 'update_topology')
    @mock.patch.object(Ostro, '_set_topology')
    @mock.patch.object(Ostro, '_set_flavors')
    @mock.patch.object(Ostro, '_set_hosts')
    @mock.patch.object(MusicHandler, 'get_resource_status')
    def test_bootstrap_topology_fail(self, mock_db, mock_hosts, mock_flavors,
                                     mock_topology, mock_update):
        mock_db.return_value = []
        mock_hosts.return_value = True
        mock_flavors.return_value = True
        mock_topology.return_value = False
        self.ostro.resource.datacenter.name = 'test_name'

        result = self.ostro.bootstrap()
        self.assertFalse(result)
        mock_db.assert_called_once_with('test_name')
        mock_hosts.assert_called_once_with()
        mock_flavors.assert_called_once_with()
        mock_topology.assert_called_once_with()
        mock_update.assert_not_called()

    @mock.patch.object(Resource, 'update_topology')
    @mock.patch.object(Ostro, '_set_topology')
    @mock.patch.object(Ostro, '_set_flavors')
    @mock.patch.object(Ostro, '_set_hosts')
    @mock.patch.object(MusicHandler, 'get_resource_status')
    def test_bootstrap_success(self, mock_db, mock_hosts, mock_flavors,
                               mock_topology, mock_update):
        mock_db.return_value = []
        mock_hosts.return_value = True
        mock_flavors.return_value = True
        mock_topology.return_value = True
        self.ostro.resource.datacenter.name = 'test_name'

        result = self.ostro.bootstrap()
        self.assertTrue(result)
        mock_db.assert_called_once_with('test_name')
        mock_hosts.assert_called_once_with()
        mock_flavors.assert_called_once_with()
        mock_topology.assert_called_once_with()
        mock_update.assert_called_once_with()

    @mock.patch.object(TopologyManager, 'set_topology')
    def test_set_topology_fail(self, mock_topology):
        mock_topology.return_value = False

        result = self.ostro._set_topology()
        self.assertFalse(result)
        mock_topology.assert_called_once_with()

    @mock.patch.object(TopologyManager, 'set_topology')
    def test_set_topology_success(self, mock_topology):
        mock_topology.return_value = True

        result = self.ostro._set_topology()
        self.assertTrue(result)
        mock_topology.assert_called_once_with()

    @mock.patch.object(ComputeManager, 'set_hosts')
    def test_set_hosts_fail(self, mock_hosts):
        mock_hosts.return_value = False

        result = self.ostro._set_hosts()
        self.assertFalse(result)
        mock_hosts.assert_called_once_with()

    @mock.patch.object(ComputeManager, 'set_hosts')
    def test_set_hosts_success(self, mock_hosts):
        mock_hosts.return_value = True

        result = self.ostro._set_hosts()
        self.assertTrue(result)
        mock_hosts.assert_called_once_with()

    @mock.patch.object(ComputeManager, 'set_flavors')
    def test_set_flavors_fail(self, mock_flavors):
        mock_flavors.return_value = False

        result = self.ostro._set_flavors()
        self.assertFalse(result)
        mock_flavors.assert_called_once_with()

    @mock.patch.object(ComputeManager, 'set_flavors')
    def test_set_flavors_success(self, mock_flavors):
        mock_flavors.return_value = True

        result = self.ostro._set_flavors()
        self.assertTrue(result)
        mock_flavors.assert_called_once_with()

    def tests_get_vms_from_logical_group_has_vms(self):
        mock_lg = LogicalGroup(uuid.uuid4().hex)
        mock_lg.group_type = "EX"
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        mock_lg.vm_list = [mock_vm_id]
        self.ostro.resource.logical_groups = {
            'test_name:group': mock_lg
        }

        result = self.ostro._get_vms_from_logical_group('group')
        self.assertEqual([mock_uuid], result)

    def tests_get_vms_from_logical_group_has_none_vm(self):
        mock_lg = LogicalGroup(uuid.uuid4().hex)
        mock_lg.group_type = "EX"
        mock_h_uuid = uuid.uuid4().hex
        mock_uuid = uuid.uuid4().hex
        mock_h_uuid_n = uuid.uuid4().hex
        mock_vm_id = (mock_h_uuid, 0, mock_uuid)
        mock_none_vm_id = (mock_h_uuid_n, 1, "none")
        mock_lg.vm_list = [mock_vm_id, mock_none_vm_id]
        self.ostro.resource.logical_groups = {
            'test_name:group': mock_lg
        }

        result = self.ostro._get_vms_from_logical_group('group')
        self.assertEqual([mock_uuid], result)
