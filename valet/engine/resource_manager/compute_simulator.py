#!/bin/python

# Modified: Sep. 4, 2016


from valet.engine.resource_manager.resource_base import Host, LogicalGroup, Flavor


class SimCompute(object):

    def __init__(self, _config):
        self.config = _config
        self.datacenter_name = "sim"

    def set_hosts(self, _hosts, _logical_groups):
        self._set_availability_zones(_hosts, _logical_groups)

        self._set_aggregates(_hosts, _logical_groups)

        self._set_placed_vms(_hosts, _logical_groups)

        self._set_resources(_hosts)

        return "success"

    def _set_availability_zones(self, _hosts, _logical_groups):
        logical_group = LogicalGroup("nova")
        logical_group.group_type = "AZ"
        _logical_groups[logical_group.name] = logical_group

        for r_num in range(0, self.config.num_of_racks):
            for h_num in range(0, self.config.num_of_hosts_per_rack):
                host = Host(self.datacenter_name + "0r" + str(r_num) + "c" + str(h_num))
                host.tag.append("nova")
                host.memberships["nova"] = logical_group

                logical_group.vms_per_host[host.name] = []

                _hosts[host.name] = host

    def _set_aggregates(self, _hosts, _logical_groups):
        for a_num in range(0, self.config.num_of_aggregates):
            metadata = {}
            metadata["cpu_allocation_ratio"] = "0.5"

            aggregate = LogicalGroup("aggregate" + str(a_num))
            aggregate.group_type = "AGGR"
            aggregate.metadata = metadata

            _logical_groups[aggregate.name] = aggregate

        for a_num in range(0, self.config.num_of_aggregates):
            aggregate = _logical_groups["aggregate" + str(a_num)]
            for r_num in range(0, self.config.num_of_racks):
                for h_num in range(0, self.config.num_of_hosts_per_rack):
                    host_name = self.datacenter_name + "0r" + str(r_num) + "c" + str(h_num)
                    if host_name in _hosts.keys():
                        if (h_num % (self.config.aggregated_ratio + a_num)) == 0:
                            host = _hosts[host_name]
                            host.memberships[aggregate.name] = aggregate

                            aggregate.vms_per_host[host.name] = []

    def _set_placed_vms(self, _hosts, _logical_groups):
        pass

    def _set_resources(self, _hosts):
        for r_num in range(0, self.config.num_of_racks):
            for h_num in range(0, self.config.num_of_hosts_per_rack):
                host_name = self.datacenter_name + "0r" + str(r_num) + "c" + str(h_num)
                if host_name in _hosts.keys():
                    host = _hosts[host_name]
                    host.original_vCPUs = float(self.config.cpus_per_host)
                    host.vCPUs_used = 0.0
                    host.original_mem_cap = float(self.config.mem_per_host)
                    host.free_mem_mb = host.original_mem_cap
                    host.original_local_disk_cap = float(self.config.disk_per_host)
                    host.free_disk_gb = host.original_local_disk_cap
                    host.disk_available_least = host.original_local_disk_cap

    def set_flavors(self, _flavors):
        for f_num in range(0, self.config.num_of_basic_flavors):
            flavor = Flavor("bflavor" + str(f_num))
            flavor.vCPUs = float(self.config.base_flavor_cpus * (f_num + 1))
            flavor.mem_cap = float(self.config.base_flavor_mem * (f_num + 1))
            flavor.disk_cap = float(self.config.base_flavor_disk * (f_num + 1)) + 10.0 + 20.0 / 1024.0

            _flavors[flavor.name] = flavor

        for a_num in range(0, self.config.num_of_aggregates):
            flavor = Flavor("sflavor" + str(a_num))
            flavor.vCPUs = self.config.base_flavor_cpus * (a_num + 1)
            flavor.mem_cap = self.config.base_flavor_mem * (a_num + 1)
            flavor.disk_cap = self.config.base_flavor_disk * (a_num + 1)

            # flavor.extra_specs["availability_zone"] = "nova"
            flavor.extra_specs["cpu_allocation_ratio"] = "0.5"

            _flavors[flavor.name] = flavor

        return "success"
