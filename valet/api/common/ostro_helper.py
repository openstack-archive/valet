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

"""Ostro helper library"""

import copy
import json
import time
import uuid

from pecan import conf

from valet.api.common.i18n import _
from valet.api.common import validation
from valet.api.db.models.music.groups import Group
from valet.api.db.models.music.ostro import PlacementRequest
from valet.api.db.models.music.ostro import PlacementResult
from valet.api.db.models import Query
from valet.api import LOG

SERVER = 'OS::Nova::Server'
SERVICEABLE_RESOURCES = [
    SERVER,
]
METADATA = 'metadata'
GROUP_ASSIGNMENT = 'OS::Valet::GroupAssignment'
GROUP_ID = 'group'
_GROUP_TYPES = (
    AFFINITY, DIVERSITY, EXCLUSIVITY,
) = (
    'affinity', 'diversity', 'exclusivity',
)


def _log(text, title="Ostro"):
    """Log helper"""
    log_text = "%s: %s" % (title, text)
    LOG.debug(log_text)


class Ostro(object):
    """Ostro optimization engine helper class."""

    args = None
    asynchronous = False
    request = None
    response = None
    error_uri = None
    tenant_id = None

    # Number of times to poll for placement.
    tries = None

    # Interval in seconds to poll for placement.
    interval = None

    # valet-engine response types
    _STATUS = (
        STATUS_OK, STATUS_ERROR,
    ) = (
        'ok', 'error',
    )

    @classmethod
    def _build_error(cls, message=None):
        """Build an Ostro-style error response"""
        if not message:
            message = _("Unknown error")
        return cls._build_response(cls.STATUS_ERROR, message)

    @classmethod
    def _build_ok(cls, message):
        """Build an Ostro-style ok response"""
        if not message:
            message = _("Unknown message")
        return cls._build_response(cls.STATUS_OK, message)

    @classmethod
    def _build_response(cls, status=None, message=None):
        """Build an Ostro-style response"""
        if status not in (cls._STATUS):
            status = cls.STATUS_ERROR
        if not message:
            message = _("Unknown")
        response = {
            'status': {
                'type': status,
                'message': message,
            }
        }
        return response

    def __init__(self):
        """Initializer"""
        self.tries = conf.music.get('tries', 1000)
        self.interval = conf.music.get('interval', 0.1)

    # TODO(JD): This really belongs in valet-engine once it exists.
    def _send(self, stack_id, request):
        """Send request."""
        # Creating the placement request effectively enqueues it.
        PlacementRequest(stack_id=stack_id, request=request)
        result_query = Query(PlacementResult)

        if self.asynchronous:
            message = _("Asynchronous request sent")
            LOG.info(_("{} for stack_id = {}").format(message, stack_id))
            response = self._build_ok(message)
            return json.dumps(response)

        for __ in range(self.tries, 0, -1):
            # Take a breather in between checks.
            # FIXME(jdandrea): This is blocking. Use futurist...
            # or oslo.message. Hint hint. :)
            time.sleep(self.interval)

            result = result_query.filter_by(stack_id=stack_id).first()
            if result:
                placement = result.placement
                result.delete()
                return placement

        self.error_uri = '/errors/server_error'
        message = _("Timed out waiting for a response")
        LOG.error(_("{} for stack_id = {}").format(message, stack_id))
        response = self._build_error(message)
        return json.dumps(response)

    def _resolve_group(self, group_id):
        """Resolve a group by ID or name"""
        if validation.is_valid_uuid4(group_id):
            group = Group.query.filter_by(id=group_id).first()
        else:
            group = Group.query.filter_by(name=group_id).first()
        if not group:
            self.error_uri = '/errors/not_found'
            message = _("Group '{}' not found").format(group_id)
            return (None, message)

        if not group.name or not group.type or not group.level:
            self.error_uri = '/errors/invalid'
            message = _("Group name, type, and level "
                        "must all be specified.")
            return (None, message)

        if group.type not in _GROUP_TYPES:
            self.error_uri = '/errors/invalid'
            message = _("Unknown group type '{}'.").format(
                group.type)
            return (None, message)
        elif (len(group.members) > 0 and
              self.tenant_id not in group.members):
            self.error_uri = '/errors/conflict'
            message = _("ID {} not a member of "
                        "group {} ({})").format(
                self.tenant_id, group.name, group.id)
            return (None, message)

        return (group, None)

    def _prepare_resources(self, resources):
        """Pre-digests resource data for use by Ostro.

        Maps Heat resource names to Orchestration UUIDs.
        Removes opaque metadata from resources.
        Ensures group assignments refer to valid groups.
        Ensures groups have tenant_id as a member.
        """

        # We're going to mess with the resources, so make a copy.
        res_copy = copy.deepcopy(resources)
        groups = {}
        message = None

        for res in res_copy.itervalues():
            if METADATA in res:
                # Discard valet-api-specific metadata.
                res.pop(METADATA)
            res_type = res.get('type')

            # If OS::Nova::Server has valet metadata, use it
            # to propagate group assignments to the engine.
            if res_type == SERVER:
                properties = res.get('properties')
                metadata = properties.get(METADATA, {})
                valet_metadata = metadata.get('valet', {})
                group_assignments = valet_metadata.get('groups', [])

                # Resolve all the groups and normalize the IDs.
                normalized_ids = []
                for group_id in group_assignments:
                    (group, message) = self._resolve_group(group_id)
                    if message:
                        return self._build_error(message)

                    # Normalize each group id
                    normalized_ids.append(group.id)

                    groups[group.id] = {
                        "name": group.name,
                        "type": group.type,
                        "level": group.level,
                    }

                # Update all the IDs with normalized values if we have 'em.
                if normalized_ids and valet_metadata:
                    valet_metadata['groups'] = normalized_ids

            # OS::Valet::GroupAssignment has been pre-empted.
            # We're opting to leave the existing/working logic as-is.
            # Propagate group assignment resources to the engine.
            if res_type == GROUP_ASSIGNMENT:
                properties = res.get('properties')
                group_id = properties.get(GROUP_ID)
                if not group_id:
                    self.error_uri = '/errors/invalid'
                    message = _("Property 'group' must be specified.")
                    break

                (group, message) = self._resolve_group(group_id)
                if message:
                    return self._build_error(message)

                # Normalize the group id
                properties[GROUP_ID] = group.id

                groups[group.id] = {
                    "name": group.name,
                    "type": group.type,
                    "level": group.level,
                }

        if message:
            return self._build_error(message)
        prepared_resources = {
            "resources": res_copy,
            "groups": groups,
        }
        return prepared_resources

    def is_request_serviceable(self):
        """Returns true if request has at least one serviceable resources."""
        # TODO(jdandrea): Ostro should return no placements vs throw an error.
        resources = self.request.get('resources', {})
        for res in resources.itervalues():
            res_type = res.get('type')
            if res_type and res_type in SERVICEABLE_RESOURCES:
                return True
        return False

    # FIXME(jdandrea): Change name to create_or_update
    def build_request(self, **kwargs):
        """Create or update a set of placements.

        If False is returned, response attribute contains error info.
        """

        self.args = kwargs.get('args')
        self.tenant_id = kwargs.get('tenant_id')
        self.response = None
        self.error_uri = None

        request = {
            "action": kwargs.get('action', 'create'),
            "stack_id": self.args.get('stack_id'),
            "tenant_id": self.tenant_id,
            "groups": {},  # Start with an empty dict to aid updates
        }

        # If we're updating, original_resources arg will have original info.
        # Get this info first.
        original_resources = self.args.get('original_resources')
        if original_resources:
            self.response = self._prepare_resources(original_resources)
            if 'status' in self.response:
                return False
            request['original_resources'] = self.response['resources']
            if 'groups' in self.response:
                request['groups'] = self.response['groups']

        # resources arg must always have new/updated info.
        resources = self.args.get('resources')
        self.response = self._prepare_resources(resources)
        if 'status' in self.response:
            return False
        request['resources'] = self.response['resources']
        if 'groups' in self.response:
            # Update groups dict with new/updated group info.
            request['groups'].update(self.response['groups'])

        locations = self.args.get('locations')
        if locations:
            request['locations'] = locations

        self.request = request
        return True

    def ping(self):
        """Send a ping request and obtain a response."""
        stack_id = str(uuid.uuid4())
        self.args = {'stack_id': stack_id}
        self.response = None
        self.error_uri = None
        self.request = {
            "action": "ping",
            "stack_id": stack_id,
        }

    def replan(self, **kwargs):
        """Replan a placement."""
        self.args = kwargs.get('args')
        self.response = None
        self.error_uri = None
        self.request = {
            "action": "replan",
            "stack_id": self.args['stack_id'],
            "locations": self.args['locations'],
            "resource_id": self.args['resource_id'],
            "orchestration_id": self.args['orchestration_id'],
            "exclusions": self.args['exclusions'],
        }

    def identify(self, **kwargs):
        """Identify a placement for an existing resource."""
        self.args = kwargs.get('args')
        self.response = None
        self.error_uri = None
        self.asynchronous = True
        self.request = {
            "action": "identify",
            "stack_id": self.args['stack_id'],
            "orchestration_id": self.args['orchestration_id'],
            "resource_id": self.args['uuid'],
        }

    def migrate(self, **kwargs):
        """Replan the placement for an existing resource."""
        self.args = kwargs.get('args')
        self.response = None
        self.error_uri = None
        self.request = {
            "action": "migrate",
            "stack_id": self.args['stack_id'],
            "tenant_id": self.args['tenant_id'],
            "excluded_hosts": self.args['excluded_hosts'],
            "orchestration_id": self.args['orchestration_id'],
        }

    def query(self, **kwargs):
        """Send a query."""
        stack_id = str(uuid.uuid4())
        self.args = kwargs.get('args')
        self.args['stack_id'] = stack_id
        self.response = None
        self.error_uri = None
        self.request = {
            "action": "query",
            "stack_id": self.args['stack_id'],
            "type": self.args['type'],
            "parameters": self.args['parameters'],
        }

    def send(self):
        """Send the request and obtain a response."""
        request_json = json.dumps([self.request])

        # TODO(JD): Pass timeout value?
        _log(request_json, 'Ostro Request')
        result = self._send(self.args['stack_id'], request_json)
        _log(result, 'Ostro Response')

        self.response = json.loads(result)

        status_type = self.response['status']['type']
        if status_type != 'ok':
            self.error_uri = '/errors/server_error'

        return self.response
