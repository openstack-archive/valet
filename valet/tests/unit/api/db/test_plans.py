'''
Created on Sep 26, 2016

@author: stack
'''

from valet.api.db.models import Plan
from valet.tests.unit.api.v1.api_base import ApiBase


class TestPlans(ApiBase):
    '''Unit tests for valet.api.v1.controllers.placements '''

    def setUp(self):
        super(TestPlans, self).setUp()

        self.plan = self.init_Plan()

    def init_Plan(self):
        return Plan("test_name", "test_stack_id", _insert=False)

    def test__repr__(self):
        self.validate_test("test_name" in self.plan.__repr__())

    def test__json__(self):
        json = self.plan.__json__()

        self.validate_test(json["name"] == "test_name")
        self.validate_test(json["stack_id"] == "test_stack_id")

    def test_pk_name(self):
        self.validate_test(self.plan.pk_name() == "id")

    def test_pk_value(self):
        self.validate_test(self.plan.pk_value() is None)

    def test_values(self):
        val = self.plan.values()

        self.validate_test(val["name"] == "test_name")
        self.validate_test(val["stack_id"] == "test_stack_id")
