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

# Modified: Sep. 22, 2016


import threading
import time

from valet.engine.resource_manager.resource_base import Datacenter, HostGroup, Host, Switch, Link
from valet.engine.resource_manager.topology import Topology


class TopologyManager(threading.Thread):

    def __init__(self, _t_id, _t_name, _resource, _data_lock, _config, _logger):
        threading.Thread.__init__(self)

        self.thread_id = _t_id
        self.thread_name = _t_name
        self.data_lock = _data_lock
        self.end_of_process = False

        self.resource = _resource

        self.config = _config

        self.logger = _logger

    def run(self):
        self.logger.info("TopologyManager: start " + self.thread_name + " ......")

        if self.config.topology_trigger_freq > 0:
            period_end = time.time() + self.config.topology_trigger_freq

            while self.end_of_process is False:
                time.sleep(70)

                if time.time() > period_end:
                    self._run()
                    period_end = time.time() + self.config.topology_trigger_freq

        else:
            (alarm_HH, alarm_MM) = self.config.topology_trigger_time.split(':')
            now = time.localtime()
            timeout = True
            last_trigger_year = now.tm_year
            last_trigger_mon = now.tm_mon
            last_trigger_mday = now.tm_mday

            while self.end_of_process is False:
                time.sleep(70)

                now = time.localtime()
                if now.tm_year > last_trigger_year or now.tm_mon > last_trigger_mon or now.tm_mday > last_trigger_mday:
                    timeout = False

                if timeout is False and \
                   now.tm_hour >= int(alarm_HH) and now.tm_min >= int(alarm_MM):
                    self._run()

                    timeout = True
                    last_trigger_year = now.tm_year
                    last_trigger_mon = now.tm_mon
                    last_trigger_mday = now.tm_mday

        self.logger.info("TopologyManager: exit " + self.thread_name)

    def _run(self):

        self.logger.info("TopologyManager: --- start topology status update ---")

        self.data_lock.acquire()
        try:
            if self.set_topology() is True:
                if self.resource.update_topology() is False:
                    # TODO(GY): ignore?
                    pass
        finally:
            self.data_lock.release()

        self.logger.info("TopologyManager: --- done topology status update ---")

    def set_topology(self):
        datacenter = None
        host_groups = {}
        hosts = {}
        switches = {}

        topology = None
        if self.config.mode.startswith("sim") is True or \
           self.config.mode.startswith("test") is True:
            datacenter = Datacenter("sim")
        else:
            datacenter = Datacenter(self.config.datacenter_name)

        topology = Topology(self.config, self.logger)

        status = topology.set_topology(datacenter, host_groups, hosts, self.resource.hosts, switches)
        if status != "success":
            self.logger.error("TopologyManager: " + status)
            return False

        self._check_update(datacenter, host_groups, hosts, switches)

        return True

    def _check_update(self, _datacenter, _host_groups, _hosts, _switches):
        for sk in _switches.keys():
            if sk not in self.resource.switches.keys():
                new_switch = self._create_new_switch(_switches[sk])
                self.resource.switches[new_switch.name] = new_switch

                new_switch.last_update = time.time()

                self.logger.warn("TopologyManager: new switch (" + new_switch.name + ") added")

        for rsk in self.resource.switches.keys():
            if rsk not in _switches.keys():
                switch = self.resource.switches[rsk]
                switch.status = "disabled"

                switch.last_update = time.time()

                self.logger.warn("TopologyManager: switch (" + switch.name + ") disabled")

        for hk in _hosts.keys():
            if hk not in self.resource.hosts.keys():
                new_host = self._create_new_host(_hosts[hk])
                self.resource.hosts[new_host.name] = new_host

                new_host.last_update = time.time()

                self.logger.warn("TopologyManager: new host (" + new_host.name + ") added from configuration")

        for rhk in self.resource.hosts.keys():
            if rhk not in _hosts.keys():
                host = self.resource.hosts[rhk]
                if "infra" in host.tag:
                    host.tag.remove("infra")

                host.last_update = time.time()

                self.logger.warn("TopologyManager: host (" + host.name + ") removed from configuration")

        for hgk in _host_groups.keys():
            if hgk not in self.resource.host_groups.keys():
                new_host_group = self._create_new_host_group(_host_groups[hgk])
                self.resource.host_groups[new_host_group.name] = new_host_group

                new_host_group.last_update = time.time()

                self.logger.warn("TopologyManager: new host_group (" + new_host_group.name + ") added")

        for rhgk in self.resource.host_groups.keys():
            if rhgk not in _host_groups.keys():
                host_group = self.resource.host_groups[rhgk]
                host_group.status = "disabled"

                host_group.last_update = time.time()

                self.logger.warn("TopologyManager: host_group (" + host_group.name + ") disabled")

        for sk in _switches.keys():
            switch = _switches[sk]
            rswitch = self.resource.switches[sk]
            link_updated = self._check_switch_update(switch, rswitch)
            if link_updated is True:
                rswitch.last_update = time.time()

        for hk in _hosts.keys():
            host = _hosts[hk]
            rhost = self.resource.hosts[hk]
            (topology_updated, link_updated) = self._check_host_update(host, rhost)
            if topology_updated is True:
                rhost.last_update = time.time()
            if link_updated is True:
                rhost.last_link_update = time.time()

        for hgk in _host_groups.keys():
            hg = _host_groups[hgk]
            rhg = self.resource.host_groups[hgk]
            (topology_updated, link_updated) = self._check_host_group_update(hg, rhg)
            if topology_updated is True:
                rhg.last_update = time.time()
            if link_updated is True:
                rhg.last_link_update = time.time()

        (topology_updated, link_updated) = self._check_datacenter_update(_datacenter)
        if topology_updated is True:
            self.resource.datacenter.last_update = time.time()
        if link_updated is True:
            self.resource.datacenter.last_link_update = time.time()

        for hk, host in self.resource.hosts.iteritems():
            if host.last_update > self.resource.current_timestamp:
                self.resource.update_rack_resource(host)

        for hgk, hg in self.resource.host_groups.iteritems():
            if hg.last_update > self.resource.current_timestamp:
                self.resource.update_cluster_resource(hg)

    def _create_new_switch(self, _switch):
        new_switch = Switch(_switch.name)
        new_switch.switch_type = _switch.switch_type

        return new_switch

    def _create_new_link(self, _link):
        new_link = Link(_link.name)
        new_link.resource = self.resource.switches[_link.resource.name]

        new_link.nw_bandwidth = _link.nw_bandwidth
        new_link.avail_nw_bandwidth = new_link.nw_bandwidth

        return new_link

    def _create_new_host(self, _host):
        new_host = Host(_host.name)
        new_host.tag.append("infra")

        return new_host

    def _create_new_host_group(self, _hg):
        new_hg = HostGroup(_hg.name)
        new_hg.host_type = _hg.host_type

        return new_hg

    def _check_switch_update(self, _switch, _rswitch):
        updated = False

        if _switch.switch_type != _rswitch.switch_type:
            _rswitch.switch_type = _switch.switch_type
            updated = True
            self.logger.warn("TopologyManager: switch (" + _rswitch.name + ") updated (switch type)")

        if _rswitch.status == "disabled":
            _rswitch.status = "enabled"
            updated = True
            self.logger.warn("TopologyManager: switch (" + _rswitch.name + ") updated (enabled)")

        for ulk in _switch.up_links.keys():
            exist = False
            for rulk in _rswitch.up_links.keys():
                if ulk == rulk:
                    exist = True
                    break
            if exist is False:
                new_link = self._create_new_link(_switch.up_links[ulk])
                _rswitch.up_links[new_link.name] = new_link
                updated = True
                self.logger.warn("TopologyManager: switch (" + _rswitch.name + ") updated (new link)")

        for rulk in _rswitch.up_links.keys():
            exist = False
            for ulk in _switch.up_links.keys():
                if rulk == ulk:
                    exist = True
                    break
            if exist is False:
                del _rswitch.up_links[rulk]
                updated = True
                self.logger.warn("TopologyManager: switch (" + _rswitch.name + ") updated (link removed)")

        for ulk in _rswitch.up_links.keys():
            link = _switch.up_links[ulk]
            rlink = _rswitch.up_links[ulk]
            if self._check_link_update(link, rlink) is True:
                updated = True
                self.logger.warn("TopologyManager: switch (" + _rswitch.name + ") updated (bandwidth)")

        for plk in _switch.peer_links.keys():
            exist = False
            for rplk in _rswitch.peer_links.keys():
                if plk == rplk:
                    exist = True
                    break
            if exist is False:
                new_link = self._create_new_link(_switch.peer_links[plk])
                _rswitch.peer_links[new_link.name] = new_link
                updated = True
                self.logger.warn("TopologyManager: switch (" + _rswitch.name + ") updated (new link)")

        for rplk in _rswitch.peer_links.keys():
            exist = False
            for plk in _switch.peer_links.keys():
                if rplk == plk:
                    exist = True
                    break
            if exist is False:
                del _rswitch.peer_links[rplk]
                updated = True
                self.logger.warn("TopologyManager: switch (" + _rswitch.name + ") updated (link removed)")

        for plk in _rswitch.peer_links.keys():
            link = _switch.peer_links[plk]
            rlink = _rswitch.peer_links[plk]
            if self._check_link_update(link, rlink) is True:
                updated = True
                self.logger.warn("TopologyManager: switch (" + _rswitch.name + ") updated (bandwidth)")

        return updated

    def _check_link_update(self, _link, _rlink):
        updated = False

        if _link.nw_bandwidth != _rlink.nw_bandwidth:
            _rlink.nw_bandwidth = _link.nw_bandwidth
            updated = True

        return updated

    def _check_host_update(self, _host, _rhost):
        updated = False
        link_updated = False

        if "infra" not in _rhost.tag:
            _rhost.tag.append("infra")
            updated = True
            self.logger.warn("TopologyManager: host (" + _rhost.name + ") updated (tag)")

        if _rhost.host_group is None or _host.host_group.name != _rhost.host_group.name:
            if _host.host_group.name in self.resource.host_groups.keys():
                _rhost.host_group = self.resource.host_groups[_host.host_group.name]
            else:
                _rhost.host_group = self.resource.datacenter
            updated = True
            self.logger.warn("TopologyManager: host (" + _rhost.name + ") updated (host_group)")

        for sk in _host.switches.keys():
            exist = False
            for rsk in _rhost.switches.keys():
                if sk == rsk:
                    exist = True
                    break
            if exist is False:
                _rhost.switches[sk] = self.resource.switches[sk]
                link_updated = True
                self.logger.warn("TopologyManager: host (" + _rhost.name + ") updated (new switch)")

        for rsk in _rhost.switches.keys():
            exist = False
            for sk in _host.switches.keys():
                if rsk == sk:
                    exist = True
                    break
            if exist is False:
                del _rhost.switches[rsk]
                link_updated = True
                self.logger.warn("TopologyManager: host (" + _rhost.name + ") updated (switch removed)")

        return (updated, link_updated)

    def _check_host_group_update(self, _hg, _rhg):
        updated = False
        link_updated = False

        if _hg.host_type != _rhg.host_type:
            _rhg.host_type = _hg.host_type
            updated = True
            self.logger.warn("TopologyManager: host_group (" + _rhg.name + ") updated (hosting type)")

        if _rhg.status == "disabled":
            _rhg.status = "enabled"
            updated = True
            self.logger.warn("TopologyManager: host_group (" + _rhg.name + ") updated (enabled)")

        if _rhg.parent_resource is None or _hg.parent_resource.name != _rhg.parent_resource.name:
            if _hg.parent_resource.name in self.resource.host_groups.keys():
                _rhg.parent_resource = self.resource.host_groups[_hg.parent_resource.name]
            else:
                _rhg.parent_resource = self.resource.datacenter
            updated = True
            self.logger.warn("TopologyManager: host_group (" + _rhg.name + ") updated (parent host_group)")

        for rk in _hg.child_resources.keys():
            exist = False
            for rrk in _rhg.child_resources.keys():
                if rk == rrk:
                    exist = True
                    break
            if exist is False:
                if _rhg.host_type == "rack":
                    _rhg.child_resources[rk] = self.resource.hosts[rk]
                elif _rhg.host_type == "cluster":
                    _rhg.child_resources[rk] = self.resource.host_groups[rk]
                updated = True
                self.logger.warn("TopologyManager: host_group (" + _rhg.name + ") updated (new child host)")

        for rrk in _rhg.child_resources.keys():
            exist = False
            for rk in _hg.child_resources.keys():
                if rrk == rk:
                    exist = True
                    break
            if exist is False:
                del _rhg.child_resources[rrk]
                updated = True
                self.logger.warn("TopologyManager: host_group (" + _rhg.name + ") updated (child host removed)")

        for sk in _hg.switches.keys():
            exist = False
            for rsk in _rhg.switches.keys():
                if sk == rsk:
                    exist = True
                    break
            if exist is False:
                _rhg.switches[sk] = self.resource.switches[sk]
                link_updated = True
                self.logger.warn("TopologyManager: host_group (" + _rhg.name + ") updated (new switch)")

        for rsk in _rhg.switches.keys():
            exist = False
            for sk in _hg.switches.keys():
                if rsk == sk:
                    exist = True
                    break
            if exist is False:
                del _rhg.switches[rsk]
                link_updated = True
                self.logger.warn("TopologyManager: host_group (" + _rhg.name + ") updated (switch removed)")

        return (updated, link_updated)

    def _check_datacenter_update(self, _datacenter):
        updated = False
        link_updated = False

        for rc in _datacenter.region_code_list:
            if rc not in self.resource.datacenter.region_code_list:
                self.resource.datacenter.region_code_list.append(rc)
                updated = True
                self.logger.warn("TopologyManager: datacenter updated (new region code, " + rc + ")")

        for rrc in self.resource.datacenter.region_code_list:
            if rrc not in _datacenter.region_code_list:
                self.resource.datacenter.region_code_list.remove(rrc)
                updated = True
                self.logger.warn("TopologyManager: datacenter updated (region code, " + rrc + ", removed)")

        for rk in _datacenter.resources.keys():
            exist = False
            for rrk in self.resource.datacenter.resources.keys():
                if rk == rrk:
                    exist = True
                    break
            if exist is False:
                r = _datacenter.resources[rk]
                if isinstance(r, HostGroup):
                    self.resource.datacenter.resources[rk] = self.resource.host_groups[rk]
                elif isinstance(r, Host):
                    self.resource.datacenter.resources[rk] = self.resource.hosts[rk]
                updated = True
                self.logger.warn("TopologyManager: datacenter updated (new resource)")

        for rrk in self.resource.datacenter.resources.keys():
            exist = False
            for rk in _datacenter.resources.keys():
                if rrk == rk:
                    exist = True
                    break
            if exist is False:
                del self.resource.datacenter.resources[rrk]
                updated = True
                self.logger.warn("TopologyManager: datacenter updated (resource removed)")

        for sk in _datacenter.root_switches.keys():
            exist = False
            for rsk in self.resource.datacenter.root_switches.keys():
                if sk == rsk:
                    exist = True
                    break
            if exist is False:
                self.resource.datacenter.root_switches[sk] = self.resource.switches[sk]
                link_updated = True
                self.logger.warn("TopologyManager: datacenter updated (new switch)")

        for rsk in self.resource.datacenter.root_switches.keys():
            exist = False
            for sk in _datacenter.root_switches.keys():
                if rsk == sk:
                    exist = True
                    break
            if exist is False:
                del self.resource.datacenter.root_switches[rsk]
                link_updated = True
                self.logger.warn("TopologyManager: datacenter updated (switch removed)")

        return (updated, link_updated)
