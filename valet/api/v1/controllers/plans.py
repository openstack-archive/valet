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

"""Plans"""

from notario import decorators
from notario.validators import types
from pecan import expose
from pecan import request
from pecan import response
from pecan_notario import validate

from valet.api.common.i18n import _
from valet.api.common.ostro_helper import Ostro
from valet.api.db.models.music.placements import Placement
from valet.api.db.models.music.plans import Plan
from valet.api import LOG
from valet.api.v1.controllers import error
from valet.api.v1.controllers import list_or_dict
from valet.api.v1.controllers import set_placements
from valet.api.v1.controllers import update_placements
from valet.api.v1.controllers import valid_plan_update_action

CREATE_SCHEMA = (
    (decorators.optional('locations'), types.array),
    ('plan_name', types.string),
    ('resources', types.dictionary),
    ('stack_id', types.string),
    (decorators.optional('timeout'), types.string))

UPDATE_SCHEMA = (
    ('action', valid_plan_update_action),
    (decorators.optional('excluded_hosts'), types.array),
    (decorators.optional('original_resources'), types.dictionary),
    (decorators.optional('plan_name'), types.string),
    ('resources', list_or_dict),  # list: migrate, dict: update
    (decorators.optional('timeout'), types.string))


class PlansItemController(object):
    """Plans Item Controller /v1/plans/{plan_id}"""

    def __init__(self, uuid4):
        """Initializer."""
        self.uuid = uuid4
        self.plan = Plan.query.filter_by(id=self.uuid).first()

        if not self.plan:
            self.plan = Plan.query.filter_by(stack_id=self.uuid).first()

            if not self.plan:
                error('/errors/not_found', _('Plan not found'))
        request.context['plan_id'] = self.plan.id

    @classmethod
    def allow(cls):
        """Allowed methods"""
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
        """Get plan"""
        return {"plan": self.plan}

    @index.when(method='PUT', template='json')
    @validate(UPDATE_SCHEMA, '/errors/schema')
    def index_put(self, **kwargs):
        """Update a Plan"""
        ostro = Ostro()
        action = kwargs.get('action', 'update')
        if action == 'migrate':
            # Replan the placement of an existing resource.
            excluded_hosts = kwargs.get('excluded_hosts', [])
            resources = kwargs.get('resources', [])

            # TODO(JD): Support replan of more than one existing resource
            if not isinstance(resources, list) or len(resources) != 1:
                error('/errors/invalid',
                      _('resources must be a list of length 1.'))

            # We either got a resource or orchestration id.
            the_id = resources[0]
            placement = Placement.query.filter_by(resource_id=the_id).first()
            if not placement:
                placement = Placement.query.filter_by(
                    orchestration_id=the_id).first()
                if not placement:
                    msg = _('Unknown resource or orchestration id: %s')
                    error('/errors/invalid', msg.format(the_id))

            msg = _('Migration request for resource id {0}, '
                    'orchestration id {1}.')
            LOG.info(msg.format(placement.resource_id,
                                placement.orchestration_id))
            args = {
                "stack_id": self.plan.stack_id,
                "tenant_id": request.context['tenant_id'],
                "excluded_hosts": excluded_hosts,
                "orchestration_id": placement.orchestration_id,
            }
            ostro_kwargs = {
                "args": args,
            }
            ostro.migrate(**ostro_kwargs)
            ostro.send()

            status_type = ostro.response['status']['type']
            if status_type != 'ok':
                message = ostro.response['status']['message']
                error(ostro.error_uri, _('Ostro error: %s') % message)

            placements = ostro.response['resources']
            update_placements(placements, unlock_all=True)
            response.status = 201

            # Flush so that the DB is current.
            self.plan.flush()
            self.plan = Plan.query.filter_by(
                stack_id=self.plan.stack_id).first()
            LOG.info(_('Plan with stack id %s updated.'), self.plan.stack_id)
            return {"plan": self.plan}
        elif action == 'update':
            # Update an existing plan.
            resources = kwargs.get('resources', [])

            if not isinstance(resources, dict):
                error('/errors/invalid', _('resources must be a dictionary.'))

            ostro_kwargs = {
                'action': 'update',
                'tenant_id': request.context['tenant_id'],
                'args': kwargs,
            }

            # stack_id comes from the plan at update-time
            ostro_kwargs['args']['stack_id'] = self.plan.stack_id

            # Prepare the request. If request prep fails,
            # an error message will be in the response.
            # Though the Ostro helper reports the error,
            # we cite it as a Valet error.
            if not ostro.build_request(**ostro_kwargs):
                message = ostro.response['status']['message']
                error(ostro.error_uri, _('Valet error: %s') % message)

            # If there are no serviceable resources, bail. Not an error.
            # Treat it as if an "empty plan" was created.
            # FIXME: Ostro should likely handle this and not error out.
            if not ostro.is_request_serviceable():
                LOG.info(_('Plan has no serviceable resources. Skipping.'))
                response.status = 201
                return {"plan": self.plan}

            ostro.send()
            status_type = ostro.response['status']['type']
            if status_type != 'ok':
                message = ostro.response['status']['message']
                error(ostro.error_uri, _('Ostro error: %s') % message)

            resources = ostro.request['resources']
            placements = ostro.response['resources']

            update_placements(placements, plan=self.plan, resources=resources)
            response.status = 201

            # Flush so that the DB is current.
            self.plan.flush()
            LOG.info(_('Plan with stack id %s updated.'), self.plan.stack_id)
            return {"plan": self.plan}

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        """Delete a Plan"""
        for placement in self.plan.placements():
            placement.delete()
        stack_id = self.plan.stack_id
        self.plan.delete()
        LOG.info(_('Plan with stack id %s deleted.'), stack_id)
        response.status = 204


