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

from valet.engine.optimizer.db_connect.music_handler import MusicHandler
from valet.engine.resource_manager.resource import Resource
from valet.tests.base import Base


class TestResource(Base):

    def setUp(self):
        super(TestResource, self).setUp()

        self.config = mock.Mock()
        self.logger = mock.Mock()
        self.db = MusicHandler(self.config, self.logger)
        self.resource = Resource(self.db, self.config, self.logger)

    # TODO(JC): test bootstrap_from_db

    def test_update_topology_store_false(self):
        result = self.resource.update_topology(False)
        self.assertTrue(result)

    @mock.patch.object(Resource, 'store_topology_updates')
    def test_update_topology_store_true(self, mock_resource):
        self.resource.update_topology(True)
        mock_resource.assert_called_once_with()
