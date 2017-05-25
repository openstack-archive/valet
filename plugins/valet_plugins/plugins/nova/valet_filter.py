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
import time

from keystoneclient.v2_0 import client
from nova.i18n import _
from nova.i18n import _LE
from nova.i18n import _LI
from nova.i18n import _LW
from nova.scheduler import filters
from oslo_config import cfg
from oslo_log import log as logging

from valet_plugins.common import valet_api

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class ValetFilter(filters.BaseHostFilter):
    '''Filter on Valet assignment.'''

    # Host state does not change within a request
    run_filter_once_per_request = True

    # Used to authenticate request. Update via _authorize()
    _auth_token = None

    def __init__(self):
        '''Initializer'''
        self.api = valet_api.ValetAPIWrapper()
        self.opt_group_str = 'valet'
        self.opt_failure_mode_str = 'failure_mode'
        self.opt_project_name_str = 'admin_tenant_name'
        self.opt_username_str = 'admin_username'
        self.opt_password_str = 'admin_password'
        self.opt_auth_uri_str = 'admin_auth_url'
        self._register_opts()

        self.retries = 60
        self.interval = 1

    def _authorize(self):
        '''Keystone AuthN'''
        opt = getattr(cfg.CONF, self.opt_group_str)
        project_name = opt[self.opt_project_name_str]
        username = opt[self.opt_username_str]
        password = opt[self.opt_password_str]
        auth_uri = opt[self.opt_auth_uri_str]

        kwargs = {
            'username': username,
            'password': password,
            'tenant_name': project_name,
            'auth_url': auth_uri
        }
        keystone_client = client.Client(**kwargs)
        self._auth_token = keystone_client.auth_token

    def _is_same_host(self, host, location):  # pylint: disable=R0201
        '''Returns true if host matches location'''
        return host == location

    def _register_opts(self):
        '''Register Options'''
        opts = []
        option = cfg.StrOpt(
            self.opt_failure_mode_str,
            choices=['reject', 'yield'], default='reject',
            help=_('Mode to operate in if Valet planning fails.'))
        opts.append(option)
        option = cfg.StrOpt(self.opt_project_name_str,
                            default=None, help=_('Valet Project Name'))
        opts.append(option)
        option = cfg.StrOpt(self.opt_username_str,
                            default=None, help=_('Valet Username'))
        opts.append(option)
        option = cfg.StrOpt(self.opt_password_str,
                            default=None, help=_('Valet Password'))
        opts.append(option)
        option = cfg.StrOpt(self.opt_auth_uri_str,
                            default=None,
                            help=_('Keystone Authorization API Endpoint'))
        opts.append(option)

        opt_group = cfg.OptGroup(self.opt_group_str)
        cfg.CONF.register_group(opt_group)
        cfg.CONF.register_opts(opts, group=opt_group)

    # TODO(JD): Factor out common code between this and the cinder filter
    def filter_all(self, filter_obj_list, filter_properties):
        '''Filter all hosts in one swell foop'''

        hints_key = 'scheduler_hints'
        orch_id_key = 'heat_resource_uuid'

        ad_hoc = False
        yield_all = False
        location = None

        opt = getattr(cfg.CONF, self.opt_group_str)
        failure_mode = opt[self.opt_failure_mode_str]

        # Get the resource_id (physical id) and host candidates
        request_spec = filter_properties.get('request_spec')
        instance_properties = request_spec.get('instance_properties')
        res_id = instance_properties.get('uuid')
        hosts = [obj.host for obj in filter_obj_list]

        # TODO(JD): If we can't reach Valet at all, we may opt to fail
        # TODO(JD): all hosts depending on a TBD config flag.

        # Max
        # fix for invaid authorization in yield mode
        failed = None
        try:
            self._authorize()
        except Exception as ex:
            failed = ex
        if failed:
            LOG.warn("Failed to filter the hosts, failure mode is %s" % failure_mode)
            if failure_mode == 'yield':
                LOG.warn(failed)
                yield_all = True
            else:
                LOG.error(failed)
