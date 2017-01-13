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

"""Root."""

import logging

from pecan import expose, request, response
from valet.api.common.i18n import _
from valet.api.v1.controllers import error
from valet.api.v1.controllers.errors import ErrorsController, error_wrapper
from valet.api.v1.controllers.v1 import V1Controller

from webob.exc import status_map

LOG = logging.getLogger(__name__)

# pylint: disable=R0201


class RootController(object):
    """Root Controller."""

    errors = ErrorsController()
    v1 = V1Controller()  # pylint: disable=C0103

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
        """Get canonical URL for each version."""
        ver = {
            "versions":
            [
                {
                    "status": "CURRENT",
                    "id": "v1.0",
                    "links":
                    [
                        {
                            "href": request.application_url + "/v1/",
                            "rel": "self"
                        }
                    ]
                }
            ]
        }

        return ver

    @error_wrapper
    def error(self, status):
        """Error handler."""
        try:
            status = int(status)
        except ValueError:  # pragma: no cover
            status = 500
        message = getattr(status_map.get(status), 'explanation', '')
        return dict(status=status, message=message)
