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

from valet_plugins.common.valet_api import requests
from valet_plugins.common.valet_api import ValetAPI
from valet_plugins.tests.base import Base


class TestValetApi(Base):

    def setUp(self):
        super(TestValetApi, self).setUp()
        self.valet_api = self.init_ValetAPI()

    @mock.patch.object(ValetAPI, "_register_opts")
    def init_ValetAPI(self, mock_api):
        mock_api.return_value = None
        return ValetAPI()

    @mock.patch.object(requests, 'request')
    def test_plans_create(self, mock_request):
        mock_request.post.return_value = None
