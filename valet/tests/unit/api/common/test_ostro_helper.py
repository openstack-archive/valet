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

"""Test Ostro Helper."""

import mock

from valet.api.common import ostro_helper
from valet.api.db.models import music as models
from valet.tests.unit.api.v1 import api_base
from valet.tests.unit import fakes


class TestOstroHelper(api_base.ApiBase):
    def setUp(self):
        """Setup Test Ostro and call init Ostro."""
        super(TestOstroHelper, self).setUp()

        self.engine = self.init_engine()
        self.groups = []

        kwargs = {
            'description': 'test',
            'members': ['test_tenant_id'],
        }
        for group_type in ('affinity', 'diversity', 'exclusivity'):
            kwargs['type'] = group_type
            for group_level in ('host', 'rack'):
                # Build names like host_affinity, rack_diversity, etc.
                kwargs['name'] = "{}_{}".format(group_level, group_type)
                kwargs['level'] = group_level
                group = models.groups.Group(**kwargs)
                self.groups.append(group)

    @mock.patch.object(ostro_helper, 'conf')
    def init_engine(self, mock_conf):
        mock_conf.music = {}
        mock_conf.music["tries"] = 10
        mock_conf.music["interval"] = 1

        return ostro_helper.Ostro()

    def build_request_kwargs(self):
        """Boilerplate for the build_request tests"""
        # TODO(jdandrea): Sample Data should be co-located elsewhere
        base_kwargs = {
            'tenant_id': 'test_tenant_id',
            'args': {
                'stack_id': 'test_stack_id',
                'plan_name': 'test_plan_name',
                'timeout': '60 sec',
                'resources': {
                    "test_server": {
                        'type': 'OS::Nova::Server',
                        'properties': {
                            'key_name': 'ssh_key',
                            'image': 'ubuntu_server',
                            'name': 'my_server',
                            'flavor': 'm1.small',
                            'metadata': {
                                'valet': {
                                    'groups': [
                                        'host_affinity'
                                    ]
                                }
                            },
                            'networks': [
                                {
                                    'network': 'private'
                                }
                            ]
                        },
                        'name': 'my_instance',
                    },
                    'test_group_assignment': {
                        'type': 'OS::Valet::GroupAssignment',
                        'properties': {
                            'group': 'host_affinity',
                            'resources': ['my-instance-1', 'my-instance-2'],
                        },
                        'name': 'test_name',
                    }
                }
            }
        }
        return base_kwargs

    # TODO(jdandrea): Turn these build_request tests into scenarios?

    # The next five build_request methods exercise OS::Nova::Server metadata

    @mock.patch.object(models.Results, 'first')
    def test_build_request_host_affinity_using_metadata(self, mock_results):
        mock_results.return_value = fakes.group(type="affinity")
        kwargs = self.build_request_kwargs()
        kwargs['args']['resources']['test_server'][
            'properties']['metadata']['valet']['groups'][0] = "host_affinity"
        request = self.engine.build_request(**kwargs)
        self.assertTrue(request)

    @mock.patch.object(models.Results, 'first')
    def test_build_request_host_diversity_using_metadata(self, mock_results):
        mock_results.return_value = fakes.group(type="diversity")
        kwargs = self.build_request_kwargs()
        kwargs['args']['resources']['test_server'][
            'properties']['metadata']['valet']['groups'][0] = \
            "host_diversity"
        request = self.engine.build_request(**kwargs)
        self.assertTrue(request)

    @mock.patch.object(models.Results, 'first')
    def test_build_request_host_exclusivity_using_metadata(self, mock_results):
        mock_results.return_value = \
            fakes.group(name="host_exclusivity", type="exclusivity")
        kwargs = self.build_request_kwargs()
        kwargs['args']['resources']['test_server'][
            'properties']['metadata']['valet']['groups'][0] = \
            "host_exclusivity"
        request = self.engine.build_request(**kwargs)
        self.assertTrue(request)

    @mock.patch.object(models.Results, 'first')
    def test_build_request_host_exclusivity_wrong_tenant_using_metadata(
            self, mock_results):
        mock_results.return_value = \
            fakes.group(name="host_exclusivity", type="exclusivity")
        kwargs = self.build_request_kwargs()
        kwargs['args']['resources']['test_server'][
            'properties']['metadata']['valet']['groups'][0] = \
            "host_exclusivity"
        kwargs['tenant_id'] = "bogus_tenant"
        request = self.engine.build_request(**kwargs)
        self.assertFalse(request)
        self.assertIn('conflict', self.engine.error_uri)

    def test_build_request_nonexistant_group_using_metadata(self):
        kwargs = self.build_request_kwargs()
        kwargs['args']['resources']['test_server'][
            'properties']['metadata']['valet']['groups'][0] = "bogus_name"
        request = self.engine.build_request(**kwargs)
        self.assertFalse(request)
        self.assertIn('not_found', self.engine.error_uri)

    # The next five build_request methods exercise OS::Valet::GroupAssignment

    @mock.patch.object(models.Results, 'first')
    def test_build_request_host_affinity(self, mock_results):
        mock_results.return_value = fakes.group(type="affinity")
        kwargs = self.build_request_kwargs()
        kwargs['args']['resources']['test_group_assignment'][
            'properties']['group'] = "host_affinity"
        request = self.engine.build_request(**kwargs)
        self.assertTrue(request)

    @mock.patch.object(models.Results, 'first')
    def test_build_request_host_diversity(self, mock_results):
        mock_results.return_value = fakes.group(type="diversity")
        kwargs = self.build_request_kwargs()
        kwargs['args']['resources']['test_group_assignment'][
            'properties']['group'] = "host_diversity"
        request = self.engine.build_request(**kwargs)
        self.assertTrue(request)

    @mock.patch.object(models.Results, 'first')
    def test_build_request_host_exclusivity(self, mock_results):
        mock_results.return_value = \
            fakes.group(name="host_exclusivity", type="exclusivity")
        kwargs = self.build_request_kwargs()
        kwargs['args']['resources']['test_group_assignment'][
            'properties']['group'] = "host_exclusivity"
        request = self.engine.build_request(**kwargs)
        self.assertTrue(request)

    @mock.patch.object(models.Results, 'first')
    def test_build_request_host_exclusivity_wrong_tenant(self, mock_results):
        mock_results.return_value = \
            fakes.group(name="host_exclusivity", type="exclusivity")
        kwargs = self.build_request_kwargs()
        kwargs['args']['resources']['test_group_assignment'][
            'properties']['group'] = "host_exclusivity"
        kwargs['tenant_id'] = "bogus_tenant"
        request = self.engine.build_request(**kwargs)
        self.assertFalse(request)
        self.assertIn('conflict', self.engine.error_uri)

    def test_build_request_nonexistant_group(self):
        kwargs = self.build_request_kwargs()
        kwargs['args']['resources']['test_group_assignment'][
            'properties']['group'] = "bogus_name"
        request = self.engine.build_request(**kwargs)
        self.assertFalse(request)
        self.assertIn('not_found', self.engine.error_uri)

    @mock.patch.object(ostro_helper, 'uuid')
    def test_ping(self, mock_uuid):
        """Validate engine ping by checking engine request equality."""
        mock_uuid.uuid4.return_value = "test_stack_id"
        self.engine.ping()

        self.assertTrue(self.engine.request['stack_id'] == "test_stack_id")

    def test_is_request_serviceable(self):
        self.engine.request = {
            'resources': {
                "bla": {
                    'type': "OS::Nova::Server",
                }
            }
        }
        self.assertTrue(self.engine.is_request_serviceable())

        self.engine.request = {}
        self.assertFalse(self.engine.is_request_serviceable())

    def test_replan(self):
        kwargs = {
            'args': {
                'stack_id': 'test_stack_id',
                'locations': 'test_locations',
                'orchestration_id': 'test_orchestration_id',
                'exclusions': 'test_exclusions',
                'resource_id': 'test_resource_id',
            }
        }
        self.engine.replan(**kwargs)

        self.assertTrue(self.engine.request['stack_id'] == "test_stack_id")
        self.assertTrue(self.engine.request['locations'] == "test_locations")
        self.assertTrue(
            self.engine.request['orchestration_id'] ==
            "test_orchestration_id")
        self.assertTrue(
            self.engine.request['exclusions'] == "test_exclusions")

    def test_identify(self):
        kwargs = {
            'args': {
                'stack_id': 'test_stack_id',
                'orchestration_id': 'test_orchestration_id',
                'uuid': 'test_uuid',
            }
        }
        self.engine.identify(**kwargs)
        self.assertEqual(self.engine.request['stack_id'], "test_stack_id")
        self.assertEqual(self.engine.request['orchestration_id'],
                         "test_orchestration_id")
        self.assertEqual(self.engine.request['resource_id'], "test_uuid")
        self.assertTrue(self.engine.asynchronous)

    def test_migrate(self):
        kwargs = {
            'args': {
                'stack_id': 'test_stack_id',
                'tenant_id': 'test_tenant_id',
                'excluded_hosts': 'test_excluded_hosts',
                'orchestration_id': 'test_orchestration_id',
            }
        }
        self.engine.migrate(**kwargs)

        self.assertTrue(self.engine.request['stack_id'] == "test_stack_id")
        self.assertTrue(
            self.engine.request['excluded_hosts'] == "test_excluded_hosts")
        self.assertTrue(
            self.engine.request['orchestration_id'] ==
            "test_orchestration_id")

    @mock.patch.object(ostro_helper, 'uuid')
    def test_query(self, mock_uuid):
        """Validate test query by validating several engine requests."""
        mock_uuid.uuid4.return_value = "test_stack_id"
        kwargs = {
            'args': {
                'type': 'test_type',
                'parameters': 'test_parameters',
            }
        }
        self.engine.query(**kwargs)

        self.assertTrue(self.engine.request['stack_id'] == "test_stack_id")
        self.assertTrue(self.engine.request['type'] == "test_type")
        self.assertTrue(
            self.engine.request['parameters'] == "test_parameters")

    @mock.patch.object(ostro_helper, '_log')
    @mock.patch.object(ostro_helper.Ostro, '_send')
    @mock.patch.object(models.ostro, 'PlacementRequest')
    @mock.patch.object(models, 'Query')
    def test_send(self, mock_query, mock_request, mock_send, mock_logger):
        mock_send.return_value = '{"status":{"type":"ok"}}'
        self.engine.args = {'stack_id': 'test_stack_id'}
        self.engine.request = {}
        self.engine.send()
        self.assertIsNone(self.engine.error_uri)
