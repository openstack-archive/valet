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

"""Test Topology."""

from valet.engine.resource_manager.topology import Topology
from valet.tests.base import Base


class TestTopology(Base):
    """Unit Tests for valet.engine.resource_manager.topology."""

    def setUp(self):
        """Setup TestTopology Test Class."""
        super(TestTopology, self).setUp()
        self.topo = Topology(Config(), None)

    def test_simple_topology(self):
        """Validate simple topology (region, rack, node_type and status)."""
        (region, rack, node_type, status) = \
            self.topo._set_layout_by_name("pdk15r05c001")

        self.validate_test(region == "pdk15")
        self.validate_test(rack == "pdk15r05")
        self.validate_test(node_type in "a,c,u,f,o,p,s")
        self.validate_test(status == "success")

    def test_domain_topology(self):
        """Test Domain Topology."""
        (region, rack, node_type, status) = \
            self.topo._set_layout_by_name("ihk01r01c001.emea.att.com")

        self.validate_test(region == "ihk01")
        self.validate_test(rack == "ihk01r01")
        self.validate_test(node_type in "a,c,u,f,o,p,s")
        self.validate_test(status == "success")

    def test_unhappy_topology_r(self):
        """Test unhappy topology, region/rack/node none, invalid status 0."""
        (region, rack, node_type, status) = \
            self.topo._set_layout_by_name("pdk1505c001")
        self.validate_test(region == "none")
        self.validate_test(rack == "none")
        self.validate_test(node_type is None)
        self.validate_test(status == "invalid number of "
                                     "identification fields = 0")

    def test_unhappy_topology_c(self):
        """Test unhappy topology with values none and 1 invalid status."""
        (region, rack, node_type, status) = \
            self.topo._set_layout_by_name("pdk15r05001")
        self.validate_test(region == "none")
        self.validate_test(rack == "none")
        self.validate_test(node_type is None)
        self.validate_test(status == "invalid number of "
                                     "identification fields = 1")

# TODO(UNKNOWN): add validation to topology for region


class Config(object):
    """Config for topology."""

    num_of_region_chars = 3
    rack_code_list = "r"
    node_code_list = "a,c,u,f,o,p,s"
