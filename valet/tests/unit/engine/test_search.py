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

import mock
import unittest

from valet.engine.optimizer.ostro.search import Search
from valet.tests.base import Base


class TestSearch(Base):
    """Unit tests for valet.engine.optimizer.ostro.search."""

    def setUp(self):
        """Setup Test Search Class."""
        super(TestSearch, self).setUp()

        self.search = Search()

    @unittest.skip("Method was removed")
    def test_copy_resource_status(self):
        """Test Copy Resource Status."""
        self.search.copy_resource_status(mock.MagicMock())
