#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright (c) 2014-2016 AT&T#
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
from tempest_lib.common.utils import data_utils
from valet.tests.tempest.api import base


class ValetPlanTest(base.BaseValetTest):

    @classmethod
    def setup_clients(cls):
        super(ValetPlanTest, cls).setup_clients()
        cls.client = cls.valet_client

    def _get_plan_name_stack_id(self):
        return data_utils.rand_uuid()

    def _get_resource_name_id(self):
        resource_info = {}
        resource_info['name'] = data_utils.rand_name(name='resource')
        resource_info['id'] = data_utils.rand_uuid()
        return resource_info

    def _create_excluded_hosts(self):
        return data_utils.rand_name(name='qos')

    def _get_resource_property(self):
        properties = {}
        # TODO(kr336r): Use tempest to get/create flavour, image, networks
        # Is it required really ???
        properties['flavor'] = "m1.small"
        properties['image'] = "ubuntu_1204"
        properties['networks'] = [{"network": "demo-net"}]
        return properties

    def _create_resource(self):
        resources = {}
        _resource_data = {}
        _resource_name_id = self._get_resource_name_id()
        _resource_property = self._get_resource_property()
        _resource_data['properties'] = _resource_property
        _resource_data['type'] = "OS::Nova::Server"
        _resource_data['name'] = _resource_name_id['name']
        resources = {
            _resource_name_id['id']: _resource_data
        }
        return resources

    def _delete_plan(self, plan_id):
        self.client.delete_plan(plan_id)

    def _get_stack_and_plan_id(self):
        stack_and_plan = {}
        _plan_name_stack_id = self._get_plan_name_stack_id()
        _resources = self._create_resource()
        resp = self.client.create_plan(_plan_name_stack_id,
                                       _resources,
                                       _plan_name_stack_id)
        stack_id = resp['plan']['stack_id']
        plan_id = resp['plan']['id']
        plan_name = resp['plan']['name']
        for key, value in resp['plan']['placements'].iteritems():
            stack_and_plan['resource_id'] = key
        location = resp['plan']['placements'][stack_and_plan['resource_id']]['location']
        stack_and_plan['stack_id'] = stack_id
        stack_and_plan['plan_id'] = plan_id
        stack_and_plan['name'] = plan_name
        stack_and_plan['location'] = location
        return stack_and_plan

    @test.idempotent_id('f25ea766-c91e-40ca-b96c-dff42129803d')
    def test_create_plan(self):
        stack_and_plan = self._get_stack_and_plan_id()
        stack_id = stack_and_plan['stack_id']
        plan_id = stack_and_plan['plan_id']
        plan_name = stack_and_plan['name']
        self.assertEqual(stack_id, plan_name)
        self.addCleanup(self._delete_plan, plan_id)

    @test.idempotent_id('973635f4-b5c9-4b78-81e7-d273e1782afc')
    def test_update_plan_action_migrate(self):
        stack_and_plan = self._get_stack_and_plan_id()
        stack_id = stack_and_plan['stack_id']
        plan_id = stack_and_plan['plan_id']
        plan_name = stack_and_plan['name']
        resource_id = stack_and_plan['resource_id']
        resources = []
        resources.append(resource_id)
        excluded_hosts = []
        excluded_hosts.append(stack_and_plan['location'])
        action = "migrate"
        body = self.client.update_plan(plan_id,
                                       action,
                                       excluded_hosts,
                                       resources)
        self.assertIn('id', body['plan'])
        self.assertEqual(stack_id, plan_name)
        self.addCleanup(self._delete_plan, plan_id)
