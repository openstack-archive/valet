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
import threading
import time

from oslo_log import log

from valet.engine.resource_manager.resource_base import Datacenter
from valet.engine.resource_manager.resource_base import Host
from valet.engine.resource_manager.resource_base import HostGroup
from valet.engine.resource_manager.topology import Topology

LOG = log.getLogger(__name__)


class TopologyManager(threading.Thread):
    """Topology Manager Class."""

    def __init__(self, _t_id, _t_name, _resource,
                 _data_lock, _config):
        """Init Topology Manager."""
        threading.Thread.__init__(self)

        self.thread_id = _t_id
        self.thread_name = _t_name
        self.data_lock = _data_lock
        self.end_of_process = False

        self.resource = _resource

        self.config = _config

        self.update_batch_wait = self.config.update_batch_wait

    def run(self):
        """Function starts and tracks Topology Manager Thread."""
        LOG.info("TopologyManager: start " +
                         self.thread_name + " ......")

        if self.config.topology_trigger_freq > 0:
            period_end = time.time() + self.config.topology_trigger_freq

            while self.end_of_process is False:
                time.sleep(70)
                curr_ts = time.time()
                if curr_ts > period_end:
                    # Give some time (batch_wait) to update resource status via
                    # message bus. Otherwise, late update will be cleaned up
                    time_diff = curr_ts - self.resource.current_timestamp
                    if time_diff > self.update_batch_wait:
                        self._run()
                        period_end = (curr_ts +
                                      self.config.topology_trigger_freq)
        # NOTE(GJ): do not timer based batch
        LOG.info("exit topology_manager " + self.thread_name)

    def _run(self):

        LOG.info("TopologyManager: --- start topology "
                         "status update ---")

        if self.set_topology() is not True:
            LOG.warning("fail to set topology")

        LOG.info("--- done topology status update ---")

    def set_topology(self):
        host_groups = {}
        hosts = {}

        # NOTE(GJ): do not consider switch topology at this version

        datacenter = Datacenter(self.config.datacenter_name)
        topology = Topology(self.config)

        status = topology.set_topology(datacenter, host_groups, hosts,
                                       self.resource.hosts)
        if status != "success":
            return False

        self.data_lock.acquire()
        if self._check_update(datacenter, host_groups, hosts) is True:
            self.resource.update_topology(store=False)
        self.data_lock.release()

        return True

    def _check_update(self, _datacenter, _host_groups, _hosts):
        updated = False

        for hk in _hosts.keys():
            if hk not in self.resource.hosts.keys():
                new_host = self._create_new_host(_hosts[hk])
                self.resource.hosts[new_host.name] = new_host

                new_host.last_update = time.time()

                LOG.warning("TopologyManager: new host (" +
                            new_host.name + ") added from configuration")
                updated = True

        for rhk in self.resource.hosts.keys():
            if rhk not in _hosts.keys():
                host = self.resource.hosts[rhk]
                if "infra" in host.tag:
                    host.tag.remove("infra")

                host.last_update = time.time()

                LOG.warning("TopologyManager: host (" +
                            host.name + ") removed from configuration")
                updated = True

        for hgk in _host_groups.keys():
            if hgk not in self.resource.host_groups.keys():
                new_host_group = self._create_new_host_group(_host_groups[hgk])
                self.resource.host_groups[new_host_group.name] = new_host_group

                new_host_group.last_update = time.time()

                LOG.warning("TopologyManager: new host_group (" +
                            new_host_group.name + ") added")
                updated = True

        for rhgk in self.resource.host_groups.keys():
            if rhgk not in _host_groups.keys():
                host_group = self.resource.host_groups[rhgk]
                host_group.status = "disabled"

                host_group.last_update = time.time()

                LOG.warning("TopologyManager: host_group (" +
                            host_group.name + ") disabled")
                updated = True

        for hk in _hosts.keys():
            host = _hosts[hk]
            rhost = self.resource.hosts[hk]
            topology_updated = self._check_host_update(host, rhost)
            if topology_updated is True:
                rhost.last_update = time.time()
                updated = True

        for hgk in _host_groups.keys():
            hg = _host_groups[hgk]
            rhg = self.resource.host_groups[hgk]
            topology_updated = self._check_host_group_update(hg, rhg)
            if topology_updated is True:
                rhg.last_update = time.time()
                updated = True

        topology_updated = self._check_datacenter_update(_datacenter)
        if topology_updated is True:
            self.resource.datacenter.last_update = time.time()
            updated = True

        for hk, host in self.resource.hosts.iteritems():
            if host.last_update >= self.resource.current_timestamp:
                self.resource.update_rack_resource(host)

        for hgk, hg in self.resource.host_groups.iteritems():
            if hg.last_update >= self.resource.current_timestamp:
                self.resource.update_cluster_resource(hg)

        return updated

    def _create_new_host(self, _host):
        new_host = Host(_host.name)
        new_host.tag.append("infra")

        return new_host

    def _create_new_host_group(self, _hg):
        new_hg = HostGroup(_hg.name)
        new_hg.host_type = _hg.host_type

        return new_hg

    def _check_host_update(self, _host, _rhost):
        updated = False

        if "infra" not in _rhost.tag:
            _rhost.tag.append("infra")
            updated = True
            LOG.warning("TopologyManager: host (" + _rhost.name +
                        ") updated (tag)")

        if (_rhost.host_group is None or
                _host.host_group.name != _rhost.host_group.name):

            if _host.host_group.name in self.resource.host_groups.keys():
                _rhost.host_group = \
                    self.resource.host_groups[_host.host_group.name]
            else:
                _rhost.host_group = self.resource.datacenter
            updated = True
            LOG.warning("TopologyManager: host (" + _rhost.name +
                        ") updated (host_group)")

        return updated

    def _check_host_group_update(self, _hg, _rhg):
        updated = False

        if _hg.host_type != _rhg.host_type:
            _rhg.host_type = _hg.host_type
            updated = True
            LOG.warning("TopologyManager: host_group (" + _rhg.name +
                        ") updated (hosting type)")

        if _rhg.status == "disabled":
            _rhg.status = "enabled"
            updated = True
            LOG.warning("TopologyManager: host_group (" + _rhg.name +
                        ") updated (enabled)")

        if _hg.parent_resource != _rhg.parent_resource:
            if _hg.parent_resource.name in self.resource.host_groups.keys():
                _rhg.parent_resource = \
                    self.resource.host_groups[_hg.parent_resource.name]
            else:
                _rhg.parent_resource = self.resource.datacenter
            updated = True
            LOG.warning("TopologyManager: host_group (" + _rhg.name +
                        ") updated (parent host_group)")

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
                LOG.warning("TopologyManager: host_group (" + _rhg.name +
                            ") updated (new child host)")

        for rrk in _rhg.child_resources.keys():
            exist = False
            for rk in _hg.child_resources.keys():
                if rrk == rk:
                    exist = True
                    break
            if exist is False:
                del _rhg.child_resources[rrk]
                updated = True
                LOG.warning("TopologyManager: host_group (" + _rhg.name +
                            ") updated (child host removed)")

        return updated

    def _check_datacenter_update(self, _datacenter):
        updated = False

        for rc in _datacenter.region_code_list:
            if rc not in self.resource.datacenter.region_code_list:
                self.resource.datacenter.region_code_list.append(rc)
                updated = True
                LOG.warning("TopologyManager: datacenter updated "
                            "(new region code, " + rc + ")")

        code_list = self.resource.datacenter.region_code_list
        blen = len(code_list)
        code_list = [r for r in code_list if r in _datacenter.region_code_list]
        alen = len(code_list)
        if alen != blen:
            updated = True
            self.resource.datacenter.region_code_list = code_list
            LOG.warning("datacenter updated (region code removed)")

        for rk in _datacenter.resources.keys():
            exist = False
            for rrk in self.resource.datacenter.resources.keys():
                if rk == rrk:
                    exist = True
                    break
            if exist is False:
                r = _datacenter.resources[rk]
                if isinstance(r, HostGroup):
                    self.resource.datacenter.resources[rk] = \
                        self.resource.host_groups[rk]
                elif isinstance(r, Host):
                    self.resource.datacenter.resources[rk] = \
                        self.resource.hosts[rk]
                updated = True
                LOG.warning("TopologyManager: datacenter updated "
                            "(new resource)")

        for rrk in self.resource.datacenter.resources.keys():
            exist = False
            for rk in _datacenter.resources.keys():
                if rrk == rk:
                    exist = True
                    break
            if exist is False:
                del self.resource.datacenter.resources[rrk]
                updated = True
                LOG.warning("TopologyManager: datacenter updated "
                            "(resource removed)")

        return updated
