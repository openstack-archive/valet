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
