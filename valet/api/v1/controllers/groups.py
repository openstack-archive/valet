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

"""Groups"""

from notario import decorators
from notario.validators import types
from pecan import conf
from pecan import expose
from pecan import request
from pecan import response
from pecan_notario import validate

from valet import api
from valet.api.common.compute import nova_client
from valet.api.common.i18n import _
from valet.api.common.ostro_helper import Ostro
from valet.api.db.models import Group
from valet.api.v1.controllers import engine_query_args
from valet.api.v1.controllers import error
from valet.api.v1.controllers import valid_group_name

GROUPS_SCHEMA = (
    (decorators.optional('description'), types.string),
    ('level', types.string),
    ('name', valid_group_name),
    ('type', types.string),
)

# Schemas with one field MUST NOT get trailing commas, kthx.
UPDATE_GROUPS_SCHEMA = (
    (decorators.optional('description'), types.string))
MEMBERS_SCHEMA = (
    ('members', types.array))


def server_list_for_group(group):
    """Returns a list of VMs associated with a member/group."""
    parameters = {
        "group_name": group.name,
    }
    ostro_kwargs = engine_query_args(query_type="group_vms",
                                     parameters=parameters)
    ostro = Ostro()
    ostro.query(**ostro_kwargs)
    ostro.send()

    status_type = ostro.response['status']['type']
    if status_type != 'ok':
        message = ostro.response['status']['message']
        error(ostro.error_uri, _('Ostro error: %s') % message)

    resources = ostro.response['resources']
    return resources or []


def tenant_servers_in_group(tenant_id, group):
    """Returns a list of servers the current tenant has in group_name"""
    servers = []
    server_list = server_list_for_group(group)
    nova = nova_client()
    for server_id in server_list:
        try:
            server = nova.servers.get(server_id)
            if server.tenant_id == tenant_id:
                servers.append(server_id)
        except Exception as ex:  # TODO(JD): update DB
            api.LOG.error("Instance %s could not be found" % server_id)
            api.LOG.error(ex)
    if len(servers) > 0:
        return servers


def no_tenant_servers_in_group(tenant_id, group):
    """Verify no servers from tenant_id are in group.

    Throws a 409 Conflict if any are found.
    """
    server_list = tenant_servers_in_group(tenant_id, group)
    if server_list:
        msg = _('Tenant Member {0} has servers in group "{1}": {2}')
        error('/errors/conflict',
              msg.format(tenant_id, group.name, server_list))


class MembersItemController(object):
    """Members Item Controller /v1/groups/{group_id}/members/{member_id}"""

    def __init__(self, member_id):
        """Initialize group member"""
        group = request.context['group']
        if member_id not in group.members:
            error('/errors/not_found', _('Member not found in group'))
        request.context['member_id'] = member_id

    @classmethod
    def allow(cls):
        """Allowed methods"""
        return 'GET,DELETE'

    @expose(generic=True, template='json')
    def index(self):
        """Catch all for unallowed methods"""
        message = _('The %s method is not allowed.') % request.method
        kwargs = {'allow': self.allow()}
        error('/errors/not_allowed', message, **kwargs)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        """Options"""
        response.headers['Allow'] = self.allow()
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        """Verify group member"""
        response.status = 204

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        """Delete group member"""
        group = request.context['group']
        member_id = request.context['member_id']

        # Can't delete a member if it has associated VMs.
        no_tenant_servers_in_group(member_id, group)

        group.members.remove(member_id)
        group.update()
        response.status = 204


