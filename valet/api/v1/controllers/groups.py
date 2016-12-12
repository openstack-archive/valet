# -*- encoding: utf-8 -*-
#
# Copyright (c) 2014-2016 AT&T
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

'''Groups'''

import logging

from notario import decorators
from notario.validators import types
from pecan import conf, expose, request, response
from pecan_notario import validate

from valet.api.common.compute import nova_client
from valet.api.common.i18n import _
from valet.api.common.ostro_helper import Ostro
from valet.api.db.models import Group
from valet.api.v1.controllers import error, valid_group_name

LOG = logging.getLogger(__name__)

GROUPS_SCHEMA = (
    (decorators.optional('description'), types.string),
    ('name', valid_group_name),
    ('type', types.string)
)

UPDATE_GROUPS_SCHEMA = (
    (decorators.optional('description'), types.string)
)

MEMBERS_SCHEMA = (
    ('members', types.array)
)

# pylint: disable=R0201


def server_list_for_group(group):
    '''Returns a list of VMs associated with a member/group.'''
    args = {
        "type": "group_vms",
        "parameters": {
            "group_name": group.name,
        },
    }
    ostro_kwargs = {
        "args": args,
    }
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
    ''' Returns a list of servers the current tenant has in group_name '''
    servers = []
    server_list = server_list_for_group(group)
    nova = nova_client()
    for server_id in server_list:
        try:
            server = nova.servers.get(server_id)
            if server.tenant_id == tenant_id:
                servers.append(server_id)
        except Exception as ex:  # TODO(JD): update DB
            LOG.error("Instance %s could not be found" % server_id)
            LOG.error(ex)
    if len(servers) > 0:
        return servers


def no_tenant_servers_in_group(tenant_id, group):
    ''' Verify no servers from tenant_id are in group.

    Throws a 409 Conflict if any are found.
    '''
    server_list = tenant_servers_in_group(tenant_id, group)
    if server_list:
        error('/errors/conflict', _('Tenant Member {0} has servers in group "{1}": {2}').format(tenant_id, group.name, server_list))


class MembersItemController(object):
    ''' Members Item Controller /v1/groups/{group_id}/members/{member_id} '''

    def __init__(self, member_id):
        '''Initialize group member'''
        group = request.context['group']
        if member_id not in group.members:
            error('/errors/not_found', _('Member not found in group'))
        request.context['member_id'] = member_id

    @classmethod
    def allow(cls):
        '''Allowed methods'''
        return 'GET,DELETE'

    @expose(generic=True, template='json')
    def index(self):
        '''Catch all for unallowed methods'''
        message = _('The %s method is not allowed.') % request.method
        kwargs = {'allow': self.allow()}
        error('/errors/not_allowed', message, **kwargs)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        '''Options'''
        response.headers['Allow'] = self.allow()
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        '''Verify group member'''
        response.status = 204

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        '''Delete group member'''
        group = request.context['group']
        member_id = request.context['member_id']

        # Can't delete a member if it has associated VMs.
        no_tenant_servers_in_group(member_id, group)

        group.members.remove(member_id)
        group.update()
        response.status = 204


class MembersController(object):
    ''' Members Controller /v1/groups/{group_id}/members '''

    @classmethod
    def allow(cls):
        '''Allowed methods'''
        return 'PUT,DELETE'

    @expose(generic=True, template='json')
    def index(self):
        '''Catchall for unallowed methods'''
        message = _('The %s method is not allowed.') % request.method
        kwargs = {'allow': self.allow()}
        error('/errors/not_allowed', message, **kwargs)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        '''Options'''
        response.headers['Allow'] = self.allow()
        response.status = 204

    @index.when(method='PUT', template='json')
    @validate(MEMBERS_SCHEMA, '/errors/schema')
    def index_put(self, **kwargs):
        '''Add one or more members to a group'''
        new_members = kwargs.get('members', None)

        if not conf.identity.engine.is_tenant_list_valid(new_members):
            error('/errors/conflict', _('Member list contains invalid tenant IDs'))

        group = request.context['group']
        group.members = list(set(group.members + new_members))
        group.update()
        response.status = 201

        # Flush so that the DB is current.
        group.flush()
        return group

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        '''Delete all group members'''
        group = request.context['group']

        # Can't delete a member if it has associated VMs.
        for member_id in group.members:
            no_tenant_servers_in_group(member_id, group)

        group.members = []
        group.update()
        response.status = 204

    @expose()
    def _lookup(self, member_id, *remainder):
        '''Pecan subcontroller routing callback'''
        return MembersItemController(member_id), remainder


class GroupsItemController(object):
    ''' Groups Item Controller /v1/groups/{group_id} '''

    members = MembersController()

    def __init__(self, group_id):
        '''Initialize group'''
        group = Group.query.filter_by(id=group_id).first()  # pylint: disable=E1101
        if not group:
            error('/errors/not_found', _('Group not found'))
        request.context['group'] = group

    @classmethod
    def allow(cls):
        ''' Allowed methods '''
        return 'GET,PUT,DELETE'

    @expose(generic=True, template='json')
    def index(self):
        '''Catchall for unallowed methods'''
        message = _('The %s method is not allowed.') % request.method
        kwargs = {'allow': self.allow()}
        error('/errors/not_allowed', message, **kwargs)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        '''Options'''
        response.headers['Allow'] = self.allow()
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        '''Display a group'''
        return {"group": request.context['group']}

    @index.when(method='PUT', template='json')
    @validate(UPDATE_GROUPS_SCHEMA, '/errors/schema')
    def index_put(self, **kwargs):
        '''Update a group'''
        # Name and type are immutable.
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
        '''Delete a group'''
        group = request.context['group']
        if isinstance(group.members, list) and len(group.members) > 0:
            error('/errors/conflict', _('Unable to delete a Group with members.'))
        group.delete()
        response.status = 204


class GroupsController(object):
    ''' Groups Controller /v1/groups '''

    @classmethod
    def allow(cls):
        '''Allowed methods'''
        return 'GET,POST'

    @expose(generic=True, template='json')
    def index(self):
        '''Catch all for unallowed methods'''
        message = _('The %s method is not allowed.') % request.method
        kwargs = {'allow': self.allow()}
        error('/errors/not_allowed', message, **kwargs)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        '''Options'''
        response.headers['Allow'] = self.allow()
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        '''List groups'''
        groups_array = []
        for group in Group.query.all():  # pylint: disable=E1101
            groups_array.append(group)
        return {'groups': groups_array}

    @index.when(method='POST', template='json')
    @validate(GROUPS_SCHEMA, '/errors/schema')
    def index_post(self, **kwargs):
        '''Create a group'''
        group_name = kwargs.get('name', None)
        description = kwargs.get('description', None)
        group_type = kwargs.get('type', None)
        members = []  # Use /v1/groups/members endpoint to add members

        try:
            group = Group(group_name, description, group_type, members)
            if group:
                response.status = 201

                # Flush so that the DB is current.
                group.flush()
                return group
        except Exception as e:
            error('/errors/server_error', _('Unable to create Group. %s') % e)

    @expose()
    def _lookup(self, group_id, *remainder):
        '''Pecan subcontroller routing callback'''
        return GroupsItemController(group_id), remainder
