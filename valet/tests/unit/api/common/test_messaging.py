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

"""Test Messaging."""

import mock
import valet.api.common.messaging as messaging
from valet.tests.unit.api.v1.api_base import ApiBase


class TestMessaging(ApiBase):
    """Test Messaging Class for messaging api."""

    def setUp(self):
        """Setup test messaging."""
        super(TestMessaging, self).setUp()

    @mock.patch.object(messaging, 'cfg')
    @mock.patch.object(messaging, 'conf')
    @mock.patch.object(messaging, 'messaging')
    def test_messaging(self, mock_msg, mock_conf, mock_cfg):
        """Validate messaging in api."""
        mock_conf.messaging.config = {"transport_url": "test_transport_url"}
        mock_msg.get_transport.return_value = "get_transport_method"
        mock_msg.Notifier.return_value = "Notifier"

        messaging.init_messaging()

        self.validate_test("Notifier" in mock_conf.messaging.notifier)
