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

"""Test Plans."""

from uuid import uuid4

from valet.api.db.models import Plan, Placement
from valet.tests.api.controllers import is_valid_uuid4

# TODO(JD): Add Keystone mock object.
STACK_ID = 'e624474b-fc80-4053-ab5f-45cc1030e692'
PLAN_NAME = 'ihaveaplan'


class TestPlansController(object):
    """Test Plans Controller Class."""

    def test_get_index_no_plans(self, session):
        """Test getting plans where there are none, should be empty."""
        result = session.app.get('/v1/plans/')
        assert result.status_int == 200
        assert result.json == []

    def test_get_index_a_plan(self, session):
        """Test get a plan using an index, should get a plan name."""
        Plan(PLAN_NAME, STACK_ID)
        session.commit()
        result = session.app.get('/v1/plans/').json
        assert result == [PLAN_NAME]

    def test_single_plan_should_have_one_item(self, session):
        """Test getting a single plan with one item."""
        Plan(PLAN_NAME, STACK_ID)
        session.commit()
        result = session.app.get('/v1/plans/')
        assert result.status_int == 200
        assert len(result.json) == 1

    def test_list_a_few_plans(self, session):
        """Test returning a list of plans."""
        for plan_number in range(20):
            stack_id = str(uuid4())
            Plan('foo_%s' % plan_number, stack_id)
        session.commit()

        result = session.app.get('/v1/plans/')
        json = result.json
        assert result.status_int == 200
        assert len(json) == 20


class TestPlansItemController(object):
    """Test Plans Item Controller Class."""

    def test_get_index_single_plan(self, session):
        """Test get index of a single plan."""
        Plan(PLAN_NAME, STACK_ID)
        session.commit()
        result = session.app.get('/v1/plans/%s/' % STACK_ID)
        assert result.status_int == 200

    def test_get_index_no_plan(self, session):
        """Test getting index of no plan, should return 404."""
        result = session.app.get('/v1/plans/%s/' % STACK_ID,
                                 expect_errors=True)
        assert result.status_int == 404

    def test_get_index_single_plan_data(self, session):
        """Test getting a single plan data."""
        Plan(PLAN_NAME, STACK_ID)
        session.commit()
        result = session.app.get('/v1/plans/%s/' % STACK_ID)
        json = result.json
        assert is_valid_uuid4(json['id'])
        assert json['name'] == PLAN_NAME
        assert json['placements'] == {}
        assert json['stack_id'] == STACK_ID

    def test_get_plan_refs(self, session):
        """Test get plan refs by getting app json result."""
        plan = Plan(PLAN_NAME, STACK_ID)
        Placement(
            'placement_1', str(uuid4()),
            plan=plan,
            location='foo_1'
        )
        Placement(
            'placement_2', str(uuid4()),
            plan=plan,
            location='foo_2'
        )
        session.commit()
        result = session.app.get('/v1/plans/%s/' % STACK_ID)
        json = result.json
        assert is_valid_uuid4(json['id'])
        assert json['name'] == PLAN_NAME
        assert json['stack_id'] == STACK_ID
        assert len(json['placements']) == 2
