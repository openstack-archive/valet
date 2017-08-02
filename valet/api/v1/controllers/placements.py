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
from pecan import expose
from pecan import request
from pecan import response

"""Placements"""

import json

from pecan import expose, request, response

from valet import api
from valet.api.common.i18n import _
from valet.api.common.ostro_helper import Ostro
from valet.api.db.models import Placement, Plan
from valet.api.v1.controllers import error
from valet.api.v1.controllers import reserve_placement
from valet.api.v1.controllers import update_placements


class PlacementsItemController(object):
    """Placements Item Controller /v1/placements/{placement_id}"""

    def __init__(self, uuid4):
        """Initializer."""
        self.uuid = uuid4
        self.placement = Placement.query.filter_by(id=self.uuid).first()
        if not self.placement:
            self.placement = Placement.query.filter_by(
                orchestration_id=self.uuid).first()
            if not self.placement:
                error('/errors/not_found', _('Placement not found'))
        request.context['placement_id'] = self.placement.id

    @classmethod
    def allow(cls):
        """Allowed methods"""
        return 'GET,POST,DELETE'

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
        """Inspect a placement.

        Use POST for reserving placements made by a scheduler.
        """
        return {"placement": self.placement}

    @index.when(method='POST', template='json')
    def index_post(self, **kwargs):
        """Reserve a placement. This and other placements may be replanned.

        Once reserved, the location effectively becomes immutable unless
        a replan is forced (due to a resource replacement, for example).
        """
        res_id = kwargs.get('resource_id')
        api.LOG.info(_('Placement reservation request for resource \
                        id %(res_id)s, orchestration id %(orch_id)s.'),
                     {'res_id': res_id,
                      'orch_id': self.placement.orchestration_id})

        actions = ('reserve', 'replan')
        action = kwargs.get('action', 'reserve')
        if action not in actions:
            message = _('Invalid action: {}. Must be one of {}')
            error('/errors/invalid', message.format(action, actions))

        locations = kwargs.get('locations', [])
        locations_str = ', '.join(locations)
        api.LOG.info(_('Candidate locations: %s'), locations_str)
        if action == 'reserve' and self.placement.location in locations:
            # Ostro's placement is in the list of candidates. Good!
            # But first, we have to pass the engine's identify test.

            plan = Plan.query.filter_by(id=self.placement.plan_id).first()

            args = {
                "stack_id": plan.stack_id,
                "orchestration_id": self.placement.orchestration_id,
                "uuid": res_id,
            }
            ostro_kwargs = {"args": args, }
            ostro = Ostro()
            ostro.identify(**ostro_kwargs)
            ostro.send()

            status_type = ostro.response['status']['type']
            if status_type != 'ok':
                message = ostro.response['status']['message']
                error(ostro.error_uri, _('Ostro error: %s') % message)

            # We're in the clear. Reserve it. Remember the resource id too.
            kwargs = {'resource_id': res_id}
            reserve_placement(self.placement, **kwargs)
            response.status = 201
        else:
            if action == 'reserve':
                # Ostro's placement is NOT in the list of candidates.
                # Time for Plan B.
                api.LOG.info(_('Placement of resource id %(res_id)s, \
                                orchestration id %(orch_id)s in %(loc)s \
                                not allowed. Replanning.'),
                             {'res_id': res_id,
                              'orch_id': self.placement.orchestration_id,
                              'loc': self.placement.location})
            else:
                # A replan was expressly requested (action == 'replan')
                api.LOG.info(_('Replanning resource id %(res_id)s, \
                                orchestration id %(orch_id)s.'),
                             {'res_id': res_id,
                              'orch_id': self.placement.orchestration_id})

            # Unreserve the placement. Remember the resource id too.
            kwargs = {'resource_id': res_id, 'reserve': False}
            reserve_placement(self.placement, **kwargs)

            # Find all the reserved placements for the related plan.
            reserved = Placement.query.filter_by(
                plan_id=self.placement.plan_id, reserved=True)

            # Keep this placement's orchestration ID handy.
            orchestration_id = self.placement.orchestration_id

            # Extract all the orchestration IDs.
            exclusions = [x.orchestration_id for x in reserved]
            if exclusions:
                exclusions_str = ', '.join(exclusions)
                api.LOG.info(_('Excluded orchestration IDs: %s'),
                             exclusions_str)
            else:
                api.LOG.info(_('No excluded orchestration IDs.'))

            # Ask Ostro to try again with new constraints.
            # We may get one or more updated placements in return.
            # One of those will be the original placement
            # we are trying to reserve.
            plan = Plan.query.filter_by(id=self.placement.plan_id).first()

            args = {
                "stack_id": plan.stack_id,
                "locations": locations,
                "resource_id": res_id,
                "orchestration_id": orchestration_id,
                "exclusions": exclusions,
            }
            ostro_kwargs = {"args": args, }
            ostro = Ostro()
            ostro.replan(**ostro_kwargs)
            ostro.send()

            status_type = ostro.response['status']['type']
            if status_type != 'ok':
                message = ostro.response['status']['message']
                error(ostro.error_uri, _('Ostro error: %s') % message)

            # Update all affected placements. Reserve the original one.
            placements = ostro.response['resources']
            update_placements(placements, reserve_id=orchestration_id)
            response.status = 201

        placement = Placement.query.filter_by(
            orchestration_id=self.placement.orchestration_id).first()
        return {"placement": placement}

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        """Delete a Placement"""
        orch_id = self.placement.orchestration_id
        self.placement.delete()
        api.LOG.info(_('Placement with orchestration id %s deleted.'),
                     orch_id)
        response.status = 204


class PlacementsController(object):
    """Placements Controller /v1/placements"""

    @classmethod
    def allow(cls):
        """Allowed methods"""
        return 'GET'

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
    def index_get(self, **kwargs):
        """Get placements."""
        placements_array = []
        for placement in Placement.query.all():
            # If there are query string args, look for them in two places,
            # and in this order:
            #
            # 1. The main placement object, only for these reserved
            #    keys: id, orchestration_id, plan_id, resource_id,
            #          location, name, reserved.
            # 2. The metadata.
            #
            # Support only exact matches for now. AND, not OR.
            #
            # Start by presuming we have a match, and look for fail cases.
            # If search fails, no error, just don't append that placement.
            # This also ends up appending if there are no kwargs (good).
            append = True
            for key, value in kwargs.iteritems():
                # We don't allow the same key multiple times, so no lists,
                # only strings. Don't even allow NoneType.
                if not isinstance(value, basestring):
                    append = False
                    break

                # Try loading as if it were json. If we can't, that's ok.
                try:
                    # Using json_value to prevent side-effects.
                    json_value = json.loads(value)
                    value = json_value
                except (TypeError, ValueError):
                    pass

                # 1. If the key is one of our reserved keys ...
                if key in ('id', 'orchestration_id', 'plan_id',
                           'resource_id', 'location', 'name',
                           'reserved') and hasattr(placement, key):
                    # ... and the value does not match in the main object,
                    # don't append it, and don't go on to check metadata.
                    if value != getattr(placement, key):
                        append = False
                        break
                # 2. Otherwise, if the key is not in the metadata or
                #    the value does not match, don't append it.
                elif key not in placement.metadata \
                    or value != placement.metadata.get(key):
                    append = False
                    break

            if append:
                placements_array.append(placement)

        return {"placements": placements_array}

    @expose()
    def _lookup(self, uuid4, *remainder):
        """Pecan subcontroller routing callback"""
        return PlacementsItemController(uuid4), remainder
