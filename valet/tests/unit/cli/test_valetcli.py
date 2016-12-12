import mock
from valet.cli.valetcli import Cli
from valet.tests.base import Base


class TestValetcli(Base):
    ''' Unit tests for valet.valetcli '''

    def setUp(self):
        super(TestValetcli, self).setUp()

    def test_parse(self):
        cli = Cli()
        cli.create_parser()
        argv = ['/path/to/valetcli.py', 'group', 'list']
        cli.parse(argv)

        self.validate_test(cli.args.service == 'group')

    def test_logic(self):
        cli = Cli()
        cli.submod = mock.MagicMock()
        cli.args = mock.MagicMock()
        cli.args.service = "group"
        cli.logic()

        self.validate_test(len(cli.submod.mock_calls) == 2)
        self.validate_test("call.__getitem__('group')" in str(cli.submod.mock_calls[0]))
        self.validate_test("call.__getitem__().run" in str(cli.submod.mock_calls[1]))
