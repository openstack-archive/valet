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

from keystoneclient.v2_0 import client
import mock
from valet_plugins.common import valet_api
from valet_plugins.plugins.nova.valet_filter import ValetFilter
from valet_plugins.tests.base import Base


class TestResources(object):
    def __init__(self, host_name):
        self.host = host_name


class TestValetFilter(Base):

    def setUp(self):
        super(TestValetFilter, self).setUp()

        client.Client = mock.MagicMock()
        self.valet_filter = self.init_ValetFilter()

    @mock.patch.object(valet_api.ValetAPIWrapper, '_register_opts')
    @mock.patch.object(ValetFilter, '_register_opts')
    def init_ValetFilter(self, mock_opt, mock_init):
        mock_init.return_value = None
        mock_opt.return_value = None
        return ValetFilter()

    @mock.patch.object(valet_api.ValetAPIWrapper, 'plans_create')
    @mock.patch.object(valet_api.ValetAPIWrapper, 'placement')
    def test_filter_all(self, mock_placement, mock_create):
        mock_placement.return_value = None
        mock_create.return_value = None

        with mock.patch('oslo_config.cfg.CONF') as config:
            setattr(config, "valet", {self.valet_filter.opt_failure_mode_str: "yield",
                                      self.valet_filter.opt_project_name_str: "test_admin_tenant_name",
                                      self.valet_filter.opt_username_str: "test_admin_username",
                                      self.valet_filter.opt_password_str: "test_admin_password",
                                      self.valet_filter.opt_auth_uri_str: "test_admin_auth_url"})

            filter_properties = {'request_spec': {'instance_properties': {'uuid': ""}},
                                 'scheduler_hints': {'heat_resource_uuid': "123456"},
                                 'instance_type': {'name': "instance_name"}}

            resources = self.valet_filter.filter_all([TestResources("first_host"), TestResources("second_host")], filter_properties)

            for resource in resources:
                self.validate_test(resource.host in "first_host, second_host")
                self.validate_test(mock_placement.called)

            filter_properties = {'request_spec': {'instance_properties': {'uuid': ""}},
                                 'scheduler_hints': "scheduler_hints",
                                 'instance_type': {'name': "instance_name"}}

            resources = self.valet_filter.filter_all([TestResources("first_host"), TestResources("second_host")], filter_properties)

            for _ in resources:
                self.validate_test(mock_create.called)
