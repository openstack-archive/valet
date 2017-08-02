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

import traceback

from novaclient import client as nova_client
from oslo_config import cfg
from oslo_log import log

from valet.engine.resource_manager.resources.flavor import Flavor
from valet.engine.resource_manager.resources.group import Group
from valet.engine.resource_manager.resources.host import Host

# Nova API v2
VERSION = 2

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class NovaCompute(object):
    """Dispatcher to collect resource status from nova."""

    def __init__(self):
        self.nova = None

        self.vm_locations = {}

    def _get_nova_client(self):
        """Get a nova client."""
        self.nova = nova_client.Client(VERSION,
                                       CONF.identity.username,
                                       CONF.identity.password,
                                       CONF.identity.project_name,
                                       CONF.identity.auth_url)

    def set_groups(self, _groups):
        """Set availability zones and host-aggregates from nova."""

        self._get_nova_client()

        status = self._set_availability_zones(_groups)
        if status != "success":
            LOG.error(status)
            return status

        status = self._set_aggregates(_groups)
        if status != "success":
            LOG.error(status)
            return status

        return "success"

    def _set_availability_zones(self, _groups):
        """Set AZs."""

        try:
            hosts_list = self.nova.hosts.list()

            for h in hosts_list:
                if h.service == "compute":
                    group = None
                    if h.zone not in _groups.keys():
                        group = Group(h.zone)
                        group.group_type = "AZ"
                        _groups[group.name] = group
                    else:
                        group = _groups[h.zone]

                    if h.host_name not in group.vms_per_host.keys():
                        group.vms_per_host[h.host_name] = []
        except (ValueError, KeyError, TypeError):
            LOG.error(traceback.format_exc())
            return "error while setting host zones from Nova"

        return "success"

    def _set_aggregates(self, _groups):
        """Set host-aggregates and corresponding hosts."""

        try:
            aggregate_list = self.nova.aggregates.list()

            for a in aggregate_list:
                aggregate = Group(a.name)
                aggregate.group_type = "AGGR"
                if a.deleted is not False:
                    aggregate.status = "disabled"

                metadata = {}
                for mk in a.metadata.keys():
                    metadata[mk] = a.metadata.get(mk)
                aggregate.metadata = metadata

                _groups[aggregate.name] = aggregate

                for hn in a.hosts:
                    aggregate.vms_per_host[hn] = []
        except (ValueError, KeyError, TypeError):
            LOG.error(traceback.format_exc())
            return "error while setting host aggregates from Nova"

        return "success"

    def set_hosts(self, _hosts):
        """Set host resources info."""

        self._get_nova_client()

        status = self._set_hosts(_hosts)
        if status != "success":
            LOG.error(status)
            return status

        status = self._set_placed_vms(_hosts)
        if status != "success":
            LOG.error(status)
            return status

        status = self._set_resources(_hosts)
        if status != "success":
            LOG.error(status)
            return status

        return "success"

    def _set_hosts(self, _hosts):
        """Init hosts."""

        try:
            hosts_list = self.nova.hosts.list()

            for h in hosts_list:
                if h.service == "compute":
                    host = Host(h.host_name)
                    host.tag.append("nova")
                    _hosts[host.name] = host
        except (ValueError, KeyError, TypeError):
            LOG.error(traceback.format_exc())
            return "error while setting hosts from Nova"

        return "success"

    def _set_placed_vms(self, _hosts):
        """Track and set vms to hosts and groups."""

        for hk in _hosts.keys():
            result_status = self._get_vms_of_host(hk)
            if result_status != "success":
                return result_status

        for vm_uuid, hk in self.vm_locations.iteritems():
            vm_info = {}
            vm_info["uuid"] = vm_uuid
            vm_info["stack_id"] = "none"
            vm_info["orch_id"] = "none"
            result_status_detail = self._get_vm_detail(vm_info)
            if result_status_detail == "success":
                _hosts[hk].vm_list.append(vm_info)
            else:
                return result_status_detail
        return "success"

    def _get_vms_of_host(self, _hk):
        """Get vms of this host."""

        try:
            hypervisor_list = self.nova.hypervisors.search(
                hypervisor_match=_hk, servers=True)

            for hv in hypervisor_list:
                if hasattr(hv, 'servers'):
                    server_list = hv.__getattr__('servers')
                    for s in server_list:
                        self.vm_locations[s['uuid']] = _hk
        except (ValueError, KeyError, TypeError):
            LOG.error(traceback.format_exc())
            return "error while getting existing vms from nova"

        return "success"

    def _get_vm_detail(self, _vm_info):
        """Get the detail of vm."""

        try:
            server = self.nova.servers.get(_vm_info["uuid"])

            _vm_info["name"] = server.name
            _vm_info["availability_zone"] = \
                server.__getattr__("OS-EXT-AZ:availability_zone")
            _vm_info["flavor_id"] = server.flavor["id"]
            # FIXME(gjung): image
            # FIXME(gjung): metadata contains stack-id
            _vm_info["metadata"] = server.metadata
            _vm_info["status"] = server.status
            _vm_info["tenant_id"] = server.tenant_id
            # FIXME(gjung): scheduler_hints?

        except (ValueError, KeyError, TypeError):
            LOG.error(traceback.format_exc())
            return "error while getting vm detail from nova"

        return "success"

    def _set_resources(self, _hosts):
        """Set Hypervisor list."""

        try:
            host_list = self.nova.hypervisors.list()

            for hv in host_list:
                if hv.service['host'] in _hosts.keys():
                    host = _hosts[hv.service['host']]
                    host.status = hv.status
                    host.state = hv.state
                    host.original_vCPUs = float(hv.vcpus)
                    host.vCPUs_used = float(hv.vcpus_used)
                    host.original_mem_cap = float(hv.memory_mb)
                    host.free_mem_mb = float(hv.free_ram_mb)
                    host.original_local_disk_cap = float(hv.local_gb)
                    host.free_disk_gb = float(hv.free_disk_gb)
                    host.disk_available_least = float(hv.disk_available_least)
        except (ValueError, KeyError, TypeError):
            LOG.error(traceback.format_exc())
            return "error while setting host resources from Nova"

        return "success"

    def set_flavors(self, _flavors):
        """Set flavors."""

        error_status = None

        self._get_nova_client()

        result_status = self._set_flavors(_flavors)
        if result_status == "success":
            for _, f in _flavors.iteritems():
                result_status_detail = self._set_extra_specs(f)
                if result_status_detail != "success":
                    error_status = result_status_detail
                    break
        else:
            error_status = result_status

        if error_status is None:
            return "success"
        else:
            LOG.error(error_status)
            return error_status

    def _set_flavors(self, _flavors):
        """Set a list of all flavors."""

        try:
            flavor_list = self.nova.flavors.list()

            for f in flavor_list:
                flavor = Flavor(f.name)
                flavor.flavor_id = f.id
                if hasattr(f, "OS-FLV-DISABLED:disabled"):
                    if getattr(f, "OS-FLV-DISABLED:disabled"):
                        flavor.status = "disabled"

                flavor.vCPUs = float(f.vcpus)
                flavor.mem_cap = float(f.ram)
                root_gb = float(f.disk)
                ephemeral_gb = 0.0
                if hasattr(f, "OS-FLV-EXT-DATA:ephemeral"):
                    ephemeral_gb = float(
                        getattr(f, "OS-FLV-EXT-DATA:ephemeral"))
                swap_mb = 0.0
                if hasattr(f, "swap"):
                    sw = getattr(f, "swap")
                    if sw != '':
                        swap_mb = float(sw)
                flavor.disk_cap = root_gb + ephemeral_gb + swap_mb \
                    / float(1024)
                _flavors[flavor.name] = flavor
        except (ValueError, KeyError, TypeError):
            LOG.error(traceback.format_exc())
            return "error while getting flavors"

        return "success"

    def _set_extra_specs(self, _flavor):
        """Set each flavor's extra-specs."""

        try:
            flavors_list = self.nova.flavors.list()

            for flavor in flavors_list:
                if flavor.id == _flavor.flavor_id:
                    extra_specs = flavor.get_keys()
                    for sk, sv in extra_specs.iteritems():
                        _flavor.extra_specs[sk] = sv
                break
        except (ValueError, KeyError, TypeError):
            LOG.error(traceback.format_exc())
            return "error while getting extra spec for flavor"

        return "success"
