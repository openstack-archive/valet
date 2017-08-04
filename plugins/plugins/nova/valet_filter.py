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

"""Valet Nova Scheduler Filter"""

import json

from keystoneclient.v2_0 import client
from nova.scheduler import filters
from oslo_config import cfg
from oslo_log import log as logging

from plugins.common import valet_api
from plugins import exceptions
from plugins.i18n import _

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class ValetFilter(filters.BaseHostFilter):
    """Filter on Valet assignment."""

    # Checked by Nova. Host state does not change within a request.
    run_filter_once_per_request = True

    def __init__(self):
        """Initializer"""
        self.api = valet_api.ValetAPI()
        self._register_opts()

    def _authorize(self):
        """Authorize against Keystone"""
        kwargs = {
            'username': CONF.valet.admin_username,
            'password': CONF.valet.admin_password,
            'tenant_name': CONF.valet.admin_tenant_name,
            'auth_url': CONF.valet.admin_auth_url,
        }
        keystone_client = client.Client(**kwargs)
        self.api.auth_token = keystone_client.auth_token

    def _first_orch_id_from_placements_search(self, response={}):
        """Return first orchestration id from placements search response.

        Return None if not found.
        """
        if type(response) is dict:
            placements = response.get('placements', [])
            if placements:
                return placements[0].get('id')

    def _is_same_host(self, host, location):
        """Returns true if host matches location"""
        return host == location

    def _location_for_resource(self, hosts, filter_properties):
        """Determine optimal location for a given resource

        Returns a tuple:

        location is the determined location.
        res_id is the physical resource id.
        orch_id is the orchestration id.
        ad_hoc is True if the placement was made on-the-fly.
        """
        orch_id = None
        location = None
        ad_hoc = False

        # Get the image, instance properties, physical id, and hints
        request_spec = filter_properties.get('request_spec')
        image = request_spec.get('image')
        instance_properties = request_spec.get('instance_properties')
        res_id = instance_properties.get('uuid')
        hints = filter_properties.get('scheduler_hints', {})

        LOG.info(("Resolving Orchestration ID "
                  "for resource {}.").format(res_id))

        if hints:
            # Plan A: Resolve Orchestration ID using scheduler hints.
            action = 'reserve'
            orch_id = self._orch_id_from_scheduler_hints(hints)

        if not orch_id:
            # Plan B: Try again using Nova-assigned resource id.
            action = 'replan'
            orch_id = self._orch_id_from_resource_id(res_id)

        if orch_id:
            # If Plan A or B resulted in an Orchestration ID ...
            if action == 'replan':
                message = ("Forcing replan for Resource ID: {}, "
                           "Orchestration ID: {}")
            else:
                message = ("Reserving with possible replan "
                           "for Resource ID: {}, "
                           "Orchestration ID: {}")
            LOG.info(message.format(res_id, orch_id))
            location = self._location_from_reserve_or_replan(
                orch_id, res_id, hosts, action)
        else:
            # Plan C: It's ad-hoc plan/placement time!
            # FIXME(jdandrea): Shouldn't reserving occur after this?
            LOG.info(("Orchestration ID not found. "
                      "Performing ad-hoc placement."))
            ad_hoc = True

            # We'll need the flavor, image name, metadata, and AZ (if any)
            instance_type = filter_properties.get('instance_type')
            flavor = instance_type.get('name')
            image_name = image.get('name')
            metadata = instance_properties.get('metadata')
            availability_zone = instance_properties.get('availability_zone')

            # The metadata may be a JSON string vs a dict.
            # If it's a string, try converting it to a dict.
            try:
                valet_meta = metadata.get('valet')
                if isinstance(valet_meta, basestring):
                    metadata['valet'] = json.loads(valet_meta)
            except Exception:
                # Leave it alone then.
                pass

            location = self._location_from_ad_hoc_plan(
                res_id, flavor, image_name, metadata,
                availability_zone, hosts)
        return (location, res_id, orch_id, ad_hoc)

    def _location_from_ad_hoc_plan(self, res_id, flavor,
                                   image=None, metadata=None,
                                   availability_zone=None,
                                   hosts=None):
        """Determine host location on-the-fly (ad-hoc).

        Create an ad hoc plan (and ad-hoc placement),
        then return the host location if found.
        """

        # Because this wasn't orchestrated, there's no stack.
        # We're going to compose a resource as if there was one.
        # In this particular case we use the nova-assigned
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
        res_properties = resources[res_id]["properties"]
        if image:
            res_properties["image"] = image
        if metadata:
            res_properties["metadata"] = metadata
        if availability_zone:
            res_properties["availability_zone"] = availability_zone

        # FIXME(jdandrea): Constant should not be here, may not even be used
        timeout = 60
        plan = {
            'plan_name': res_id,
            'stack_id': res_id,
            'locations': hosts,
            'timeout': '%d sec' % timeout,
            'resources': resources,
        }
        kwargs = {
            'stack': None,
            'plan': plan,
        }
        response = self.api.plans_create(**kwargs)
        if response and response.get('plan'):
            plan = response['plan']
            if plan and plan.get('placements'):
                placements = plan['placements']
                if placements.get(res_id):
                    placement = placements.get(res_id)
                    location = placement['location']
                    return location

    def _location_from_reserve_or_replan(self, orch_id, res_id,
                                         hosts=None, action='reserve'):
        """Reserve placement with possible replan, or force replan."""
        kwargs = {
            'orch_id': orch_id,
            'res_id': res_id,
            'hosts': hosts,
            'action': action,
        }
        response = self.api.placement(**kwargs)

        if response and response.get('placement'):
            placement = response['placement']
            if placement.get('location'):
                location = placement['location']
                return location

    def _orch_id_from_resource_id(self, res_id):
        """Find Orchestration ID via Nova-assigned Resource ID."""
        kwargs = {
            'query': {
                'resource_id': res_id,
            },
        }
        LOG.info(("Searching by Resource ID: {}.").format(res_id))
        response = self.api.placements_search(**kwargs)
        orch_id = \
            self._first_orch_id_from_placements_search(response)
        return orch_id

    def _orch_id_from_scheduler_hints(self, hints={}):
        """Find Orchestration ID via Lifecycle Scheduler Hints.

        This is either within the hints or via searching Valet
        placements using the hints. It's most likely the former
        now that we handle each stack level as its own plan.

        If we try to flatten the entire stack into one plan,
        a bug/anomaly in Heat makes the orchestration IDs
        unusable, which is why we added search. But that led
        to new problems with stack creation, so instead we now
        treat each stack level as its own plan, which means all
        that work on implementing search is not being used.

        Still, the search logic can remain for the time being.
        """
        orch_id_key = 'heat_resource_uuid'
        root_stack_id_key = 'heat_root_stack_id'
        resource_name_key = 'heat_resource_name'
        path_in_stack_key = 'heat_path_in_stack'

        # Maybe the orch_id is already in the hints? If so, return it.
        orch_id = hints.get(orch_id_key)
        if orch_id:
            return orch_id

        # If it's not, try searching for it using remaining hint info.
        if all(k in hints for k in (root_stack_id_key, resource_name_key,
                                    path_in_stack_key)):
            kwargs = {
                'query': {
                    root_stack_id_key: hints.get(root_stack_id_key),
                    resource_name_key: hints.get(resource_name_key),
                    # Path in stack is made up of tuples. Make it a string.
                    path_in_stack_key: json.dumps(
                        hints.get(path_in_stack_key)),
                },
            }
            LOG.info("Searching placements via scheduler hints.")
            response = self.api.placements_search(**kwargs)
            orch_id = \
                self._first_orch_id_from_placements_search(response)
            return orch_id

    def _register_opts(self):
        """Register additional options specific to this filter plugin"""
        opts = []
        option = cfg.StrOpt('failure_mode',
                            choices=['reject', 'yield'], default='reject',
                            help=_('Mode to operate in if Valet '
                                   'planning fails for any reason.'))

        # In the filter plugin space, there's no access to Nova's
        # keystone credentials, so we have to specify our own.
        # This also means we can't act as the user making the request
        # at scheduling-time.
        opts.append(option)
        option = cfg.StrOpt('admin_tenant_name', default=None,
                            help=_('Valet Project Name'))
        opts.append(option)
        option = cfg.StrOpt('admin_username', default=None,
                            help=_('Valet Username'))
        opts.append(option)
        option = cfg.StrOpt('admin_password', default=None,
                            help=_('Valet Password'))
        opts.append(option)
        option = cfg.StrOpt('admin_auth_url', default=None,
                            help=_('Keystone Authorization API Endpoint'))
        opts.append(option)

        opt_group = cfg.OptGroup('valet')
        cfg.CONF.register_group(opt_group)
        cfg.CONF.register_opts(opts, group=opt_group)

    def filter_all(self, filter_obj_list, filter_properties):
        """Filter all hosts in one swell foop"""
        res_id = None
        orch_id = None
        location = None

        authorized = False
        ad_hoc = False
        yield_all = False

        hosts = [obj.host for obj in filter_obj_list]

        # Do AuthN as late as possible (here), not in init().
        try:
            self._authorize()
            authorized = True
        except Exception as err:
            LOG.error(('Authorization exception: {}').format(err.message))

        if authorized:
            # nova-conductor won't catch exceptions like heat-engine does.
            # The best we can do is log it.
            try:
                (location, res_id, orch_id, ad_hoc) = \
                    self._location_for_resource(hosts, filter_properties)
            except exceptions.ValetOpenStackPluginException as err:
                LOG.error(('API Exception: {}').format(err.message))

        # Honk if we didn't find a location and decide if we yield to Nova.
        if not location:
            if ad_hoc:
                message = ("Ad-hoc placement unknown, "
                           "Resource ID: {}")
                LOG.error(message.format(res_id))
            elif orch_id:
                message = ("Placement unknown, Resource ID: {}, "
                           "Orchestration ID: {}.")
                LOG.error(message.format(res_id, orch_id))
            elif res_id:
                message = ("Placement unknown, Resource ID: {}")
                LOG.error(message.format(res_id))
            else:
                message = ("Placement unknown.")
                LOG.error(message)

            if CONF.valet.failure_mode == 'yield':
                message = ("Yielding to Nova or placement decisions.")
                LOG.warn(message)
                yield_all = True
            else:
                message = ("Rejecting all Nova placement decisions.")
                LOG.error(message)
                yield_all = False

        # Yield the hosts that pass.
        # Like the Highlander, there can (should) be only one.
        # It's possible there could be none if Valet can't solve it.
        for obj in filter_obj_list:
            if location:
                match = self._is_same_host(obj.host, location)
                if match:
                    if ad_hoc:
                        message = ("Ad-Hoc host selection "
                                   "is {} for Resource ID {}.")
                        LOG.info(message.format(obj.host, res_id))
                    else:
                        message = ("Host selection is {} for "
                                   "Resource ID: {}, "
                                   "Orchestration ID: {}.")
                        LOG.info(message.format(obj.host, res_id, orch_id))
            else:
                match = None
            if yield_all or match:
                yield obj

    def host_passes(self, host_state, filter_properties):
        """Individual host pass check"""
        # Intentionally let filter_all() handle it.
        return False
