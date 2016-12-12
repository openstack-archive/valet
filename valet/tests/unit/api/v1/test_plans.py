'''
Created on Sep 25, 2016

@author: stack
'''

import mock
import valet.api.v1.controllers.plans as plans
from valet.api.v1.controllers.plans import PlansController, PlansItemController
from valet.api.db.models.music import Query, Results
from valet.api.db.models import Plan
from valet.tests.unit.api.v1.api_base import ApiBase


class TestPlans(ApiBase):
    '''Unit tests for valet.api.v1.controllers.placements '''

    def setUp(self):
        super(TestPlans, self).setUp()

        self.plans_controller = PlansController()
        self.plans_item_controller = self.init_PlansItemController()

    @mock.patch.object(plans, 'error', ApiBase.mock_error)
    @mock.patch.object(Query, 'filter_by')
    @mock.patch.object(plans, 'request')
    def init_PlansItemController(self, mock_request, mock_filter):
        mock_request.context = {}
        mock_filter.return_value = Results(["", "second"])
        try:
            PlansItemController("uuid4")
        except Exception as e:
            self.validate_test("'str' object has no attribute 'id'" in e)
        self.validate_test("Plan not found" in ApiBase.response)

        mock_filter.return_value = Results([Plan("test_name", "stack_id", _insert=False)])

        return PlansItemController("uuid4")

    def test_allow(self):
        self.validate_test(self.plans_controller.allow() == 'GET,POST')

        self.validate_test(self.plans_item_controller.allow() == 'GET,PUT,DELETE')

    @mock.patch.object(plans, 'error', ApiBase.mock_error)
    @mock.patch.object(plans, 'request')
    def test_index(self, mock_request):
        mock_request.method = "PUT"
        self.plans_controller.index()
        self.validate_test("The PUT method is not allowed" in ApiBase.response)

        mock_request.method = "POST"
        self.plans_item_controller.index()
        self.validate_test("The POST method is not allowed" in ApiBase.response)

    def test_index_options(self):
        self.plans_controller.index_options()
        self.validate_test(plans.response.status == 204)

        self.plans_item_controller.index_options()
        self.validate_test(plans.response.status == 204)

    @mock.patch.object(Query, 'all')
    def test_index_get(self, mock_all):
        all_groups = ["group1", "group2", "group3"]
        mock_all.return_value = all_groups
        response = self.plans_controller.index_get()

        self.validate_test(len(response) == 1)
        self.validate_test(len(response["plans"]) == len(all_groups))
        self.validate_test(all_groups == response["plans"])

        response = self.plans_item_controller.index_get()

        self.validate_test(len(response) == 1)
        self.validate_test(response["plan"].name == "test_name")

    @mock.patch.object(plans, 'error', ApiBase.mock_error)
    def test_index_post(self):
        with mock.patch('valet.api.v1.controllers.plans.Ostro'):
            self.plans_controller.index_post()
            self.validate_test("Ostro error:" in ApiBase.response)

    @mock.patch.object(plans, 'error', ApiBase.mock_error)
    @mock.patch.object(Query, 'filter_by', mock.MagicMock)
    def test_index_put(self):
        kwargs = {'action': "migrate", 'excluded_hosts': [], "resources": ["ggg", "fff"]}

        with mock.patch('valet.api.v1.controllers.plans.Ostro'):
            self.plans_item_controller.index_put(**kwargs)
            self.validate_test("Ostro error:" in ApiBase.response)

# TODO(YB): test_index_post, test_index_put needs to be written again
