'''
Created on Sep 27, 2016

@author: stack
'''

import mock
import valet.api.common.ostro_helper as helper
from valet.api.common.ostro_helper import Ostro
import valet.api.db.models as models
from valet.tests.unit.api.v1.api_base import ApiBase


class TestOstroHelper(ApiBase):

    def setUp(self):
        super(TestOstroHelper, self).setUp()

        self.ostro = self.init_Ostro()

    @mock.patch.object(helper, 'conf')
    def init_Ostro(self, mock_conf):
        mock_conf.ostro = {}
        mock_conf.ostro["tries"] = 10
        mock_conf.ostro["interval"] = 1

        return Ostro()

    def test_build_request(self):
        kwargs = {'tenant_id': 'test_tenant_id',
                  'args': {'stack_id': 'test_stack_id',
                           'plan_name': 'test_plan_name',
                           'resources': {'test_resource': {'Type': 'ATT::Valet::GroupAssignment',
                                                           'Properties': {'resources': ['my-instance-1', 'my-instance-2'],
                                                                          'group_type': 'affinity',
                                                                          'level': 'host'},
                                                           'name': 'test-affinity-group3'}}}}
        self.validate_test(self.ostro.build_request(**kwargs))

        kwargs = {'tenant_id': 'test_tenant_id',
                  'args': {'stack_id': 'test_stack_id',
                           'plan_name': 'test_plan_name',
                           'resources': {'test_resource': {'Type': 'ATT::Valet::GroupAssignment',
                                                           'Properties': {'resources': ['my-instance-1', 'my-instance-2'],
                                                                          'group_type': 'affinity',
                                                                          'group_name': "test_group_name",
                                                                          'level': 'host'},
                                                           'name': 'test-affinity-group3'}}}}
        self.validate_test(not self.ostro.build_request(**kwargs))
        self.validate_test("conflict" in self.ostro.error_uri)

        kwargs = {'tenant_id': 'test_tenant_id',
                  'args': {'stack_id': 'test_stack_id',
                           'plan_name': 'test_plan_name',
                           'resources': {'test_resource': {'Type': 'ATT::Valet::GroupAssignment',
                                                           'Properties': {'resources': ['my-instance-1', 'my-instance-2'],
                                                                          'group_type': 'exclusivity',
                                                                          'level': 'host'},
                                                           'name': 'test-affinity-group3'}}}}
        self.validate_test(not self.ostro.build_request(**kwargs))
        self.validate_test("invalid" in self.ostro.error_uri)

        kwargs = {'tenant_id': 'test_tenant_id',
                  'args': {'stack_id': 'test_stack_id',
                           'plan_name': 'test_plan_name',
                           'resources': {'test_resource': {'Type': 'ATT::Valet::GroupAssignment',
                                                           'Properties': {'resources': ['my-instance-1', 'my-instance-2'],
                                                                          'group_type': 'exclusivity',
                                                                          'group_name': "test_group_name",
                                                                          'level': 'host'},
                                                           'name': 'test-affinity-group3'}}}}
        self.validate_test(not self.ostro.build_request(**kwargs))
        self.validate_test("not_found" in self.ostro.error_uri)

        kwargs = {'tenant_id': 'test_tenant_id',
                  'args': {'stack_id': 'test_stack_id',
                           'plan_name': 'test_plan_name',
                           'timeout': '60 sec',
                           'resources': {'ca039d18-1976-4e13-b083-edb12b806e25': {'Type': 'ATT::Valet::GroupAssignment',
                                                                                  'Properties': {'resources': ['my-instance-1', 'my-instance-2'],
                                                                                                 'group_type': 'non_type',
                                                                                                 'group_name': "test_group_name",
                                                                                                 'level': 'host'},
                                                                                  'name': 'test-affinity-group3'}}}}
        self.validate_test(not self.ostro.build_request(**kwargs))
        self.validate_test("invalid" in self.ostro.error_uri)

    @mock.patch.object(helper, 'uuid')
    def test_ping(self, mock_uuid):
        mock_uuid.uuid4.return_value = "test_stack_id"
        self.ostro.ping()

        self.validate_test(self.ostro.request['stack_id'] == "test_stack_id")

    def test_is_request_serviceable(self):
        self.ostro.request = {'resources': {"bla": {'type': "OS::Nova::Server"}}}
        self.validate_test(self.ostro.is_request_serviceable())

        self.ostro.request = {}
        self.validate_test(not self.ostro.is_request_serviceable())

    def test_replan(self):
        kwargs = {'args': {'stack_id': 'test_stack_id',
                           'locations': 'test_locations',
                           'orchestration_id': 'test_orchestration_id',
                           'exclusions': 'test_exclusions'}}
        self.ostro.replan(**kwargs)

        self.validate_test(self.ostro.request['stack_id'] == "test_stack_id")
        self.validate_test(self.ostro.request['locations'] == "test_locations")
        self.validate_test(self.ostro.request['orchestration_id'] == "test_orchestration_id")
        self.validate_test(self.ostro.request['exclusions'] == "test_exclusions")

    def test_migrate(self):
        kwargs = {'args': {'stack_id': 'test_stack_id',
                           'excluded_hosts': 'test_excluded_hosts',
                           'orchestration_id': 'test_orchestration_id'}}
        self.ostro.migrate(**kwargs)

        self.validate_test(self.ostro.request['stack_id'] == "test_stack_id")
        self.validate_test(self.ostro.request['excluded_hosts'] == "test_excluded_hosts")
        self.validate_test(self.ostro.request['orchestration_id'] == "test_orchestration_id")

    @mock.patch.object(helper, 'uuid')
    def test_query(self, mock_uuid):
        mock_uuid.uuid4.return_value = "test_stack_id"
        kwargs = {'args': {'type': 'test_type',
                           'parameters': 'test_parameters'}}
        self.ostro.query(**kwargs)

        self.validate_test(self.ostro.request['stack_id'] == "test_stack_id")
        self.validate_test(self.ostro.request['type'] == "test_type")
        self.validate_test(self.ostro.request['parameters'] == "test_parameters")

    @mock.patch.object(models, 'PlacementRequest', mock.MagicMock)
    @mock.patch.object(models, 'Query', mock.MagicMock)
    def test_send(self):
        self.ostro.args = {'stack_id': 'test_stack_id'}
        self.ostro.send()
        self.validate_test("server_error" in self.ostro.error_uri)
