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

from copy import deepcopy
import threading
import time

from oslo_log import log

# from valet.engine.optimizer.simulator.compute_sim import ComputeSim
from valet.engine.resource_manager.nova_compute import NovaCompute
from valet.engine.resource_manager.resources.host import Host

LOG = log.getLogger(__name__)


class ComputeManager(threading.Thread):
    """Resource Manager to maintain compute host resources."""

    def __init__(self, _t_id, _t_name, _resource, _data_lock, _config):
        threading.Thread.__init__(self)

        self.thread_id = _t_id
        self.thread_name = _t_name
        self.data_lock = _data_lock
        self.end_of_process = False

        self.phandler = None
        self.ahandler = None
        self.resource = _resource

        self.config = _config

        self.update_batch_wait = self.config.update_batch_wait

    def set_handlers(self, _placement_handler, _app_handler):
        """Set handlers."""
        self.phandler = _placement_handler
        self.ahandler = _app_handler

    def run(self):
        """Keep checking for timing for this batch job."""

        LOG.info("start " + self.thread_name + " ......")

        period_end = 0
        if self.config.compute_trigger_freq > 0:
            period_end = time.time() + self.config.compute_trigger_freq

        while self.end_of_process is False:
            time.sleep(60)

            curr_ts = time.time()
            if curr_ts > period_end:
                # Give some time (batch_wait) to sync resource status via message bus
                if (curr_ts - self.resource.current_timestamp) > self.update_batch_wait:
                    self._run()

                    period_end = time.time() + self.config.compute_trigger_freq

        LOG.info("exit " + self.thread_name)

    def _run(self):
        """Run this batch job."""
        if self.set_hosts() is not True:
            LOG.warn("fail to set hosts from nova")

    def set_hosts(self):
        """Check any inconsistency and perform garbage collection if necessary."""

        LOG.info("set compute hosts")

        hosts = {}

        # compute = ComputeSim(self.config)
        compute = NovaCompute(LOG)
        if compute.set_hosts(hosts) != "success":
            return False

        for hk, host in hosts.iteritems():
            self.resource.compute_avail_resources(hk, host)

        self.data_lock.acquire()
        if self._check_host_update(hosts, compute.vm_locations) is True:
            self.resource.update_topology(store=False)
        self.data_lock.release()

        return True

    def _check_host_update(self, _hosts, _vm_locations):
        """Check the inconsistency of hosts."""

        updated = False

        for hk in _hosts.keys():
            if hk not in self.resource.hosts.keys():
                new_host = Host(hk)
                self.resource.hosts[new_host.name] = new_host
                self.resource.update_host_time(new_host.name)
                LOG.info("new host (" + new_host.name + ") added")
                updated = True

        for rhk, rhost in self.resource.hosts.iteritems():
            if rhk not in _hosts.keys():
                if "nova" in rhost.tag:
                    rhost.tag.remove("nova")
                    self.resource.update_host_time(rhk)
                    LOG.info("host (" + rhost.name + ") disabled")
                    updated = True

        for hk in _hosts.keys():
            host = _hosts[hk]
            rhost = self.resource.hosts[hk]
            if self._check_host_config_update(host, rhost) is True:
                self.resource.update_host_time(hk)
                updated = True

        inconsistent_hosts = self._check_placements(_hosts, _vm_locations)
        if inconsistent_hosts is None:
            return False
        elif len(inconsistent_hosts) > 0:
            for hk, h in inconsistent_hosts.iteritems():
                if hk in _hosts.keys() and hk in self.resource.hosts.keys():
                    self.resource.update_host_time(hk)
            updated = True

        return updated

    def _check_host_config_update(self, _host, _rhost):
        """Check host configuration consistency."""

        config_updated = False

        if self._check_host_status(_host, _rhost) is True:
            config_updated = True

        if self._check_host_resources(_host, _rhost) is True:
            config_updated = True

        return config_updated

    def _check_host_status(self, _host, _rhost):
        """Check host status consistency."""

        status_updated = False

        if "nova" not in _rhost.tag:
            _rhost.tag.append("nova")
            LOG.info("host (" + _rhost.name + ") updated (tag added)")
            status_updated = True

        if _host.status != _rhost.status:
            _rhost.status = _host.status
            LOG.info("host (" + _rhost.name + ") updated (status changed)")
            status_updated = True

        if _host.state != _rhost.state:
            _rhost.state = _host.state
            LOG.info("host (" + _rhost.name + ") updated (state changed)")
            status_updated = True

        return status_updated

    def _check_host_resources(self, _host, _rhost):
        """Check the resource amount consistency."""

        resource_updated = False

        if _host.vCPUs != _rhost.vCPUs or \
           _host.original_vCPUs != _rhost.original_vCPUs or \
           _host.avail_vCPUs != _rhost.avail_vCPUs:
            _rhost.vCPUs = _host.vCPUs
            _rhost.original_vCPUs = _host.original_vCPUs
            _rhost.avail_vCPUs = _host.avail_vCPUs
            LOG.info("host (" + _rhost.name + ") updated (CPU updated)")
            resource_updated = True

        if _host.mem_cap != _rhost.mem_cap or \
           _host.original_mem_cap != _rhost.original_mem_cap or \
           _host.avail_mem_cap != _rhost.avail_mem_cap:
            _rhost.mem_cap = _host.mem_cap
            _rhost.original_mem_cap = _host.original_mem_cap
            _rhost.avail_mem_cap = _host.avail_mem_cap
            LOG.info("host (" + _rhost.name + ") updated (mem updated)")
            resource_updated = True

        if _host.local_disk_cap != _rhost.local_disk_cap or \
           _host.original_local_disk_cap != _rhost.original_local_disk_cap or \
           _host.avail_local_disk_cap != _rhost.avail_local_disk_cap:
            _rhost.local_disk_cap = _host.local_disk_cap
            _rhost.original_local_disk_cap = _host.original_local_disk_cap
            _rhost.avail_local_disk_cap = _host.avail_local_disk_cap
            LOG.info("host (" + _rhost.name + ") updated (local disk space updated)")
            resource_updated = True

        if _host.vCPUs_used != _rhost.vCPUs_used or \
           _host.free_mem_mb != _rhost.free_mem_mb or \
           _host.free_disk_gb != _rhost.free_disk_gb or \
           _host.disk_available_least != _rhost.disk_available_least:
            _rhost.vCPUs_used = _host.vCPUs_used
            _rhost.free_mem_mb = _host.free_mem_mb
            _rhost.free_disk_gb = _host.free_disk_gb
            _rhost.disk_available_least = _host.disk_available_least
            LOG.info("host (" + _rhost.name + ") updated (other resource numbers)")
            resource_updated = True

        return resource_updated

    def _check_placements(self, _hosts, _vm_locations):
        """Check the consistency of vm placements with nova."""

        inconsistent_hosts = {}
        curr_time = time.time()

        for vk, hk in _vm_locations.iteritems():
            placement = self.phandler.get_placement(vk)
            if placement is None:
                return None

            elif placement.uuid == "none":
                LOG.info("unknown vm found in nova")

                vm_info = _hosts[hk].get_vm_info(uuid=vk)

                p = self.phandler.insert_placement(vk, vm_info["stack_id"], hk, vm_info["orch_id"], "created")
                if p is None:
                    return None
                self.phandler.set_unverified(p.uuid)

                LOG.info("host (" + hk + ") updated (new unknown vm added)")

                rhost = self.resource.hosts[hk]
                if rhost.exist_vm(uuid=vk):
                    rhost.remove_vm(uuid=vk)

                rhost.vm_list.append(vm_info)
                inconsistent_hosts[hk] = rhost

                # FIXME(gjung): add to corresponding groups with verification?
                #     currently, do this at bootstrap time and requested.

            else:
                if hk != placement.host:
                    LOG.warn("PANIC: placed in different host")

                    vm_info = _hosts[hk].get_vm_info(uuid=vk)
                    vm_info["stack_id"] = placement.stack_id
                    vm_info["orch_id"] = placement.orch_id

                    rhost = self.resource.hosts[hk]
                    if rhost.exist_vm(uuid=vk):
                        rhost.remove_vm(uuid=vk)

                    rhost.vm_list.append(vm_info)
                    inconsistent_hosts[hk] = rhost

                    LOG.warn("host (" + rhost.name + ") updated (vm added)")

                    # FIXME(gjung): add to corresponding groups with verification?

                    if placement.host in self.resource.hosts.keys():
                        old_rhost = self.resource.hosts[placement.host]
                        if old_rhost.remove_vm(uuid=vk) is True:
                            LOG.warn("host (" + old_rhost.name + ") updated (vm removed)")

                            inconsistent_hosts[placement.host] = old_rhost

                        self.resource.remove_vm_from_groups_of_host(old_rhost, uuid=vk)

                    placement.host = hk
                    placement.status = "none"
                    placement.timestamp = curr_time
                    if not self.phandler.store_placement(vk, placement):
                        return None

                    if placement.stack_id is not None or placement.stack_id != "none":
                        (vid, hk) = self.ahandler.update_stack(placement.stack_id, uuid=vk, host=hk)
                        if vid is None:
                            return None

                new_state = None
                if placement.state is None or placement.state == "none":
                    new_state = "created"

                if placement.state not in ("created", "rebuilt", "migrated"):
                    LOG.warn("vm is incomplete state = " + placement.state)

                    if placement.state == "planned" or placement.state == "building":
                        new_state = "created"
                    elif placement.state == "rebuilding" or placement.state == "rebuild":
                        new_state = "rebuilt"
                    elif placement.state == "migrating" or placement.state == "migrate":
                        new_state = "migrated"

                if new_state is not None:
                    placement.state = new_state
                    placement.timestamp = curr_time
                    if not self.phandler.store_placement(vk, placement):
                        return None

        for rk, rhost in self.resource.hosts.iteritems():
            deletion_list = []

            for vm_info in rhost.vm_list:
                if vm_info["uuid"] is None or vm_info["uuid"] == "none":
                    LOG.warn("host (" + rhost.name + ") pending vm removed")

                    deletion_list.append(vm_info)

                    if vm_info["stack_id"] is not None and vm_info["stack_id"] != "none":
                        if not self.ahandler.delete_from_stack(vm_info["stack_id"], orch_id=vm_info["orch_id"]):
                            return None

                else:
                    placement = self.phandler.get_placement(vm_info["uuid"])
                    if placement is None:
                        return None

                    if vm_info["uuid"] not in _vm_locations.keys():
                        LOG.warn("vm is mising with state = " + placement.state)

                        deletion_list.append(vm_info)

                        if placement.stack_id is not None and placement.stack_id != "none":
                            if not self.ahandler.delete_from_stack(placement.stack_id, uuid=vm_info["uuid"]):
                                return None

                        if not self.phandler.delete_placement(vm_info["uuid"]):
                            return None

                    elif _vm_locations[vm_info["uuid"]] != rk:
                        LOG.warn("placed in different host")

                        if rhost.remove_vm(uuid=vm_info["uuid"]) is True:
                            LOG.warn("host (" + rk + ") updated (vm removed)")

                            inconsistent_hosts[rk] = rhost

                            self.resource.remove_vm_from_groups_of_host(rhost, uuid=vm_info["uuid"])

                            # FIXME(gjung): placement.status?

            if len(deletion_list) > 0:
                LOG.warn("host (" + rhost.name + ") updated (vms removed)")

                inconsistent_hosts[rk] = rhost

                for vm_info in deletion_list:
                    if vm_info["orch_id"] is not None and vm_info["orch_id"] != "none":
                        rhost.remove_vm(orch_id=vm_info["orch_id"])
                        self.resource.remove_vm_from_groups(rhost, orch_id=vm_info["orch_id"])
                    else:
                        if not rhost.remove_vm(uuid=vm_info["uuid"]):
                            LOG.warn("fail to remove vm from host")

                        self.resource.remove_vm_from_groups(rhost, uuid=vm_info["uuid"])

        return inconsistent_hosts
