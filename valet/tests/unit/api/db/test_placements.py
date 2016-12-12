'''
Created on Sep 26, 2016

@author: stack
'''

import mock
from valet.api.db.models.music import Base
from valet.api.db.models import Placement, Plan
from valet.tests.unit.api.v1.api_base import ApiBase


class TestPlacement(ApiBase):
    '''Unit tests for valet.api.v1.controllers.placements '''

    def setUp(self):
        super(TestPlacement, self).setUp()

        self.placement = self.init_Placement()

    @mock.patch.object(Base, 'insert')
    def init_Placement(self, mock_insert):
        mock_insert.return_value = None
        return Placement("test_name", "test_orchestration_id", plan=Plan("plan_name", "stack_id", _insert=False), location="test_location", _insert=False)

    def test__repr__(self):
        self.validate_test("test_name" in self.placement.__repr__())

    def test__json__(self):
        json = self.placement.__json__()

        self.validate_test(json["name"] == "test_name")
        self.validate_test(json["location"] == "test_location")
        self.validate_test(json["orchestration_id"] == "test_orchestration_id")

    def test_pk_name(self):
        self.validate_test(self.placement.pk_name() == "id")

    def test_pk_value(self):
        self.validate_test(self.placement.pk_value() is None)

    def test_values(self):
        val = self.placement.values()

        self.validate_test(val["name"] == "test_name")
        self.validate_test(val["location"] == "test_location")
        self.validate_test(val["orchestration_id"] == "test_orchestration_id")
