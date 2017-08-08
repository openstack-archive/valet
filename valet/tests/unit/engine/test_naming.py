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
from oslo_log import log

from valet.engine.resource_manager.naming import Naming
from valet.tests.base import Base

LOG = log.getLogger(__name__)


class TestNaming(Base):
    """Unit Tests for valet.engine.resource_manager.naming."""

    def setUp(self):
        """Setup TestNaming Test Class."""
        super(TestNaming, self).setUp()
        self.topo = Naming(Config(), LOG)

    def test_simple_topology(self):
        """Validate simple topology (region, rack, node_type and status)."""
        (full_rack_name, status) = \
            self.topo._set_layout_by_name("pdk15r05c001")

        self.validate_test(full_rack_name == "pdk15r05")
        self.validate_test(status == "success")

    def test_domain_topology(self):
        """Test Domain Topology."""
        (full_rack_name, status) = \
            self.topo._set_layout_by_name("ihk01r01c001.emea.att.com")

        self.validate_test(full_rack_name == "ihk01r01")
        self.validate_test(status == "success")

    def test_unhappy_topology_r(self):
        """Test unhappy topology, region/rack/node none, invalid status 0."""
        (full_rack_name, status) = \
            self.topo._set_layout_by_name("pdk1505c001")

        self.validate_test(full_rack_name == "none")
        self.validate_test(status == "invalid rack_char = c. "
                                     "missing rack_char = r")

    def test_unhappy_topology_c(self):
        """Test unhappy topology with values none and 1 invalid status."""
        (full_rack_name, status) = \
            self.topo._set_layout_by_name("pdk15r05001")
        self.validate_test(full_rack_name == "none")
        self.validate_test(status == "incorrect format of rack "
                                     "name = ")

# TODO(UNKNOWN): add validation to topology for region


class Config(object):
    """Config for topology."""

    num_of_region_chars = 3
    rack_code_list = "r"
    node_code_list = "a,c,u,f,o,p,s"
