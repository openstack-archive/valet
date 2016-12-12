import mock
# from valet.cli.groupcli import cmd_details
import valet.cli.groupcli as grpcli
from valet.tests.base import Base
# from valet.cli.valetcli import Cli


class TestGroupcli(Base):
    ''' Unit tests for valet.valetcli '''

    def setUp(self):
        super(TestGroupcli, self).setUp()

    @mock.patch.object(grpcli, 'requests')
    def test_cmd_details(self, mock_requests):
        mock_requests.post = 'post'

        ar = mock.MagicMock()
        ar.subcmd = "create"

#         res = grpcli.cmd_details(ar)
#         print(res)
