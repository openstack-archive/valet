import mock
import valet.engine.optimizer.ostro_server.health_checker as ping
from valet.engine.optimizer.ostro_server.health_checker import HealthCheck
from valet.tests.base import Base

json = r'{"row 0":{"placement": "{\"status\": {\"message\": \"ping\", \"type\": \"ok\"},' \
       r'\"resources\": {\"ip\": \"localhost\", \"id\": %d}}","stack_id":"%s"}}'


class TestHealthCheck(Base):

    def setUp(self):
        super(TestHealthCheck, self).setUp()
        ping.CONF = mock.MagicMock()
        ping.REST = mock.MagicMock()
        self.pingger = HealthCheck()

    @mock.patch.object(HealthCheck, '_send')
    @mock.patch.object(HealthCheck, '_read_response')
    def test_ping(self, mock_read, mock_send):
        mock_send.return_value = True
        mock_read.return_value = True

        self.validate_test(self.pingger.ping() == 1)

    @mock.patch.object(HealthCheck, '_send')
    @mock.patch.object(HealthCheck, '_read_response')
    def test_ping_unhappy(self, mock_read, mock_send):
        mock_send.return_value = False
        mock_read.return_value = True

        self.validate_test(self.pingger.ping() is None)

    @mock.patch.object(HealthCheck, '_send')
    @mock.patch.object(HealthCheck, '_read_response')
    def test_ping_unhappy_2(self, mock_read, mock_send):
        mock_send.return_value = True
        mock_read.return_value = False

        self.validate_test(not self.pingger.ping())

    def test_send(self):
        self.pingger.rest.request.return_value.status_code = 204
        self.validate_test(self.pingger._send())

    def test_send_unhappy(self):
        self.pingger.rest.request.return_value.status_code = 200
        self.validate_test(not self.pingger._send())

    def test_read_response(self):
        mid = 1
        self.pingger.rest.request.return_value.status_code = 200
        self.pingger.rest.request.return_value.text = json % (mid, self.pingger.uuid)
        self.validate_test(self.pingger._read_response())

    def test_read_response_from_other_engine(self):
        my_id = 1
        self.pingger.rest.request.return_value.status_code = 200
        self.pingger.rest.request.return_value.text = json % (my_id, self.pingger.uuid)
        self.validate_test(not self.pingger._read_response() == 2)

    def test_read_response_unhappy_wrong_res_code(self):
        self.pingger.rest.request.return_value.status_code = 204
        self.pingger.rest.request.return_value.text = self.pingger.uuid
        self.validate_test(not self.pingger._read_response())

    def test_read_response_unhappy_wrong_body(self):
        self.pingger.rest.request.return_value.status_code = 200
        self.pingger.rest.request.return_value.text = ""
        self.validate_test(not self.pingger._read_response())

    def test_read_response_unhappy_wrong_both(self):
        self.pingger.rest.request.return_value.status_code = 204
        self.pingger.rest.request.return_value.text = ""
        self.validate_test(not self.pingger._read_response())
