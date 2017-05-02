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

from tempest import config
from tempest import test

from valet.tests.tempest.scenario.scenario_base import ScenarioTestCase

CONF = config.CONF


class TestStackUpdatesNonValet(ScenarioTestCase):

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e001')
    def test_updates_no_groups_upd_desc(self):
        # Update the stack description in the template
        stack_id, stack_name = self.create_stack(
            "test_updates_no_groups_upd_desc",
            "/templates/no_groups_2_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/no_groups_2_instances_upd_desc.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e002')
    def test_updates_no_groups_upd_flavor(self):
        # Update the flavor of one of the servers (tiny->small)
        stack_id, stack_name = self.create_stack(
            "test_updates_no_groups_upd_flavor",
            "/templates/no_groups_2_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/no_groups_2_instances_upd_flavor.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e003')
    def test_updates_no_groups_add_server(self):
        # Add a server to the template
        stack_id, stack_name = self.create_stack(
            "test_updates_no_groups_add_server",
            "/templates/no_groups_2_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/no_groups_2_instances_add_server.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e004')
    def test_updates_no_groups_remove_server(self):
        # Remove a server from the template
        stack_id, stack_name = self.create_stack(
            "test_updates_no_groups_remove_server",
            "/templates/no_groups_2_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/no_groups_2_instances_remove_server.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e005')
    def test_updates_nova_group_remove_server(self):
        # Remove a server from an existing Nova Server group
        stack_id, stack_name = self.create_stack(
            "test_updates_nova_group_remove_server",
            "/templates/nova_group_2_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/nova_group_1_instance.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e006')
    def test_updates_nova_group_add_server(self):
        # Add a server to an existing Nova Server group
        stack_id, stack_name = self.create_stack(
            "test_updates_nova_group_add_server",
            "/templates/nova_group_1_instance.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/nova_group_2_instances.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e007')
    def test_updates_nova_group_upd_flavor(self):
        # Update the flavor of a server in a Nova Server group
        stack_id, stack_name = self.create_stack(
            "test_updates_nova_group_upd_flavor",
            "/templates/nova_group_2_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/nova_group_2_instances_upd_flavor.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e008')
    def test_updates_nova_group_add_group(self):
        # Add a new Nova Server group
        stack_id, stack_name = self.create_stack(
            "test_updates_nova_group_add_group",
            "/templates/nova_group_2_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/nova_group_2_instances_2_groups.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e009')
    def test_updates_nova_group_remove_group(self):
        # Remove a Nova Server group
        stack_id, stack_name = self.create_stack(
            "test_updates_nova_group_remove_group",
            "/templates/nova_group_2_instances_2_groups.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/nova_group_2_instances.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e00a')
    def test_updates_nova_group_upd_group_policy(self):
        # Change the group policy of a Nova Server group (affinity ->
        # anti-affinity)
        stack_id, stack_name = self.create_stack(
            "test_updates_nova_group_upd_group_policy",
            "/templates/nova_group_2_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/nova_group_2_instances_antiaffinity.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e00b')
    def test_updates_nova_group_move_server(self):
        # Move a server from one Nova Server group to another
        stack_id, stack_name = self.create_stack(
            "test_updates_nova_group_move_server",
            "/templates/nova_group_2_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/nova_group_1_instance_2_groups.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e00c')
    def test_updates_nova_group_remove_group_assignment(self):
        # Remove the Nova Server group assignment from the existing servers
        stack_id, stack_name = self.create_stack(
            "test_updates_nova_group_remove_group_assignment",
            "/templates/nova_group_2_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/no_groups_2_instances.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e00d')
    def test_updates_multiple_resources_upd_security_rule(self):
        # Change the security rules for one of the networks
        stack_id, stack_name = self.create_stack(
            "test_updates_multiple_resources_upd_security_rule",
            "/templates/multiple_resource_types.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/multiple_resource_types_upd_secrule.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e00e')
    def test_updates_multiple_resources_remove_network(self):
        # Remove the network, and the associated ports for both servers
        stack_id, stack_name = self.create_stack(
            "test_updates_multiple_resources_remove_network",
            "/templates/multiple_resource_types.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/"
                          "multiple_resource_types_remove_network.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e00f')
    def test_updates_nested_upd_desc(self):
        # Update the stack description on both inner and outer templates
        stack_id, stack_name = self.create_stack(
            "test_updates_nested_upd_desc",
            "/templates/nested_total_2_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/nested_total_2_instances_upd_desc.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e010')
    def test_updates_nested_upd_flavor(self):
        # Update the flavor of the inner template
        stack_id, stack_name = self.create_stack(
            "test_updates_nested_upd_flavor",
            "/templates/nested_total_2_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/nested_total_2_instances_upd_flavor.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e011')
    def test_updates_nested_add_server(self):
        # Add a server to the inner template
        stack_id, stack_name = self.create_stack(
            "test_updates_nested_add_server",
            "/templates/nested_total_2_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/nested_total_3_instances.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e012')
    def test_updates_nested_remove_server(self):
        # Remove a server from the inner template
        stack_id, stack_name = self.create_stack(
            "test_updates_nested_remove_server",
            "/templates/nested_total_3_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/nested_total_2_instances.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e013')
    def test_updates_nested_increase_inner_instance_count(self):
        # Increase the count of inner template instances in the outer template.
        stack_id, stack_name = self.create_stack(
            "test_updates_nested_increase_inner_instance_count",
            "/templates/nested_total_2_instances.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/"
                          "nested_total_3_instances_count_increase.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e014')
    def test_updates_nested_decrease_inner_instance_count(self):
        # Decrease the count of inner template instances in the outer template.
        stack_id, stack_name = self.create_stack(
            "test_updates_nested_decrease_inner_instance_count",
            "/templates/nested_total_3_instances_count_increase.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/nested_total_2_instances.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e015')
    def test_updates_nested_nova_group_upd_flavor(self):
        # Update the flavor of the nova server inside the inner template
        stack_id, stack_name = self.create_stack(
            "test_updates_nested_nova_group_upd_flavor",
            "/templates/nested_total_2_instances_nova_group.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/"
                          "nested_total_2_instances_nova_group_upd_flavor.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e016')
    def test_updates_nested_nova_group_add_server(self):
        # Add a nova server to the nova group inside the inner template
        stack_id, stack_name = self.create_stack(
            "test_updates_nested_nova_group_add_server",
            "/templates/nested_total_2_instances_nova_group.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/nested_total_3_instances_nova_group.yml")

    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-00005869e017')
    def test_updates_nested_nova_group_remove_server(self):
        # Remove one of the nova servers from the group inside the inner
        # template
        stack_id, stack_name = self.create_stack(
            "test_updates_nested_nova_group_remove_server",
            "/templates/nested_total_3_instances_nova_group.yml")
        self.update_stack(stack_id, stack_name,
                          "/templates/nested_total_2_instances_nova_group.yml")
