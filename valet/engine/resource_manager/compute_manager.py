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

"""Compute Manager."""

import threading
import time

from copy import deepcopy
from valet.engine.resource_manager.compute import Compute
from valet.engine.resource_manager.resource_base import Host


class ComputeManager(threading.Thread):
    """Compute Manager Class.

    Threaded class to setup and manage compute for resources, hosts,
    flavors, etc. Calls many functions from Resource.
    """

    def __init__(self, _t_id, _t_name, _rsc, _data_lock, _config, _logger):
        """Init Compute Manager."""
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

        self.update_batch_wait = self.config.update_batch_wait

    def run(self):
        """Start Compute Manager thread to run setup."""
        self.logger.info("ComputeManager: start " + self.thread_name +
                         " ......")

        if self.config.compute_trigger_freq > 0:
            period_end = time.time() + self.config.compute_trigger_freq

            while self.end_of_process is False:
                time.sleep(60)
                curr_ts = time.time()
                if curr_ts > period_end:
                    # Give some time (batch_wait) to update resource status via message bus
                    # Otherwise, late update will be cleaned up
                    if (curr_ts - self.resource.current_timestamp) > self.update_batch_wait:
                        self._run()
                        period_end = curr_ts + self.config.compute_trigger_freq

        # NOTE(GJ): do not timer based batch
        self.logger.info("exit compute_manager " + self.thread_name)

    def _run(self):
        self.logger.info("ComputeManager: --- start compute_nodes "
                         "status update ---")

        triggered_host_updates = self.set_hosts()
        if triggered_host_updates is not True:
            self.logger.warn("fail to set hosts from nova")
        triggered_flavor_updates = self.set_flavors()
        if triggered_flavor_updates is not True:
            self.logger.warn("fail to set flavor from nova")

        self.logger.info("ComputeManager: --- done compute_nodes "
                         "status update ---")

        return True

    def set_hosts(self):
        """Return True if hosts set, compute avail resources, checks update."""
        hosts = {}
        logical_groups = {}

        compute = Compute(self.logger)

        status = compute.set_hosts(hosts, logical_groups)
        if status != "success":
            return False

        self._compute_avail_host_resources(hosts)

        self.data_lock.acquire()
        lg_updated = self._check_logical_group_update(logical_groups)
        host_updated = self._check_host_update(hosts)

        if lg_updated is True or host_updated is True:
            self.resource.update_topology(store=False)
        self.data_lock.release()

        return True

    def _compute_avail_host_resources(self, _hosts):
        for hk, host in _hosts.iteritems():
            self.resource.compute_avail_resources(hk, host)

    def _check_logical_group_update(self, _logical_groups):
        updated = False

        for lk in _logical_groups.keys():
            if lk not in self.resource.logical_groups.keys():
                self.resource.logical_groups[lk] = deepcopy(_logical_groups[lk])

                self.resource.logical_groups[lk].last_update = time.time()
                self.logger.warn("ComputeManager: new logical group (" +
                                 lk + ") added")
                updated = True

        for rlk in self.resource.logical_groups.keys():
            rl = self.resource.logical_groups[rlk]
            if rl.group_type != "EX" and rl.group_type != "AFF" and \
                    rl.group_type != "DIV":
                if rlk not in _logical_groups.keys():
                    self.resource.logical_groups[rlk].status = "disabled"

                    self.resource.logical_groups[rlk].last_update = time.time()
                    self.logger.warn("ComputeManager: logical group (" +
                                     rlk + ") removed")
                    updated = True

        for lk in _logical_groups.keys():
            lg = _logical_groups[lk]
            rlg = self.resource.logical_groups[lk]
            if lg.group_type != "EX" and lg.group_type != "AFF" and \
                    lg.group_type != "DIV":
                if self._check_logical_group_metadata_update(lg, rlg) is True:

                    rlg.last_update = time.time()
                    self.logger.warn("ComputeManager: logical group (" +
                                     lk + ") updated")
                    updated = True

        return updated

    def _check_logical_group_metadata_update(self, _lg, _rlg):
        updated = False

        if _lg.status != _rlg.status:
            _rlg.status = _lg.status
            updated = True

        for mdk in _lg.metadata.keys():
            if mdk not in _rlg.metadata.keys():
                _rlg.metadata[mdk] = _lg.metadata[mdk]
                updated = True

        for rmdk in _rlg.metadata.keys():
            if rmdk not in _lg.metadata.keys():
                del _rlg.metadata[rmdk]
                updated = True

        for hk in _lg.vms_per_host.keys():
            if hk not in _rlg.vms_per_host.keys():
                _rlg.vms_per_host[hk] = deepcopy(_lg.vms_per_host[hk])
                updated = True

        for rhk in _rlg.vms_per_host.keys():
            if rhk not in _lg.vms_per_host.keys():
                del _rlg.vms_per_host[rhk]
                updated = True

        return updated

    def _check_host_update(self, _hosts):
        updated = False

        for hk in _hosts.keys():
            if hk not in self.resource.hosts.keys():
                new_host = Host(hk)
                self.resource.hosts[new_host.name] = new_host

                new_host.last_update = time.time()
                self.logger.warn("ComputeManager: new host (" +
                                 new_host.name + ") added")
                updated = True

        for rhk, rhost in self.resource.hosts.iteritems():
            if rhk not in _hosts.keys():
                if "nova" in rhost.tag:
                    rhost.tag.remove("nova")

                    rhost.last_update = time.time()
                    self.logger.warn("ComputeManager: host (" +
                                     rhost.name + ") disabled")
                    updated = True

        for hk in _hosts.keys():
            host = _hosts[hk]
            rhost = self.resource.hosts[hk]
            if self._check_host_config_update(host, rhost) is True:
                rhost.last_update = time.time()
                updated = True

        for hk, h in self.resource.hosts.iteritems():
            if h.clean_memberships() is True:
                h.last_update = time.time()
                self.logger.warn("ComputeManager: host (" + h.name +
                                 ") updated (delete EX/AFF/DIV membership)")
                updated = True

        for hk, host in self.resource.hosts.iteritems():
            if host.last_update >= self.resource.current_timestamp:
                self.resource.update_rack_resource(host)

        return updated

    def _check_host_config_update(self, _host, _rhost):
        topology_updated = False

        if self._check_host_status(_host, _rhost) is True:
            topology_updated = True
        if self._check_host_resources(_host, _rhost) is True:
            topology_updated = True
        if self._check_host_memberships(_host, _rhost) is True:
            topology_updated = True
        if self._check_host_vms(_host, _rhost) is True:
            topology_updated = True

        return topology_updated

    def _check_host_status(self, _host, _rhost):
        topology_updated = False

        if "nova" not in _rhost.tag:
            _rhost.tag.append("nova")
            topology_updated = True
            self.logger.warn("ComputeManager: host (" + _rhost.name +
                             ") updated (tag added)")

        if _host.status != _rhost.status:
            _rhost.status = _host.status
            topology_updated = True
            self.logger.warn("ComputeManager: host (" + _rhost.name +
                             ") updated (status changed)")

        if _host.state != _rhost.state:
            _rhost.state = _host.state
            topology_updated = True
            self.logger.warn("ComputeManager: host (" + _rhost.name +
                             ") updated (state changed)")

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
            self.logger.warn("ComputeManager: host (" + _rhost.name +
                             ") updated (CPU updated)")

        if _host.mem_cap != _rhost.mem_cap or \
           _host.original_mem_cap != _rhost.original_mem_cap or \
           _host.avail_mem_cap != _rhost.avail_mem_cap:
            _rhost.mem_cap = _host.mem_cap
            _rhost.original_mem_cap = _host.original_mem_cap
            _rhost.avail_mem_cap = _host.avail_mem_cap
            topology_updated = True
            self.logger.warn("ComputeManager: host (" + _rhost.name +
                             ") updated (mem updated)")

        if _host.local_disk_cap != _rhost.local_disk_cap or \
           _host.original_local_disk_cap != _rhost.original_local_disk_cap or \
           _host.avail_local_disk_cap != _rhost.avail_local_disk_cap:
            _rhost.local_disk_cap = _host.local_disk_cap
            _rhost.original_local_disk_cap = _host.original_local_disk_cap
            _rhost.avail_local_disk_cap = _host.avail_local_disk_cap
            topology_updated = True
            self.logger.warn("ComputeManager: host (" + _rhost.name +
                             ") updated (local disk space updated)")

        if _host.vCPUs_used != _rhost.vCPUs_used or \
           _host.free_mem_mb != _rhost.free_mem_mb or \
           _host.free_disk_gb != _rhost.free_disk_gb or \
           _host.disk_available_least != _rhost.disk_available_least:
            _rhost.vCPUs_used = _host.vCPUs_used
            _rhost.free_mem_mb = _host.free_mem_mb
            _rhost.free_disk_gb = _host.free_disk_gb
            _rhost.disk_available_least = _host.disk_available_least
            topology_updated = True
            self.logger.warn("ComputeManager: host (" + _rhost.name +
                             ") updated (other resource numbers)")

        return topology_updated

    def _check_host_memberships(self, _host, _rhost):
        topology_updated = False

        for mk in _host.memberships.keys():
            if mk not in _rhost.memberships.keys():
                _rhost.memberships[mk] = self.resource.logical_groups[mk]
                topology_updated = True
                self.logger.warn("ComputeManager: host (" + _rhost.name +
                                 ") updated (new membership)")

        for mk in _rhost.memberships.keys():
            m = _rhost.memberships[mk]
            if m.group_type != "EX" and m.group_type != "AFF" and \
                    m.group_type != "DIV":
                if mk not in _host.memberships.keys():
                    del _rhost.memberships[mk]
                    topology_updated = True
                    self.logger.warn("ComputeManager: host (" + _rhost.name +
                                     ") updated (delete membership)")

        return topology_updated

    def _check_host_vms(self, _host, _rhost):
        topology_updated = False

        # Clean up VMs
        blen = len(_rhost.vm_list)
        _rhost.vm_list = [v for v in _rhost.vm_list if v[2] != "none"]
        alen = len(_rhost.vm_list)
        if alen != blen:
            topology_updated = True
            self.logger.warn("host (" + _rhost.name + ") " + str(blen - alen) + " none vms removed")

        self.resource.clean_none_vms_from_logical_groups(_rhost)

        for vm_id in _host.vm_list:
            if _rhost.exist_vm_by_uuid(vm_id[2]) is False:
                _rhost.vm_list.append(vm_id)
                topology_updated = True
                self.logger.warn("ComputeManager: host (" + _rhost.name +
                                 ") updated (new vm placed)")

        for rvm_id in _rhost.vm_list:
            if _host.exist_vm_by_uuid(rvm_id[2]) is False:
                self.resource.remove_vm_by_uuid_from_logical_groups(_rhost, rvm_id[2])
                topology_updated = True
                self.logger.warn("ComputeManager: host (" + _rhost.name +
                                 ") updated (vm removed)")

        blen = len(_rhost.vm_list)
        _rhost.vm_list = [v for v in _rhost.vm_list if _host.exist_vm_by_uuid(v[2]) is True]
        alen = len(_rhost.vm_list)
        if alen != blen:
            topology_updated = True
            self.logger.warn("host (" + _rhost.name + ") " + str(blen - alen) + " vms removed")

        return topology_updated

    def set_flavors(self):
        """Return True if compute set flavors returns success."""
        flavors = {}

        compute = Compute(self.logger)

        status = compute.set_flavors(flavors)
        if status != "success":
            self.logger.error(status)
            return False

        self.data_lock.acquire()
        if self._check_flavor_update(flavors) is True:
            self.resource.update_topology(store=False)
        self.data_lock.release()

        return True

    def _check_flavor_update(self, _flavors):
        updated = False

        for fk in _flavors.keys():
            if fk not in self.resource.flavors.keys():
                self.resource.flavors[fk] = deepcopy(_flavors[fk])

                self.resource.flavors[fk].last_update = time.time()
                self.logger.warn("ComputeManager: new flavor (" +
                                 fk + ":" + _flavors[fk].flavor_id + ") added")
                updated = True

        for rfk in self.resource.flavors.keys():
            rf = self.resource.flavors[rfk]
            if rfk not in _flavors.keys():
                rf.status = "disabled"

                rf.last_update = time.time()
                self.logger.warn("ComputeManager: flavor (" + rfk + ":" +
                                 rf.flavor_id + ") removed")
                updated = True

        for fk in _flavors.keys():
            f = _flavors[fk]
            rf = self.resource.flavors[fk]

            if self._check_flavor_spec_update(f, rf) is True:
                rf.last_update = time.time()
                self.logger.warn("ComputeManager: flavor (" + fk + ":" +
                                 rf.flavor_id + ") spec updated")
                updated = True

        return updated

    def _check_flavor_spec_update(self, _f, _rf):
        spec_updated = False

        if _f.status != _rf.status:
            _rf.status = _f.status
            spec_updated = True

        if _f.vCPUs != _rf.vCPUs or _f.mem_cap != _rf.mem_cap or \
                _f.disk_cap != _rf.disk_cap:
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
