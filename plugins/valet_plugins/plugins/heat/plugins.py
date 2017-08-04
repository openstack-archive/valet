#
# Copyright (c) 2014-2017 AT&T Intellectual Property
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

"""Valet Plugins for Heat"""

import string
import uuid

from heat.engine import lifecycle_plugin
from oslo_config import cfg
from oslo_log import log as logging

from valet_plugins.common import valet_api
from valet_plugins import exceptions

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


def valid_uuid_for_resource(resource):
    """Return uuid if resource has a uuid attribute and a valid uuid4"""
    if hasattr(resource, 'uuid') and \
            resource.uuid and validate_uuid4(resource.uuid):
        return resource.uuid


class ValetLifecyclePlugin(lifecycle_plugin.LifecyclePlugin):
    """Base class for pre-op and post-op work on a stack.

    Implementations should extend this class and override the methods.
    """

    _RESOURCE_TYPES = (
        VALET_GROUP, VALET_GROUP_ASSIGNMENT, NOVA_SERVER,
    ) = (
        "OS::Valet::Group", "OS::Valet::GroupAssignment", "OS::Nova::Server",
    )

    VALET_RESOURCE_TYPES = [
        VALET_GROUP, VALET_GROUP_ASSIGNMENT,
    ]
    OS_RESOURCE_TYPES = [
        NOVA_SERVER,
    ]

    def __init__(self):
        """"Initialization"""
        self.api = valet_api.ValetAPI()
        self.hints_enabled = False

        # This plugin can only work if stack_scheduler_hints is true
        CONF.import_opt('stack_scheduler_hints', 'heat.common.config')
        self.hints_enabled = CONF.stack_scheduler_hints

    def _parse_stack(self, stack, original_stack={}):
        """Fetch resources out of the stack. Does not traverse."""
        resources = {}

        # We used to call Stack.preview_resources() and this used to
        # be a recursive method. However, this breaks down significantly
        # when nested stacks are involved. Previewing and creating/updating
        # a stack are divergent operations. There are also side-effects for
        # a preview-within-create operation that only happen to manifest
        # with nested stacks.

        valet_group_declared = False
        resource_declared = False
        for name, resource in stack.resources.iteritems():
            # VALET_GROUP must not co-exist with other resources
            # in the same stack.
            resource_type = resource.type()
            if resource_type == self.VALET_GROUP:
                valet_group_declared = True
            else:
                resource_declared = True
            if valet_group_declared and resource_declared:
                raise exceptions.GroupResourceNotIsolatedError()

            # Skip over resource types we aren't interested in.
            # This test used to cover VALET_RESOURCE_TYPES as well.
            # VALET_GROUP is implemented as a bona fide plugin,
            # so that doesn't count, and VALET_GROUP_ASSIGNMENT
            # has been pre-empted before v1.0 (not deprecated), so
            # that doesn't count either, at least for now. There's
            # a good chance it will re-appear in the future so
            # the logic for Group Assignments remains within this loop.
            if resource_type not in self.OS_RESOURCE_TYPES:
                continue

            # Find the original resource. We may need it in two cases.
            # This may also end up being effectively null.
            original_res = None
            if original_stack:
                original_res = original_stack.resources.get(name, {})

            key = valid_uuid_for_resource(resource)
            if not key:
                # Here's the first case where we can use original_res.
                #
                # We can't proceed without a UUID in OS-facing resources.
                # During a stack update, the current resources don't have
                # their uuid's populated, but the original stack does.
                # If that has been passed in, use that as a hint.
                key = valid_uuid_for_resource(original_res)
                if not key:
                    # Given that we're no longer traversing stack levels,
                    # it would be surprising if this exception is thrown
                    # in the stack create case (original stack is not
                    # passed in so it's easy to spot).
                    if stack and not original_stack:
                        # Keeping this here as a safety net and a way to
                        # indicate the specific problem.
                        raise exceptions.ResourceUUIDMissingError(resource)

                    # Unfortunately, stack updates are beyond messy.
                    # Heat is inconsistent in what context it has
                    # in various resources at update time.
                    #
                    # To mitigate, we create a mock orch_id and send
                    # that to valet-api instead. It can be resolved to the
                    # proper orch_id by valet-api at location scheduling time
                    # (e.g., nova-scheduler, cinder-scheduler) by using the
                    # stack lifecycle scheduler hints as clues. That also means
                    # valet-api must now have detailed knowledge of those hints
                    # to figure out which placement to actually use/adjust.
                    key = str(uuid.uuid4())
                    LOG.warn(("Orchestration ID not found for resource "
                              "named {}. Using mock orchestration "
                              "ID {}.").format(resource.name, key))

            # Parse the resource, then ensure all keys at the top level
            # are lowercase. (Heat makes some of them uppercase.)
            parsed = resource.parsed_template()
            parsed = dict((k.lower(), v) for k, v in parsed.iteritems())

            parsed['name'] = name

            # Resolve identifiers to resources with valid orch ids.
            # The referenced resources MUST be at the same stack level.
            if resource.type() == self.VALET_GROUP_ASSIGNMENT:
                properties = parsed.get('properties', {})
                uuids = []
                # The GroupAssignment resource list consists of
                # Heat resource names or IDs (physical UUIDs).
                # Find that resource in the stack or original stack.
                # The resource must have a uuid (orchestration id).
                for ref_identifier in properties.get('resources'):
                    ref_resource = self._resource_with_uuid_for_identifier(
                        stack.resources, ref_identifier)
                    if not ref_resource and original_stack:
                        ref_resource = \
                            self._resource_with_uuid_for_identifier(
                                original_stack.resources, ref_identifier)
                    if not ref_resource:
                        msg = "Resource {} with an assigned " \
                              "orchestration id not found"
                        msg = msg.format(ref_identifier)
                        raise exceptions.ResourceNotFoundError(
                            ref_identifier, msg)
                    uuids.append(ref_resource.uuid)
                properties['resources'] = uuids

            # Add whatever stack lifecycle scheduler hints we can, in
            # advance of when they would normally be added to the regular
            # scheduler hints, provided the _scheduler_hints mixin exists.
            # Give preference to the original resource, if it exists, as it
            # is always more accurate.
            hints = None
            if hasattr(original_res, '_scheduler_hints'):
                hints = original_res._scheduler_hints({})
            elif hasattr(resource, '_scheduler_hints'):
                hints = resource._scheduler_hints({})
            if hints:
                # Remove keys with empty values and store as metadata
                parsed['metadata'] = \
                    dict((k, v) for k, v in hints.iteritems() if v)
            else:
                parsed['metadata'] = {}

            # If the physical UUID is already known, store that too.
            if resource.resource_id is not None:
                parsed['resource_id'] = resource.resource_id
            elif original_res and hasattr(original_res, 'resource_id'):
                # Here's the second case where we can use original_res.
                #
                # It's not a showstopper if we can't find the physical
                # UUID, but if it wasn't in the updated resource, we
                # will try to see if it's in the original one, if any.
                parsed['resource_id'] = original_res.resource_id

            LOG.info(("Adding Resource, Type: {}, "
                      "Name: {}, UUID: {}").format(
                     resource.type(), name, resource.uuid))
            resources[key] = parsed
        return resources

    # TODO(jdandrea) DO NOT USE. This code has changes that have not yet
    # been committed, but are potentially valuable. Leaving it here in the
    # event bug 1516807 is resolved and we can cross-reference resources
    # in nested stacks.
    def _parse_stack_preview(self, dest, preview):
        """Walk the preview list (possibly nested)

        Extract parsed template dicts. Store mods in a flat dict.
        """

        # KEEP THIS so that the method is not usable (on purpose).
        return

        # The preview is either a list or not.
        if not isinstance(preview, list):
            # Heat does not assign orchestration UUIDs to
            # all resources, so we must make our own sometimes.
            # This also means nested templates can't be supported yet.

            # FIXME(jdandrea): Either propose uniform use of UUIDs within
            # Heat (related to Heat bug 1516807), or store
            # resource UUIDs within the parsed template and
            # use only Valet-originating UUIDs as keys.
            if hasattr(preview, 'uuid') and \
               preview.uuid and validate_uuid4(preview.uuid):
                key = preview.uuid
            else:
                # TODO(jdandrea): Heat must be authoritative for UUIDs.
                # This will require a change to heat-engine.
                # This is one culprit: heat/db/sqlalchemy/models.py#L279
                # Note that stacks are stored in the DB just-in-time.
                key = str(uuid.uuid4())
            parsed = preview.parsed_template()
            parsed['name'] = preview.name

            # Add whatever stack lifecycle scheduler hints we can, in
            # advance of when they would normally be added to the regular
            # scheduler hints, provided the _scheduler_hints mixin exists.
            if hasattr(preview, '_scheduler_hints'):
                hints = preview._scheduler_hints({})

                # Remove keys with empty values and store as metadata
                parsed['metadata'] = \
                    dict((k, v) for k, v in hints.iteritems() if v)
            else:
                parsed['metadata'] = {}

            # TODO(jdandrea): Replace resource referenced names w/UUIDs.

            # Ensure all keys at the top level are lowercase (heat makes
            # some of them uppercase) before storing.
            parsed = dict((k.lower(), v) for k, v in parsed.iteritems())

            # TODO(jdandrea): Need to resolve the names within
            # OS::Valet::GroupAssignment to corresponding UUIDs.
            dest[key] = parsed
        else:
            for item in preview:
                self._parse_stack_preview(dest, item)

    # TODO(jdandrea): DO NOT USE. This code has not yet been committed,
    # but is potentially valuable. Leaving it here in the event bug 1516807
    # is resolved and we can cross-reference resources in nested stacks.
    def _resolve_group_assignment_resources(self, resources):
        """Resolve Resource Names in GroupAssignments

        This presumes a resource is being referenced from within
        the same template/stack. No cross-template/stack references.
        """

        # KEEP THIS so that the method is not usable (on purpose).
        return

        # TODO(jdandrea): Use pyobjc-core someday. KVC simplifies this.
        # Ref: https://bitbucket.org/ronaldoussoren/pyobjc/issues/187/
        #   pyobjc-core-on-platforms-besides-macos
        for orch_id, resource in resources.iteritems():
            if resource.get('type') == self.VALET_GROUP_ASSIGNMENT:
                # Grab our stack name and path-in-stack
                metadata = resource.get('metadata', {})
                stack_name = metadata.get('heat_stack_name')
                path_in_stack = metadata.get('heat_path_in_stack')

                # For each referenced Heat resource name ...
                properties = resource.get('properties')
                ref_resources = properties.get('resources', [])
                ref_orch_ids = []
                for ref_res_name in ref_resources:
                    # Search all the resources for a mapping.
                    for _orch_id, _resource in resources.iteritems():
                        # Grab this resource's stack name and path-in-stack
                        _metadata = _resource.get('metadata', {})
                        _stack_name = _metadata.get('heat_stack_name')
                        _path_in_stack = _metadata.get('heat_path_in_stack')

                        # Grab the Heat resource name
                        _res_name = _resource.get('name')

                        # If everything matches, we found our orch_id
                        if ref_res_name == _res_name and \
                           stack_name == _stack_name and \
                           path_in_stack == _path_in_stack:
                            ref_orch_ids.append(_orch_id)
                            break
                properties['resources'] = ref_orch_ids

    def _resource_with_uuid_for_identifier(self, resources, identifier):
        """Return resource matching an identifier if it has a valid uuid.

        uuid means "orchestration id"
        resource_id means "physical id"
        identifier is either a heat resource name or a resource_id.
        identifier is never a uuid (orchestation id).
        """
        if type(resources) is not dict:
            return
        for resource in resources.values():
            if resource.name == identifier or \
                    resource.resource_id == identifier:
                if valid_uuid_for_resource(resource):
                    return resource

    def do_pre_op(self, cnxt, stack, current_stack=None, action=None):
        """Method to be run by heat before stack operations."""
        if not self.hints_enabled:
            LOG.warn("stack_scheduler_hints is False, skipping stack")
            return

        # We can now set the auth token in advance, so let's do that.
        self.api.auth_token = cnxt.auth_token

        # Take note of the various status states as they pass through here.
        if stack:
            original_stack_status = "{} ({})".format(stack.name, stack.status)
        else:
            original_stack_status = "n/a"
        if current_stack:
            updated_stack_status = "{} ({})".format(current_stack.name,
                                                    current_stack.status)
        else:
            updated_stack_status = "n/a"
        msg = "Stack Lifecycle Action: {}, Original: {}, Updated: {}"
        LOG.debug(msg.format(
                  action, original_stack_status, updated_stack_status))

        if action == 'DELETE' and stack and stack.status == 'IN_PROGRESS':
            # TODO(jdandrea): Consider moving this action to do_post_op.
            LOG.info(('Requesting plan delete for '
                      'stack "{}" ({})').format(stack.name, stack.id))
            try:
                self.api.plans_delete(stack)
            except exceptions.NotFoundError:
                # Be forgiving only if the plan wasn't found.
                # It might have been deleted via a direct API call.
                LOG.warn("Plan not found, proceeding with stack delete.")
        elif action == 'UPDATE' and stack \
                and current_stack and current_stack.status == 'IN_PROGRESS':
            LOG.info(('Building plan update request for '
                      'stack "{}" ({})').format(stack.name, stack.id))

            # For an update, stack has the *original* resource declarations.
            # current_stack has the updated resource declarations.
            resources = self._parse_stack(stack)
            if not resources:
                # Original stack had no resources for Valet. That's ok.
                LOG.warn("No prior resources found, proceeding")
            try:
                current_resources = self._parse_stack(current_stack, stack)
                if not current_resources:
                    # Updated stack has no resources for Valet. Also ok.
                    LOG.warn("No current resources found, skipping stack")
                    return
            except exceptions.ResourceUUIDMissingError:
                current_resources = {}

            plan = {
                'action': 'update',  # 'update' vs. 'migrate'
                'original_resources': resources,
                'resources': current_resources,
            }
            try:
                # Treat this as an update.
                self.api.plans_update(stack, plan)
            except exceptions.NotFoundError:
                # Valet hasn't seen this plan before (brownfield scenario).
                # Treat it as a create instead, using the current resources.
                LOG.warn("Plan not found, creating a new plan")
                plan = {
                    'plan_name': stack.name,
                    'stack_id': stack.id,
                    'resources': current_resources,
                }
                self.api.plans_create(stack, plan)
        elif action == 'CREATE' and stack and stack.status == 'IN_PROGRESS':
            LOG.info(('Building plan create request for '
                      'stack "{}" ({})').format(stack.name, stack.id))

            resources = self._parse_stack(stack)
            if not resources:
                LOG.warn("No resources found, skipping stack")
                return

            plan = {
                'plan_name': stack.name,
                'stack_id': stack.id,
                'resources': resources,
            }
            self.api.plans_create(stack, plan)

    def do_post_op(self, cnxt, stack, current_stack=None, action=None,
                   is_stack_failure=False):
        """Method run by heat after stack ops, including failures."""
        pass

    def get_ordinal(self):
        """An ordinal used to order class instances for pre/post ops."""
        return 100
