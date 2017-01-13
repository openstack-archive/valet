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

"""Test GroupCli."""

import mock
# from valet.cli.groupcli import cmd_details
import valet.cli.groupcli as grpcli
from valet.tests.base import Base
# from valet.cli.valetcli import Cli


class TestGroupcli(Base):
    """Unit tests for valet.valetcli."""

    def setUp(self):
        """Setup Test Group cli."""
        super(TestGroupcli, self).setUp()

    @mock.patch.object(grpcli, 'requests')
    def test_cmd_details(self, mock_requests):
        """Test command details, mock the requests and ar."""
        mock_requests.post = 'post'

        ar = mock.MagicMock()
        ar.subcmd = "create"
