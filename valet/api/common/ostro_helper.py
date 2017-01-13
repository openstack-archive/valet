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

"""Ostro helper library."""

import json
import logging

from pecan import conf
import time

import uuid
from valet.api.common.i18n import _
from valet.api.db.models import Group
from valet.api.db.models import PlacementRequest
from valet.api.db.models import PlacementResult
from valet.api.db.models import Query

LOG = logging.getLogger(__name__)

SERVICEABLE_RESOURCES = [
    'OS::Nova::Server'
]
GROUP_ASSIGNMENT = 'ATT::Valet::GroupAssignment'
GROUP_TYPE = 'group_type'
GROUP_NAME = 'group_name'
AFFINITY = 'affinity'
DIVERSITY = 'diversity'
EXCLUSIVITY = 'exclusivity'


def _log(text, title="Ostro"):
    """Log helper."""
    log_text = "%s: %s" % (title, text)
    LOG.debug(log_text)


class Ostro(object):
    """Ostro optimization engine helper class."""

    args = None
    request = None
    response = None
    error_uri = None
    tenant_id = None

    # Number of times to poll for placement.
    tries = None

    # Interval in seconds to poll for placement.
    interval = None

    @classmethod
    def _build_error(cls, message):
        """Build an Ostro-style error message."""
        if not message:
            message = _("Unknown error")
        error = {
            'status': {
                'type': 'error',
                'message': message,
            }
        }
        return error

    @classmethod
    def _build_uuid_map(cls, resources):
        """Build a dict mapping names to UUIDs."""
        mapping = {}
        for key in resources.iterkeys():
            if 'name' in resources[key]:
                name = resources[key]['name']
                mapping[name] = key
        return mapping

    @classmethod
    def _sanitize_resources(cls, resources):
        """Ensure lowercase keys at the top level of each resource."""
        for res in resources.itervalues():
            for key in list(res.keys()):
                if not key.islower():
                    res[key.lower()] = res.pop(key)
        return resources

    def __init__(self):
        """Initializer."""
        self.tries = conf.music.get('tries', 10)
        self.interval = conf.music.get('interval', 1)

    def _map_names_to_uuids(self, mapping, data):
        """Map resource names to their UUID equivalents."""
        if isinstance(data, dict):
            for key in data.iterkeys():
                if key != 'name':
                    data[key] = self._map_names_to_uuids(mapping, data[key])
        elif isinstance(data, list):
            for key, value in enumerate(data):
                data[key] = self._map_names_to_uuids(mapping, value)
        elif isinstance(data, basestring) and data in mapping:
            return mapping[data]
        return data

    def _prepare_resources(self, resources):
        """Pre-digest resource data for use by Ostro.

        Maps Heat resource names to Orchestration UUIDs.
        Ensures exclusivity groups exist and have tenant_id as a member.
        """
        mapping = self._build_uuid_map(resources)
        ostro_resources = self._map_names_to_uuids(mapping, resources)
        self._sanitize_resources(ostro_resources)

        verify_error = self._verify_groups(ostro_resources, self.tenant_id)
        if isinstance(verify_error, dict):
            return verify_error
        return {'resources': ostro_resources}

    # TODO(JD): This really belongs in valet-engine once it exists.
    def _send(self, stack_id, request):
        """Send request."""
        # Creating the placement request effectively enqueues it.
        PlacementRequest(stack_id=stack_id, request=request)  # pylint: disable=W0612

        # Wait for a response.
        # TODO(JD): This is a blocking operation at the moment.
        for __ in range(self.tries, 0, -1):  # pylint: disable=W0612
            query = Query(PlacementResult)
            placement_result = query.filter_by(stack_id=stack_id).first()
            if placement_result:
                placement = placement_result.placement
                placement_result.delete()
                return placement
            else:
                time.sleep(self.interval)

        self.error_uri = '/errors/server_error'
        message = "Timed out waiting for a response."
        response = self._build_error(message)
        return json.dumps(response)

    def _verify_groups(self, resources, tenant_id):
        """Verify group settings.

        Returns an error status dict if the group type is invalid, if a
        group name is used when the type is affinity or diversity, if a
        nonexistant exclusivity group is found, or if the tenant
        is not a group member. Returns None if ok.
        """
        message = None
        for res in resources.itervalues():
            res_type = res.get('type')
            if res_type == GROUP_ASSIGNMENT:
                properties = res.get('properties')
                group_type = properties.get(GROUP_TYPE, '').lower()
                group_name = properties.get(GROUP_NAME, '').lower()
                if group_type == AFFINITY or \
                   group_type == DIVERSITY:
                    if group_name:
                        self.error_uri = '/errors/conflict'
                        message = _("%s must not be used when"
                                    " {0} is '{1}'.").format(GROUP_NAME,
                                                             GROUP_TYPE,
                                                             group_type)
                        break
                elif group_type == EXCLUSIVITY:
                    message = self._verify_exclusivity(group_name, tenant_id)
                else:
                    self.error_uri = '/errors/invalid'
                    message = _("{0} '{1}' is invalid.").format(GROUP_TYPE,
                                                                group_type)
                    break
        if message:
            return self._build_error(message)

    def _verify_exclusivity(self, group_name, tenant_id):
        return_message = None
        if not group_name:
            self.error_uri = '/errors/invalid'
            return _("%s must be used when {0} is '{1}'.").format(GROUP_NAME,
                                                                  GROUP_TYPE,
                                                                  EXCLUSIVITY)

        group = Group.query.filter_by(  # pylint: disable=E1101
            name=group_name).first()
        if not group:
            self.error_uri = '/errors/not_found'
            return_message = "%s '%s' not found" % (GROUP_NAME, group_name)
        elif group and tenant_id not in group.members:
            self.error_uri = '/errors/conflict'
            return_message = _("Tenant ID %s not a member of "
                               "{0} '{1}' ({2})").format(self.tenant_id,
                                                         GROUP_NAME,
                                                         group.name,
                                                         group.id)
        return return_message

    def build_request(self, **kwargs):
        """Build an Ostro request.

        If False is returned then the response attribute contains
        status as to the error.
        """
        # TODO(JD): Refactor this into create and update methods?
        self.args = kwargs.get('args')
        self.tenant_id = kwargs.get('tenant_id')
        self.response = None
        self.error_uri = None

        resources = self.args['resources']
        if 'resources_update' in self.args:
            action = 'update'
            resources_update = self.args['resources_update']
        else:
            action = 'create'
            resources_update = None

        # If we get any status in the response, it's an error. Bail.
        self.response = self._prepare_resources(resources)
        if 'status' in self.response:
            return False

        self.request = {
            "action": action,
            "resources": self.response['resources'],
            "stack_id": self.args['stack_id'],
        }

        if resources_update:
            # If we get any status in the response, it's an error. Bail.
            self.response = self._prepare_resources(resources_update)
            if 'status' in self.response:
                return False
            self.request['resources_update'] = self.response['resources']

        return True

    def is_request_serviceable(self):
        """Return true if request has at least one serviceable resource."""
        # TODO(JD): Ostro should return no placements vs throw an error.
        resources = self.request.get('resources', {})
        for res in resources.itervalues():
            res_type = res.get('type')
            if res_type and res_type in SERVICEABLE_RESOURCES:
                return True
        return False

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
            "orchestration_id": self.args['orchestration_id'],
            "exclusions": self.args['exclusions'],
        }

    def migrate(self, **kwargs):
        """Replan the placement for an existing resource."""
        self.args = kwargs.get('args')
        self.response = None
        self.error_uri = None
        self.request = {
            "action": "migrate",
            "stack_id": self.args['stack_id'],
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
