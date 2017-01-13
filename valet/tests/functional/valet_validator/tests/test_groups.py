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

from valet.tests.functional.valet_validator.common.auth import Auth
from valet.tests.functional.valet_validator.common import GeneralLogger
from valet.tests.functional.valet_validator.group_api.valet_group import ValetGroup
from valet.tests.functional.valet_validator.tests.functional_base import FunctionalTestCase


class TestGroups(FunctionalTestCase):
    """Test valet groups functional."""

    def setUp(self):
        """Add configuration and logging mechanism."""
        super(TestGroups, self).setUp()
        self.groups = ValetGroup()
        self.group_name = "test_group"
        self.group_type = "exclusivity"

    def test_groups(self):
        """Test groups using multiple methods and checking response codes."""
        GeneralLogger.log_group("Delete all stacks")
        self.load.delete_all_stacks()

        GeneralLogger.log_group("Delete all members and groups")

        respose_code = self.groups.delete_all_groups()
        self.assertEqual(204, respose_code,
                         "delete_all_groups failed with code %s"
                         % respose_code)

        self.assertEqual([], self.groups.get_list_groups(),
                         "delete_all_groups failed")

        GeneralLogger.log_group("Try to delete not existing group")
        response = self.groups.delete_group(
            "d68f62b1-4758-4ea5-a93a-8f9d9c0ae912")
        self.assertEqual(404, response.status_code,
                         "delete_group failed with code %s"
                         % response.status_code)

        GeneralLogger.log_group("Create test_group")
        group_info = self.groups.create_group(self.group_name, self.group_type)
        self.assertEqual(201, group_info.status_code,
                         "create_group failed with code %s"
                         % group_info.status_code)

        grp_id = group_info.json()["id"]

        GeneralLogger.log_group("Return list of groups")
        GeneralLogger.log_group(str(self.groups.get_list_groups()))

        GeneralLogger.log_group("Create test member (NOT tenant ID)")
        member_respone = self.groups.update_group_members(grp_id,
                                                          members="test_member")
        self.assertEqual(409, member_respone.status_code,
                         "update_group_members failed with code %s"
                         % member_respone.status_code)

        GeneralLogger.log_group("Add description to group")
        desc_response = self.groups.update_group(grp_id, "new_description")
        self.assertEqual(201, desc_response.status_code,
                         "update_group failed with code %s"
                         % desc_response.status_code)

        GeneralLogger.log_group("Create member (tenant ID)")
        member_respone = self.groups.update_group_members(grp_id)
        self.assertEqual(201, member_respone.status_code,
                         "update_group_members failed with code %s"
                         % member_respone.status_code)

        GeneralLogger.log_group("Return list of groups")
        GeneralLogger.log_group(self.groups.get_group_details(grp_id).json())

        GeneralLogger.log_group("Delete test member (NOT tenant ID)")
        member_respone = self.groups.delete_group_member(grp_id, "test_member")
        self.assertEqual(404, member_respone.status_code,
                         "delete_group_member failed with code %s"
                         % member_respone.status_code)

        GeneralLogger.log_group("Delete member (tenant ID)")
        member_respone = self.groups.delete_group_member(grp_id,
                                                         Auth.get_project_id())
        self.assertEqual(204, member_respone.status_code,
                         "delete_group_member failed with code %s"
                         % member_respone.status_code)

        GeneralLogger.log_group("Return list of groups")
        GeneralLogger.log_group(self.groups.get_group_details(grp_id).json())

    def get_name(self):
        """Return name."""
        return __name__
