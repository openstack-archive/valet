'''
Created on Sep 28, 2016

@author: stack
'''

import mock
import valet.api.common.messaging as messaging
from valet.tests.unit.api.v1.api_base import ApiBase


class TestMessaging(ApiBase):

    def setUp(self):
        super(TestMessaging, self).setUp()

    @mock.patch.object(messaging, 'cfg')
    @mock.patch.object(messaging, 'conf')
    @mock.patch.object(messaging, 'messaging')
    def test_messaging(self, mock_msg, mock_conf, mock_cfg):
        mock_conf.messaging.config = {"transport_url": "test_transport_url"}
        mock_msg.get_transport.return_value = "get_transport_method"
        mock_msg.Notifier.return_value = "Notifier"

        messaging.init_messaging()

        self.validate_test("Notifier" in mock_conf.messaging.notifier)
