#
# Copyright (c) 2014-2017 AT&T Intellectual Property
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

"""Valet API Wrapper"""

# TODO(jdandrea): Factor out and refashion into python-valetclient.

import json
import sys

from oslo_config import cfg
from oslo_log import log as logging
import requests

from valet_plugins import exceptions
from valet_plugins.i18n import _

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class ValetAPI(object):
    """Valet Python API

    self.auth_token can be set once in advance,
    or sent as auth_token with each request.
    """

    def __init__(self):
        """Initializer"""
        self._auth_token = None
        self._register_opts()

    @property
    def auth_token(self):
        """Auth Token Property/Getter"""
        return self._auth_token

    @auth_token.setter
    def auth_token(self, value):
        """Auth Token Setter"""
        self._auth_token = value

    @auth_token.deleter
    def auth_token(self):
        """Auth Token Deleter"""
        del self._auth_token

    def _exception(self, exc_info, response):
        """Build exception/message and raise it.

        Exceptions are of type ValetOpenStackPluginException.

        exc_info must be sys.exc_info() tuple
        response must be of type requests.models.Response
        """

        msg = None
        exception = exceptions.UnknownError

        try:
            response_dict = response.json()
            error = response_dict.get('error', {})
            msg = "{} (valet-api: {})".format(
                response_dict.get('explanation', 'Unknown remediation'),
                error.get('message', 'Unknown error'))
            if response.status_code == 404:
                exception = exceptions.NotFoundError
            else:
                exception = exceptions.PythonAPIError
        except (AttributeError, ValueError):
            # Plan B: Pick apart exc_info (HTTPError)
            exc_class, exc, traceback = exc_info
            if hasattr(exc.response, 'request'):
                fmt = "Original Exception: {} for {} {} with body {}"
                msg = fmt.format(
                    exc, exc.response.request.method,
                    exc.response.request.url, exc.response.request.body)
            else:
                msg = "Original Exception: {}".format(exc)
            # TODO(jdandrea): Is this *truly* an "HTTP Error?"
            exception = exceptions.HTTPError
        raise exception(msg)

    def _register_opts(self):
        """Register oslo.config options"""
        opts = []
        option = cfg.StrOpt('url', default=None,
                            help=_('API endpoint url'))
        opts.append(option)
        option = cfg.IntOpt('read_timeout', default=5,
                            help=_('API read timeout in seconds'))
        opts.append(option)
        option = cfg.IntOpt('retries', default=3,
                            help=_('API request retries'))
        opts.append(option)

        opt_group = cfg.OptGroup('valet')
        CONF.register_group(opt_group)
        CONF.register_opts(opts, group=opt_group)

    def _request(self, method='get', content_type='application/json',
                 path='', headers=None, data=None, params=None):
        """Performs HTTP request.

        Returns a response dict or raises an exception.
        """
        if method not in ('post', 'get', 'put', 'delete'):
            method = 'get'
        method_fn = getattr(requests, method)

        full_headers = {
            'Accept': content_type,
            'Content-Type': content_type,
        }
        if headers:
            full_headers.update(headers)
        if not full_headers.get('X-Auth-Token') and self.auth_token:
            full_headers['X-Auth-Token'] = self.auth_token
        full_url = '{}/{}'.format(CONF.valet.url, path.lstrip('/'))

        # Prepare the request args
        try:
            data_str = json.dumps(data) if data else None
        except (TypeError, ValueError):
            data_str = data
        kwargs = {
            'data': data_str,
            'params': params,
            'headers': full_headers,
            'timeout': CONF.valet.read_timeout,
        }

        LOG.debug("Request: {} {}".format(method.upper(), full_url))
        if data:
            LOG.debug("Request Body: {}".format(json.dumps(data)))

        retries = CONF.valet.retries
        response = None
        response_dict = {}

        # Use exc_info to wrap exceptions from internally used libraries.
        # Callers are on a need-to-know basis, and they don't need to know.
        exc_info = None

        # FIXME(jdandrea): Retrying is questionable; it masks bigger issues.
        for attempt in range(retries):
            if attempt > 0:
                LOG.warn(("Retry #{}/{}").format(attempt + 1, retries))
            try:
                response = method_fn(full_url, **kwargs)
                if not response.ok:
                    LOG.debug("Response Status: {} {}".format(
                        response.status_code, response.reason))
                try:
                    # This load/unload tidies up the unicode stuffs
                    response_dict = response.json()
                    LOG.debug("Response JSON: {}".format(
                        json.dumps(response_dict)))
                except ValueError:
                    LOG.debug("Response Body: {}".format(response.text))
                response.raise_for_status()
                break  # Don't retry, we're done.
            except requests.exceptions.HTTPError as exc:
                # Just grab the exception info. Don't retry.
                exc_info = sys.exc_info()
                break
            except requests.exceptions.RequestException as exc:
                # Grab exception info, log the error, and try again.
                exc_info = sys.exc_info()
                LOG.error(exc.message)

        if exc_info:
            # Response.__bool__ returns false if status is not ok. Ruh roh!
            # That means we must check the object type vs treating as a bool.
            # More info: https://github.com/kennethreitz/requests/issues/2002
            if isinstance(response, requests.models.Response) \
                    and not response.ok:
                LOG.debug("Status {} {}; attempts: {}; url: {}".format(
                    response.status_code, response.reason,
                    attempt + 1, full_url))
            self._exception(exc_info, response)
        return response_dict

    def groups_create(self, group, auth_token=None):
        """Create a group"""
        kwargs = {
            "method": "post",
            "path": "/groups",
            "headers": {"X-Auth-Token": auth_token},
            "data": group,
        }
        return self._request(**kwargs)

    def groups_get(self, group_id, auth_token=None):
        """Get a group"""
        kwargs = {
            "method": "get",
            "path": "/groups/{}".format(group_id),
            "headers": {"X-Auth-Token": auth_token},
        }
        return self._request(**kwargs)

    def groups_update(self, group_id, group, auth_token=None):
        """Update a group"""
        kwargs = {
            "method": "put",
            "path": "/groups/{}".format(group_id),
            "headers": {"X-Auth-Token": auth_token},
            "data": group,
        }
        return self._request(**kwargs)

    def groups_delete(self, group_id, auth_token=None):
        """Delete a group"""
        kwargs = {
            "method": "delete",
            "path": "/groups/{}".format(group_id),
            "headers": {"X-Auth-Token": auth_token},
        }
        return self._request(**kwargs)

    def groups_members_update(self, group_id, members, auth_token=None):
        """Update a group with new members"""
        kwargs = {
            "method": "put",
            "path": "/groups/{}/members".format(group_id),
            "headers": {"X-Auth-Token": auth_token},
            "data": {'members': members},
        }
        return self._request(**kwargs)

    def groups_member_delete(self, group_id, member_id, auth_token=None):
        """Delete one member from a group"""
        kwargs = {
            "method": "delete",
            "path": "/groups/{}/members/{}".format(group_id, member_id),
            "headers": {"X-Auth-Token": auth_token},
        }
        return self._request(**kwargs)

    def groups_members_delete(self, group_id, auth_token=None):
        """Delete all members from a group"""
        kwargs = {
            "method": "delete",
            "path": "/groups/{}/members".format(group_id),
            "headers": {"X-Auth-Token": auth_token},
        }
        return self._request(**kwargs)

    def plans_create(self, stack, plan, auth_token=None):
        """Create a plan"""
        kwargs = {
            "method": "post",
            "path": "/plans",
            "headers": {"X-Auth-Token": auth_token},
            "data": plan,
        }
        return self._request(**kwargs)

    def plans_update(self, stack, plan, auth_token=None):
        """Update a plan"""
        kwargs = {
            "method": "put",
            "path": "/plans/{}".format(stack.id),
            "headers": {"X-Auth-Token": auth_token},
            "data": plan,
        }
        return self._request(**kwargs)

    def plans_delete(self, stack, auth_token=None):
        """Delete a plan"""
        kwargs = {
            "method": "delete",
            "path": "/plans/{}".format(stack.id),
            "headers": {"X-Auth-Token": auth_token},
        }
        return self._request(**kwargs)

    def placement(self, orch_id, res_id,
                  action='reserve', hosts=None, auth_token=None):
        """Reserve previously made placement or force a replan.

        action can be reserve or replan.
        """
        kwargs = {
            "path": "/placements/{}".format(orch_id),
            "headers": {"X-Auth-Token": auth_token},
        }
        if hosts:
            kwargs['method'] = 'post'
            kwargs['data'] = {
                "action": action,
                "locations": hosts,
                "resource_id": res_id,
            }
        return self._request(**kwargs)

    def placements_search(self, query={}, auth_token=None):
        """Search Placements"""
        kwargs = {
            "path": "/placements",
            "headers": {"X-Auth-Token": auth_token},
            "params": query,
        }
        return self._request(**kwargs)
