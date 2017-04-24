#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright (c) 2014-2017 AT&T
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.

from tempest import test
from valet.tests.tempest.scenario.scenario_base import ScenarioTestCase


class TestNestedStackTemplates(ScenarioTestCase):

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00000')
    def test_affinity_nested_one_instances(self):
        self.create_valet_group("test_affinity_group1", 'host', 'affinity')
        template_file = "/templates/affinity_nested_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_affinity_nested_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host'], ['affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00001')
    def test_diversity_nested_one_instances(self):
        self.create_valet_group("test_diversity_group1", 'host', 'diversity')
        template_file = "/templates/diversity_nested_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_diversity_nested_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host'], ['diversity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00002')
    def test_exclusivity_nested_one_instances(self):
        self.create_valet_group("test_exclusivity_group1", 'host', 'exclusivity')
        template_file = "/templates/exclusivity_nested_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_exclusivity_nested_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host'], ['exclusivity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00003')
    def test_affinity_nested_two_instances(self):
        self.create_valet_group("test_affinity_group2", 'host', 'affinity')
        template_file = "/templates/affinity_nested_2_instances.yml"
        stack_id, stack_name = self.create_stack("test_affinity_nested_two_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host'], ['affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00004')
    def test_diversity_nested_two_instances(self):
        self.create_valet_group("test_diversity_group2", 'host', 'diversity')
        template_file = "/templates/diversity_nested_2_instances.yml"
        stack_id, stack_name = self.create_stack("test_diversity_nested_two_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host'], ['diversity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00005')
    def test_exclusivity_nested_two_instances(self):
        self.create_valet_group("test_exclusivity_group2", 'host', 'exclusivity')
        template_file = "/templates/exclusivity_nested_2_instances.yml"
        stack_id, stack_name = self.create_stack("test_exclusivity_nested_two_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host'], ['exclusivity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00006')
    def test_affinity_nested_three_instances(self):
        self.create_valet_group("test_affinity_group3", 'host', 'affinity')
        template_file = "/templates/affinity_nested_3_instances.yml"
        stack_id, stack_name = self.create_stack("test_affinity_nested_three_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host'], ['affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00007')
    def test_exclusivity_nested_three_instances(self):
        self.create_valet_group("test_exclusivity_group3", 'host', 'exclusivity')
        template_file = "/templates/exclusivity_nested_3_instances.yml"
        stack_id, stack_name = self.create_stack("test_exclusivity_nested_three_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host'], ['exclusivity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00008')
    def test_exclusivity_nested_diversity_one_instances(self):
        self.create_valet_group("test_exclusivity_group4", 'host', 'exclusivity')
        self.create_valet_group("test_diversity_group4", 'host', 'diversity')
        template_file = "/templates/exclusivity_nested_diversity_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_exclusivity_nested_diversity_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host', 'host'], ['exclusivity', 'diversity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00009')
    def test_exclusivity_nested_diversity_two_instances(self):
        self.create_valet_group("test_exclusivity_group5", 'host', 'exclusivity')
        self.create_valet_group("test_diversity_group5a", 'host', 'diversity')
        self.create_valet_group("test_diversity_group5b", 'host', 'diversity')
        template_file = "/templates/exclusivity_nested_diversity_2_instances.yml"
        stack_id, stack_name = self.create_stack("test_exclusivity_nested_diversity_two_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host', 'host', 'host'], ['exclusivity', 'diversity', 'diversity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0000a')
    def test_exclusivity_nested_affinity_two_instances(self):
        self.create_valet_group("test_exclusivity_group6", 'host', 'exclusivity')
        self.create_valet_group("test_affinity_group6a", 'host', 'affinity')
        self.create_valet_group("test_affinity_group6b", 'host', 'affinity')
        template_file = "/templates/exclusivity_nested_affinity_2_instances.yml"
        stack_id, stack_name = self.create_stack("test_exclusivity_nested_affinity_two_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host', 'host', 'host'], ['exclusivity', 'affinity', 'affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0000b')
    def test_affinity_nested_diversity_one_instances(self):
        self.create_valet_group("test_affinity_group7", 'host', 'affinity')
        self.create_valet_group("test_diversity_group7", 'host', 'diversity')
        template_file = "/templates/affinity_nested_diversity_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_affinity_nested_diversity_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host', 'host'], ['affinity', 'diversity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0000c')
    def test_affinity_nested_exclusivity_one_instances(self):
        self.create_valet_group("test_affinity_group9", 'host', 'affinity')
        self.create_valet_group("test_exclusivity_group9", 'host', 'exclusivity')
        template_file = "/templates/affinity_nested_exclusivity_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_affinity_nested_exclusivity_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host', 'host'], ['affinity', 'exclusivity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0000d')
    def test_exclusivity_nested_diversity_and_affinity_one_instances(self):
        self.create_valet_group("test_exclusivity_group15", 'host', 'exclusivity')
        self.create_valet_group("test_diversity_group15", 'host', 'diversity')
        self.create_valet_group("test_affinity_group15", 'host', 'affinity')
        template_file = "/templates/exclusivity_nested_diversity_and_affinity_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_exclusivity_nested_diversity_and_affinity_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host', 'host', 'host'], ['exclusivity', 'diversity', 'affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0000e')
    def test_diversity_nested_exclusivity_and_affinity_one_instances(self):
        self.create_valet_group("test_diversity_group17", 'host', 'diversity')
        self.create_valet_group("test_exclusivity_group17", 'host', 'exclusivity')
        self.create_valet_group("test_affinity_group17", 'host', 'affinity')
        template_file = "/templates/diversity_nested_exclusivity_and_affinity_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_diversity_nested_exclusivity_and_affinity_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host', 'host', 'host'], ['diversity', 'exclusivity', 'affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0000f')
    def test_rack_affinity_nested_two_instances(self):
        self.create_valet_group("test_affinity_group20", 'rack', 'affinity')
        template_file = "/templates/affinity_rack_nested_2_instances.yml"
        stack_id, stack_name = self.create_stack("test_affinity_rack_nested_two_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack'], ['affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00010')
    def test_rack_diversity_nested_two_instances(self):
        self.create_valet_group("test_diversity_group20", 'rack', 'diversity')
        template_file = "/templates/diversity_rack_nested_2_instances.yml"
        stack_id, stack_name = self.create_stack("test_diversity_rack_nested_two_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack'], ['diversity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00011')
    def test_rack_exclusivity_nested_two_instances(self):
        self.create_valet_group("test_exclusivity_group20", 'rack', 'exclusivity')
        template_file = "/templates/exclusivity_rack_nested_2_instances.yml"
        stack_id, stack_name = self.create_stack("test_exclusivity_rack_nested_two_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack'], ['exclusivity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00012')
    def test_rack_affinity_nested_three_instances(self):
        self.create_valet_group("test_affinity_group21", 'rack', 'affinity')
        template_file = "/templates/affinity_rack_nested_3_instances.yml"
        stack_id, stack_name = self.create_stack("test_affinity_rack_nested_three_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack'], ['affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00013')
    def test_rack_exclusivity_nested_diversity_one_instances(self):
        self.create_valet_group("test_exclusivity_group22", 'rack', 'exclusivity')
        self.create_valet_group("test_diversity_group22", 'host', 'diversity')
        template_file = "/templates/exclusivity_rack_nested_diversity_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_exclusivity_rack_nested_diversity_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'host'], ['exclusivity', 'diversity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00014')
    def test_rack_exclusivity_nested_diversity_two_instances(self):
        self.create_valet_group("test_exclusivity_group23", 'rack', 'exclusivity')
        self.create_valet_group("test_diversity_group23a", 'host', 'diversity')
        self.create_valet_group("test_diversity_group23b", 'host', 'diversity')
        template_file = "/templates/exclusivity_rack_nested_diversity_2_instances.yml"
        stack_id, stack_name = self.create_stack("test_exclusivity_rack_nested_diversity_two_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'host', 'host'], ['exclusivity', 'diversity', 'diversity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00015')
    def test_rack_exclusivity_nested_affinity_one_instances(self):
        self.create_valet_group("test_exclusivity_group24", 'rack', 'exclusivity')
        self.create_valet_group("test_affinity_group24", 'host', 'affinity')
        template_file = "/templates/exclusivity_rack_nested_affinity_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_exclusivity_rack_nested_affinity_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'host'], ['exclusivity', 'affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00016')
    def test_rack_exclusivity_nested_affinity_two_instances(self):
        self.create_valet_group("test_exclusivity_group25", 'rack', 'exclusivity')
        self.create_valet_group("test_affinity_group25a", 'host', 'affinity')
        self.create_valet_group("test_affinity_group25b", 'host', 'affinity')
        template_file = "/templates/exclusivity_rack_nested_affinity_2_instances.yml"
        stack_id, stack_name = self.create_stack("test_exclusivity_rack_nested_affinity_two_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'host', 'host'], ['exclusivity', 'affinity', 'affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00017')
    def test_rack_affinity_nested_diversity_one_instances(self):
        self.create_valet_group("test_affinity_group26", 'rack', 'affinity')
        self.create_valet_group("test_diversity_group26", 'host', 'diversity')
        template_file = "/templates/affinity_rack_nested_diversity_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_affinity_rack_nested_diversity_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'host'], ['affinity', 'diversity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00018')
    def test_rack_affinity_nested_exclusivity_one_instances(self):
        self.create_valet_group("test_affinity_group28", 'rack', 'affinity')
        self.create_valet_group("test_exclusivity_group28", 'host', 'exclusivity')
        template_file = "/templates/affinity_rack_nested_exclusivity_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_affinity_rack_nested_exclusivity_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'host'], ['affinity', 'exclusivity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00019')
    def test_rack_diversity_nested_affinity_one_instances(self):
        self.create_valet_group("test_diversity_group30", 'rack', 'diversity')
        self.create_valet_group("test_affinity_group30", 'host', 'affinity')
        template_file = "/templates/diversity_rack_nested_affinity_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_diversity_rack_nested_affinity_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'host'], ['diversity', 'affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0001a')
    def test_rack_diversity_nested_exclusivity_one_instances(self):
        self.create_valet_group("test_diversity_group32", 'rack', 'diversity')
        self.create_valet_group("test_exclusivity_group32", 'host', 'exclusivity')
        template_file = "/templates/diversity_rack_nested_exclusivity_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_diversity_rack_nested_exclusivity_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'host'], ['diversity', 'exclusivity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0001b')
    def test_rack_exclusivity_nested_diversity_and_affinity_one_instances(self):
        self.create_valet_group("test_exclusivity_group34", 'rack', 'exclusivity')
        self.create_valet_group("test_diversity_group34", 'host', 'diversity')
        self.create_valet_group("test_affinity_group34", 'host', 'affinity')
        template_file = "/templates/exclusivity_rack_nested_diversity_and_affinity_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_exclusivity_rack_nested_diversity_and_affinity_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'host', 'host'], ['exclusivity', 'diversity', 'affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0001c')
    def test_rack_diversity_nested_exclusivity_and_affinity_one_instances(self):
        self.create_valet_group("test_diversity_group36", 'rack', 'diversity')
        self.create_valet_group("test_exclusivity_group36", 'host', 'exclusivity')
        self.create_valet_group("test_affinity_group36", 'host', 'affinity')
        template_file = "/templates/diversity_rack_nested_exclusivity_and_affinity_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_diversity_rack_nested_exclusivity_and_affinity_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'host', 'host'], ['diversity', 'exclusivity', 'affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0001d')
    def test_host_exclusivity_multiple_resource_types(self):
        self.create_valet_group("oam_exclusivity_group_1", 'host', 'exclusivity')
        template_file = "/templates/exclusivity_host_multiple_resource_types.yaml"
        stack_id, stack_name = self.create_stack("test_exclusivity_host_multiple_resource_types", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host'], ['exclusivity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0001e')
    def test_host_affinity_multiple_resource_types(self):
        self.create_valet_group("oam_affinity_group_1", 'host', 'affinity')
        template_file = "/templates/affinity_host_multiple_resource_types.yaml"
        stack_id, stack_name = self.create_stack("test_affinity_host_multiple_resource_types", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host'], ['affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0001f')
    def test_host_diversity_multiple_resource_types(self):
        self.create_valet_group("oam_diversity_group_1", 'host', 'diversity')
        template_file = "/templates/diversity_host_multiple_resource_types.yaml"
        stack_id, stack_name = self.create_stack("test_diversity_host_multiple_resource_types", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host'], ['diversity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00020')
    def test_rack_exclusivity_nested_affinity_multiple_resource_types(self):
        self.create_valet_group("oam_exclusivity_group_2", 'rack', 'exclusivity')
        self.create_valet_group("oam_affinity_group_2a", 'host', 'affinity')
        self.create_valet_group("oam_affinity_group_2b", 'host', 'affinity')
        template_file = "/templates/exclusivity_rack_nested_affinity_multiple_resource_types.yaml"
        stack_id, stack_name = self.create_stack("test_exclusivity_rack_nested_affinity_multiple_resource_types", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'host', 'host'], ['exclusivity', 'affinity', 'affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00021')
    def test_rack_exclusivity_nested_diversity_multiple_resource_types(self):
        self.create_valet_group("oam_exclusivity_group_3", 'rack', 'exclusivity')
        self.create_valet_group("oam_diversity_group_3a", 'host', 'diversity')
        self.create_valet_group("oam_diversity_group_3b", 'host', 'diversity')
        template_file = "/templates/exclusivity_rack_nested_diversity_multiple_resource_types.yaml"
        stack_id, stack_name = self.create_stack("test_exclusivity_rack_nested_diversity_multiple_resource_types", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'host', 'host'], ['exclusivity', 'diversity', 'diversity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00024')
    def test_rack_rack_affinity_one_instances(self):
        self.create_valet_group("test_affinity_group37a", 'rack', 'affinity')
        self.create_valet_group("test_affinity_group37b", 'rack', 'affinity')
        template_file = "/templates/affinity_rack_affinity_rack_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_affinity_rack_affinity_rack_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'rack'], ['affinity', 'affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00025')
    def test_rack_rack_diversity_one_instances(self):
        self.create_valet_group("test_diversity_group37a", 'rack', 'diversity')
        self.create_valet_group("test_diversity_group37b", 'rack', 'diversity')
        template_file = "/templates/diversity_rack_diversity_rack_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_diveristy_rack_diversity_rack_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'rack'], ['diversity', 'diversity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00026')
    def test_rack_rack_exclusivity_one_instances(self):
        self.create_valet_group("test_exclusivity_group37a", 'rack', 'exclusivity')
        self.create_valet_group("test_exclusivity_group37b", 'rack', 'exclusivity')
        template_file = "/templates/exclusivity_rack_exclusivity_rack_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_exclusivity_rack_exclusivity_rack_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'rack'], ['exclusivity', 'exclusivity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00027')
    def test_rack_affinity_rack_diversity_one_instances(self):
        self.create_valet_group("test_affinity_group38", 'rack', 'affinity')
        self.create_valet_group("test_diversity_group38", 'rack', 'diversity')
        template_file = "/templates/affinity_rack_diversity_rack_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_affinity_rack_diversity_rack_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'rack'], ['affinity', 'diversity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00028')
    def test_rack_affinity_rack_exclusivity_one_instances(self):
        self.create_valet_group("test_affinity_group39", 'rack', 'affinity')
        self.create_valet_group("test_exclusivity_group39", 'rack', 'exclusivity')
        template_file = "/templates/affinity_rack_exclusivity_rack_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_affinity_rack_exclusivity_rack_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'rack'], ['affinity', 'exclusivity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00029')
    def test_rack_diversity_rack_exclusivity_one_instances(self):
        self.create_valet_group("test_diversity_group40", 'rack', 'diversity')
        self.create_valet_group("test_exclusivity_group40", 'rack', 'exclusivity')
        template_file = "/templates/diversity_rack_exclusivity_rack_1_instances.yml"
        stack_id, stack_name = self.create_stack("test_diversity_rack_exclusivity_rack_one_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'rack'], ['diversity', 'exclusivity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0002a')
    def test_rack_affinity_rack_diversity_two_instances(self):
        self.create_valet_group("test_affinity_group41", 'rack', 'affinity')
        self.create_valet_group("test_diversity_group41", 'rack', 'diversity')
        template_file = "/templates/affinity_rack_diversity_rack_2_instances.yml"
        stack_id, stack_name = self.create_stack("test_affinity_rack_diversity_rack_two_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'rack'], ['affinity', 'diversity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0002b')
    def test_rack_affinity_rack_exclusivity_two_instances(self):
        self.create_valet_group("test_affinity_group42", 'rack', 'affinity')
        self.create_valet_group("test_exclusivity_group42", 'rack', 'exclusivity')
        template_file = "/templates/affinity_rack_exclusivity_rack_2_instances.yml"
        stack_id, stack_name = self.create_stack("test_affinity_rack_exclusivity_rack_two_instances", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['rack', 'rack'], ['affinity', 'exclusivity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0002c')
    def test_affinity_one_instance_nested_one_instance(self):
        self.create_valet_group("test_affinity_group44", 'host', 'affinity')
        template_file = "/templates/affinity_1_instance_nested_1_instance.yml"
        stack_id, stack_name = self.create_stack("test_affinity_one_instance_nested_one_instance", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host'], ['affinity'])

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a0002d')
    def test_diversity_one_instance_nested_one_instance(self):
        self.create_valet_group("test_diversity_group44", 'host', 'diversity')
        template_file = "/templates/diversity_1_instance_nested_1_instance.yml"
        stack_id, stack_name = self.create_stack("test_diversity_one_instance_nested_one_instance", template_file, "/templates/std_env_1_flavor.env")
        self.check_stack(stack_id, template_file, ['host'], ['diversity'])
