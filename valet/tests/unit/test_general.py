
from valet.tests.base import Base


class TestGeneral(Base):

    def setUp(self):
        super(TestGeneral, self).setUp()

    def test_general(self):
        self.validate_test(True)
