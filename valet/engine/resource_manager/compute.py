# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Modified: Sep. 27, 2016

from novaclient import client as nova_client
from oslo_config import cfg
from resource_base import Host, LogicalGroup, Flavor
import traceback

# Nova API v2
VERSION = 2

CONF = cfg.CONF


class Compute(object):
    def __init__(self, _logger):
        self.logger = _logger
        self.nova = None

    def set_hosts(self, _hosts, _logical_groups):

        self._get_nova_client()

        status = self._set_availability_zones(_hosts, _logical_groups)
        if status != "success":
            self.logger.error('_set_availability_zones failed')
            return status

        status = self._set_aggregates(_hosts, _logical_groups)
        if status != "success":
            self.logger.error('_set_aggregates failed')
            return status

        status = self._set_placed_vms(_hosts, _logical_groups)
        if status != "success":
            self.logger.error('_set_placed_vms failed')
            return status

        status = self._set_resources(_hosts)
        if status != "success":
            self.logger.error('_set_resources failed')
            return status

        return "success"

    def _get_nova_client(self):
        '''Returns a nova client'''
        self.nova = nova_client.Client(VERSION,
                                       CONF.identity.username,
                                       CONF.identity.password,
                                       CONF.identity.project_name,
                                       CONF.identity.auth_url)

    def _set_availability_zones(self, _hosts, _logical_groups):
        try:
            hosts_list = self.nova.hosts.list()

            try:
                for h in hosts_list:
                    if h.service == "compute":
                        host = Host(h.host_name)
                        host.tag.append("nova")

                        logical_group = None
                        if h.zone not in _logical_groups.keys():
                            logical_group = LogicalGroup(h.zone)
                            logical_group.group_type = "AZ"
                            _logical_groups[logical_group.name] = logical_group
                        else:
                            logical_group = _logical_groups[h.zone]

                        host.memberships[logical_group.name] = logical_group

                        if host.name not in logical_group.vms_per_host.keys():
                            logical_group.vms_per_host[host.name] = []

                        self.logger.info("adding Host LogicalGroup: " + str(host.__dict__))

                        _hosts[host.name] = host

            except (ValueError, KeyError, TypeError):
                self.logger.error(traceback.format_exc())
                return "Error while setting host zones from Nova"

        except Exception:
            self.logger.critical(traceback.format_exc())

        return "success"

    def _set_aggregates(self, _hosts, _logical_groups):
        aggregate_list = self.nova.aggregates.list()

        try:
            for a in aggregate_list:
                aggregate = LogicalGroup(a.name)
                aggregate.group_type = "AGGR"
                if a.deleted is not False:
                    aggregate.status = "disabled"

                metadata = {}
                for mk in a.metadata.keys():
                    metadata[mk] = a.metadata.get(mk)
                aggregate.metadata = metadata

                self.logger.info("adding aggregate LogicalGroup: " + str(aggregate.__dict__))

                _logical_groups[aggregate.name] = aggregate

                for hn in a.hosts:
                    host = _hosts[hn]
                    host.memberships[aggregate.name] = aggregate

                    aggregate.vms_per_host[host.name] = []

        except (ValueError, KeyError, TypeError):
            self.logger.error(traceback.format_exc())
            return "Error while setting host aggregates from Nova"

        return "success"

    # NOTE: do not set any info in _logical_groups
    def _set_placed_vms(self, _hosts, _logical_groups):
        error_status = None

        for hk in _hosts.keys():
            vm_uuid_list = []
            result_status = self._get_vms_of_host(hk, vm_uuid_list)

            if result_status == "success":
                for vm_uuid in vm_uuid_list:
                    vm_detail = []  # (vm_name, az, metadata, status)
                    result_status_detail = self._get_vm_detail(vm_uuid, vm_detail)

                    if result_status_detail == "success":
                        # if vm_detail[3] != "SHUTOFF":  # status == "ACTIVE" or "SUSPENDED"
                        vm_id = ("none", vm_detail[0], vm_uuid)
                        _hosts[hk].vm_list.append(vm_id)

                        # _logical_groups[vm_detail[1]].vm_list.append(vm_id)
                        # _logical_groups[vm_detail[1]].vms_per_host[hk].append(vm_id)
                    else:
                        error_status = result_status_detail
                        break
            else:
                error_status = result_status

            if error_status is not None:
                break

        if error_status is None:
            return "success"
        else:
            return error_status

    def _get_vms_of_host(self, _hk, _vm_list):
        hypervisor_list = self.nova.hypervisors.search(hypervisor_match=_hk, servers=True)

        try:
            for hv in hypervisor_list:
                if hasattr(hv, 'servers'):
                    server_list = hv.__getattr__('servers')
                    for s in server_list:
                        _vm_list.append(s.uuid)

        except (ValueError, KeyError, TypeError):
            self.logger.error(traceback.format_exc())
            return "Error while getting existing vms"

        return "success"

    def _get_vm_detail(self, _vm_uuid, _vm_detail):
        server = self.nova.servers.get(_vm_uuid)

        try:
            vm_name = server.name
            _vm_detail.append(vm_name)
            az = server.__getattr("OS-EXT-AZ:availability_zone")
            _vm_detail.append(az)
            metadata = server.metadata
            _vm_detail.append(metadata)
            status = server.status
            _vm_detail.append(status)

        except (ValueError, KeyError, TypeError):
            self.logger.error(traceback.format_exc())
            return "Error while getting vm detail"

        return "success"

    def _set_resources(self, _hosts):
        # Returns Hypervisor list
        host_list = self.nova.hypervisors.list()

        try:
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
            self.logger.error(traceback.format_exc())
            return "Error while setting host resources from Nova"

        return "success"

    def set_flavors(self, _flavors):
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
            return error_status

    def _set_flavors(self, _flavors):
        # Get a list of all flavors
        flavor_list = self.nova.flavors.list()

        try:
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
                    ephemeral_gb = float(getattr(f, "OS-FLV-EXT-DATA:ephemeral"))

                swap_mb = 0.0
                if hasattr(f, "swap"):
                    sw = getattr(f, "swap")
                    if sw != '':
                        swap_mb = float(sw)

                flavor.disk_cap = root_gb + ephemeral_gb + swap_mb / float(1024)

                self.logger.info("adding flavor " + str(flavor.__dict__))

                _flavors[flavor.name] = flavor

        except (ValueError, KeyError, TypeError):
            self.logger.error(traceback.format_exc())
            return "Error while getting flavors"

        return "success"

    def _set_extra_specs(self, _flavor):
        try:
            # Get a list of all flavors
            flavors_list = self.nova.flavors.list()
            # Get flavor from flavor_list
            for flavor in flavors_list:
                if flavor.id == _flavor.flavor_id:

                    extra_specs = flavor.get_keys()

                    for sk, sv in extra_specs.iteritems():
                        _flavor.extra_specs[sk] = sv

                break

        except (ValueError, KeyError, TypeError):
            self.logger.error(traceback.format_exc())
            return "Error while getting flavor extra spec"

        return "success"


# Unit test
'''
if __name__ == '__main__':
    config = Config()
    config_status = config.configure()
    if config_status != "success":
        print "Error while configuring Ostro: " + config_status
        sys.exit(2)

    auth = Authentication()

    admin_token = auth.get_tenant_token(config)
    if admin_token is None:
        print "Error while getting admin_token"
        sys.exit(2)
    else:
        print "admin_token=",admin_token

    project_token = auth.get_project_token(config, admin_token)
    if project_token is None:
        print "Error while getting project_token"
        sys.exit(2)
    else:
        print "project_token=",project_token

    c = Compute(config, admin_token, project_token)

    hosts = {}
    logical_groups = {}
    flavors = {}

    #c._set_availability_zones(hosts, logical_groups)
    #c._set_aggregates(None, logical_groups)
    #c._set_placed_vms(hosts, logical_groups)
    #c._get_vms_of_host("qos101", None)
    #c._get_vm_detail("20b2890b-81bb-4942-94bf-c6bee29630bb", None)
    c._set_resources(hosts)
    #c._set_flavors(flavors)
'''
