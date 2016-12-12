'''
Created on Sep 22, 2016

@author: stack
'''

import mock
import pecan
import valet.api.v1.controllers.v1 as v1
from valet.api.v1.controllers.v1 import V1Controller
from valet.tests.unit.api.v1.api_base import ApiBase


class TestV1(ApiBase):

    @mock.patch.object(pecan, 'conf')
    def setUp(self, mock_conf):
        super(TestV1, self).setUp()

        mock_conf.identity.engine.validate_token.return_value = True
        mock_conf.identity.engine.is_token_admin.return_value = True
        mock_conf.identity.engine.tenant_from_token.return_value = "tenant_id"
        mock_conf.identity.engine.user_from_token.return_value = "user_id"

        self.v1_controller = V1Controller()

    @mock.patch.object(v1, 'request')
    def test_check_permissions(self, mock_request):
        mock_request.headers.get.return_value = "auth_token"
        mock_request.path.return_value = "bla bla bla"
        mock_request.json.return_value = {"action": "create"}
        mock_request.context = {}

        self.validate_test(self.v1_controller.check_permissions() is True)

    @mock.patch.object(v1, 'error', ApiBase.mock_error)
    @mock.patch.object(v1, 'request')
    def test_check_permissions_auth_unhappy(self, mock_request):
        mock_request.headers.get.return_value = None
        mock_request.path.return_value = "bla bla bla"
        mock_request.json.return_value = {"action": "create"}
        mock_request.context = {}

        self.v1_controller.check_permissions()
        self.validate_test("Unauthorized - No auth token" in ApiBase.response)

    def test_allow(self):
        self.validate_test(self.v1_controller.allow() == 'GET')

    @mock.patch.object(v1, 'error', ApiBase.mock_error)
    @mock.patch.object(v1, 'request')
    def test_index(self, mock_request):
        mock_request.method = "PUT"
        self.v1_controller.index()
        self.validate_test("The PUT method is not allowed" in ApiBase.response)

    def test_index_options(self):
        self.v1_controller.index_options()
        self.validate_test(v1.response.status == 204)

    @mock.patch.object(v1, 'request')
    def test_index_get(self, mock_request):
        mock_request.application_url.return_value = "application_url"
        response = self.v1_controller.index_get()

        self.validate_test(response['versions'][0])
        self.validate_test(response['versions'][0]['links'])
