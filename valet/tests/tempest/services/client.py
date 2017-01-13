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

"""Client."""

import json

from tempest_lib.common import rest_client


class ValetClient(rest_client.RestClient):
    """Tempest REST client for Valet.

    Implements
    1. create, delete, update, list and show groups
    2. add, verify, delete and delete all members
    3. create, update and delete plan
    """

    def _resp_helper(self, resp, body=None):
        if body:
            body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_groups(self):
        """List all groups."""
        resp, body = self.get('/groups')
        self.expected_success(200, resp.status)
        return self._resp_helper(resp, body)

    def create_group(self, name, group_type, description):
        """Create group with name, type and description."""
        params = {
            "name": name,
            "type": group_type,
            "description": description,
        }
        req_body = json.dumps(params)
        resp, body = self.post('/groups', req_body)
        self.expected_success(201, resp.status)
        return self._resp_helper(resp, body)

    def delete_group(self, group_id):
        """Delete group with id."""
        resp, body = self.delete('/groups/%s' % str(group_id))
        self.expected_success(204, resp.status)
        return self._resp_helper(resp, body)

    def update_group(self, group_id, description):
        """Update group description param for group with matching id."""
        params = {
            'description': description
        }
        req_body = json.dumps(params)
        resp, body = self.put('/groups/%s' % group_id, req_body)
        self.expected_success(201, resp.status)
        return self._resp_helper(resp, body)

    def show_group(self, group_id):
        """Show group corresponding to passed in id."""
        resp, body = self.get('/groups/%s' % group_id)
        self.expected_success(200, resp.status)
        return self._resp_helper(resp, body)

    def add_members(self, group_id, members):
        """Add members to corresponding group (group_id)."""
        params = {
            "members": members
        }
        data = json.dumps(params)
        resp, body = self.put('/groups/%s/members' % (str(group_id)), data)
        self.expected_success(201, resp.status)
        return self._resp_helper(resp, body)

    def verify_membership(self, group_id, member_id):
        """Verify member (member_id) is part of group (group_id)."""
        resp, body = self.get('/groups/%s/members/%s' % (str(group_id),
                                                         str(member_id)))
        self.expected_success(204, resp.status)
        return self._resp_helper(resp, body)

    def delete_member(self, group_id, member_id):
        """Delete single member (member_id) of a group (group_id)."""
        resp, body = self.delete('/groups/%s/members/%s' % (str(group_id),
                                                            str(member_id)))
        self.expected_success(204, resp.status)
        return self._resp_helper(resp, body)

    def delete_all_members(self, group_id):
        """Delete all members of group."""
        resp, body = self.delete('/groups/%s/members' % (str(group_id)))
        self.expected_success(204, resp.status)
        return self._resp_helper(resp, body)

    def create_plan(self, plan_name, resources, stack_id):
        """Create plan with name, resources and stack id."""
        params = {
            "plan_name": plan_name,
            "stack_id": stack_id,
            "resources": resources
        }
        data = json.dumps(params)
        resp, body = self.post('/plans', data)
        self.expected_success(201, resp.status)
        return self._resp_helper(resp, body)

    def update_plan(self, plan_id, action, excluded_hosts, resources):
        """Update action, excluded hosts and resources of plan with id."""
        params = {
            "action": action,
            "excluded_hosts": excluded_hosts,
            "resources": resources
        }
        data = json.dumps(params)
        resp, body = self.put('/plans/%s' % (str(plan_id)), data)
        self.expected_success(201, resp.status)
        return self._resp_helper(resp, body)

    def delete_plan(self, plan_id):
        """Delete plan with matching id."""
        resp, body = self.delete('/plans/%s' % (str(plan_id)))
        self.expected_success(204, resp.status)
        return self._resp_helper(resp, body)
