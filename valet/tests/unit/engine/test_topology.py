'''
Created on Aug 17, 2016

@author: YB
'''

from valet.engine.resource_manager.topology import Topology
from valet.tests.base import Base


class TestTopology(Base):

    def setUp(self):
        super(TestTopology, self).setUp()
        self.topo = Topology(Config(), None)

    def test_simple_topology(self):
        (region, rack, node_type, status) = self.topo._set_layout_by_name("pdk15r05c001")

        self.validate_test(region == "pdk15")
        self.validate_test(rack == "pdk15r05")
        self.validate_test(node_type in "a,c,u,f,o,p,s")
        self.validate_test(status == "success")

    def test_domain_topology(self):
        (region, rack, node_type, status) = self.topo._set_layout_by_name("ihk01r01c001.emea.att.com")

        self.validate_test(region == "ihk01")
        self.validate_test(rack == "ihk01r01")
        self.validate_test(node_type in "a,c,u,f,o,p,s")
        self.validate_test(status == "success")

    def test_unhappy_topology_r(self):
        (region, rack, node_type, status) = self.topo._set_layout_by_name("pdk1505c001")
        self.validate_test(region == "none")
        self.validate_test(rack == "none")
        self.validate_test(node_type is None)
        self.validate_test(status == "invalid number of identification fields = 0")

    def test_unhappy_topology_c(self):
        (region, rack, node_type, status) = self.topo._set_layout_by_name("pdk15r05001")
        self.validate_test(region == "none")
        self.validate_test(rack == "none")
        self.validate_test(node_type is None)
        self.validate_test(status == "invalid number of identification fields = 1")

#     def test_unhappy_topology_c_domain(self):
#         (region, rack, node_type, status) = self.topo._set_layout_by_name("pdk15r05001.emea.att.com")
#         self.validate_test(region == "none")
#         self.validate_test(rack == "none")
#         self.validate_test(node_type is None)
#         self.validate_test(status == "invalid number of identification fields = 1")

# TODO(GY): add validation to topology for region


class Config(object):
    num_of_region_chars = 3
    rack_code_list = "r"
    node_code_list = "a,c,u,f,o,p,s"
