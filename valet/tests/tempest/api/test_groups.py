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

from tempest.common.utils import data_utils
from tempest import test

from valet.tests.tempest.api import base


class ValetGroupsTest(base.BaseValetTest):
    """Here we test the basic group operations of Valet Groups."""

    @classmethod
    def setup_clients(cls):
        """Setup Valet client for Groups Test."""
        super(ValetGroupsTest, cls).setup_clients()
        cls.client = cls.valet_client

    @test.idempotent_id('b2655098-5a0d-11e6-9efd-525400af9658')
    def test_list_groups(self):
        """List groups using client assert no groups missing to verify."""
        group_ids = list()
        fetched_ids = list()

        for _ in range(3):
            group_name = data_utils.rand_name('group')
            description = data_utils.rand_name('Description')
            group = self.client.create_group(
                name=group_name, group_type='exclusivity',
                description=description)
            self.addCleanup(self.client.delete_group, group['id'])
            group_ids.append(group['id'])

        # List and Verify Groups
        body = self.client.list_groups()['groups']

        for group in body:
            fetched_ids.append(group['id'])
        missing_groups = [g for g in group_ids if g not in fetched_ids]

        self.assertEqual([], missing_groups)

    @test.idempotent_id('2ab0337e-6472-11e6-b6c6-080027824017')
    def test_create_group(self):
        """Test created group by checking details equal to group details."""
        group_name = data_utils.rand_name('group')
        description = data_utils.rand_name('Description')
        group = self.client.create_group(
            name=group_name, group_type='exclusivity',
            description=description)
        self.addCleanup(self.client.delete_group, group['id'])

        self.assertIn('id', group)
        self.assertIn('name', group)
        self.assertEqual(group_name, group['name'])
        self.assertIn('type', group)
        self.assertIn('description', group)

    @test.idempotent_id('35f0aa20-6472-11e6-b6c6-080027824017')
    def test_delete_group(self):
        """Client Delete group with id, check group with id not in groups."""
        # Create group
        group_name = data_utils.rand_name('group')
        description = data_utils.rand_name('Description')
        body = self.client.create_group(
            name=group_name, group_type='exclusivity',
            description=description)

        group_id = body.get('id')

        # Delete Group
        self.client.delete_group(group_id)

        # List and verify group doesn't exist
        groups = self.client.list_groups()['groups']
        groups_id = [group['id'] for group in groups]

        self.assertNotIn(group_id, groups_id)

    @test.attr(type='smoke')
    @test.idempotent_id('460d86e4-6472-11e6-b6c6-080027824017')
    def test_update_group(self):
        """Client Update group with id, using a new description."""
        # Create group
        group_name = data_utils.rand_name('group')
        description = data_utils.rand_name('Description')
        group = self.client.create_group(
            name=group_name, group_type='exclusivity',
            description=description)

        self.addCleanup(self.client.delete_group, group['id'])

        group_id = group.get('id')

        new_desc = data_utils.rand_name('UpdateDescription')
        updated_group = self.client.update_group(
            group_id, new_desc)

        self.assertEqual(updated_group['description'], new_desc)

    @test.idempotent_id('4f660e50-6472-11e6-b6c6-080027824017')
    def test_show_group(self):
        """Test client show group by checking values against group_details."""
        # Create group
        group_name = data_utils.rand_name('group')
        description = data_utils.rand_name('Description')
        group = self.client.create_group(
            name=group_name, group_type='exclusivity',
            description=description)

        self.addCleanup(self.client.delete_group, group['id'])

        group_id = group.get('id')

        group_details = self.client.show_group(group_id)['group']

        self.assertIn('id', group_details)
        self.assertIn('name', group_details)
        self.assertEqual(group_name, group_details['name'])
        self.assertIn('type', group_details)
        self.assertIn('description', group_details)
        self.assertIn('members', group_details)
