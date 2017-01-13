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

"""Test Groups."""

import mock
from valet.api.db.models.music import Base
from valet.api.db.models.music.groups import Group
from valet.tests.unit.api.v1.api_base import ApiBase


class TestGroups(ApiBase):
    """Unit tests for valet.api.v1.controllers.placements."""

    def setUp(self):
        """Setup Test Groups by calling super setup and init."""
        super(TestGroups, self).setUp()

        self.group = self.init_group()

    @mock.patch.object(Base, 'insert')
    def init_group(self, mock_insert):
        """Init a test group object and return."""
        mock_insert.return_value = None
        members = ["me", "you"]
        return Group("test_name", "test_description", "test_type", members)

    def test__repr__(self):
        """Validate test name in group repr."""
        self.validate_test("test_name" in self.group.__repr__())

    def test__json__(self):
        """Test json of a group object."""
        json = self.group.__json__()

        self.validate_test(json["name"] == "test_name")
        self.validate_test(json["type"] == "test_type")
        self.validate_test(json["description"] == "test_description")

    def test_pk_name(self):
        """Test pk name of a group object."""
        self.validate_test(self.group.pk_name() == "id")

    def test_pk_value(self):
        """Test pk value of a group object."""
        self.validate_test(self.group.pk_value() is None)

    def test_values(self):
        """Test values (name, type, description) of a group object."""
        val = self.group.values()

        self.validate_test(val["name"] == "test_name")
        self.validate_test(val["type"] == "test_type")
        self.validate_test(val["description"] == "test_description")
