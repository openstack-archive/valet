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
import valet.api.v1.controllers.placements as placements
from valet.api.v1.controllers.placements import PlacementsController, PlacementsItemController
from valet.api.db.models.music import Query, Results
from valet.api.db.models import Placement, Plan
from valet.tests.unit.api.v1.api_base import ApiBase


class TestPlacements(ApiBase):
    """Unit tests for valet.api.v1.controllers.placements."""

    def setUp(self):
        """Setup Test Placements, call placements controller/ItemController."""
        super(TestPlacements, self).setUp()

        self.placements_controller = PlacementsController()
        self.placements_item_controller = self.init_PlacementsItemController()

    @mock.patch.object(placements, 'error', ApiBase.mock_error)
    @mock.patch.object(Query, 'filter_by')
    @mock.patch.object(placements, 'request')
    def init_PlacementsItemController(self, mock_request, mock_filter):
        """Called by Setup, return PlacementsItemController with uuid4."""
        mock_request.context = {}
        mock_filter.return_value = Results(["", "second"])
        try:
            PlacementsItemController("uuid4")
        except Exception as e:
            self.validate_test("'str' object has no attribute 'id'" in e)
        self.validate_test("Placement not found" in ApiBase.response)

        mock_filter.return_value = Results([
            Placement("test_name",
                      "test_orchestration_id",
                      plan=Plan("plan_name", "stack_id", _insert=False),
                      location="test_location",
                      _insert=False)])

        return PlacementsItemController("uuid4")

    def test_allow(self):
        """Test placements allow method with GET and GET,POST,DELETE."""
        self.validate_test(self.placements_controller.allow() == 'GET')

        self.validate_test(
            self.placements_item_controller.allow() == 'GET,POST,DELETE')

    @mock.patch.object(placements, 'error', ApiBase.mock_error)
    @mock.patch.object(placements, 'request')
    def test_index(self, mock_request):
        """Test placements index method with POST and PUT (not allowed)."""
        mock_request.method = "POST"
        self.placements_controller.index()
        self.validate_test("The POST method is not allowed" in ApiBase.response)

        mock_request.method = "PUT"
        self.placements_item_controller.index()
        self.validate_test("The PUT method is not allowed" in ApiBase.response)

    def test_index_options(self):
        """Test placements index_options method."""
        self.placements_controller.index_options()
        self.validate_test(placements.response.status == 204)

        self.placements_item_controller.index_options()
        self.validate_test(placements.response.status == 204)

    @mock.patch.object(Query, 'all')
    def test_index_get(self, mock_all):
        """Test index_get method for placements, validate based on response."""
        all_groups = ["group1", "group2", "group3"]
        mock_all.return_value = all_groups
        response = self.placements_controller.index_get()

        self.validate_test(len(response) == 1)
        self.validate_test(len(response["placements"]) == len(all_groups))
        self.validate_test(all_groups == response["placements"])

        response = self.placements_item_controller.index_get()

        self.validate_test("test_name" in response['placement'].name)
        self.validate_test("test_orchestration_id" in
                           response['placement'].orchestration_id)
        self.validate_test("plan_name" in response['placement'].plan.name)
        self.validate_test("stack_id" in response['placement'].plan.stack_id)

    @mock.patch.object(placements, 'error', ApiBase.mock_error)
    @mock.patch.object(Query, 'filter_by', mock.MagicMock)
    @mock.patch.object(placements, 'update_placements')
    def test_index_post(self, mock_plcment):
        """Test index_post for placements, validate from response status."""
        kwargs = {'resource_id': "resource_id", 'locations': ["test_location"]}
        self.placements_item_controller.index_post(**kwargs)
        self.validate_test(placements.response.status == 201)

        with mock.patch('valet.api.v1.controllers.placements.Ostro') \
                as mock_ostro:
            kwargs = {'resource_id': "resource_id", 'locations': [""]}
            self.placements_item_controller.index_post(**kwargs)
            self.validate_test("Ostro error:" in ApiBase.response)

            mock_plcment.return_value = None

            status_type = mock.MagicMock()
            status_type.response = {"status": {"type": "ok"},
                                    "resources": {"iterkeys": []}}
            mock_ostro.return_value = status_type

            self.placements_item_controller.index_post(**kwargs)
            self.validate_test(placements.response.status == 201)

    def test_index_delete(self):
        """Test placements_item_controller index_delete method."""
        self.placements_item_controller.index_delete()
        self.validate_test(placements.response.status == 204)
