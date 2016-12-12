# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
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
