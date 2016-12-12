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
Created on Sep 25, 2016

@author: stack
'''

import mock
import pecan
from valet.tests.base import Base


class ApiBase(Base):

    def setUp(self):
        super(ApiBase, self).setUp()
        pecan.conf.identity = mock.MagicMock()
        pecan.conf.music = mock.MagicMock()
        self.response = None
        pecan.core.state = mock.MagicMock()

    @classmethod
    def mock_error(cls, url, msg=None, **kwargs):
        cls.response = msg
