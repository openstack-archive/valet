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

"""Api Base."""

import mock
import pecan
from valet.tests.base import Base


class ApiBase(Base):
    """Api Base Test Class, calls valet tests base."""

    def setUp(self):
        """Setup api base and mock pecan identity/music/state."""
        super(ApiBase, self).setUp()
        pecan.conf.identity = mock.MagicMock()
        pecan.conf.music = mock.MagicMock()
        self.response = None
        pecan.core.state = mock.MagicMock()

    @classmethod
    def mock_error(cls, url, msg=None, **kwargs):
        """Mock error and set response to msg."""
        cls.response = msg
