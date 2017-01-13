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

"""Loader."""

from heatclient.client import Client
import sys
import time
import traceback
from valet.tests.functional.valet_validator.common import Result, GeneralLogger
from valet.tests.functional.valet_validator.common.auth import Auth
from valet.tests.functional.valet_validator.common.init import CONF
from valet.tests.functional.valet_validator.group_api.valet_group import ValetGroup


class Loader(object):
    """Class is responsible for loading stacks and groups."""

    def __init__(self):
        """Initializing the loader - connecting to heat."""
        GeneralLogger.log_info("Initializing Loader")

        heat_url = CONF.heat.HEAT_URL + str(Auth.get_project_id())
        token = Auth.get_auth_token()

        heat = Client(CONF.heat.VERSION, endpoint=heat_url, token=token)
        self.stacks = heat.stacks

    def create_stack(self, stack_name, template_resources):
        """Create stack from template resources."""
        GeneralLogger.log_info("Starting to create stacks")
        groups = template_resources.groups

        try:
            for key in groups:
                if groups[key].group_type == "exclusivity":
                    self.create_valet_group(groups[key].group_name)

            self.stacks.create(stack_name=stack_name,
                               template=template_resources.template_data)
            return self.wait(stack_name, operation="create")

        except Exception:
            GeneralLogger.log_error("Failed to create stack",
                                    traceback.format_exc())
            sys.exit(1)

    def create_valet_group(self, group_name):
        """Create valet group."""
        try:
            v_group = ValetGroup()

            # (group_name, group_type)
            group_details = v_group.get_group_id_and_members(group_name)
            v_group.add_group_member(group_details)

        except Exception:
            GeneralLogger.log_error("Failed to create valet group",
                                    traceback.format_exc())
            sys.exit(1)

    def delete_stack(self, stack_name):
        """Delete stack according to stack_name."""
        self.stacks.delete(stack_id=stack_name)
        return self.wait(stack_name, operation="delete")

    def delete_all_stacks(self):
        """Delete all stacks."""
        GeneralLogger.log_info("Starting to delete stacks")
        try:
            for stack in self.stacks.list():
                self.delete_stack(stack.id)

        except Exception:
            GeneralLogger.log_error("Failed to delete stacks",
                                    traceback.format_exc())

    def wait(self, stack_name, count=CONF.valet.TIME_CAP,
             operation="Operation"):
        """Check result of process (create/delete) and write result to log."""
        while str(self.stacks.get(stack_name).status) == "IN_PROGRESS" \
                and count > 0:
            count -= 1
            time.sleep(1)

        if str(self.stacks.get(stack_name).status) == "COMPLETE":
            GeneralLogger.log_info(operation + " Successfully completed")
            return Result()
        elif str(self.stacks.get(stack_name).status) == "FAILED":
            msg = operation + " failed  -  " + \
                self.stacks.get(stack_name).stack_status_reason
        else:
            msg = operation + " timed out"
        GeneralLogger.log_error(msg)

        return Result(False, msg)
