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

from valet.engine.optimizer.ostro.search_base import Resource
from valet.tests.base import Base


class TestSearchBase(Base):
    """Unit tests for valet.engine.optimizer.ostro.search_base."""

    def setUp(self):
        """Setup Test Search Base Class."""
        super(TestSearchBase, self).setUp()

        self.resource = Resource()

    def test_get_common_placement_cluster(self):
        self.resource.cluster_name = "foo"
        mock_resource = mock.Mock()
        mock_resource.cluster_name = "bar"

        result = self.resource.get_common_placement(mock_resource)
        self.assertEqual("cluster", result)

    def test_get_common_placement_rack(self):
        self.resource.cluster_name = "foo"
        self.resource.rack_name = "bar"
        mock_resource = mock.Mock()
        mock_resource.cluster_name = "foo"
        mock_resource.rack_name = "baz"

        result = self.resource.get_common_placement(mock_resource)
        self.assertEqual("rack", result)

    def test_get_common_placement_host(self):
        self.resource.cluster_name = "foo"
        self.resource.rack_name = "bar"
        self.resource.host_name = "baz"
        mock_resource = mock.Mock()
        mock_resource.cluster_name = "foo"
        mock_resource.rack_name = "bar"
        mock_resource.host_name = "bat"

        result = self.resource.get_common_placement(mock_resource)
        self.assertEqual("host", result)

    def test_get_common_placement_any(self):
        self.resource.cluster_name = "foo"
        self.resource.rack_name = "bar"
        self.resource.host_name = "baz"
        mock_resource = mock.Mock()
        mock_resource.cluster_name = "foo"
        mock_resource.rack_name = "bar"
        mock_resource.host_name = "baz"

        result = self.resource.get_common_placement(mock_resource)
        self.assertEqual("ANY", result)

    def test_get_resource_name_cluster(self):
        self.resource.cluster_name = "testname"

        result = self.resource.get_resource_name("cluster")
        self.assertEqual("testname", result)

    def test_get_resource_name_rack(self):
        self.resource.rack_name = "testname"

        result = self.resource.get_resource_name("rack")
        self.assertEqual("testname", result)

    def test_get_resource_name_host(self):
        self.resource.host_name = "testname"

        result = self.resource.get_resource_name("host")
        self.assertEqual("testname", result)

    def test_get_resource_name_none(self):

        result = self.resource.get_resource_name(None)
        self.assertEqual("unknown", result)

    def test_get_memberships_cluster(self):
        self.resource.cluster_memberships = "testval"

        result = self.resource.get_memberships("cluster")
        self.assertEqual("testval", result)

    def test_get_memberships_rack(self):
        self.resource.rack_memberships = "testval"

        result = self.resource.get_memberships("rack")
        self.assertEqual("testval", result)

    def test_get_memberships_host(self):
        self.resource.host_memberships = "testval"

        result = self.resource.get_memberships("host")
        self.assertEqual("testval", result)

    def test_get_memberships_none(self):

        result = self.resource.get_memberships(None)
        self.assertEqual(None, result)

    def test_get_num_of_placed_vms_cluster(self):
        self.resource.cluster_num_of_placed_vms = 5

        result = self.resource.get_num_of_placed_vms("cluster")
        self.assertEqual(5, result)

    def test_get_num_of_placed_vms_rack(self):
        self.resource.rack_num_of_placed_vms = 5

        result = self.resource.get_num_of_placed_vms("rack")
        self.assertEqual(5, result)

    def test_get_num_of_placed_vms_host(self):
        self.resource.host_num_of_placed_vms = 5

        result = self.resource.get_num_of_placed_vms("host")
        self.assertEqual(5, result)

    def test_get_num_of_placed_vms_none(self):

        result = self.resource.get_num_of_placed_vms(None)
        self.assertEqual(0, result)

    def test_get_avail_resources_cluster(self):
        self.resource.cluster_avail_vCPUs = 1
        self.resource.cluster_avail_mem = 2
        self.resource.cluster_avail_local_disk = 3

        result = self.resource.get_avail_resources("cluster")
        self.assertEqual((1, 2, 3), result)

    def test_get_avail_resources_rack(self):
        self.resource.rack_avail_vCPUs = 1
        self.resource.rack_avail_mem = 2
        self.resource.rack_avail_local_disk = 3

        result = self.resource.get_avail_resources("rack")
        self.assertEqual((1, 2, 3), result)

    def test_get_avail_resources_host(self):
        self.resource.host_avail_vCPUs = 1
        self.resource.host_avail_mem = 2
        self.resource.host_avail_local_disk = 3

        result = self.resource.get_avail_resources("host")
        self.assertEqual((1, 2, 3), result)

    def test_get_avail_resources_none(self):

        result = self.resource.get_avail_resources(None)
        self.assertEqual((0, 0, 0), result)

    def test_get_local_disk_cluster(self):
        self.resource.cluster_local_disk = 1
        self.resource.cluster_avail_local_disk = 2

        result = self.resource.get_local_disk("cluster")
        self.assertEqual((1, 2), result)

    def test_get_local_disk_rack(self):
        self.resource.rack_local_disk = 1
        self.resource.rack_avail_local_disk = 2

        result = self.resource.get_local_disk("rack")
        self.assertEqual((1, 2), result)

    def test_get_local_disk_host(self):
        self.resource.host_local_disk = 1
        self.resource.host_avail_local_disk = 2

        result = self.resource.get_local_disk("host")
        self.assertEqual((1, 2), result)

    def test_get_local_disk_none(self):

        result = self.resource.get_local_disk(None)
        self.assertEqual((0, 0), result)

    def test_get_vCPUs_cluster(self):
        self.resource.cluster_vCPUs = 1
        self.resource.cluster_avail_vCPUs = 2

        result = self.resource.get_vCPUs("cluster")
        self.assertEqual((1, 2), result)

    def test_get_vCPUs_rack(self):
        self.resource.rack_vCPUs = 1
        self.resource.rack_avail_vCPUs = 2

        result = self.resource.get_vCPUs("rack")
        self.assertEqual((1, 2), result)

    def test_get_vCPUs_host(self):
        self.resource.host_vCPUs = 1
        self.resource.host_avail_vCPUs = 2

        result = self.resource.get_vCPUs("host")
        self.assertEqual((1, 2), result)

    def test_get_vCPUs_none(self):

        result = self.resource.get_vCPUs(None)
        self.assertEqual((0, 0), result)

    def test_get_mem_cluster(self):
        self.resource.cluster_mem = 1
        self.resource.cluster_avail_mem = 2

        result = self.resource.get_mem("cluster")
        self.assertEqual((1, 2), result)

    def test_get_mem_rack(self):
        self.resource.rack_mem = 1
        self.resource.rack_avail_mem = 2

        result = self.resource.get_mem("rack")
        self.assertEqual((1, 2), result)

    def test_get_mem_host(self):
        self.resource.host_mem = 1
        self.resource.host_avail_mem = 2

        result = self.resource.get_mem("host")
        self.assertEqual((1, 2), result)

    def test_get_mem_none(self):

        result = self.resource.get_mem(None)
        self.assertEqual((0, 0), result)
