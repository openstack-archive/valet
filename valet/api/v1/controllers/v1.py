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

"""v1."""

import logging

from pecan import conf, expose, request, response
from pecan.secure import SecureController

from valet.api.common.i18n import _
from valet.api.v1.controllers import error
from valet.api.v1.controllers.groups import GroupsController
from valet.api.v1.controllers.placements import PlacementsController
from valet.api.v1.controllers.plans import PlansController
from valet.api.v1.controllers.status import StatusController


LOG = logging.getLogger(__name__)

# pylint: disable=R0201


class V1Controller(SecureController):
    """v1 Controller  /v1."""

    groups = GroupsController()
    placements = PlacementsController()
    plans = PlansController()
    status = StatusController()

    # Update this whenever a new endpoint is made.
    endpoints = ["groups", "placements", "plans", "status"]

    @classmethod
    def check_permissions(cls):
        """SecureController permission check callback."""
        token = None
        auth_token = request.headers.get('X-Auth-Token')
        msg = "Unauthorized - No auth token"

        if auth_token:
            msg = "Unauthorized - invalid token"
            # The token must have an admin role
            # and be associated with a tenant.
            token = conf.identity.engine.validate_token(auth_token)

        if token:
            LOG.debug("Checking token permissions")
            msg = "Unauthorized - Permission was not granted"
            if V1Controller._permission_granted(request, token):
                tenant_id = conf.identity.engine.tenant_from_token(token)
                LOG.info("tenant_id - " + str(tenant_id))
                if tenant_id:
                    request.context['tenant_id'] = tenant_id
                    user_id = conf.identity.engine.user_from_token(token)
                    request.context['user_id'] = user_id

                    return True

        error('/errors/unauthorized', msg)

    @classmethod
    def _action_is_migrate(cls, request):
        return "plan" in request.path \
               and hasattr(request, "json") \
               and "action" in request.json \
               and request.json["action"] == "migrate"

    @classmethod
    def _permission_granted(cls, request, token):
        return not ("group" in request.path or
                    V1Controller._action_is_migrate(request)) or\
            (conf.identity.engine.is_token_admin(token))

    @classmethod
    def allow(cls):
        """Allowed methods."""
        return 'GET'

    @expose(generic=True, template='json')
    def index(self):
        """Catchall for unallowed methods."""
        message = _('The %s method is not allowed.') % request.method
        kwargs = {'allow': self.allow()}
        error('/errors/not_allowed', message, **kwargs)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        """Index Options."""
        response.headers['Allow'] = self.allow()
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        """Get canonical URL for each endpoint."""
        links = []
        for endpoint in V1Controller.endpoints:
            links.append({
                "href": "%(url)s/v1/%(endpoint)s/" %
                {
                    'url': request.application_url,
                    'endpoint': endpoint
                },
                "rel": "self"
            })
        ver = {
            "versions":
            [
                {
                    "status": "CURRENT",
                    "id": "v1.0",
                    "links": links
                }
            ]
        }

        return ver