#         if not filter_properties.get(hints_key, {}).has_key(orch_id_key):
        elif orch_id_key not in filter_properties.get(hints_key, {}):
            LOG.info(_LW("Valet: Heat Stack Lifecycle Scheduler Hints not found. Performing ad-hoc placement."))
            ad_hoc = True

            # We'll need the flavor.
            instance_type = filter_properties.get('instance_type')
            flavor = instance_type.get('name')

            # Because this wasn't orchestrated, there's no stack.
            # We're going to compose a resource as if there as one.
            # In this particular case we use the physical
            # resource id as both the orchestration and stack id.
            resources = {
                res_id: {
                    "properties": {
                        "flavor": flavor,
                    },
                    "type": "OS::Nova::Server",
                    "name": "ad_hoc_instance"
                }
            }

            # Only add the AZ if it was expressly defined
            res_properties = resources[res_id]["properties"]
            a_zone = instance_properties.get('availability_zone')
            if a_zone:
                res_properties["availability_zone"] = a_zone

            timeout = 60
            plan = {
                'plan_name': res_id,
                'stack_id': res_id,
                'locations': hosts,
                'timeout': '%d sec' % timeout,
                'resources': resources
            }

            count = 0
            response = None
            while count < self.retries:
                try:
                    response = self.api.plans_create(None, plan, auth_token=self._auth_token)
                except Exception:
                    # TODO(JD): Get context from exception
                    LOG.error(_LE("Raise exception for ad hoc placement request."))
                    response = None
                if response is None:
                    count += 1
                    LOG.warn("Valet conn error for plan_create, Retry " + str(count) + " for stack = " + res_id)
                    time.sleep(self.interval)
                else:
                    break

            if response and response.get('plan'):
                plan = response['plan']
                if plan and plan.get('placements'):
                    placements = plan['placements']
                    if placements.get(res_id):
                        placement = placements.get(res_id)
                        location = placement['location']

            if not location:
                LOG.error(_LE("Valet ad-hoc placement unknown for resource id %s.") % res_id)
                if failure_mode == 'yield':
                    LOG.warn(_LW("Valet will yield to Nova for placement decisions."))
                    yield_all = True
                else:
                    yield_all = False
        else:
            orch_id = filter_properties[hints_key][orch_id_key]

            count = 0
            response = None
            while count < self.retries:
                try:
                    response = self.api.placement(orch_id, res_id, hosts=hosts, auth_token=self._auth_token)
                except Exception:
                    LOG.error(_LW("Raise exception for placement request."))
                    response = None

                if response is None:
                    count += 1
                    LOG.warn("Valet conn error for placement Retry " + str(count) + " for stack = " + orch_id)
                    time.sleep(self.interval)
                else:
                    break

            if response and response.get('placement'):
                placement = response['placement']
                if placement.get('location'):
                    location = placement['location']

            if not location:
                # TODO(JD): Get context from exception
                msg = ("Valet placement unknown for resource id {0}, "
                       "orchestration id {1}.")
                LOG.error(_LE(msg).format(res_id, orch_id))
                if failure_mode == 'yield':
                    msg = "Valet will yield to Nova for placement decisions."
                    LOG.warn(_LW(msg))
                    yield_all = True
                else:
                    yield_all = False

        # Yield the hosts that pass.
        # Like the Highlander, there can (should) be only one.
        # It's possible there could be none if Valet can't solve it.
        for obj in filter_obj_list:
            if location:
                match = self._is_same_host(obj.host, location)
                if match:
                    if ad_hoc:
                        msg = ("Valet ad-hoc placement for resource id "
                               "{0}: {1}.")
                        LOG.info(_LI(msg).format(res_id, obj.host))
                    else:
                        msg = ("Valet placement for resource id %s, "
                               "orchestration id {0}: {1}.")
                        LOG.info(_LI(msg).format(res_id, orch_id, obj.host))
            else:
                match = None
            if yield_all or match:
                yield obj

    def host_passes(self, host_state, filter_properties):
        '''Individual host pass check'''
        # Intentionally let filter_all() handle in one swell foop.
        return False
