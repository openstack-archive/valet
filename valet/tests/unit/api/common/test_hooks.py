# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
'''
Created on Sep 29, 2016

@author: stack
'''

import mock
import valet.api.common.hooks as hooks
from valet.api.common.hooks import MessageNotificationHook
from valet.tests.unit.api.v1.api_base import ApiBase


class TestHooks(ApiBase):

    def setUp(self):
        super(TestHooks, self).setUp()

        self.message_notification_hook = MessageNotificationHook()

    @mock.patch.object(hooks, 'threading')
    @mock.patch.object(hooks, 'conf')
    @mock.patch.object(hooks, 'webob')
    def test_after_ok(self, mock_bob, mock_conf, mock_threading):
        mock_bob.exc.status_map = {"test_status_code": State}
        mock_bob.exc.HTTPOk = State
        mock_conf.messaging.notifier.return_value = "notifier"
        mock_conf.messaging.timeout = 1

        self.message_notification_hook.after(State)
        # print (dir(mock_conf))
        # self.validate_test(mock_conf.messaging.notifier.info.called)

        self.validate_test(mock_threading.Thread.called)
        mock_threading.Thread.assert_called_once_with(target=mock_conf.messaging.notifier.info, args=(
            {},
            'api', {'response': {'body': State.response.body, 'status_code': State.response.status_code},
                    'context': State.request.context,
                    'request': {'path': 'test_path', 'method': 'test_method', 'body': None}}
        ), )

    @mock.patch.object(hooks, 'threading')
    @mock.patch.object(hooks, 'conf')
    @mock.patch.object(hooks, 'webob')
    def test_after_with_error(self, mock_bob, mock_conf, mock_threading):
        mock_bob.exc.status_map = {"test_status_code": State}
        mock_conf.messaging.notifier.return_value = "notifier"
        mock_conf.messaging.timeout = 1

        mock_bob.exc.HTTPOk = ApiBase
        self.message_notification_hook.after(State)

        # self.validate_test(mock_conf.messaging.notifier.error.called)
        self.validate_test(mock_threading.Thread.called)

        mock_threading.Thread.assert_called_once_with(target=mock_conf.messaging.notifier.error, args=(
            {},
            'api', {'response': {'body': State.response.body, 'status_code': State.response.status_code},
                    'context': State.request.context,
                    'request': {'path': 'test_path', 'method': 'test_method', 'body': None}}
        ), )


class State(object):
    class response(object):
        status_code = "test_status_code"
        body = "test_body"

    class request(object):
        path = "test_path"
        method = "test_method"
        body = "test_req_body"
        context = {'tenant_id': 'test_tenant_id', 'user_id': 'test_user_id'}

        @classmethod
        def path_info_pop(cls):
            return None
