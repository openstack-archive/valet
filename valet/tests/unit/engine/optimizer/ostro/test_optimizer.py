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

from valet.engine.optimizer.db_connect.music_handler import MusicHandler
from valet.engine.optimizer.ostro.optimizer import Optimizer
from valet.engine.optimizer.ostro.search_base import Resource as _Resource
from valet.engine.optimizer.ostro_server.configuration import Config
from valet.engine.resource_manager.resource_base import LogicalGroup
from valet.engine.resource_manager.resource import Resource
from valet.tests.base import Base


class TestOptimizer(Base):
    """Unit tests for valet.engine.optimizer.ostro.optimizer."""

    def setUp(self):
        """Setup Test Optimizer Class."""
        super(TestOptimizer, self).setUp()

        self.config = Config("/valet/tests/unit/engine/optimizer/ostro/empty.cfg")
        self.db = MusicHandler(self.config)
        self.resource = Resource(self.db, self.config)
        self.optimizer = Optimizer(self.resource)
        # self.optimizer = Optimizer(mock.Mock())

    # @mock.patch.object(Resource, 'add_vm_to_logical_groups')
    # @mock.patch.object(Optimizer, '_collect_logical_groups_of_vm')
    # @mock.patch.object(Resource, 'add_logical_group')
    # def test_update_logical_grouping_host(self, mock_add_lg, mock_collect_lg, mock_add_vm):
    #     mock_lg = LogicalGroup(uuid.uuid4().hex)
    #     mock_lg.group_type = "EX"
    #     mock_lg.rack_name = "not_any"
    #     mock_lg.cluster_name = "not_any"

    #     mock_avail_host = _Resource()
    #     mock_avail_host.host_name = "host1"
    #     mock_avail_host.host_memberships = {
    #         'host:not_any': mock_lg
    #     }
    #     self.optimizer.resource.hosts = {
    #         'host1': 'is_valid'
    #     }

    #     mock_uuid = uuid.uuid4().hex
    #     mock_v = mock.Mock()
    #     mock_v.uuid = uuid.uuid4().hex
    #     mock_v.name = "testVM"

    #     self.optimizer._update_logical_grouping(mock_v, mock_avail_host, mock_uuid)
    #     mock_add_lg.assert_called_once_with('host1', 'host:not_any', 'EX')
    #     mock_collect_lg.assert_called_once_with(mock_v, [])
    #     mock_add_vm.assert_called_once_with('is_valid', (mock_v.uuid, mock_v.name, mock_uuid), [])
