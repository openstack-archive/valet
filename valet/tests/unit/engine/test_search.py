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
