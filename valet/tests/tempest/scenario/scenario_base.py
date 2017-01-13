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

"""Scenario Base."""

import os
from tempest import config
from tempest import exceptions
from tempest import test
from tempest_lib.common.utils import data_utils
import time
import traceback
from valet.tests.tempest.scenario.analyzer import Analyzer
from valet.tests.tempest.scenario.resources import TemplateResources
from valet.tests.tempest.services.client import ValetClient

CONF = config.CONF


class ScenarioTestCase(test.BaseTestCase):
    """Base class for Scenario Test cases."""

    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        """Skip checks, if valet service not available, raise exception."""
        super(ScenarioTestCase, cls).skip_checks()
        if not CONF.service_available.valet:
            skip_msg = ("%s skipped as valet is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def resource_setup(cls):
        """Setup resource, set catalog_type."""
        super(ScenarioTestCase, cls).resource_setup()
        cls.catalog_type = CONF.placement.catalog_type

    @classmethod
    def resource_cleanup(cls):
        """Class method resource cleanup."""
        super(ScenarioTestCase, cls).resource_cleanup()

    @classmethod
    def setup_clients(cls):
        """Setup clients (valet)."""
        super(ScenarioTestCase, cls).setup_clients()
        cls.heat_client = cls.os.orchestration_client
        cls.nova_client = cls.os.servers_client
        cls.tenants_client = cls.os.identity_client
        cls.valet_client = ValetClient(
            cls.os.auth_provider, CONF.placement.catalog_type,
            CONF.identity.region, **cls.os.default_params_with_timeout_values)

        cls.possible_topdir = os.path.normpath(
            os.path.join(os.path.abspath(__file__), os.pardir))
        cls.stack_identifier = None
        cls.tries = CONF.valet.TRIES_TO_CREATE

    def run_test(self, logger, stack_name, template_path):
        """Scenario.

        create new stack
        checks if host (or rack) is the same for all instances
        """
        self.log = logger
        self.log.log_info(" ******** Running Test ******** ")
        tmplt_url = self.possible_topdir + template_path
        template = TemplateResources(tmplt_url)

        env_data = self.get_env_file(tmplt_url)

        self.log.log_info(" ******** Creating Stack ******** ")
        name = data_utils.rand_name(name=stack_name)
        self.assertEqual(True, self.create_stack(name, env_data, template))

        self.log.log_info(" ******** Analyzing Stack ******** ")
        analyzer = Analyzer(self.log, self.stack_identifier, self.heat_client,
                            self.nova_client)
        self.assertEqual(True, analyzer.check(template))

        self.log.log_info(" ********** THE END ****************")

    def create_stack(self, stack_name, env_data, template_resources):
        """Create stack with name/env/resource. Create all groups/instances."""
        try:
            groups = template_resources.groups

            for key in groups:
                if groups[key].group_type == "exclusivity":
                    self.log.log_info(" creating group ")
                    grp_name = data_utils.rand_name(name=groups[key].group_name)
                    template_resources.template_data = \
                        template_resources.template_data.replace(
                            groups[key].group_name, grp_name)
                    self.create_valet_group(grp_name)

            for instance in template_resources.instances:
                generated_name = data_utils.rand_name(instance.name)
                template_resources.template_data = \
                    template_resources.template_data.replace(
                        instance.name, generated_name)
                instance.name = generated_name

            self.wait_for_stack(stack_name, env_data, template_resources)
            self.addCleanup(self.delete_stack)

        except Exception:
            self.log.log_error("Failed to create stack", traceback.format_exc())
            return False
        return True

    def create_valet_group(self, group_name):
        """Create valet group with name using valet client. Add members."""
        try:
            v_group = self.valet_client.create_group(name=group_name,
                                                     group_type='exclusivity',
                                                     description="description")
            group_id = v_group['id']
            tenant_id = self.tenants_client.tenant_id
            self.addCleanup(self._delete_group, group_id)

            self.valet_client.add_members(group_id, [tenant_id])

        except Exception:
            self.log.log_error("Failed to create valet group",
                               traceback.format_exc())

    def get_env_file(self, template):
        """Return file.read for env file or return None."""
        env_url = template.replace(".yml", ".env")

        if os.path.exists(env_url):
            with open(env_url, "r") as f:
                return f.read()
        else:
            return None

    def _delete_group(self, group_id):
        self.valet_client.delete_all_members(group_id)
        self.valet_client.delete_group(group_id)

    def delete_stack(self):
        """Use heat client to delete stack."""
        self.heat_client.delete_stack(self.stack_identifier)
        self.heat_client.wait_for_stack_status(
            self.stack_identifier, "DELETE_COMPLETE",
            failure_pattern='^.*DELETE_FAILED$')

    def show_stack(self, stack_id):
        """Return show stack with given id from heat client."""
        return self.heat_client.show_stack(stack_id)

    def wait_for_stack(self, stack_name, env_data, template_resources):
        """Use heat client to create stack, then wait for status."""
        try:
            self.log.log_info("Trying to create stack")
            new_stack = self.heat_client.create_stack(
                stack_name, environment=env_data,
                template=template_resources.template_data)
            stack_id = new_stack["stack"]["id"]
            self.stack_identifier = stack_name + "/" + stack_id

            self.heat_client.wait_for_stack_status(
                self.stack_identifier, "CREATE_COMPLETE",
                failure_pattern='^.*CREATE_FAILED$')

        except exceptions.StackBuildErrorException as ex:
            if "Ostro error" in str(ex):
                if self.tries > 0:
                    self.log.log_error(
                        "Ostro error - try number %d" %
                        (CONF.valet.TRIES_TO_CREATE - self.tries + 2))
                    self.tries -= 1
                    self.delete_stack()
                    time.sleep(CONF.valet.PAUSE)
                    self.wait_for_stack(stack_name, env_data,
                                        template_resources)
                else:
                    raise
            else:
                self.log.log_error("Failed to create stack",
                                   traceback.format_exc())
