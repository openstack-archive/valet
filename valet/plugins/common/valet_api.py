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


import json
import requests
import sys

from heat.common.i18n import _

from oslo_config import cfg
from oslo_log import log as logging


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
        reason = response.get('explanation', _('No remediation available'))
        msg_body = {
            'explanation': reason,
            'message': error.get('message', _('Unknown error'))
        }

        msg = "%(explanation)s (valet-api: %(message)s)" % msg_body
        LOG.error("Response with error: " + msg)
        return "error"
    else:
        msg_body = {
            'exc': info,
            'method': info.request.method,
            'url': info.request.url,
            'body': info.request.body
        }

        msg = _("%(exc)s for %(method)s %(url)s with body %(body)s") % msg_body
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
            # exception.Error(_('API Endpoint not defined.'))
            raise

    def _get_timeout(self):
        """Returns Valet plugin API request timeout tuple
        (conn_timeout, read_timeout)
        """

        read_timeout = 600

        try:
            opt = getattr(cfg.CONF, self.opt_group_str)
            # conn_timeout = opt[self.opt_conn_timeout]
            read_timeout = opt[self.opt_read_timeout]
        except Exception:
            pass
        # Timeout accepts tupple on 'requests' version 2.4.0 and above
        # adding *connect* timeouts
        # return conn_timeout, read_timeout
        return read_timeout

    def _register_opts(self):
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

        opt_group = cfg.OptGroup(self.opt_group_str)
        cfg.CONF.register_group(opt_group)
        cfg.CONF.register_opts(opts, group=opt_group)

    # TODO(JD): Keep stack param for now. We may need it again.
    def plans_create(self, stack, plan, auth_token=None):
        """Create a plan"""

        response = None

        try:
            req = None
            timeout = self._get_timeout()
            url = self._api_endpoint() + '/plans/'
            payload = json.dumps(plan)
            self.headers['X-Auth-Token'] = auth_token
            req = requests.post(url,
                                data=payload,
                                headers=self.headers,
                                timeout=timeout)
            req.raise_for_status()
            response = json.loads(req.text)
        except (requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
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
        except (requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
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
                req = requests.post(url,
                                    data=payload,
                                    headers=self.headers,
                                    timeout=timeout)
            else:
                req = requests.get(url, headers=self.headers, timeout=timeout)

            # TODO(JD): Raise an exception IFF the scheduler can handle it
            # req.raise_for_status()

            response = json.loads(req.text)
        except (requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as exc:
            return _exception(exc, sys.exc_info(), req)
        except Exception as e:  # pylint: disable=W0702
            LOG.error("Exception (placement) is: %s" % e)
            # FIXME: Find which exceptions we should really handle here.
            response = None

        return response
