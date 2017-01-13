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

"""Test Valetcli."""

import mock
from valet.cli.valetcli import Cli
from valet.tests.base import Base


class TestValetcli(Base):
    """Unit tests for valet.valetcli."""

    def setUp(self):
        """Setup TestValetCli class."""
        super(TestValetcli, self).setUp()

    def test_parse(self):
        """Create cli parser and validate by parsing test args."""
        cli = Cli()
        cli.create_parser()
        argv = ['/path/to/valetcli.py', 'group', 'list']
        cli.parse(argv)

        self.validate_test(cli.args.service == 'group')

    def test_logic(self):
        """Test cli logic methods getitem and getitem.run."""
        cli = Cli()
        cli.submod = mock.MagicMock()
        cli.args = mock.MagicMock()
        cli.args.service = "group"
        cli.logic()

        self.validate_test(len(cli.submod.mock_calls) == 2)
        self.validate_test("call.__getitem__('group')" in
                           str(cli.submod.mock_calls[0]))
        self.validate_test("call.__getitem__().run" in
                           str(cli.submod.mock_calls[1]))
