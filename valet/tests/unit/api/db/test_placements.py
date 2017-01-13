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

"""Test Placements."""

import mock
from valet.api.db.models.music import Base
from valet.api.db.models import Placement, Plan
from valet.tests.unit.api.v1.api_base import ApiBase


class TestPlacement(ApiBase):
    """Unit tests for valet.api.v1.controllers.placements."""

    def setUp(self):
        """Setup test placements and call init placement."""
        super(TestPlacement, self).setUp()

        self.placement = self.init_Placement()

    @mock.patch.object(Base, 'insert')
    def init_Placement(self, mock_insert):
        """Return init test placement object for class init."""
        mock_insert.return_value = None
        return Placement("test_name",
                         "test_orchestration_id",
                         plan=Plan("plan_name", "stack_id", _insert=False),
                         location="test_location",
                         _insert=False)

    def test__repr__(self):
        """Test name from placement repr."""
        self.validate_test("test_name" in self.placement.__repr__())

    def test__json__(self):
        """Test json return value of placement object."""
        json = self.placement.__json__()

        self.validate_test(json["name"] == "test_name")
        self.validate_test(json["location"] == "test_location")
        self.validate_test(json["orchestration_id"] == "test_orchestration_id")

    def test_pk_name(self):
        """Test placement pk name is id."""
        self.validate_test(self.placement.pk_name() == "id")

    def test_pk_value(self):
        """Test placement pk value is none."""
        self.validate_test(self.placement.pk_value() is None)

    def test_values(self):
        """Test placement values (name, location, orchestration id)."""
        val = self.placement.values()

        self.validate_test(val["name"] == "test_name")
        self.validate_test(val["location"] == "test_location")
        self.validate_test(val["orchestration_id"] == "test_orchestration_id")
