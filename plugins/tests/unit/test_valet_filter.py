#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
import uuid

from keystoneclient.v2_0 import client

from valet.plugins.common import valet_api
from valet.plugins.plugins.nova.valet_filter import ValetFilter
from valet.plugins.tests.base import Base


class TestResources(object):
    def __init__(self, host_name):
        self.host = host_name


class TestValetFilter(Base):

    def setUp(self):
        super(TestValetFilter, self).setUp()

        client.Client = mock.MagicMock()
        self.valet_filter = self.init_ValetFilter()

    @mock.patch.object(valet_api.ValetAPI, '_register_opts')
    @mock.patch.object(ValetFilter, '_register_opts')
    def init_ValetFilter(self, mock_opt, mock_init):
        mock_init.return_value = None
        mock_opt.return_value = None
        return ValetFilter()

    @mock.patch.object(ValetFilter, '_orch_id_from_resource_id')
    @mock.patch.object(ValetFilter, '_location_from_ad_hoc_plan')
    def test_filter_location_for_resource_ad_hoc(self, mock_loc_ad_hoc,
                                                 mock_orch_id_res):
        host = 'hostname'
        physical_id = str(uuid.uuid4())

        mock_loc_ad_hoc.return_value = host
        mock_orch_id_res.return_value = None

        filter_properties = {
            'request_spec': {
                'image': {'name': 'image_name'},
                'metadata': {},
                'instance_properties': {'uuid': physical_id}
            },
            'instance_type': {
                'name': "flavor"
            }
        }

        (location, res_id, orch_id, ad_hoc) = \
            self.valet_filter._location_for_resource([host],
                                                     filter_properties)

        self.assertEqual(location, host)
        self.assertEqual(res_id, physical_id)
        self.assertEqual(orch_id, None)
        self.assertTrue(ad_hoc)

    @mock.patch.object(ValetFilter, '_location_for_resource')
    @mock.patch.object(ValetFilter, '_authorize')
    @mock.patch.object(valet_api.ValetAPI, 'plans_create')
    @mock.patch.object(valet_api.ValetAPI, 'placement')
    def test_filter_all(self, mock_placement, mock_create,
                        mock_auth, mock_location_tuple):
        mock_placement.return_value = None
        mock_create.return_value = None
        mock_location_tuple.return_value = \
            ('location', 'res_id', 'orch_id', 'ad_hoc')

        with mock.patch('oslo_config.cfg.CONF') as config:
            hosts = [
                TestResources("first_host"),
                TestResources("second_host"),
            ]

            config.valet.failure_mode = 'yield'

            filter_properties = {
                'request_spec': {
                    'image': {'name': 'image_name'},
                    'instance_properties': {'uuid': ""},
                },
                'scheduler_hints': {'heat_resource_uuid': "123456"},
                'instance_type': {'name': "instance_name"},
            }

            resources = self.valet_filter.filter_all(hosts, filter_properties)

            for resource in resources:
                self.validate_test(resource.host in "first_host, second_host")
                self.validate_test(mock_placement.called)

            filter_properties = {
                'request_spec': {
                    'image': {'name': 'image_name'},
                    'instance_properties': {'uuid': ""},
                },
                'scheduler_hints': "scheduler_hints",
                'instance_type': {'name': "instance_name"},
            }

            resources = self.valet_filter.filter_all(hosts, filter_properties)

            for _ in resources:
                self.validate_test(mock_create.called)
