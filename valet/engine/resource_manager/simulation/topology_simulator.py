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

"""Simulate datacenter configurations (i.e., layout, cabling)."""

from valet.engine.resource_manager.resource_base \
    import HostGroup, Host, Switch, Link


class SimTopology(object):
    """Simulate Network and Host Topology class."""

    def __init__(self, _config):
        """Init."""
        self.config = _config

    def set_topology(self, _datacenter, _host_groups, _hosts, _switches):
        """Return success string after setting network and host topology."""
        self._set_network_topology(_switches)
        self._set_host_topology(_datacenter, _host_groups, _hosts, _switches)

        return "success"

    def _set_network_topology(self, _switches):
        root_switch = Switch("r0")
        root_switch.switch_type = "root"
        _switches[root_switch.name] = root_switch

        if self.config.num_of_spine_switches > 0:
            for s_num in range(0, self.config.num_of_spine_switches):
                switch = Switch(root_switch.name + "s" + str(s_num))
                switch.switch_type = "spine"
                _switches[switch.name] = switch

        for r_num in range(0, self.config.num_of_racks):
            switch = Switch(root_switch.name + "t" + str(r_num))
            switch.switch_type = "ToR"
            _switches[switch.name] = switch

            for h_num in range(0, self.config.num_of_hosts_per_rack):
                leaf_switch = Switch(switch.name + "l" + str(h_num))
                leaf_switch.switch_type = "leaf"
                _switches[leaf_switch.name] = leaf_switch

        if self.config.num_of_spine_switches > 0:
            for s_num in range(0, self.config.num_of_spine_switches):
                s = _switches[root_switch.name + "s" + str(s_num)]

                up_link = Link(s.name + "-" + root_switch.name)
                up_link.resource = root_switch
                up_link.nw_bandwidth = self.config.bandwidth_of_spine
                up_link.avail_nw_bandwidth = up_link.nw_bandwidth
                s.up_links[up_link.name] = up_link

                if self.config.num_of_spine_switches > 1:
                    ps = None
                    if (s_num % 2) == 0:
                        if (s_num + 1) < self.config.num_of_spine_switches:
                            ps = _switches[root_switch.name + "s" +
                                           str(s_num + 1)]
                    else:
                        ps = _switches[root_switch.name + "s" + str(s_num - 1)]
                    if ps is not None:
                        peer_link = Link(s.name + "-" + ps.name)
                        peer_link.resource = ps
                        peer_link.nw_bandwidth = self.config.bandwidth_of_spine
                        peer_link.avail_nw_bandwidth = peer_link.nw_bandwidth
                        s.peer_links[peer_link.name] = peer_link

        for r_num in range(0, self.config.num_of_racks):
            s = _switches[root_switch.name + "t" + str(r_num)]

            parent_switch_list = []
            if self.config.num_of_spine_switches > 0:
                for s_num in range(0, self.config.num_of_spine_switches):
                    parent_switch_list.append(_switches[root_switch.name +
                                                        "s" + str(s_num)])
            else:
                parent_switch_list.append(_switches[root_switch.name])

            for parent_switch in parent_switch_list:
                up_link = Link(s.name + "-" + parent_switch.name)
                up_link.resource = parent_switch
                up_link.nw_bandwidth = self.config.bandwidth_of_rack
                up_link.avail_nw_bandwidth = up_link.nw_bandwidth
                s.up_links[up_link.name] = up_link

            if self.config.num_of_racks > 1:
                ps = None
                if (r_num % 2) == 0:
                    if (r_num + 1) < self.config.num_of_racks:
                        ps = _switches[root_switch.name + "t" + str(r_num + 1)]
                else:
                    ps = _switches[root_switch.name + "t" + str(r_num - 1)]
                if ps is not None:
                    peer_link = Link(s.name + "-" + ps.name)
                    peer_link.resource = ps
                    peer_link.nw_bandwidth = self.config.bandwidth_of_rack
                    peer_link.avail_nw_bandwidth = peer_link.nw_bandwidth
                    s.peer_links[peer_link.name] = peer_link

            for h_num in range(0, self.config.num_of_hosts_per_rack):
                ls = _switches[s.name + "l" + str(h_num)]

                l_up_link = Link(ls.name + "-" + s.name)
                l_up_link.resource = s
                l_up_link.nw_bandwidth = self.config.bandwidth_of_host
                l_up_link.avail_nw_bandwidth = l_up_link.nw_bandwidth
                ls.up_links[l_up_link.name] = l_up_link

    def _set_host_topology(self, _datacenter, _host_groups, _hosts, _switches):
        root_switch = _switches["r0"]

        for r_num in range(0, self.config.num_of_racks):
            host_group = HostGroup(_datacenter.name + "r" + str(r_num))
            host_group.host_type = "rack"
            switch = _switches[root_switch.name + "t" + str(r_num)]
            host_group.switches[switch.name] = switch
            _host_groups[host_group.name] = host_group

            for h_num in range(0, self.config.num_of_hosts_per_rack):
                host = Host(host_group.name + "c" + str(h_num))
                leaf_switch = _switches[switch.name + "l" + str(h_num)]
                host.switches[leaf_switch.name] = leaf_switch
                _hosts[host.name] = host

        for r_num in range(0, self.config.num_of_racks):
            host_group = _host_groups[_datacenter.name + "r" + str(r_num)]
            host_group.parent_resource = _datacenter

            for h_num in range(0, self.config.num_of_hosts_per_rack):
                host = _hosts[host_group.name + "c" + str(h_num)]
                host.host_group = host_group

                host_group.child_resources[host.name] = host

        _datacenter.root_switches[root_switch.name] = root_switch

        for r_num in range(0, self.config.num_of_racks):
            host_group = _host_groups[_datacenter.name + "r" + str(r_num)]
            _datacenter.resources[host_group.name] = host_group