class MembersController(object):
    """Members Controller /v1/groups/{group_id}/members"""

    @classmethod
    def allow(cls):
        """Allowed methods"""
        return 'PUT,DELETE'

    @expose(generic=True, template='json')
    def index(self):
        """Catchall for unallowed methods"""
        message = _('The %s method is not allowed.') % request.method
        kwargs = {'allow': self.allow()}
        error('/errors/not_allowed', message, **kwargs)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        """Options"""
        response.headers['Allow'] = self.allow()
        response.status = 204

    @index.when(method='PUT', template='json')
    @validate(MEMBERS_SCHEMA, '/errors/schema')
    def index_put(self, **kwargs):
        """Add one or more members to a group"""
        new_members = kwargs.get('members', [])

        if not conf.identity.engine.is_tenant_list_valid(new_members):
            error('/errors/conflict',
                  _('Member list contains invalid tenant IDs'))

        group = request.context['group']
        member_list = group.members or []
        group.members = list(set(member_list + new_members))
        group.update()
        response.status = 201

        # Flush so that the DB is current.
        group.flush()
        return group

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        """Delete all group members"""
        group = request.context['group']

        # Can't delete a member if it has associated VMs.
        for member_id in group.members:
            no_tenant_servers_in_group(member_id, group)

        group.members = []
        group.update()
        response.status = 204

    @expose()
    def _lookup(self, member_id, *remainder):
        """Pecan subcontroller routing callback"""
        return MembersItemController(member_id), remainder


class GroupsItemController(object):
    """Groups Item Controller /v1/groups/{group_id}"""

    members = MembersController()

    def __init__(self, group_id):
        """Initialize group"""
        group = Group.query.filter_by(id=group_id).first()
        if not group:
            group = Group.query.filter_by(name=group_id).first()
            if not group:
                error('/errors/not_found', _('Group not found'))
        request.context['group'] = group

    @classmethod
    def allow(cls):
        """ Allowed methods """
        return 'GET,PUT,DELETE'

    @expose(generic=True, template='json')
    def index(self):
        """Catchall for unallowed methods"""
        message = _('The %s method is not allowed.') % request.method
        kwargs = {'allow': self.allow()}
        error('/errors/not_allowed', message, **kwargs)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        """Options"""
        response.headers['Allow'] = self.allow()
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        """Display a group"""
        return {"group": request.context['group']}

    @index.when(method='PUT', template='json')
    @validate(UPDATE_GROUPS_SCHEMA, '/errors/schema')
    def index_put(self, **kwargs):
        """Update a group"""
        # Name, type, and level are immutable.
        # Group Members are updated in MembersController.
        group = request.context['group']
        group.description = kwargs.get('description', group.description)
        group.update()
        response.status = 201

        # Flush so that the DB is current.
        group.flush()
        return group

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        """Delete a group"""
        group = request.context['group']
        # tenant_id = request.context['tenant_id']
        if isinstance(group.members, list) and len(group.members) > 0:
            message = _('Unable to delete a Group with members.')
            error('/errors/conflict', message)

        group.delete()
        response.status = 204


class GroupsController(object):
    """Groups Controller /v1/groups"""

    @classmethod
    def allow(cls):
        """Allowed methods"""
        return 'GET,POST'

    @expose(generic=True, template='json')
    def index(self):
        """Catch all for unallowed methods"""
        message = _('The %s method is not allowed.') % request.method
        kwargs = {'allow': self.allow()}
        error('/errors/not_allowed', message, **kwargs)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        """Options"""
        response.headers['Allow'] = self.allow()
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        """List groups"""
        try:
            groups_array = []
            for group in Group.query.all():
                groups_array.append(group)
        except Exception:
            import traceback
            api.LOG.error(traceback.format_exc())
            response.status = 500
        return {'groups': groups_array}

    @index.when(method='POST', template='json')
    @validate(GROUPS_SCHEMA, '/errors/schema')
    def index_post(self, **kwargs):
        """Create a group"""
        group_name = kwargs.get('name', None)
        description = kwargs.get('description', None)
        group_type = kwargs.get('type', None)
        group_level = kwargs.get('level', None)
        members = []  # Use /v1/groups/members endpoint to add members

        group = Group.query.filter_by(name=group_name).first()
        if group:
            message = _("A group named {} already exists")
            error('/errors/invalid', message.format(group_name))

        try:
            group = Group(group_name, description, group_type,
                          group_level, members)
            if group:
                response.status = 201

                # Flush so that the DB is current.
                group.flush()
                return group
        except Exception as e:
            error('/errors/server_error', _('Unable to create Group. %s') % e)

    @expose()
    def _lookup(self, group_id, *remainder):
        """Pecan subcontroller routing callback"""
        return GroupsItemController(group_id), remainder
