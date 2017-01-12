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

from copy import deepcopy
from valet.engine.resource_manager.compute import Compute
from valet.engine.resource_manager.compute_simulator import SimCompute
from valet.engine.resource_manager.resource_base import Host


class ComputeManager(threading.Thread):

    def __init__(self, _t_id, _t_name, _rsc, _data_lock, _config, _logger):
        threading.Thread.__init__(self)

        self.thread_id = _t_id
        self.thread_name = _t_name
        self.data_lock = _data_lock
        self.end_of_process = False

        self.resource = _rsc

        self.config = _config

        self.logger = _logger

        self.admin_token = None
        self.project_token = None

    def run(self):
        self.logger.info("ComputeManager: start " + self.thread_name + " ......")

        if self.config.compute_trigger_freq > 0:
            period_end = time.time() + self.config.compute_trigger_freq

            while self.end_of_process is False:
                time.sleep(60)

                if time.time() > period_end:
                    self._run()
                    period_end = time.time() + self.config.compute_trigger_freq

        else:
            (alarm_HH, alarm_MM) = self.config.compute_trigger_time.split(':')

            now = time.localtime()
            timeout = True
            last_trigger_year = now.tm_year
            last_trigger_mon = now.tm_mon
            last_trigger_mday = now.tm_mday

            while self.end_of_process is False:
                time.sleep(60)

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

        self.logger.info("ComputeManager: exit " + self.thread_name)

    def _run(self):
        self.logger.info("ComputeManager: --- start compute_nodes status update ---")

        self.data_lock.acquire()
        try:
            triggered_host_updates = self.set_hosts()
            triggered_flavor_updates = self.set_flavors()

            if triggered_host_updates is True and triggered_flavor_updates is True:
                if self.resource.update_topology() is False:
                    # TODO: error in MUSIC. ignore?
                    pass
            else:
                # TODO: error handling, e.g., 3 times failure then stop Ostro?
                pass
        finally:
            self.data_lock.release()

        self.logger.info("ComputeManager: --- done compute_nodes status update ---")

        return True

    def set_hosts(self):
        hosts = {}
        logical_groups = {}

        compute = None
        if self.config.mode.startswith("sim") is True or \
           self.config.mode.startswith("test") is True:
            compute = SimCompute(self.config)
        else:
            compute = Compute(self.logger)

        status = compute.set_hosts(hosts, logical_groups)
        if status != "success":
            self.logger.error("ComputeManager: " + status)
            return False

        self._compute_avail_host_resources(hosts)

        self._check_logical_group_update(logical_groups)
        self._check_host_update(hosts)

        return True

    def _compute_avail_host_resources(self, _hosts):
        for hk, host in _hosts.iteritems():
            self.resource.compute_avail_resources(hk, host)

    def _check_logical_group_update(self, _logical_groups):
        for lk in _logical_groups.keys():
            if lk not in self.resource.logical_groups.keys():
                self.resource.logical_groups[lk] = deepcopy(_logical_groups[lk])

                self.resource.logical_groups[lk].last_update = time.time()
                self.logger.warn("ComputeManager: new logical group (" + lk + ") added")

        for rlk in self.resource.logical_groups.keys():
            rl = self.resource.logical_groups[rlk]
            if rl.group_type != "EX" and rl.group_type != "AFF" and rl.group_type != "DIV":
                if rlk not in _logical_groups.keys():
                    self.resource.logical_groups[rlk].status = "disabled"

                    self.resource.logical_groups[rlk].last_update = time.time()
                    self.logger.warn("ComputeManager: logical group (" + rlk + ") removed")

        for lk in _logical_groups.keys():
            lg = _logical_groups[lk]
            rlg = self.resource.logical_groups[lk]
            if lg.group_type != "EX" and lg.group_type != "AFF" and lg.group_type != "DIV":
                if self._check_logical_group_metadata_update(lg, rlg) is True:

                    rlg.last_update = time.time()
                    self.logger.warn("ComputeManager: logical group (" + lk + ") updated")

    def _check_logical_group_metadata_update(self, _lg, _rlg):
        if _lg.status != _rlg.status:
            _rlg.status = _lg.status

        for mdk in _lg.metadata.keys():
            if mdk not in _rlg.metadata.keys():
                _rlg.metadata[mdk] = _lg.metadata[mdk]

        for rmdk in _rlg.metadata.keys():
            if rmdk not in _lg.metadata.keys():
                del _rlg.metadata[rmdk]

        for hk in _lg.vms_per_host.keys():
            if hk not in _rlg.vms_per_host.keys():
                _rlg.vms_per_host[hk] = deepcopy(_lg.vms_per_host[hk])

        for rhk in _rlg.vms_per_host.keys():
            if rhk not in _lg.vms_per_host.keys():
                del _rlg.vms_per_host[rhk]

    def _check_host_update(self, _hosts):
        for hk in _hosts.keys():
            if hk not in self.resource.hosts.keys():
                new_host = Host(hk)
                self.resource.hosts[new_host.name] = new_host

                new_host.last_update = time.time()
                self.logger.warn("ComputeManager: new host (" + new_host.name + ") added")

        for rhk, rhost in self.resource.hosts.iteritems():
            if rhk not in _hosts.keys():
                if "nova" in rhost.tag:
                    rhost.tag.remove("nova")

                    rhost.last_update = time.time()
                    self.logger.warn("ComputeManager: host (" + rhost.name + ") disabled")

        for hk in _hosts.keys():
            host = _hosts[hk]
            rhost = self.resource.hosts[hk]
            if self._check_host_config_update(host, rhost) is True:
                rhost.last_update = time.time()

        for hk, h in self.resource.hosts.iteritems():
            if h.clean_memberships() is True:
                h.last_update = time.time()
                self.logger.warn("ComputeManager: host (" + h.name + ") updated (delete EX/AFF/DIV membership)")

        for hk, host in self.resource.hosts.iteritems():
            if host.last_update > self.resource.current_timestamp:
                self.resource.update_rack_resource(host)

    def _check_host_config_update(self, _host, _rhost):
        topology_updated = False

        topology_updated = self._check_host_status(_host, _rhost)
        topology_updated = self._check_host_resources(_host, _rhost)
        topology_updated = self._check_host_memberships(_host, _rhost)
        topology_updated = self._check_host_vms(_host, _rhost)

        return topology_updated

    def _check_host_status(self, _host, _rhost):
        topology_updated = False

        if "nova" not in _rhost.tag:
            _rhost.tag.append("nova")
            topology_updated = True
            self.logger.warn("ComputeManager: host (" + _rhost.name + ") updated (tag added)")

        if _host.status != _rhost.status:
            _rhost.status = _host.status
            topology_updated = True
            self.logger.warn("ComputeManager: host (" + _rhost.name + ") updated (status changed)")

        if _host.state != _rhost.state:
            _rhost.state = _host.state
            topology_updated = True
            self.logger.warn("ComputeManager: host (" + _rhost.name + ") updated (state changed)")

        return topology_updated

    def _check_host_resources(self, _host, _rhost):
        topology_updated = False

        if _host.vCPUs != _rhost.vCPUs or \
           _host.original_vCPUs != _rhost.original_vCPUs or \
           _host.avail_vCPUs != _rhost.avail_vCPUs:
            _rhost.vCPUs = _host.vCPUs
            _rhost.original_vCPUs = _host.original_vCPUs
            _rhost.avail_vCPUs = _host.avail_vCPUs
            topology_updated = True
            self.logger.warn("ComputeManager: host (" + _rhost.name + ") updated (CPU updated)")

        if _host.mem_cap != _rhost.mem_cap or \
           _host.original_mem_cap != _rhost.original_mem_cap or \
           _host.avail_mem_cap != _rhost.avail_mem_cap:
            _rhost.mem_cap = _host.mem_cap
            _rhost.original_mem_cap = _host.original_mem_cap
            _rhost.avail_mem_cap = _host.avail_mem_cap
            topology_updated = True
            self.logger.warn("ComputeManager: host (" + _rhost.name + ") updated (mem updated)")

        if _host.local_disk_cap != _rhost.local_disk_cap or \
           _host.original_local_disk_cap != _rhost.original_local_disk_cap or \
           _host.avail_local_disk_cap != _rhost.avail_local_disk_cap:
            _rhost.local_disk_cap = _host.local_disk_cap
            _rhost.original_local_disk_cap = _host.original_local_disk_cap
            _rhost.avail_local_disk_cap = _host.avail_local_disk_cap
            topology_updated = True
            self.logger.warn("ComputeManager: host (" + _rhost.name + ") updated (local disk space updated)")

        if _host.vCPUs_used != _rhost.vCPUs_used or \
           _host.free_mem_mb != _rhost.free_mem_mb or \
           _host.free_disk_gb != _rhost.free_disk_gb or \
           _host.disk_available_least != _rhost.disk_available_least:
            _rhost.vCPUs_used = _host.vCPUs_used
            _rhost.free_mem_mb = _host.free_mem_mb
            _rhost.free_disk_gb = _host.free_disk_gb
            _rhost.disk_available_least = _host.disk_available_least
            topology_updated = True
            self.logger.warn("ComputeManager: host (" + _rhost.name + ") updated (other resource numbers)")

        return topology_updated

    def _check_host_memberships(self, _host, _rhost):
        topology_updated = False

        for mk in _host.memberships.keys():
            if mk not in _rhost.memberships.keys():
                _rhost.memberships[mk] = self.resource.logical_groups[mk]
                topology_updated = True
                self.logger.warn("ComputeManager: host (" + _rhost.name + ") updated (new membership)")

        for mk in _rhost.memberships.keys():
            m = _rhost.memberships[mk]
            if m.group_type != "EX" and m.group_type != "AFF" and m.group_type != "DIV":
                if mk not in _host.memberships.keys():
                    del _rhost.memberships[mk]
                    topology_updated = True
                    self.logger.warn("ComputeManager: host (" + _rhost.name + ") updated (delete membership)")

        return topology_updated

    def _check_host_vms(self, _host, _rhost):
        topology_updated = False

        ''' clean up VMs '''
        for rvm_id in _rhost.vm_list:
            if rvm_id[2] == "none":
                _rhost.vm_list.remove(rvm_id)

                topology_updated = True
                self.logger.warn("ComputeManager: host (" + _rhost.name + ") updated (none vm removed)")

        self.resource.clean_none_vms_from_logical_groups(_rhost)

        for vm_id in _host.vm_list:
            if _rhost.exist_vm_by_uuid(vm_id[2]) is False:
                _rhost.vm_list.append(vm_id)

                topology_updated = True
                self.logger.warn("ComputeManager: host (" + _rhost.name + ") updated (new vm placed)")

        for rvm_id in _rhost.vm_list:
            if _host.exist_vm_by_uuid(rvm_id[2]) is False:
                _rhost.vm_list.remove(rvm_id)

                self.resource.remove_vm_by_uuid_from_logical_groups(_rhost, rvm_id[2])

                topology_updated = True
                self.logger.warn("ComputeManager: host (" + _rhost.name + ") updated (vm removed)")

        return topology_updated

    def set_flavors(self):
        flavors = {}

        compute = None
        if self.config.mode.startswith("sim") is True or \
           self.config.mode.startswith("test") is True:
            compute = SimCompute(self.config)
        else:
            compute = Compute(self.logger)

        status = compute.set_flavors(flavors)
        if status != "success":
            self.logger.error("ComputeManager: " + status)
            return False

        self._check_flavor_update(flavors)

        return True

    def _check_flavor_update(self, _flavors):
        for fk in _flavors.keys():
            if fk not in self.resource.flavors.keys():
                self.resource.flavors[fk] = deepcopy(_flavors[fk])

                self.resource.flavors[fk].last_update = time.time()
                self.logger.warn("ComputeManager: new flavor (" + fk + ") added")

        for rfk in self.resource.flavors.keys():
            if rfk not in _flavors.keys():
                self.resource.flavors[rfk].status = "disabled"

                self.resource.flavors[rfk].last_update = time.time()
                self.logger.warn("ComputeManager: flavor (" + rfk + ") removed")

        for fk in _flavors.keys():
            f = _flavors[fk]
            rf = self.resource.flavors[fk]

            if self._check_flavor_spec_update(f, rf) is True:
                rf.last_update = time.time()
                self.logger.warn("ComputeManager: flavor (" + fk + ") spec updated")

    def _check_flavor_spec_update(self, _f, _rf):
        spec_updated = False

        if _f.status != _rf.status:
            _rf.status = _f.status
            spec_updated = True

        if _f.vCPUs != _rf.vCPUs or _f.mem_cap != _rf.mem_cap or _f.disk_cap != _rf.disk_cap:
            _rf.vCPUs = _f.vCPUs
            _rf.mem_cap = _f.mem_cap
            _rf.disk_cap = _f.disk_cap
            spec_updated = True

        for sk in _f.extra_specs.keys():
            if sk not in _rf.extra_specs.keys():
                _rf.extra_specs[sk] = _f.extra_specs[sk]
                spec_updated = True

        for rsk in _rf.extra_specs.keys():
            if rsk not in _f.extra_specs.keys():
                del _rf.extra_specs[rsk]
                spec_updated = True

        return spec_updated
