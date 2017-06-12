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

from valet.engine.resource_manager.compute import Compute
from valet.tests.base import Base


class TestCompute(Base):

    def setUp(self):
        super(TestCompute, self).setUp()

        self.compute = Compute()

    @mock.patch.object(Compute, '_set_availability_zones')
    @mock.patch.object(Compute, '_get_nova_client')
    def test_set_hosts_set_zones_failed(self, mock_get_nova, mock_set_zones):
        mock_get_nova.return_value = None
        mock_set_zones.return_value = "test_failed"
        mock_hosts = mock.Mock()
        mock_lg = mock.Mock()

        result = self.compute.set_hosts(mock_hosts, mock_lg)
        self.assertEqual("test_failed", result)

    @mock.patch.object(Compute, '_set_aggregates')
    @mock.patch.object(Compute, '_set_availability_zones')
    @mock.patch.object(Compute, '_get_nova_client')
    def test_set_hosts_set_aggregates_failed(self, mock_get_nova,
                                             mock_set_zones,
                                             mock_set_aggregates):
        mock_get_nova.return_value = None
        mock_set_zones.return_value = "success"
        mock_set_aggregates.return_value = "test_failed"
        mock_hosts = mock.Mock()
        mock_lg = mock.Mock()

        result = self.compute.set_hosts(mock_hosts, mock_lg)
        self.assertEqual("test_failed", result)

    @mock.patch.object(Compute, '_set_placed_vms')
    @mock.patch.object(Compute, '_set_aggregates')
    @mock.patch.object(Compute, '_set_availability_zones')
    @mock.patch.object(Compute, '_get_nova_client')
    def test_set_hosts_place_vms_failed(self, mock_get_nova, mock_set_zones,
                                        mock_set_aggregates, mock_set_vms):
        mock_get_nova.return_value = None
        mock_set_zones.return_value = "success"
        mock_set_aggregates.return_value = "success"
        mock_set_vms.return_value = "test_failed"
        mock_hosts = mock.Mock()
        mock_lg = mock.Mock()

        result = self.compute.set_hosts(mock_hosts, mock_lg)
        self.assertEqual("test_failed", result)

    @mock.patch.object(Compute, '_set_resources')
    @mock.patch.object(Compute, '_set_placed_vms')
    @mock.patch.object(Compute, '_set_aggregates')
    @mock.patch.object(Compute, '_set_availability_zones')
    @mock.patch.object(Compute, '_get_nova_client')
    def test_set_hosts_set_resources_failed(self, mock_get_nova,
                                            mock_set_zones,
                                            mock_set_aggregates,
                                            mock_set_vms,
                                            mock_set_resources):
        mock_get_nova.return_value = None
        mock_set_zones.return_value = "success"
        mock_set_aggregates.return_value = "success"
        mock_set_vms.return_value = "success"
        mock_set_resources.return_value = "test_failed"
        mock_hosts = mock.Mock()
        mock_lg = mock.Mock()

        result = self.compute.set_hosts(mock_hosts, mock_lg)
        self.assertEqual("test_failed", result)
