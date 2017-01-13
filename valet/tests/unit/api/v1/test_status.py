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

"""Test Status."""

import mock
import valet.api.v1.controllers.status as status
from valet.api.v1.controllers.status import StatusController
from valet.tests.unit.api.v1.api_base import ApiBase


class TestStatus(ApiBase):
    """Unit tests for valet.api.v1.controllers.status."""

    def setUp(self):
        """Setup Test Status controller."""
        super(TestStatus, self).setUp()

        self.status_controller = StatusController()

    def test_allow(self):
        """Test status_controller allow method."""
        self.validate_test(self.status_controller.allow() == 'HEAD,GET')

    @mock.patch.object(status, 'error', ApiBase.mock_error)
    @mock.patch.object(status, 'request')
    def test_index(self, mock_request):
        """Test status_controller index method with errored (PUT) request."""
        mock_request.method = "PUT"
        self.status_controller.index()
        self.validate_test("The PUT method is not allowed" in ApiBase.response)

    def test_index_options(self):
        """Test status_controller index_options method."""
        self.status_controller.index_options()
        self.validate_test(status.response.status == 204)

    def test_index_head(self):
        """Test status_controller index_head method."""
        with mock.patch('valet.api.v1.controllers.status.Ostro'):
            self.status_controller.index_head()
            self.validate_test(status.response.status == 204)

    def test_index_get(self):
        """Test status_controller index_get method."""
        with mock.patch('valet.api.v1.controllers.status.Ostro'):
            self.status_controller.index_get()
            self.validate_test(status.response.status == 200)
