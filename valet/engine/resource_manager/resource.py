#!/bin/python

# Modified: Sep. 27, 2016

import json
import sys
import time
import traceback

from valet.engine.optimizer.app_manager.app_topology_base import LEVELS
from valet.engine.optimizer.util import util as util
from valet.engine.resource_manager.resource_base import Datacenter, HostGroup, Host, LogicalGroup
from valet.engine.resource_manager.resource_base import Flavor, Switch, Link


class Resource(object):

    def __init__(self, _db, _config, _logger):
        self.db = _db

        self.config = _config
        self.logger = _logger

        ''' resource data '''
        self.datacenter = Datacenter(self.config.datacenter_name)
        self.host_groups = {}
        self.hosts = {}
        self.switches = {}
        self.storage_hosts = {}

        ''' metadata '''
        self.logical_groups = {}
        self.flavors = {}

        self.current_timestamp = 0
        self.last_log_index = 0

        ''' resource status aggregation '''
        self.CPU_avail = 0
        self.mem_avail = 0
        self.local_disk_avail = 0
        self.disk_avail = 0
        self.nw_bandwidth_avail = 0

    def bootstrap_from_db(self, _resource_status):
        try:
            logical_groups = _resource_status.get("logical_groups")
            if logical_groups:
                for lgk, lg in logical_groups.iteritems():
                    logical_group = LogicalGroup(lgk)
                    logical_group.group_type = lg.get("group_type")
                    logical_group.status = lg.get("status")
                    logical_group.metadata = lg.get("metadata")
                    logical_group.vm_list = lg.get("vm_list")
                    logical_group.volume_list = lg.get("volume_list", [])
                    logical_group.vms_per_host = lg.get("vms_per_host")

                    self.logical_groups[lgk] = logical_group

            if len(self.logical_groups) > 0:
                self.logger.debug("Resource.bootstrap_from_db: logical_groups loaded")
            else:
                self.logger.warn("Resource.bootstrap_from_db: no logical_groups")

            flavors = _resource_status.get("flavors")
            if flavors:
                for fk, f in flavors.iteritems():
                    flavor = Flavor(fk)
                    flavor.flavor_id = f.get("flavor_id")
                    flavor.status = f.get("status")
                    flavor.vCPUs = f.get("vCPUs")
                    flavor.mem_cap = f.get("mem")
                    flavor.disk_cap = f.get("disk")
                    flavor.extra_specs = f.get("extra_specs")

                    self.flavors[fk] = flavor

            if len(self.flavors) > 0:
                self.logger.debug("Resource.bootstrap_from_db: flavors loaded")
            else:
                self.logger.error("Resource.bootstrap_from_db: fail loading flavors")
                # return False

            switches = _resource_status.get("switches")
            if switches:
                for sk, s in switches.iteritems():
                    switch = Switch(sk)
                    switch.switch_type = s.get("switch_type")
                    switch.status = s.get("status")

                    self.switches[sk] = switch

            if len(self.switches) > 0:
                self.logger.debug("Resource.bootstrap_from_db: switches loaded")
                for sk, s in switches.iteritems():
                    switch = self.switches[sk]

                    up_links = {}
                    uls = s.get("up_links")
                    for ulk, ul in uls.iteritems():
                        ulink = Link(ulk)
                        ulink.resource = self.switches[ul.get("resource")]
                        ulink.nw_bandwidth = ul.get("bandwidth")
                        ulink.avail_nw_bandwidth = ul.get("avail_bandwidth")

                        up_links[ulk] = ulink

                    switch.up_links = up_links

                    peer_links = {}
                    pls = s.get("peer_links")
                    for plk, pl in pls.iteritems():
                        plink = Link(plk)
                        plink.resource = self.switches[pl.get("resource")]
                        plink.nw_bandwidth = pl.get("bandwidth")
                        plink.avail_nw_bandwidth = pl.get("avail_bandwidth")

                        peer_links[plk] = plink

                    switch.peer_links = peer_links

                self.logger.debug("Resource.bootstrap_from_db: switch links loaded")
            else:
                self.logger.error("Resource.bootstrap_from_db: fail loading switches")
                # return False

            # storage_hosts
            hosts = _resource_status.get("hosts")
            if hosts:
                for hk, h in hosts.iteritems():
                    host = Host(hk)
                    host.tag = h.get("tag")
                    host.status = h.get("status")
                    host.state = h.get("state")
                    host.vCPUs = h.get("vCPUs")
                    host.original_vCPUs = h.get("original_vCPUs")
                    host.avail_vCPUs = h.get("avail_vCPUs")
                    host.mem_cap = h.get("mem")
                    host.original_mem_cap = h.get("original_mem")
                    host.avail_mem_cap = h.get("avail_mem")
                    host.local_disk_cap = h.get("local_disk")
                    host.original_local_disk_cap = h.get("original_local_disk")
                    host.avail_local_disk_cap = h.get("avail_local_disk")
                    host.vCPUs_used = h.get("vCPUs_used")
                    host.free_mem_mb = h.get("free_mem_mb")
                    host.free_disk_gb = h.get("free_disk_gb")
                    host.disk_available_least = h.get("disk_available_least")
                    host.vm_list = h.get("vm_list")
                    host.volume_list = h.get("volume_list", [])

                    for lgk in h["membership_list"]:
                        host.memberships[lgk] = self.logical_groups[lgk]

                    for sk in h.get("switch_list", []):
                        host.switches[sk] = self.switches[sk]

                    # host.storages

                    self.hosts[hk] = host

                if len(self.hosts) > 0:
                    self.logger.debug("Resource.bootstrap_from_db: hosts loaded")
                else:
                    self.logger.error("Resource.bootstrap_from_db: fail loading hosts")
                    # return False

            host_groups = _resource_status.get("host_groups")
            if host_groups:
                for hgk, hg in host_groups.iteritems():
                    host_group = HostGroup(hgk)
                    host_group.host_type = hg.get("host_type")
                    host_group.status = hg.get("status")
                    host_group.vCPUs = hg.get("vCPUs")
                    host_group.original_vCPUs = hg.get("original_vCPUs")
                    host_group.avail_vCPUs = hg.get("avail_vCPUs")
                    host_group.mem_cap = hg.get("mem")
                    host_group.original_mem_cap = hg.get("original_mem")
                    host_group.avail_mem_cap = hg.get("avail_mem")
                    host_group.local_disk_cap = hg.get("local_disk")
                    host_group.original_local_disk_cap = hg.get("original_local_disk")
                    host_group.avail_local_disk_cap = hg.get("avail_local_disk")
                    host_group.vm_list = hg.get("vm_list")
                    host_group.volume_list = hg.get("volume_list", [])

                    for lgk in hg.get("membership_list"):
                        host_group.memberships[lgk] = self.logical_groups[lgk]

                    for sk in hg.get("switch_list", []):
                        host_group.switches[sk] = self.switches[sk]

                    # host.storages

                    self.host_groups[hgk] = host_group

                if len(self.host_groups) > 0:
                    self.logger.debug("Resource.bootstrap_from_db: host_groups loaded")
                else:
                    self.logger.error("Resource.bootstrap_from_db: fail loading host_groups")
                    # return False

            dc = _resource_status.get("datacenter")
            if dc:
                self.datacenter.name = dc.get("name")
                self.datacenter.region_code_list = dc.get("region_code_list")
                self.datacenter.status = dc.get("status")
                self.datacenter.vCPUs = dc.get("vCPUs")
                self.datacenter.original_vCPUs = dc.get("original_vCPUs")
                self.datacenter.avail_vCPUs = dc.get("avail_vCPUs")
                self.datacenter.mem_cap = dc.get("mem")
                self.datacenter.original_mem_cap = dc.get("original_mem")
                self.datacenter.avail_mem_cap = dc.get("avail_mem")
                self.datacenter.local_disk_cap = dc.get("local_disk")
                self.datacenter.original_local_disk_cap = dc.get("original_local_disk")
                self.datacenter.avail_local_disk_cap = dc.get("avail_local_disk")
                self.datacenter.vm_list = dc.get("vm_list")
                self.datacenter.volume_list = dc.get("volume_list", [])

                for lgk in dc.get("membership_list"):
                    self.datacenter.memberships[lgk] = self.logical_groups[lgk]

                for sk in dc.get("switch_list", []):
                    self.datacenter.root_switches[sk] = self.switches[sk]

                # host.storages

                for ck in dc.get("children"):
                    if ck in self.host_groups.keys():
                        self.datacenter.resources[ck] = self.host_groups[ck]
                    elif ck in self.hosts.keys():
                        self.datacenter.resources[ck] = self.hosts[ck]

                if len(self.datacenter.resources) > 0:
                    self.logger.debug("Resource.bootstrap_from_db: datacenter loaded")
                else:
                    self.logger.error("Resource.bootstrap_from_db: fail loading datacenter")
                    # return False

            hgs = _resource_status.get("host_groups")
            if hgs:
                for hgk, hg in hgs.iteritems():
                    host_group = self.host_groups[hgk]

                    pk = hg.get("parent")
                    if pk == self.datacenter.name:
                        host_group.parent_resource = self.datacenter
                    elif pk in self.host_groups.keys():
                        host_group.parent_resource = self.host_groups[pk]

                    for ck in hg.get("children"):
                        if ck in self.hosts.keys():
                            host_group.child_resources[ck] = self.hosts[ck]
                        elif ck in self.host_groups.keys():
                            host_group.child_resources[ck] = self.host_groups[ck]

                self.logger.debug("Resource.bootstrap_from_db: host_groups'layout loaded")

            hs = _resource_status.get("hosts")
            if hs:
                for hk, h in hs.iteritems():
                    host = self.hosts[hk]

                    pk = h.get("parent")
                    if pk == self.datacenter.name:
                        host.host_group = self.datacenter
                    elif pk in self.host_groups.keys():
                        host.host_group = self.host_groups[pk]

                self.logger.debug("Resource.bootstrap_from_db: hosts'layout loaded")

            self._update_compute_avail()
            self._update_storage_avail()
            self._update_nw_bandwidth_avail()

            self.logger.debug("Resource.bootstrap_from_db: resource availability updated")

        except Exception:
            self.logger.error("Resource.bootstrap_from_db - FAILED:" + traceback.format_exc())

        return True

    def update_topology(self, store=True):
        self._update_topology()

        self._update_compute_avail()
        self._update_storage_avail()
        self._update_nw_bandwidth_avail()

        if store is False:
            return True

        ct = self._store_topology_updates()
        if ct is None:
            return False
        else:
            self.current_timestamp = ct
            return True

    def _update_topology(self):
        for level in LEVELS:
            for _, host_group in self.host_groups.iteritems():
                if host_group.host_type == level and host_group.check_availability() is True:
                    if host_group.last_update > self.current_timestamp:
                        self._update_host_group_topology(host_group)

        if self.datacenter.last_update > self.current_timestamp:
            self._update_datacenter_topology()

    def _update_host_group_topology(self, _host_group):
        _host_group.init_resources()
        del _host_group.vm_list[:]
        del _host_group.volume_list[:]
        _host_group.storages.clear()

        for _, host in _host_group.child_resources.iteritems():
            if host.check_availability() is True:
                _host_group.vCPUs += host.vCPUs
                _host_group.original_vCPUs += host.original_vCPUs
                _host_group.avail_vCPUs += host.avail_vCPUs
                _host_group.mem_cap += host.mem_cap
                _host_group.original_mem_cap += host.original_mem_cap
                _host_group.avail_mem_cap += host.avail_mem_cap
                _host_group.local_disk_cap += host.local_disk_cap
                _host_group.original_local_disk_cap += host.original_local_disk_cap
                _host_group.avail_local_disk_cap += host.avail_local_disk_cap

                for shk, storage_host in host.storages.iteritems():
                    if storage_host.status == "enabled":
                        _host_group.storages[shk] = storage_host

                for vm_id in host.vm_list:
                    _host_group.vm_list.append(vm_id)

                for vol_name in host.volume_list:
                    _host_group.volume_list.append(vol_name)

        _host_group.init_memberships()

        for _, host in _host_group.child_resources.iteritems():
            if host.check_availability() is True:
                for mk in host.memberships.keys():
                    _host_group.memberships[mk] = host.memberships[mk]

    def _update_datacenter_topology(self):
        self.datacenter.init_resources()
        del self.datacenter.vm_list[:]
        del self.datacenter.volume_list[:]
        self.datacenter.storages.clear()
        self.datacenter.memberships.clear()

        for _, resource in self.datacenter.resources.iteritems():
            if resource.check_availability() is True:
                self.datacenter.vCPUs += resource.vCPUs
                self.datacenter.original_vCPUs += resource.original_vCPUs
                self.datacenter.avail_vCPUs += resource.avail_vCPUs
                self.datacenter.mem_cap += resource.mem_cap
                self.datacenter.original_mem_cap += resource.original_mem_cap
                self.datacenter.avail_mem_cap += resource.avail_mem_cap
                self.datacenter.local_disk_cap += resource.local_disk_cap
                self.datacenter.original_local_disk_cap += resource.original_local_disk_cap
                self.datacenter.avail_local_disk_cap += resource.avail_local_disk_cap

                for shk, storage_host in resource.storages.iteritems():
                    if storage_host.status == "enabled":
                        self.datacenter.storages[shk] = storage_host

                for vm_name in resource.vm_list:
                    self.datacenter.vm_list.append(vm_name)

                for vol_name in resource.volume_list:
                    self.datacenter.volume_list.append(vol_name)

                for mk in resource.memberships.keys():
                    self.datacenter.memberships[mk] = resource.memberships[mk]

    def _update_compute_avail(self):
        self.CPU_avail = self.datacenter.avail_vCPUs
        self.mem_avail = self.datacenter.avail_mem_cap
        self.local_disk_avail = self.datacenter.avail_local_disk_cap

    def _update_storage_avail(self):
        self.disk_avail = 0

        for _, storage_host in self.storage_hosts.iteritems():
            if storage_host.status == "enabled":
                self.disk_avail += storage_host.avail_disk_cap

    def _update_nw_bandwidth_avail(self):
        self.nw_bandwidth_avail = 0

        level = "leaf"
        for _, s in self.switches.iteritems():
            if s.status == "enabled":
                if level == "leaf":
                    if s.switch_type == "ToR" or s.switch_type == "spine":
                        level = s.switch_type
                elif level == "ToR":
                    if s.switch_type == "spine":
                        level = s.switch_type

        if level == "leaf":
            self.nw_bandwidth_avail = sys.maxint
        elif level == "ToR":
            for _, h in self.hosts.iteritems():
                if h.status == "enabled" and h.state == "up" and \
                   ("nova" in h.tag) and ("infra" in h.tag):
                    avail_nw_bandwidth_list = [sys.maxint]
                    for sk, s in h.switches.iteritems():
                        if s.status == "enabled":
                            for ulk, ul in s.up_links.iteritems():
                                avail_nw_bandwidth_list.append(ul.avail_nw_bandwidth)
                    self.nw_bandwidth_avail += min(avail_nw_bandwidth_list)
        elif level == "spine":
            for _, hg in self.host_groups.iteritems():
                if hg.host_type == "rack" and hg.status == "enabled":
                    avail_nw_bandwidth_list = [sys.maxint]
                    for _, s in hg.switches.iteritems():
                        if s.status == "enabled":
                            for _, ul in s.up_links.iteritems():
                                avail_nw_bandwidth_list.append(ul.avail_nw_bandwidth)
                            # NOTE: peer links?
                    self.nw_bandwidth_avail += min(avail_nw_bandwidth_list)

    def _store_topology_updates(self):
        last_update_time = self.current_timestamp

        flavor_updates = {}
        logical_group_updates = {}
        storage_updates = {}
        switch_updates = {}
        host_updates = {}
        host_group_updates = {}
        datacenter_update = None

        for fk, flavor in self.flavors.iteritems():
            if flavor.last_update > self.current_timestamp:
                flavor_updates[fk] = flavor.get_json_info()

                last_update_time = flavor.last_update

        for lgk, lg in self.logical_groups.iteritems():
            if lg.last_update > self.current_timestamp:
                logical_group_updates[lgk] = lg.get_json_info()

                last_update_time = lg.last_update

        for shk, storage_host in self.storage_hosts.iteritems():
            if storage_host.last_update > self.current_timestamp or \
               storage_host.last_cap_update > self.current_timestamp:
                storage_updates[shk] = storage_host.get_json_info()

                if storage_host.last_update > self.current_time_stamp:
                    last_update_time = storage_host.last_update
                if storage_host.last_cap_update > self.current_timestamp:
                    last_update_time = storage_host.last_cap_update

        for sk, s in self.switches.iteritems():
            if s.last_update > self.current_timestamp:
                switch_updates[sk] = s.get_json_info()

                last_update_time = s.last_update

        for hk, host in self.hosts.iteritems():
            if host.last_update > self.current_timestamp or host.last_link_update > self.current_timestamp:
                host_updates[hk] = host.get_json_info()

                if host.last_update > self.current_timestamp:
                    last_update_time = host.last_update
                if host.last_link_update > self.current_timestamp:
                    last_update_time = host.last_link_update

        for hgk, host_group in self.host_groups.iteritems():
            if host_group.last_update > self.current_timestamp or \
               host_group.last_link_update > self.current_timestamp:
                host_group_updates[hgk] = host_group.get_json_info()

                if host_group.last_update > self.current_timestamp:
                    last_update_time = host_group.last_update
                if host_group.last_link_update > self.current_timestamp:
                    last_update_time = host_group.last_link_update

        if self.datacenter.last_update > self.current_timestamp or \
           self.datacenter.last_link_update > self.current_timestamp:
            datacenter_update = self.datacenter.get_json_info()

            if self.datacenter.last_update > self.current_timestamp:
                last_update_time = self.datacenter.last_update
            if self.datacenter.last_link_update > self.current_timestamp:
                last_update_time = self.datacenter.last_link_update

        (resource_logfile, last_index, mode) = util.get_last_logfile(self.config.resource_log_loc,
                                                                     self.config.max_log_size,
                                                                     self.config.max_num_of_logs,
                                                                     self.datacenter.name,
                                                                     self.last_log_index)
        self.last_log_index = last_index

        logging = open(self.config.resource_log_loc + resource_logfile, mode)

        json_logging = {}
        json_logging['timestamp'] = last_update_time

        if len(flavor_updates) > 0:
            json_logging['flavors'] = flavor_updates
        if len(logical_group_updates) > 0:
            json_logging['logical_groups'] = logical_group_updates
        if len(storage_updates) > 0:
            json_logging['storages'] = storage_updates
        if len(switch_updates) > 0:
            json_logging['switches'] = switch_updates
        if len(host_updates) > 0:
            json_logging['hosts'] = host_updates
        if len(host_group_updates) > 0:
            json_logging['host_groups'] = host_group_updates
        if datacenter_update is not None:
            json_logging['datacenter'] = datacenter_update

        logged_data = json.dumps(json_logging)

        logging.write(logged_data)
        logging.write("\n")

        logging.close()

        self.logger.info("Resource._store_topology_updates: log resource status in " + resource_logfile)

        if self.db is not None:
            if self.db.update_resource_status(self.datacenter.name, json_logging) is False:
                return None
            if self.db.update_resource_log_index(self.datacenter.name, self.last_log_index) is False:
                return None

        return last_update_time

    def update_rack_resource(self, _host):
        rack = _host.host_group

        if rack is not None:
            rack.last_update = time.time()

            if isinstance(rack, HostGroup):
                self.update_cluster_resource(rack)

    def update_cluster_resource(self, _rack):
        cluster = _rack.parent_resource

        if cluster is not None:
            cluster.last_update = time.time()

            if isinstance(cluster, HostGroup):
                self.datacenter.last_update = time.time()

    def get_uuid(self, _h_uuid, _host_name):
        host = self.hosts[_host_name]

        return host.get_uuid(_h_uuid)

    def add_vm_to_host(self, _host_name, _vm_id, _vcpus, _mem, _ldisk):
        host = self.hosts[_host_name]

        host.vm_list.append(_vm_id)

        host.avail_vCPUs -= _vcpus
        host.avail_mem_cap -= _mem
        host.avail_local_disk_cap -= _ldisk

        host.vCPUs_used += _vcpus
        host.free_mem_mb -= _mem
        host.free_disk_gb -= _ldisk
        host.disk_available_least -= _ldisk

    def remove_vm_by_h_uuid_from_host(self, _host_name, _h_uuid, _vcpus, _mem, _ldisk):
        host = self.hosts[_host_name]

        host.remove_vm_by_h_uuid(_h_uuid)

        host.avail_vCPUs += _vcpus
        host.avail_mem_cap += _mem
        host.avail_local_disk_cap += _ldisk

        host.vCPUs_used -= _vcpus
        host.free_mem_mb += _mem
        host.free_disk_gb += _ldisk
        host.disk_available_least += _ldisk

    def remove_vm_by_uuid_from_host(self, _host_name, _uuid, _vcpus, _mem, _ldisk):
        host = self.hosts[_host_name]

        host.remove_vm_by_uuid(_uuid)

        host.avail_vCPUs += _vcpus
        host.avail_mem_cap += _mem
        host.avail_local_disk_cap += _ldisk

        host.vCPUs_used -= _vcpus
        host.free_mem_mb += _mem
        host.free_disk_gb += _ldisk
        host.disk_available_least += _ldisk

    def add_vol_to_host(self, _host_name, _storage_name, _v_id, _disk):
        host = self.hosts[_host_name]

        host.volume_list.append(_v_id)

        storage_host = self.storage_hosts[_storage_name]
        storage_host.volume_list.append(_v_id)

        storage_host.avail_disk_cap -= _disk

    # NOTE: Assume the up-link of spine switch is not used except out-going from datacenter
    # NOTE: What about peer-switches?
    def deduct_bandwidth(self, _host_name, _placement_level, _bandwidth):
        host = self.hosts[_host_name]

        if _placement_level == "host":
            self._deduct_host_bandwidth(host, _bandwidth)

        elif _placement_level == "rack":
            self._deduct_host_bandwidth(host, _bandwidth)

            rack = host.host_group
            if not isinstance(rack, Datacenter):
                self._deduct_host_bandwidth(rack, _bandwidth)

        elif _placement_level == "cluster":
            self._deduct_host_bandwidth(host, _bandwidth)

            rack = host.host_group
            self._deduct_host_bandwidth(rack, _bandwidth)

            cluster = rack.parent_resource
            for _, s in cluster.switches.iteritems():
                if s.switch_type == "spine":
                    for _, ul in s.up_links.iteritems():
                        ul.avail_nw_bandwidth -= _bandwidth

                    s.last_update = time.time()

    def _deduct_host_bandwidth(self, _host, _bandwidth):
        for _, hs in _host.switches.iteritems():
            for _, ul in hs.up_links.iteritems():
                ul.avail_nw_bandwidth -= _bandwidth

            hs.last_update = time.time()

    def update_host_resources(self, _hn, _st, _vcpus, _vcpus_used, _mem, _fmem, _ldisk, _fldisk, _avail_least):
        updated = False

        host = self.hosts[_hn]

        if host.status != _st:
            host.status = _st
            self.logger.debug("Resource.update_host_resources: host status changed")
            updated = True

        if host.original_vCPUs != _vcpus or \
           host.vCPUs_used != _vcpus_used:
            self.logger.debug("Resource.update_host_resources: host cpu changed")
            host.original_vCPUs = _vcpus
            host.vCPUs_used = _vcpus_used
            updated = True

        if host.free_mem_mb != _fmem or \
           host.original_mem_cap != _mem:
            self.logger.debug("Resource.update_host_resources: host mem changed")
            host.free_mem_mb = _fmem
            host.original_mem_cap = _mem
            updated = True

        if host.free_disk_gb != _fldisk or \
           host.original_local_disk_cap != _ldisk or \
           host.disk_available_least != _avail_least:
            self.logger.debug("Resource.update_host_resources: host disk changed")
            host.free_disk_gb = _fldisk
            host.original_local_disk_cap = _ldisk
            host.disk_available_least = _avail_least
            updated = True

        if updated is True:
            self.compute_avail_resources(_hn, host)

        return updated

    def update_host_time(self, _host_name):
        host = self.hosts[_host_name]

        host.last_update = time.time()
        self.update_rack_resource(host)

    def update_storage_time(self, _storage_name):
        storage_host = self.storage_hosts[_storage_name]

        storage_host.last_cap_update = time.time()

    def add_logical_group(self, _host_name, _lg_name, _lg_type):
        host = None
        if _host_name in self.hosts.keys():
            host = self.hosts[_host_name]
        else:
            host = self.host_groups[_host_name]

        if host is not None:
            if _lg_name not in self.logical_groups.keys():
                logical_group = LogicalGroup(_lg_name)
                logical_group.group_type = _lg_type
                logical_group.last_update = time.time()
                self.logical_groups[_lg_name] = logical_group

            if _lg_name not in host.memberships.keys():
                host.memberships[_lg_name] = self.logical_groups[_lg_name]

                if isinstance(host, HostGroup):
                    host.last_update = time.time()

                    self.update_cluster_resource(host)

    def add_vm_to_logical_groups(self, _host, _vm_id, _logical_groups_of_vm):
        for lgk in _host.memberships.keys():
            if lgk in _logical_groups_of_vm:
                lg = self.logical_groups[lgk]

                if isinstance(_host, Host):
                    if lg.add_vm_by_h_uuid(_vm_id, _host.name) is True:
                        lg.last_update = time.time()
                elif isinstance(_host, HostGroup):
                    if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                        if lgk.split(":")[0] == _host.host_type:
                            if lg.add_vm_by_h_uuid(_vm_id, _host.name) is True:
                                lg.last_update = time.time()

        if isinstance(_host, Host) and _host.host_group is not None:
            self.add_vm_to_logical_groups(_host.host_group, _vm_id, _logical_groups_of_vm)
        elif isinstance(_host, HostGroup) and _host.parent_resource is not None:
            self.add_vm_to_logical_groups(_host.parent_resource, _vm_id, _logical_groups_of_vm)

    def remove_vm_by_h_uuid_from_logical_groups(self, _host, _h_uuid):
        for lgk in _host.memberships.keys():
            if lgk not in self.logical_groups.keys():
                continue
            lg = self.logical_groups[lgk]

            if isinstance(_host, Host):
                if lg.remove_vm_by_h_uuid(_h_uuid, _host.name) is True:
                    lg.last_update = time.time()

                if _host.remove_membership(lg) is True:
                    _host.last_update = time.time()

            elif isinstance(_host, HostGroup):
                if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                    if lgk.split(":")[0] == _host.host_type:
                        if lg.remove_vm_by_h_uuid(_h_uuid, _host.name) is True:
                            lg.last_update = time.time()

                        if _host.remove_membership(lg) is True:
                            _host.last_update = time.time()

            if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                if len(lg.vm_list) == 0:
                    del self.logical_groups[lgk]

        if isinstance(_host, Host) and _host.host_group is not None:
            self.remove_vm_by_h_uuid_from_logical_groups(_host.host_group, _h_uuid)
        elif isinstance(_host, HostGroup) and _host.parent_resource is not None:
            self.remove_vm_by_h_uuid_from_logical_groups(_host.parent_resource, _h_uuid)

    def remove_vm_by_uuid_from_logical_groups(self, _host, _uuid):
        for lgk in _host.memberships.keys():
            if lgk not in self.logical_groups.keys():
                continue
            lg = self.logical_groups[lgk]

            if isinstance(_host, Host):
                if lg.remove_vm_by_uuid(_uuid, _host.name) is True:
                    lg.last_update = time.time()

                if _host.remove_membership(lg) is True:
                    _host.last_update = time.time()

            elif isinstance(_host, HostGroup):
                if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                    if lgk.split(":")[0] == _host.host_type:
                        if lg.remove_vm_by_uuid(_uuid, _host.name) is True:
                            lg.last_update = time.time()

                        if _host.remove_membership(lg) is True:
                            _host.last_update = time.time()

            if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                if len(lg.vm_list) == 0:
                    del self.logical_groups[lgk]

        if isinstance(_host, Host) and _host.host_group is not None:
            self.remove_vm_by_uuid_from_logical_groups(_host.host_group, _uuid)
        elif isinstance(_host, HostGroup) and _host.parent_resource is not None:
            self.remove_vm_by_uuid_from_logical_groups(_host.parent_resource, _uuid)

    def clean_none_vms_from_logical_groups(self, _host):
        for lgk in _host.memberships.keys():
            if lgk not in self.logical_groups.keys():
                continue
            lg = self.logical_groups[lgk]

            if isinstance(_host, Host):
                if lg.clean_none_vms(_host.name) is True:
                    lg.last_update = time.time()

                if _host.remove_membership(lg) is True:
                    _host.last_update = time.time()

            elif isinstance(_host, HostGroup):
                if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                    if lgk.split(":")[0] == _host.host_type:
                        if lg.clean_none_vms(_host.name) is True:
                            lg.last_update = time.time()

                        if _host.remove_membership(lg) is True:
                            _host.last_update = time.time()

            if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                if len(lg.vm_list) == 0:
                    del self.logical_groups[lgk]

        if isinstance(_host, Host) and _host.host_group is not None:
            self.clean_none_vms_from_logical_groups(_host.host_group)
        elif isinstance(_host, HostGroup) and _host.parent_resource is not None:
            self.clean_none_vms_from_logical_groups(_host.parent_resource)

    def update_uuid_in_logical_groups(self, _h_uuid, _uuid, _host):
        for lgk in _host.memberships.keys():
            lg = self.logical_groups[lgk]

            if isinstance(_host, Host):
                if lg.update_uuid(_h_uuid, _uuid, _host.name) is True:
                    lg.last_update = time.time()
            elif isinstance(_host, HostGroup):
                if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                    if lgk.split(":")[0] == _host.host_type:
                        if lg.update_uuid(_h_uuid, _uuid, _host.name) is True:
                            lg.last_update = time.time()

        if isinstance(_host, Host) and _host.host_group is not None:
            self.update_uuid_in_logical_groups(_h_uuid, _uuid, _host.host_group)
        elif isinstance(_host, HostGroup) and _host.parent_resource is not None:
            self.update_uuid_in_logical_groups(_h_uuid, _uuid, _host.parent_resource)

    def update_h_uuid_in_logical_groups(self, _h_uuid, _uuid, _host):
        for lgk in _host.memberships.keys():
            lg = self.logical_groups[lgk]

            if isinstance(_host, Host):
                if lg.update_h_uuid(_h_uuid, _uuid, _host.name) is True:
                    lg.last_update = time.time()
            elif isinstance(_host, HostGroup):
                if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                    if lgk.split(":")[0] == _host.host_type:
                        if lg.update_h_uuid(_h_uuid, _uuid, _host.name) is True:
                            lg.last_update = time.time()

        if isinstance(_host, Host) and _host.host_group is not None:
            self.update_h_uuid_in_logical_groups(_h_uuid, _uuid, _host.host_group)
        elif isinstance(_host, HostGroup) and _host.parent_resource is not None:
            self.update_h_uuid_in_logical_groups(_h_uuid, _uuid, _host.parent_resource)

    def compute_avail_resources(self, hk, host):
        ram_allocation_ratio_list = []
        cpu_allocation_ratio_list = []
        disk_allocation_ratio_list = []

        for _, lg in host.memberships.iteritems():
            if lg.group_type == "AGGR":
                if "ram_allocation_ratio" in lg.metadata.keys():
                    ram_allocation_ratio_list.append(float(lg.metadata["ram_allocation_ratio"]))
                if "cpu_allocation_ratio" in lg.metadata.keys():
                    cpu_allocation_ratio_list.append(float(lg.metadata["cpu_allocation_ratio"]))
                if "disk_allocation_ratio" in lg.metadata.keys():
                    disk_allocation_ratio_list.append(float(lg.metadata["disk_allocation_ratio"]))

        ram_allocation_ratio = 1.0
        if len(ram_allocation_ratio_list) > 0:
            ram_allocation_ratio = min(ram_allocation_ratio_list)
        else:
            if self.config.default_ram_allocation_ratio > 0:
                ram_allocation_ratio = self.config.default_ram_allocation_ratio

        static_ram_standby_ratio = 0
        if self.config.static_mem_standby_ratio > 0:
            static_ram_standby_ratio = float(self.config.static_mem_standby_ratio) / float(100)

        host.compute_avail_mem(ram_allocation_ratio, static_ram_standby_ratio)

        self.logger.debug("Resource.compute_avail_resources: host (" + hk + ")'s total_mem = " +
                          str(host.mem_cap) + ", avail_mem = " + str(host.avail_mem_cap))

        cpu_allocation_ratio = 1.0
        if len(cpu_allocation_ratio_list) > 0:
            cpu_allocation_ratio = min(cpu_allocation_ratio_list)
        else:
            if self.config.default_cpu_allocation_ratio > 0:
                cpu_allocation_ratio = self.config.default_cpu_allocation_ratio

        static_cpu_standby_ratio = 0
        if self.config.static_cpu_standby_ratio > 0:
            static_cpu_standby_ratio = float(self.config.static_cpu_standby_ratio) / float(100)

        host.compute_avail_vCPUs(cpu_allocation_ratio, static_cpu_standby_ratio)

        self.logger.debug("Resource.compute_avail_resources: host (" + hk + ")'s total_vCPUs = " +
                          str(host.vCPUs) + ", avail_vCPUs = " + str(host.avail_vCPUs))

        disk_allocation_ratio = 1.0
        if len(disk_allocation_ratio_list) > 0:
            disk_allocation_ratio = min(disk_allocation_ratio_list)
        else:
            if self.config.default_disk_allocation_ratio > 0:
                disk_allocation_ratio = self.config.default_disk_allocation_ratio

        static_disk_standby_ratio = 0
        if self.config.static_local_disk_standby_ratio > 0:
            static_disk_standby_ratio = float(self.config.static_local_disk_standby_ratio) / float(100)

        host.compute_avail_disk(disk_allocation_ratio, static_disk_standby_ratio)

        self.logger.debug("Resource.compute_avail_resources: host (" + hk + ")'s total_local_disk = " +
                          str(host.local_disk_cap) + ", avail_local_disk = " + str(host.avail_local_disk_cap))

    def get_flavor(self, _name):
        flavor = None

        if _name in self.flavors.keys():
            if self.flavors[_name].status == "enabled":
                flavor = self.flavors[_name]

        return flavor
