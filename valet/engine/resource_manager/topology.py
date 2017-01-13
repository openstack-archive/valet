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

"""Topology class - performs actual setting up of Topology object."""

import copy
import sys

from sre_parse import isdigit
from valet.engine.resource_manager.resource_base import HostGroup, Switch, Link


class Topology(object):
    """Topology class."""

    def __init__(self, _config, _logger):
        """Init config and logger."""
        self.config = _config
        self.logger = _logger

    # Triggered by rhosts change
    def set_topology(self, _datacenter, _host_groups, _hosts, _rhosts,
                     _switches):
        """Return result status if setting host or network topology fails."""
        result_status = self._set_host_topology(_datacenter, _host_groups,
                                                _hosts, _rhosts)
        if result_status != "success":
            return result_status

        result_status = self._set_network_topology(_datacenter, _host_groups,
                                                   _hosts, _switches)
        if result_status != "success":
            return result_status

        return "success"

    # NOTE: currently, the hosts are copied from Nova
    def _set_host_topology(self, _datacenter, _host_groups, _hosts, _rhosts):
        for rhk, rh in _rhosts.iteritems():
            h = copy.deepcopy(rh)

            if "infra" not in h.tag:
                h.tag.append("infra")

            (region_name, rack_name, _, status) = self._set_layout_by_name(rhk)
            if status != "success":
                self.logger.warn(status + " in host_name (" + rhk + ")")

            if region_name not in _datacenter.region_code_list:
                _datacenter.region_code_list.append(region_name)

            if rack_name not in _host_groups.keys():
                host_group = HostGroup(rack_name)
                host_group.host_type = "rack"
                _host_groups[host_group.name] = host_group

            h.host_group = _host_groups[rack_name]

            _hosts[h.name] = h

        for hgk, hg in _host_groups.iteritems():
            hg.parent_resource = _datacenter

            for _, h in _hosts.iteritems():
                if h.host_group.name == hgk:
                    hg.child_resources[h.name] = h

            _datacenter.resources[hgk] = hg

        if len(_datacenter.region_code_list) > 1:
            self.logger.warn("more than one region code")

        if "none" in _host_groups.keys():
            self.logger.warn("some hosts are into unknown rack")

        return "success"

    # NOTE: this is just muck-ups
    def _set_network_topology(self, _datacenter, _host_groups, _hosts,
                              _switches):
        root_switch = Switch(_datacenter.name)
        root_switch.switch_type = "root"

        _datacenter.root_switches[root_switch.name] = root_switch
        _switches[root_switch.name] = root_switch

        for hgk, hg in _host_groups.iteritems():
            switch = Switch(hgk)
            switch.switch_type = "ToR"

            up_link = Link(hgk + "-" + _datacenter.name)
            up_link.resource = root_switch
            up_link.nw_bandwidth = sys.maxint
            up_link.avail_nw_bandwidth = up_link.nw_bandwidth
            switch.up_links[up_link.name] = up_link

            hg.switches[switch.name] = switch
            _switches[switch.name] = switch

            for hk, h in hg.child_resources.iteritems():
                leaf_switch = Switch(hk)
                leaf_switch.switch_type = "leaf"

                l_up_link = Link(hk + "-" + hgk)
                l_up_link.resource = switch
                l_up_link.nw_bandwidth = sys.maxint
                l_up_link.avail_nw_bandwidth = l_up_link.nw_bandwidth
                leaf_switch.up_links[l_up_link.name] = l_up_link

                h.switches[leaf_switch.name] = leaf_switch
                _switches[leaf_switch.name] = leaf_switch

        return "success"

    def _set_layout_by_name(self, _host_name):
        region_name = None
        rack_name = None
        node_type = None
        status = "success"

        validated_name = True

        num_of_fields = 0

        index = 0
        end_of_region_index = 0
        end_of_rack_index = 0
        index_of_node_type = 0

        for c in _host_name:
            if index >= self.config.num_of_region_chars:
                if not isdigit(c):
                    if index == self.config.num_of_region_chars:
                        status = "invalid region name = " + \
                                 _host_name[:index] + c
                        validated_name = False
                        break

                    if end_of_region_index == 0:
                        if c not in self.config.rack_code_list:
                            status = "invalid rack_char = " + c
                            validated_name = False
                            break

                        end_of_region_index = index
                        num_of_fields += 1

                    if index == (end_of_region_index + 1):
                        status = "invalid rack name = " + _host_name[:index] + c
                        validated_name = False
                        break

                    if end_of_rack_index == 0 and \
                        index > (end_of_region_index + 1):

                        end_of_rack_index = index
                        num_of_fields += 1

                    if node_type is None and end_of_rack_index > 0:
                        node_type = c
                        if node_type not in self.config.node_code_list:
                            status = "invalid node_char = " + c
                            validated_name = False
                            break
                        index_of_node_type = index
                        num_of_fields += 1

                    if c == '.':
                        break

                    if index_of_node_type > 0 and index > index_of_node_type:
                        num_of_fields += 1
                        break

            index += 1

        if not index > (index_of_node_type + 1):
            status = "invalid node name = " + _host_name[:index]
            validated_name = False

        if num_of_fields != 3:
            status = "invalid number of identification fields = " + \
                     str(num_of_fields)
            validated_name = False

        if validated_name is False:
            region_name = "none"
            rack_name = "none"
        else:
            region_name = _host_name[:end_of_region_index]
            rack_name = _host_name[:end_of_rack_index]

        return (region_name, rack_name, node_type, status)
