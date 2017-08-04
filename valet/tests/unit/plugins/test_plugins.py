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

from valet.plugins.heat.plugins import ValetLifecyclePlugin
from valet.tests.unit.plugins.base import Base


class TestPlugins(Base):

    @mock.patch('valet_plugins.plugins.heat.plugins.CONF')
    def setUp(self, mock_conf):
        super(TestPlugins, self).setUp()

        self.valet_life_cycle_plugin = self.init_ValetLifecyclePlugin()

    @mock.patch('valet_plugins.common.valet_api.ValetAPI')
    def init_ValetLifecyclePlugin(self, mock_class):
        return ValetLifecyclePlugin()

    @mock.patch.object(ValetLifecyclePlugin, '_parse_stack')
    def test_do_pre_op(self, mock_parse_stack):
        mock_parse_stack.return_value = {'test': 'resources'}

        stack = mock.MagicMock()
        stack.name = "test_stack"
        stack.id = "test_id"

        cnxt = mock.MagicMock()
        cnxt.auth_token = "test_auth_token"

        # returns due to hints_enabled
        self.valet_life_cycle_plugin.hints_enabled = False
        stack.status = "IN_PROGRESS"
        self.valet_life_cycle_plugin.do_pre_op(cnxt, stack, action="DELETE")
        self.validate_test(self.valet_life_cycle_plugin.api.method_calls == [])

        # returns due to stack.status
        self.valet_life_cycle_plugin.hints_enabled = True
        stack.status = "NOT_IN_PROGRESS"
        self.valet_life_cycle_plugin.do_pre_op(cnxt, stack, action="DELETE")
        self.validate_test(self.valet_life_cycle_plugin.api.method_calls == [])

        # action delete
        self.valet_life_cycle_plugin.hints_enabled = True
        stack.status = "IN_PROGRESS"
        self.valet_life_cycle_plugin.do_pre_op(cnxt, stack, action="DELETE")
        self.validate_test("plans_delete" in
                           self.valet_life_cycle_plugin.api.method_calls[0])

        # action create
        self.valet_life_cycle_plugin.do_pre_op(cnxt, stack, action="CREATE")
        self.validate_test("plans_create"
                           in self.valet_life_cycle_plugin.api.method_calls[1])
