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

from valet.api.db.models.music.ostro import PlacementRequest, PlacementResult, Event
from valet.tests.unit.api.v1.api_base import ApiBase


class TestOstro(ApiBase):
    '''Unit tests for valet.api.v1.controllers.placements '''

    def setUp(self):
        super(TestOstro, self).setUp()

        self.placement_request = self.init_PlacementRequest()

        self.placement_result = self.init_PlacementResult()

        self.event = self.init_Event()

    def init_PlacementRequest(self):
        return PlacementRequest("test_request", "test_stack_id", False)

    def init_PlacementResult(self):
        return PlacementResult("test_placement", "test_stack_id", False)

    def init_Event(self):
        return Event("test_event", "test_event_id", False)

    def test__repr__(self):
        self.validate_test("test_stack_id" in self.placement_request.__repr__())

        self.validate_test("test_stack_id" in self.placement_result.__repr__())

        self.validate_test("test_event_id" in self.event.__repr__())

    def test__json__(self):
        request_json = self.placement_request.__json__()

        self.validate_test(request_json["request"] == "test_request")
        self.validate_test(request_json["stack_id"] == "test_stack_id")

        result_json = self.placement_result.__json__()

        self.validate_test(result_json["placement"] == "test_placement")
        self.validate_test(result_json["stack_id"] == "test_stack_id")

        event_json = self.event.__json__()

        self.validate_test(event_json["event_id"] == "test_event_id")
        self.validate_test(event_json["event"] == "test_event")

    def test_pk_name(self):
        self.validate_test(self.placement_request.pk_name() == "stack_id")

        self.validate_test(self.placement_result.pk_name() == "stack_id")

        self.validate_test(self.event.pk_name() == "event_id")

    def test_pk_value(self):
        self.validate_test(self.placement_request.pk_value() == "test_stack_id")

        self.validate_test(self.placement_result.pk_value() == "test_stack_id")

        self.validate_test(self.event.pk_value() == "test_event_id")

    def test_values(self):
        request_val = self.placement_request.values()

        self.validate_test(request_val["request"] == "test_request")
        self.validate_test(request_val["stack_id"] == "test_stack_id")

        result_val = self.placement_result.values()

        self.validate_test(result_val["placement"] == "test_placement")
        self.validate_test(result_val["stack_id"] == "test_stack_id")

        event_val = self.event.values()

        self.validate_test(event_val["event"] == "test_event")
        self.validate_test(event_val["event_id"] == "test_event_id")

    def test_schema(self):
        request_schema = self.placement_request.schema()

        self.validate_test(request_schema["request"] == "text")
        self.validate_test(request_schema["stack_id"] == "text")

        result_schema = self.placement_result.schema()

        self.validate_test(result_schema["placement"] == "text")
        self.validate_test(result_schema["stack_id"] == "text")

        event_schema = self.event.schema()

        self.validate_test(event_schema["event"] == "text")
        self.validate_test(event_schema["event_id"] == "text")
