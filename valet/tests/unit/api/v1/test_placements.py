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

from valet.api.common import ostro_helper
from valet.api.db.models.music.plans import Plan
from valet.api.db.models.music import Query
from valet.api.db.models.music import Results
import valet.api.v1.controllers.placements as placements
from valet.api.v1.controllers.placements import Placement
from valet.api.v1.controllers.placements import PlacementsController
from valet.api.v1.controllers.placements import PlacementsItemController
from valet.tests.unit.api.v1.api_base import ApiBase


def fake_filter_by(self, **kwargs):
    """Fake filter for Music queries.

    FIXME(jdandrea): Find a way to get rid of this. It's here
    in order to get some of the tests working, but there ought
    to be a better way that doesn't introduce more surface area.
    """
    if 'id' in kwargs:
        return Results([Plan("plan_name", "stack_id", _insert=False)])
    elif 'plan_id' in kwargs:
        # FIXME(jdandrea) this is duplicated in
        # init_PlacementsItemController (and there shouldn't be a
        # separate init; that pattern blurs/confuses things IMO)
        return Results([
            Placement("placement_name", "test_orchestration_id",
                      plan=Plan("plan_name", "stack_id", _insert=False),
                      location="test_location", _insert=False)])
    else:
        return Results([])


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
        self.validate_test(
            "The POST method is not allowed" in ApiBase.response)

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

    @mock.patch.object(ostro_helper, '_log')
    @mock.patch.object(ostro_helper.Ostro, '_send')
    @mock.patch.object(Query, 'filter_by')
    def test_index_post_with_locations(self, mock_filter,
                                       mock_send, mock_logging):
        kwargs = {'resource_id': "resource_id", 'locations': ["test_location"]}
        mock_filter.return_value = Results([
            Plan("plan_name", "stack_id", _insert=False)])
        mock_send.return_value = '{"status":{"type":"ok"}}'
        self.placements_item_controller.index_post(**kwargs)
        self.validate_test(placements.response.status == 201)

    @mock.patch('valet.api.db.models.music.Query.filter_by',
                fake_filter_by)
    @mock.patch.object(placements, 'error', ApiBase.mock_error)
    @mock.patch.object(ostro_helper, '_log')
    @mock.patch.object(ostro_helper.Ostro, '_send')
    def test_index_post_with_engine_error(self, mock_send, mock_logging):
        kwargs = {'resource_id': "resource_id", 'locations': [""]}
        mock_send.return_value = \
            '{"status":{"type":"error","message":"error"},' \
            '"resources":{"iterkeys":[]}}'
        self.placements_item_controller.index_post(**kwargs)
        self.validate_test("Ostro error:" in ApiBase.response)

    @mock.patch('valet.api.db.models.music.Query.filter_by',
                fake_filter_by)
    @mock.patch.object(ostro_helper, '_log')
    @mock.patch.object(ostro_helper.Ostro, '_send')
    @mock.patch.object(placements, 'update_placements')
    def test_index_post_with_placement_update(self, mock_update,
                                              mock_send, mock_logging):
        kwargs = {'resource_id': "resource_id", 'locations': [""]}
        mock_update.return_value = None

        # FIXME(jdandrea): Why was "iterkeys" used here as a resource??
        # That's a Python iterator reference, not a reasonable resource key.
        mock_send.return_value = \
            '{"status":{"type":"ok"},"resources":{"iterkeys":[]}}'

        self.placements_item_controller.index_post(**kwargs)
        self.validate_test(placements.response.status == 201)

    def test_index_delete(self):
        """Test placements_item_controller index_delete method."""
        self.placements_item_controller.index_delete()
        self.validate_test(placements.response.status == 204)
