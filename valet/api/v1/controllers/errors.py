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

"""Errors."""

import logging
from pecan import expose, request, response
from valet.api.common.i18n import _
from webob.exc import status_map

LOG = logging.getLogger(__name__)

# pylint: disable=R0201


def error_wrapper(func):
    """Error decorator."""
    def func_wrapper(self, **kw):
        """Wrapper."""
        kwargs = func(self, **kw)
        status = status_map.get(response.status_code)
        message = getattr(status, 'explanation', '')
        explanation = request.context.get('error_message', message)
        error_type = status.__name__
        title = status.title
        traceback = getattr(kwargs, 'traceback', None)

        LOG.error(explanation)

        # Modeled after Heat's format
        return {
            "explanation": explanation,
            "code": response.status_code,
            "error": {
                "message": message,
                "traceback": traceback,
                "type": error_type,
            },
            "title": title,
        }
    return func_wrapper


# pylint: disable=W0613
class ErrorsController(object):
    """Error Controller /errors/{error_name}."""

    @expose('json')
    @error_wrapper
    def schema(self, **kw):
        """400."""
        request.context['error_message'] = str(request.validation_error)
        response.status = 400
        return request.context.get('kwargs')

    @expose('json')
    @error_wrapper
    def invalid(self, **kw):
        """400."""
        response.status = 400
        return request.context.get('kwargs')

    @expose()
    def unauthorized(self, **kw):
        """401."""
        # This error is terse and opaque on purpose.
        # Don't give any clues to help AuthN along.
        response.status = 401
        response.content_type = 'text/plain'
        LOG.error('unauthorized')
        import traceback
        traceback.print_stack()
        LOG.error(self.__class__)
        LOG.error(kw)
        response.body = _('Authentication required')
        LOG.error(response.body)
        return response

    @expose('json')
    @error_wrapper
    def forbidden(self, **kw):
        """403."""
        response.status = 403
        return request.context.get('kwargs')

    @expose('json')
    @error_wrapper
    def not_found(self, **kw):
        """404."""
        response.status = 404
        return request.context.get('kwargs')

    @expose('json')
    @error_wrapper
    def not_allowed(self, **kw):
        """405."""
        kwargs = request.context.get('kwargs')
        if kwargs:
            allow = kwargs.get('allow', None)
            if allow:
                response.headers['Allow'] = allow
        response.status = 405
        return kwargs

    @expose('json')
    @error_wrapper
    def conflict(self, **kw):
        """409."""
        response.status = 409
        return request.context.get('kwargs')

    @expose('json')
    @error_wrapper
    def server_error(self, **kw):
        """500."""
        response.status = 500
        return request.context.get('kwargs')

    @expose('json')
    @error_wrapper
    def unavailable(self, **kw):
        """503."""
        response.status = 503
        return request.context.get('kwargs')
