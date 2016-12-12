'''
Created on Sep 26, 2016

@author: stack
'''

import logging
import mock
from valet.engine.optimizer.ostro.search import Search
from valet.tests.base import Base

LOG = logging.getLogger(__name__)


class TestSearch(Base):

    def setUp(self):
        super(TestSearch, self).setUp()

        self.search = Search(LOG)

    def test_copy_resource_status(self):
        self.search.copy_resource_status(mock.MagicMock())

#     def test_place_nodes(self):
