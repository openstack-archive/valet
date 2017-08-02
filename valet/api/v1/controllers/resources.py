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

"""Resources"""

from pecan import expose, request, response
from valet.api.common.i18n import _
from valet.api.common.ostro_helper import Ostro
from valet.api.v1.controllers import engine_query_args
from valet.api.v1.controllers import error


class ResourcesController(object):
    """Status Controller /v1/resources"""

    def _invalid_placements(self):
        """Returns a dict of VMs with invalid placements."""

        # TODO(gjung): Support checks on individual placements as well
        ostro_kwargs = engine_query_args(query_type="invalid_placements")
        ostro = Ostro()
        ostro.query(**ostro_kwargs)
        ostro.send()

        status_type = ostro.response['status']['type']
        if status_type != 'ok':
            message = ostro.response['status']['message']
            error(ostro.error_uri, _('Ostro error: %s') % message)

        resources = ostro.response['resources']
        return resources or {}

    def _resource_status(self):
        """Get resource status."""

        # All we do at the moment is check for invalid placements.
        # This structure will evolve in the future. The only kind of
        # resource type we'll see at the moment are servers.
        invalid = self._invalid_placements()
        resources = {}
        for resource_id, info in invalid.items():
            resources[resource_id] = {
                "type": "OS::Nova::Server",
                "status": "error",
                "message": info.get('status'),
            }
        response = {
            "resources": resources,
        }
        return response

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
    def index_get(self):
        """Get Valet resource status"""
        _response = self._resource_status()
        response.status = 200
        return _response
