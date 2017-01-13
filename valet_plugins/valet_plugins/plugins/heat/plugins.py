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

"""Valet Plugins for Heat."""

from heat.engine import lifecycle_plugin

from valet_plugins.common import valet_api

from oslo_config import cfg
from oslo_log import log as logging

import string
import uuid

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def validate_uuid4(uuid_string):
    """Validate that a UUID string is in fact a valid uuid4.

    Happily, the uuid module does the actual checking for us.
    It is vital that the 'version' kwarg be passed to the
    UUID() call, otherwise any 32-character hex string
    is considered valid.
    """
    try:
        val = uuid.UUID(uuid_string, version=4)
    except ValueError:
        # If it's a value error, then the string
        # is not a valid hex code for a UUID.
        return False

    # If the uuid_string is a valid hex code, # but an invalid uuid4,
    # the UUID.__init__ will convert it to a valid uuid4.
    # This is bad for validation purposes.

    # uuid_string will sometimes have separators.
    return string.replace(val.hex, '-', '') == \
        string.replace(uuid_string, '-', '')


class ValetLifecyclePlugin(lifecycle_plugin.LifecyclePlugin):
    """Base class for pre-op and post-op work on a stack.

    Implementations should extend this class and override the methods.
    """

    def __init__(self):
        """Initialize."""
        self.api = valet_api.ValetAPIWrapper()
        self.hints_enabled = False

        # This plugin can only work if stack_scheduler_hints is true
        cfg.CONF.import_opt('stack_scheduler_hints', 'heat.common.config')
        self.hints_enabled = cfg.CONF.stack_scheduler_hints

    def _parse_stack_preview(self, dest, preview):
        """Walk the preview list (possibly nested).

        extracting parsed template dicts and storing modified versions in a flat
        dict.
        """
        # The preview is either a list or not.
        if not isinstance(preview, list):
            # Heat does not assign orchestration UUIDs to
            # all resources, so we must make our own sometimes.
            # This also means nested templates can't be supported yet.

            # FIXME: Either propose uniform use of UUIDs within
            # Heat (related to Heat bug 1516807), or store
            # resource UUIDs within the parsed template and
            # use only Valet-originating UUIDs as keys.
            if hasattr(preview, 'uuid') and \
               preview.uuid and validate_uuid4(preview.uuid):
                key = preview.uuid
            else:
                # TODO(UNK): Heat should be authoritative for UUID assignments.
                # This will require a change to heat-engine.
                # Looks like it may be: heat/db/sqlalchemy/models.py#L279
                # It could be that nested stacks aren't added to the DB yet.
                key = str(uuid.uuid4())
            parsed = preview.parsed_template()
            parsed['name'] = preview.name
            # TODO(UNKWN): Replace resource referenced names with their UUIDs.
            dest[key] = parsed
        else:
            for item in preview:
                self._parse_stack_preview(dest, item)

    def do_pre_op(self, cnxt, stack, current_stack=None, action=None):
        """Method to be run by heat before stack operations."""
        if not self.hints_enabled or stack.status != 'IN_PROGRESS':
            return

        if action == 'DELETE':
            self.api.plans_delete(stack, auth_token=cnxt.auth_token)
        elif action == 'CREATE':
            resources = dict()
            specifications = dict()
            reservations = dict()

            stack_preview = stack.preview_resources()
            self._parse_stack_preview(resources, stack_preview)

            timeout = 60
            plan = {
                'plan_name': stack.id,
                'stack_id': stack.id,
                'timeout': '%d sec' % timeout,
            }
            if resources and len(resources) > 0:
                plan['resources'] = resources
            else:
                return
            if specifications:
                plan['specifications'] = specifications
            if reservations:
                plan['reservations'] = reservations

            self.api.plans_create(stack, plan, auth_token=cnxt.auth_token)

    def do_post_op(self, cnxt, stack,   # pylint: disable=R0913
                   current_stack=None, action=None, is_stack_failure=False):
        """Method to be run by heat after stack operations, including failures.

        On failure to execute all the registered pre_ops, this method will be
        called if and only if the corresponding pre_op was successfully called.
        On failures of the actual stack operation, this method will
        be called if all the pre operations were successfully called.
        """
        pass

    def get_ordinal(self):
        """Ordinal to order class instances for pre /post operation execution.

        The values returned by get_ordinal are used to create a partial order
        for pre and post operation method invocations. The default ordinal
        value of 100 may be overridden.
        If class1inst.ordinal() < class2inst.ordinal(), then the method on
        class1inst will be executed before the method on class2inst.
        If class1inst.ordinal() > class2inst.ordinal(), then the method on
        class1inst will be executed after the method on class2inst.
        If class1inst.ordinal() == class2inst.ordinal(), then the order of
        method invocation is indeterminate.
        """
        return 100
