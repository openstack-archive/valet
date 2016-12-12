'''
Created on Sep 26, 2016

@author: stack
'''

import mock
import valet.api.v1.controllers.root as root
from valet.api.v1.controllers.root import RootController
from valet.tests.unit.api.v1.api_base import ApiBase


class TestRoot(ApiBase):
    '''Unit tests for valet.api.v1.controllers.placements '''

    def setUp(self):
        super(TestRoot, self).setUp()

        self.root_controller = RootController()

    def test_allow(self):
        self.validate_test(self.root_controller.allow() == 'GET')

    @mock.patch.object(root, 'error', ApiBase.mock_error)
    @mock.patch.object(root, 'request')
    def test_index(self, mock_request):
        mock_request.method = "PUT"
        self.root_controller.index()
        self.validate_test("The PUT method is not allowed" in ApiBase.response)

    def test_index_options(self):
        self.root_controller.index_options()
        self.validate_test(root.response.status == 204)

    @mock.patch.object(root, 'request')
    def test_index_get(self, mock_request):
        mock_request.application_url.return_value = "application_url"
        response = self.root_controller.index_get()

        self.validate_test(response['versions'][0])
        self.validate_test(response['versions'][0]['links'])
