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

"""Group Heat Resource Plugin"""

from heat.common import exception as heat_exception
from heat.common.i18n import _
from heat.engine import attributes
from heat.engine import constraints
from heat.engine import properties
from heat.engine import resource
from heat.engine.resources import scheduler_hints as sh
from heat.engine import support
from oslo_log import log as logging

from plugins.common import valet_api
from plugins import exceptions

LOG = logging.getLogger(__name__)


class Group(resource.Resource, sh.SchedulerHintsMixin):
    """Valet Group Resource

    A Group is used to define a particular association amongst
    resources. Groups may be used only by their assigned members,
    currently identified by project (tenant) IDs. If no members are
    assigned, any project (tenant) may assign resources to the group.

    There are three types of groups: affinity, diversity, and exclusivity.
    There are two levels: host and rack.

    All groups must have a unique name, regardless of how they were created
    and regardless of membership.

    There is no lone group owner. Any user with an admin role, regardless
    of project/tenant, can edit or delete the group.
    """

    support_status = support.SupportStatus(version='2015.1')

    _LEVEL_TYPES = (
        HOST, RACK,
    ) = (
        'host', 'rack',
    )

    _RELATIONSHIP_TYPES = (
        AFFINITY, DIVERSITY, EXCLUSIVITY,
    ) = (
        'affinity', 'diversity', 'exclusivity',
    )

    PROPERTIES = (
        DESCRIPTION, LEVEL, MEMBERS, NAME, TYPE,
    ) = (
        'description', 'level', 'members', 'name', 'type',
    )

    ATTRIBUTES = (
        DESCRIPTION_ATTR, LEVEL_ATTR, MEMBERS_ATTR, NAME_ATTR, TYPE_ATTR,
    ) = (
        'description', 'level', 'members', 'name', 'type',
    )

    properties_schema = {
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of group.'),
            required=False,
            update_allowed=True
        ),
        LEVEL: properties.Schema(
            properties.Schema.STRING,
            _('Level of relationship between resources.'),
            constraints=[
                constraints.AllowedValues([HOST, RACK])
            ],
            required=True,
            update_allowed=False
        ),
        MEMBERS: properties.Schema(
            properties.Schema.LIST,
            _('List of one or more member IDs allowed to use this group.'),
            required=False,
            update_allowed=True
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of group.'),
            constraints=[
                constraints.CustomConstraint('valet.group_name'),
            ],
            required=True,
            update_allowed=False
        ),
        TYPE: properties.Schema(
            properties.Schema.STRING,
            _('Type of group.'),
            constraints=[
                constraints.AllowedValues([AFFINITY, DIVERSITY, EXCLUSIVITY])
            ],
            required=True,
            update_allowed=False
        ),
    }

    # To maintain Kilo compatibility, do not use "type" here.
    attributes_schema = {
        DESCRIPTION_ATTR: attributes.Schema(
            _('Description of group.')
        ),
        LEVEL_ATTR: attributes.Schema(
            _('Level of relationship between resources.')
        ),
        MEMBERS_ATTR: attributes.Schema(
            _('List of one or more member IDs allowed to use this group.')
        ),
        NAME_ATTR: attributes.Schema(
            _('Name of group.')
        ),
        TYPE_ATTR: attributes.Schema(
            _('Type of group.')
        ),
    }

    def __init__(self, name, json_snippet, stack):
        """Initialization"""
        super(Group, self).__init__(name, json_snippet, stack)
        self.api = valet_api.ValetAPI()
        self.api.auth_token = self.context.auth_token
        self._group = None

    def _get_resource(self):
        if self._group is None and self.resource_id is not None:
            try:
                groups = self.api.groups_get(
                    self.resource_id)
                if groups:
                    self._group = groups.get('group', {})
            except exceptions.NotFoundError:
                # Ignore Not Found and fall through
                pass

        return self._group

    def _group_name(self):
        """Group Name"""
        name = self.properties.get(self.NAME)
        if name:
            return name

        return self.physical_resource_name()

    def FnGetRefId(self):
        """Get Reference ID"""
        return self.physical_resource_name_or_FnGetRefId()

    def handle_create(self):
        """Create resource"""
        if self.resource_id is not None:
            # TODO(jdandrea): Delete the resource and re-create?
            # I've seen this called if a stack update fails.
            # For now, just leave it be.
            return

        group_type = self.properties.get(self.TYPE)
        level = self.properties.get(self.LEVEL)
        description = self.properties.get(self.DESCRIPTION)
        members = self.properties.get(self.MEMBERS)
        group_args = {
            'name': self._group_name(),
            'type': group_type,
            'level': level,
            'description': description,
        }
        kwargs = {
            'group': group_args,
        }

        # Create the group first. If an exception is
        # thrown by groups_create, let Heat catch it.
        group = self.api.groups_create(**kwargs)
        if group is not None and 'id' in group:
            self.resource_id_set(group.get('id'))
        else:
            raise heat_exception.ResourceNotAvailable(
                resource_name=self._group_name())

        # Now add members to the group
        if members:
            kwargs = {
                'group_id': self.resource_id,
                'members': members,
            }
            err = None
            group = None
            try:
                group = self.api.groups_members_update(**kwargs)
            except exceptions.PythonAPIError as err:
                # Hold on to err. We'll use it in a moment.
                pass
            finally:
                if group is None:
                    # Members couldn't be added.
                    # Delete the group we just created.
                    kwargs = {
                        'group_id': self.resource_id,
                    }
                    try:
                        self.api.groups_delete(**kwargs)
                    except exceptions.PythonAPIError:
                        # Ignore group deletion errors.
                        pass
                    if err:
                        raise err
                    else:
                        raise heat_exception.ResourceNotAvailable(
                            resource_name=self._group_name())

    def handle_update(self, json_snippet, templ_diff, prop_diff):
        """Update resource"""
        if prop_diff:
            if self.DESCRIPTION in prop_diff:
                description = prop_diff.get(
                    self.DESCRIPTION, self.properties.get(self.DESCRIPTION))

                # If an exception is thrown by groups_update,
                # let Heat catch it. Let the state remain as-is.
                kwargs = {
                    'group_id': self.resource_id,
                    'group': {
                        self.DESCRIPTION: description,
                    },
                }
                self.api.groups_update(**kwargs)

            if self.MEMBERS in prop_diff:
                members_update = prop_diff.get(self.MEMBERS, [])
                members = self.properties.get(self.MEMBERS, [])

                # Delete original members not in updated list.
                # If an exception is thrown by groups_member_delete,
                # let Heat catch it. Let the state remain as-is.
                member_deletions = set(members) - set(members_update)
                for member_id in member_deletions:
                    kwargs = {
                        'group_id': self.resource_id,
                        'member_id': member_id,
                    }
                    self.api.groups_member_delete(**kwargs)

                # Add members_update members not in original list.
                # If an exception is thrown by groups_members_update,
                # let Heat catch it. Let the state remain as-is.
                member_additions = set(members_update) - set(members)
                if member_additions:
                    kwargs = {
                        'group_id': self.resource_id,
                        'members': list(member_additions),
                    }
                    self.api.groups_members_update(**kwargs)

            # Clear cached group info
            self._group = None

    def handle_delete(self):
        """Delete resource"""
        if self.resource_id is None:
            return

        kwargs = {
            'group_id': self.resource_id,
        }

        group = self._get_resource()
        if group:
            # First, delete all the members
            members = group.get('members', [])
            if members:
                try:
                    self.api.groups_members_delete(**kwargs)
                except exceptions.NotFoundError:
                    # Ignore Not Found and fall through
                    pass

            # Now delete the group.
            try:
                response = self.api.groups_delete(**kwargs)
                if type(response) is dict and len(response) == 0:
                    self.resource_id_set(None)
                    self._group = None
            except exceptions.NotFoundError:
                # Ignore Not Found and fall through
                pass

    def _resolve_attribute(self, key):
        """Resolve Attributes"""
        if self.resource_id is None:
            return
        group = self._get_resource()
        if group:
            attributes = {
                self.NAME_ATTR: group.get(self.NAME),
                self.TYPE_ATTR: group.get(self.TYPE),
                self.LEVEL_ATTR: group.get(self.LEVEL),
                self.DESCRIPTION_ATTR: group.get(self.DESCRIPTION),
                self.MEMBERS_ATTR: group.get(self.MEMBERS, []),
            }
            return attributes.get(key)


def resource_mapping():
    """Map names to resources."""
    return {
        'OS::Valet::Group': Group,
    }