class PlansController(object):
    """Plans Controller /v1/plans"""

    @classmethod
    def allow(cls):
        """Allowed methods"""
        return 'GET,POST'

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
        """Get all the plans"""
        plans_array = []
        for plan in Plan.query.all():
            plans_array.append(plan)
        return {"plans": plans_array}

    @index.when(method='POST', template='json')
    @validate(CREATE_SCHEMA, '/errors/schema')
    def index_post(self):
        """Create a Plan"""
        ostro = Ostro()
        args = request.json

        kwargs = {
            'action': 'create',
            'tenant_id': request.context['tenant_id'],
            'args': args,
        }

        # Prepare the request. If request prep fails,
        # an error message will be in the response.
        # Though the Ostro helper reports the error,
        # we cite it as a Valet error.
        if not ostro.build_request(**kwargs):
            message = ostro.response['status']['message']
            error(ostro.error_uri, _('Valet error: %s') % message)

        # If there are no serviceable resources, bail. Not an error.
        # Treat it as if an "empty plan" was created.
        # FIXME: Ostro should likely handle this and not error out.
        if not ostro.is_request_serviceable():
            LOG.info(_('Plan has no serviceable resources. Skipping.'))
            response.status = 201
            return {"plan": {}}

        ostro.send()
        status_type = ostro.response['status']['type']
        if status_type != 'ok':
            message = ostro.response['status']['message']
            error(ostro.error_uri, _('Ostro error: %s') % message)

        plan_name = args['plan_name']
        stack_id = args['stack_id']
        resources = ostro.request['resources']
        placements = ostro.response['resources']

        plan = Plan(plan_name, stack_id)
        if plan:
            set_placements(plan, resources, placements)
            response.status = 201

            # Flush so that the DB is current.
            plan.flush()
            LOG.info(_('Plan with stack id %s created.'), plan.stack_id)
            return {"plan": plan}
        else:
            error('/errors/server_error', _('Unable to create Plan.'))

    @expose()
    def _lookup(self, uuid4, *remainder):
        """Pecan subcontroller routing callback"""
        return PlansItemController(uuid4), remainder
