#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.


import sys
import json
import requests

from oslo_config import cfg
from oslo_log import log as logging

from heat.common.i18n import _

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def _exception(exc, info, req):
    """Handle an exception"""
    response = None

    try:
        if req is not None:
            response = json.loads(req.text)
    except Exception as e:
        LOG.error("Exception is: %s, body is: %s" % (e, req.text))
        return None

    if response and 'error' in response:
        error = response.get('error')
<<<<<<< 7de1e62db57776cc8db132d419963e650c6c7af2:plugins/valet_plugins/common/valet_api.py
        msg = "%(explanation)s (valet-api: %(message)s)" % {
            'explanation': response.get('explanation',
                                        _('No remediation available')),
=======
        reason = response.get('explanation', _('No remediation available'))
        msg_body = {
            'explanation': reason, 
>>>>>>> [WIP] Refactoring the plugin code and tests:valet/plugins/common/valet_api.py
            'message': error.get('message', _('Unknown error'))
        }

        msg = "%(explanation)s (valet-api: %(message)s)" % msg_body
        LOG.error("Response with error: " + msg)
        return "error"
    else:
<<<<<<< 7de1e62db57776cc8db132d419963e650c6c7af2:plugins/valet_plugins/common/valet_api.py
        # TODO(JD): Re-evaluate if this clause is necessary.
        exc_class, exc, traceback = exc_info  # pylint: disable=W0612
        msg = (_("%(exc)s for %(method)s %(url)s with body %(body)s") %
               {'exc': exc, 'method': exc.request.method,
                'url': exc.request.url, 'body': exc.request.body})
=======
        msg_body = {
            'exc': info,
            'method': info.request.method,
            'url': info.request.url,
            'body': info.request.body
        }

        msg = _("%(exc)s for %(method)s %(url)s with body %(body)s") % msg_body
>>>>>>> [WIP] Refactoring the plugin code and tests:valet/plugins/common/valet_api.py
        LOG.error("Response is none: " + msg)
        return "error"


# TODO(JD): Improve exception reporting back up to heat
class ValetAPIError(Exception):
    pass


class ValetAPIWrapper(object):
    """Valet API Wrapper"""

    def __init__(self):
        self.headers = {'Content-Type': 'application/json'}
        self.opt_group_str = 'valet'
        self.opt_name_str = 'url'
        self.opt_conn_timeout = 'connect_timeout'
        self.opt_read_timeout = 'read_timeout'
        self._register_opts()

    def _api_endpoint(self):
        """Returns API endpoint"""
        try:
            opt = getattr(cfg.CONF, self.opt_group_str)
            endpoint = opt[self.opt_name_str]
            return endpoint
        except Exception:
            raise  # exception.Error(_('API Endpoint not defined.'))

    def _get_timeout(self):
<<<<<<< 7de1e62db57776cc8db132d419963e650c6c7af2:plugins/valet_plugins/common/valet_api.py
        '''Returns Valet plugin API request timeout.

        Returns the timeout values tuple (conn_timeout, read_timeout)
        '''
=======
        """Returns Valet plugin API request timeout tuple
        (conn_timeout, read_timeout)"""
>>>>>>> [WIP] Refactoring the plugin code and tests:valet/plugins/common/valet_api.py
        read_timeout = 600

        try:
            opt = getattr(cfg.CONF, self.opt_group_str)
            # conn_timeout = opt[self.opt_conn_timeout]
            read_timeout = opt[self.opt_read_timeout]
        except Exception:
            pass
<<<<<<< 7de1e62db57776cc8db132d419963e650c6c7af2:plugins/valet_plugins/common/valet_api.py
        # Timeout accepts tupple on 'requests' version 2.4.0 and above -
=======

        # Timeout accepts tupple on 'requests' version 2.4.0 and above
>>>>>>> [WIP] Refactoring the plugin code and tests:valet/plugins/common/valet_api.py
        # adding *connect* timeouts
        # return conn_timeout, read_timeout
        return read_timeout

    def _register_opts(self):
<<<<<<< 7de1e62db57776cc8db132d419963e650c6c7af2:plugins/valet_plugins/common/valet_api.py
        '''Register options'''
        opts = []
        option = cfg.StrOpt(
            self.opt_name_str, default=None, help=_('Valet API endpoint'))
        opts.append(option)
        option = cfg.IntOpt(
            self.opt_conn_timeout, default=3,
            help=_('Valet Plugin Connect Timeout'))
        opts.append(option)
        option = cfg.IntOpt(
            self.opt_read_timeout, default=5,
            help=_('Valet Plugin Read Timeout'))
        opts.append(option)
=======
        """Register options"""
        opts = [
            cfg.StrOpt(self.opt_name_str,
                       default=None,
                       help=_('Valet API endpoint')),
            cfg.IntOpt(self.opt_conn_timeout,
                       default=3,
                       help=_('Valet Plugin Connect Timeout')),
            cfg.IntOpt(self.opt_read_timeout,
                       default=5,
                       help=_('Valet Plugin Read Timeout')),
        ]
>>>>>>> [WIP] Refactoring the plugin code and tests:valet/plugins/common/valet_api.py

        opt_group = cfg.OptGroup(self.opt_group_str)
        cfg.CONF.register_group(opt_group)
        cfg.CONF.register_opts(opts, group=opt_group)

    # TODO(JD): Keep stack param for now. We may need it again.
<<<<<<< 7de1e62db57776cc8db132d419963e650c6c7af2:plugins/valet_plugins/common/valet_api.py
    def plans_create(self, stack, plan, auth_token=None):
        '''Create a plan'''
=======
    def plans_create(self, stack, plan, auth_token=None):  # pylint: disable=W0613
        """Create a plan"""
>>>>>>> [WIP] Refactoring the plugin code and tests:valet/plugins/common/valet_api.py
        response = None

        try:
            req = None
            timeout = self._get_timeout()
            url = self._api_endpoint() + '/plans/'
            payload = json.dumps(plan)
            self.headers['X-Auth-Token'] = auth_token
<<<<<<< 7de1e62db57776cc8db132d419963e650c6c7af2:plugins/valet_plugins/common/valet_api.py
            req = requests.post(
                url, data=payload, headers=self.headers, timeout=timeout)
            req.raise_for_status()
            response = json.loads(req.text)
        except (requests.exceptions.HTTPError, requests.exceptions.Timeout,
=======
            req = requests.post(url,
                                data=payload,
                                headers=self.headers,
                                timeout=timeout)
            req.raise_for_status()
            response = json.loads(req.text)
        except (requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
>>>>>>> [WIP] Refactoring the plugin code and tests:valet/plugins/common/valet_api.py
                requests.exceptions.ConnectionError) as exc:
            return _exception(exc, sys.exc_info(), req)
        except Exception as e:
            LOG.error("Exception (at plans_create) is: %s" % e)
            return None
        return response

    # TODO(JD): Keep stack param for now. We may need it again.
    def plans_delete(self, stack, auth_token=None):  # pylint: disable=W0613
        """Delete a plan
        Delete does not return a response body.
        """
        try:
            req = None
            timeout = self._get_timeout()
            url = self._api_endpoint() + '/plans/' + stack.id
            self.headers['X-Auth-Token'] = auth_token
            req = requests.delete(url, headers=self.headers, timeout=timeout)
<<<<<<< 7de1e62db57776cc8db132d419963e650c6c7af2:plugins/valet_plugins/common/valet_api.py
        except (requests.exceptions.HTTPError, requests.exceptions.Timeout,
=======
        except (requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
>>>>>>> [WIP] Refactoring the plugin code and tests:valet/plugins/common/valet_api.py
                requests.exceptions.ConnectionError) as exc:
            return _exception(exc, sys.exc_info(), req)
        except Exception as e:
            LOG.error("Exception (plans_delete) is: %s" % e)
            return None

    def placement(self, orch_id, res_id, hosts=None, auth_token=None):
        """Reserve previously made placement."""
        try:
            req = None
            payload = None
            timeout = self._get_timeout()
            url = self._api_endpoint() + '/placements/' + orch_id
            self.headers['X-Auth-Token'] = auth_token
            if hosts:
                kwargs = {
                    "locations": hosts,
                    "resource_id": res_id
                }
                payload = json.dumps(kwargs)
<<<<<<< 7de1e62db57776cc8db132d419963e650c6c7af2:plugins/valet_plugins/common/valet_api.py
                req = requests.post(
                    url, data=payload, headers=self.headers, timeout=timeout)
=======
                req = requests.post(url,
                                    data=payload,
                                    headers=self.headers,
                                    timeout=timeout)
>>>>>>> [WIP] Refactoring the plugin code and tests:valet/plugins/common/valet_api.py
            else:
                req = requests.get(url, headers=self.headers, timeout=timeout)

            # TODO(JD): Raise an exception IFF the scheduler can handle it
            # req.raise_for_status()

            response = json.loads(req.text)
<<<<<<< 7de1e62db57776cc8db132d419963e650c6c7af2:plugins/valet_plugins/common/valet_api.py
        except (requests.exceptions.HTTPError, requests.exceptions.Timeout,
=======
        except (requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
>>>>>>> [WIP] Refactoring the plugin code and tests:valet/plugins/common/valet_api.py
                requests.exceptions.ConnectionError) as exc:
            return _exception(exc, sys.exc_info(), req)
        except Exception as e:  # pylint: disable=W0702
            LOG.error("Exception (placement) is: %s" % e)
            # FIXME: Find which exceptions we should really handle here.
            response = None

        return response
