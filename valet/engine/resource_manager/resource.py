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

import six
import time
import traceback

from oslo_log import log

from valet.engine.optimizer.app_manager.group import LEVEL
from valet.engine.resource_manager.resources.datacenter import Datacenter
from valet.engine.resource_manager.resources.flavor import Flavor
from valet.engine.resource_manager.resources.group import Group
from valet.engine.resource_manager.resources.host import Host
from valet.engine.resource_manager.resources.host_group import HostGroup

LOG = log.getLogger(__name__)


class Resource(object):
    """Container and Handler to deal with change of datacenter resource status.

    """

    def __init__(self, _db, _config):
        """Init Resource Class."""
        self.db = _db
        self.config = _config

        """ resource data """
        self.datacenter = Datacenter(self.config.datacenter_name)
        self.host_groups = {}
        self.hosts = {}

        self.groups = {}
        self.flavors = {}

        self.current_timestamp = 0
        self.curr_db_timestamp = 0

        self.resource_updated = False

        """ resource status aggregation """
        self.CPU_avail = 0
        self.mem_avail = 0
        self.local_disk_avail = 0

    def load_from_db(self, _resource_status):
        """Load all resource status info from DB."""

        LOG.info("load prior data")

        try:
            groups = _resource_status.get("groups")
            if groups:
                for lgk, lg in groups.iteritems():
                    group = Group(lgk)
                    group.group_type = lg.get("group_type")
                    group.status = lg.get("status")
                    group.metadata = lg.get("metadata")
                    group.vm_list = lg.get("vm_list")
                    group.vms_per_host = lg.get("vms_per_host")

                    self.groups[lgk] = group

            if len(self.groups) == 0:
                LOG.warning("no groups in db record")

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

            if len(self.flavors) == 0:
                LOG.warning("no flavors in db record")

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

                    for lgk in h["membership_list"]:
                        host.memberships[lgk] = self.groups[lgk]

                    self.hosts[hk] = host

                if len(self.hosts) == 0:
                    LOG.warning("no hosts in db record")

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
                    host_group.original_local_disk_cap = \
                        hg.get("original_local_disk")
                    host_group.avail_local_disk_cap = hg.get(
                        "avail_local_disk")
                    host_group.vm_list = hg.get("vm_list")

                    for lgk in hg.get("membership_list"):
                        host_group.memberships[lgk] = self.groups[lgk]

                    self.host_groups[hgk] = host_group

                if len(self.host_groups) == 0:
                    LOG.warning("no host_groups (rack)")

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
                self.datacenter.original_local_disk_cap = \
                    dc.get("original_local_disk")
                self.datacenter.avail_local_disk_cap = dc.get(
                    "avail_local_disk")
                self.datacenter.vm_list = dc.get("vm_list")

                for lgk in dc.get("membership_list"):
                    self.datacenter.memberships[lgk] = self.groups[lgk]

                for ck in dc.get("children"):
                    if ck in self.host_groups.keys():
                        self.datacenter.resources[ck] = self.host_groups[ck]
                    elif ck in self.hosts.keys():
                        self.datacenter.resources[ck] = self.hosts[ck]

                if len(self.datacenter.resources) == 0:
                    LOG.warning("fail loading datacenter")

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
                            host_group.child_resources[ck] = (
                                self.host_groups[ck])

            hs = _resource_status.get("hosts")
            if hs:
                for hk, h in hs.iteritems():
                    host = self.hosts[hk]

                    pk = h.get("parent")
                    if pk == self.datacenter.name:
                        host.host_group = self.datacenter
                    elif pk in self.host_groups.keys():
                        host.host_group = self.host_groups[pk]

            self._update_compute_avail()

        except Exception:
            LOG.error("while bootstrap_from_db: ",
                      traceback.format_exc())

        return True

    def update_topology(self, store=True):
        """Update resource status triggered by placements, events, and batch.

        """

        self._update_topology()
        self._update_compute_avail()

        if store is False:
            return True

        return self.store_topology_updates()

    def _update_topology(self):
        """Update host group (rack) and datacenter status."""

        updated = False
        for level in LEVEL:
            for _, host_group in self.host_groups.iteritems():
                if (host_group.host_type == level and
                        host_group.check_availability()):
                    if host_group.last_update > self.current_timestamp:
                        self._update_host_group_topology(host_group)
                        updated = True

        if self.datacenter.last_update >= self.current_timestamp:
            self._update_datacenter_topology()
            updated = True

        if updated is True:
            self.current_timestamp = time.time()
            self.resource_updated = True

    def _update_host_group_topology(self, _host_group):
        """Update host group (rack) status."""

        _host_group.init_resources()
        del _host_group.vm_list[:]

        for _, host in _host_group.child_resources.iteritems():
            if host.check_availability() is True:
                _host_group.vCPUs += host.vCPUs
                _host_group.original_vCPUs += host.original_vCPUs
                _host_group.avail_vCPUs += host.avail_vCPUs
                _host_group.mem_cap += host.mem_cap
                _host_group.original_mem_cap += host.original_mem_cap
                _host_group.avail_mem_cap += host.avail_mem_cap
                _host_group.local_disk_cap += host.local_disk_cap
                _host_group.original_local_disk_cap += \
                    host.original_local_disk_cap
                _host_group.avail_local_disk_cap += host.avail_local_disk_cap

                for vm_info in host.vm_list:
                    _host_group.vm_list.append(vm_info)

        _host_group.init_memberships()

        for _, host in _host_group.child_resources.iteritems():
            if host.check_availability() is True:
                for mk in host.memberships.keys():
                    _host_group.memberships[mk] = host.memberships[mk]

    def _update_datacenter_topology(self):
        """Update datacenter status."""

        self.datacenter.init_resources()
        del self.datacenter.vm_list[:]
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
                self.datacenter.original_local_disk_cap += \
                    resource.original_local_disk_cap
                self.datacenter.avail_local_disk_cap += \
                    resource.avail_local_disk_cap

                for vm_name in resource.vm_list:
                    self.datacenter.vm_list.append(vm_name)

                for mk in resource.memberships.keys():
                    self.datacenter.memberships[mk] = resource.memberships[mk]

    def _update_compute_avail(self):
        """Update amount of total available resources."""
        self.CPU_avail = self.datacenter.avail_vCPUs
        self.mem_avail = self.datacenter.avail_mem_cap
        self.local_disk_avail = self.datacenter.avail_local_disk_cap

    def store_topology_updates(self):
        """Store resource status in batch."""

        if not self.resource_updated:
            return True

        updated = False
        flavor_updates = {}
        group_updates = {}
        host_updates = {}
        host_group_updates = {}
        datacenter_update = None

        LOG.info("check and store resource status")

        for fk, flavor in self.flavors.iteritems():
            if flavor.last_update >= self.curr_db_timestamp:
                flavor_updates[fk] = flavor.get_json_info()
                updated = True

        for lgk, lg in self.groups.iteritems():
            if lg.last_update >= self.curr_db_timestamp:
                group_updates[lgk] = lg.get_json_info()
                updated = True

        for hk, host in self.hosts.iteritems():
            if host.last_update >= self.curr_db_timestamp:
                host_updates[hk] = host.get_json_info()
                updated = True

        for hgk, host_group in self.host_groups.iteritems():
            if host_group.last_update >= self.curr_db_timestamp:
                host_group_updates[hgk] = host_group.get_json_info()
                updated = True

        if self.datacenter.last_update >= self.curr_db_timestamp:
            datacenter_update = self.datacenter.get_json_info()
            updated = True

        if updated:
            json_logging = {}
            json_logging['timestamp'] = self.curr_db_timestamp

            if len(flavor_updates) > 0:
                json_logging['flavors'] = flavor_updates

            if len(group_updates) > 0:
                json_logging['groups'] = group_updates

            if len(host_updates) > 0:
                json_logging['hosts'] = host_updates

            if len(host_group_updates) > 0:
                json_logging['host_groups'] = host_group_updates

            if datacenter_update is not None:
                json_logging['datacenter'] = datacenter_update

            if not self.db.update_resource_status(self.datacenter.name,
                                                  json_logging):
                return False

            self.curr_db_timestamp = time.time()
            self.resource_updated = False

        return True

    def update_rack_resource(self, _host):
        """Mark the host update time for batch resource status update."""
        rack = _host.host_group
        if rack is not None:
            rack.last_update = time.time()
            if isinstance(rack, HostGroup):
                self.update_cluster_resource(rack)

    def update_cluster_resource(self, _rack):
        """Mark the host update time for batch resource status update."""
        cluster = _rack.parent_resource
        if cluster is not None:
            cluster.last_update = time.time()
            if isinstance(cluster, HostGroup):
                self.datacenter.last_update = time.time()

    def get_uuid(self, _orch_id, _host_name):
        host = self.hosts[_host_name]
        return host.get_uuid(_orch_id)

    def add_vm_to_host(self, _vm_alloc, _vm_info):
        """Add vm to host and update the amount of available resource."""

        host = self.hosts[_vm_alloc["host"]]

        if host.exist_vm(orch_id=_vm_info["orch_id"], uuid=_vm_info["uuid"]):
            LOG.warning("vm already exists in the host")

            # host.remove_vm(orch_id=_vm_info["orch_id"],
            # uuid=_vm_info["uuid"])
            self.remove_vm_from_host(_vm_alloc, orch_id=_vm_info["orch_id"],
                                     uuid=_vm_info["uuid"])

        host.vm_list.append(_vm_info)

        host.avail_vCPUs -= _vm_alloc["vcpus"]
        host.avail_mem_cap -= _vm_alloc["mem"]
        host.avail_local_disk_cap -= _vm_alloc["local_volume"]
        host.vCPUs_used += _vm_alloc["vcpus"]
        host.free_mem_mb -= _vm_alloc["mem"]
        host.free_disk_gb -= _vm_alloc["local_volume"]
        host.disk_available_least -= _vm_alloc["local_volume"]

        return True

    def remove_vm_from_host(self, _vm_alloc, orch_id=None, uuid=None):
        """Remove vm from host with orch_id."""

        host = self.hosts[_vm_alloc["host"]]

        if host.remove_vm(orch_id, uuid) is True:
            host.avail_vCPUs += _vm_alloc["vcpus"]
            host.avail_mem_cap += _vm_alloc["mem"]
            host.avail_local_disk_cap += _vm_alloc["local_volume"]
            host.vCPUs_used -= _vm_alloc["vcpus"]
            host.free_mem_mb += _vm_alloc["mem"]
            host.free_disk_gb += _vm_alloc["local_volume"]
            host.disk_available_least += _vm_alloc["local_volume"]
            return True
        else:
            LOG.warning("vm to be removed not exist")
            return False

    def update_host_resources(self, _hn, _st):
        """Check and update compute node status."""
        host = self.hosts[_hn]
        if host.status != _st:
            host.status = _st
            LOG.warning("host(" + _hn + ") status changed")
            return True
        else:
            return False

    def update_host_time(self, _host_name):
        """Mark the host update time for batch resource status update."""
        host = self.hosts[_host_name]
        host.last_update = time.time()
        self.update_rack_resource(host)

    def add_group(self, _host_name, _lg_name, _lg_type):
        """Add a group to resource unless the group exists."""

        success = True

        host = None
        if _host_name in self.hosts.keys():
            host = self.hosts[_host_name]
        else:
            host = self.host_groups[_host_name]

        if host is not None:
            if _lg_name not in self.groups.keys():
                group = Group(_lg_name)
                group.group_type = _lg_type
                group.last_update = time.time()
                self.groups[_lg_name] = group
            else:
                success = False

            if _lg_name not in host.memberships.keys():
                host.memberships[_lg_name] = self.groups[_lg_name]

                if isinstance(host, HostGroup):
                    host.last_update = time.time()
                    self.update_cluster_resource(host)
            else:
                success = False
        else:
            LOG.warning("host not found while adding group")
            return False

        return success

    def add_vm_to_groups(self, _host, _vm_info, _groups_of_vm):
        """Add new vm into related groups."""

        for lgk in _host.memberships.keys():
            if lgk in _groups_of_vm:
                if lgk in self.groups.keys():
                    lg = self.groups[lgk]

                    if isinstance(_host, Host):
                        if lg.add_vm(_vm_info, _host.name) is True:
                            lg.last_update = time.time()
                        else:
                            LOG.warning("vm already exists in group")
                    elif isinstance(_host, HostGroup):
                        if lg.group_type == "EX" or \
                           lg.group_type == "AFF" or lg.group_type == "DIV":
                            if lgk.split(":")[0] == _host.host_type:
                                if lg.add_vm(_vm_info, _host.name) is True:
                                    lg.last_update = time.time()
                                else:
                                    LOG.warning("vm already exists in group")
                else:
                    LOG.warning("nof found group while adding vm")

        if isinstance(_host, Host) and _host.host_group is not None:
            self.add_vm_to_groups(_host.host_group, _vm_info, _groups_of_vm)
        elif isinstance(_host, HostGroup) and \
                _host.parent_resource is not None:
            self.add_vm_to_groups(_host.parent_resource,
                                  _vm_info, _groups_of_vm)

    def remove_vm_from_groups(self, _host, orch_id=None, uuid=None):
        """Remove vm from related groups."""

        for lgk in _host.memberships.keys():
            if lgk not in self.groups.keys():
                continue
            lg = self.groups[lgk]

            if isinstance(_host, Host):
                # Remove host from lg's membership if the host has no vms of lg
                if lg.remove_vm(_host.name, orch_id, uuid) is True:
                    lg.last_update = time.time()

                # Remove lg from host's membership if lg does not
                # have the host
                if _host.remove_membership(lg) is True:
                    _host.last_update = time.time()

            elif isinstance(_host, HostGroup):
                if self._check_group_type(lg.group_type):
                    if lgk.split(":")[0] == _host.host_type:
                        if lg.remove_vm(_host.name, orch_id, uuid) is True:
                            lg.last_update = time.time()

                        if _host.remove_membership(lg) is True:
                            _host.last_update = time.time()

            if lg.group_type == "EX" or \
                    lg.group_type == "AFF" or lg.group_type == "DIV":
                # FIXME(gjung): del self.groups[lgk] if len(lg.vm_list) == 0?
                pass

        if isinstance(_host, Host) and _host.host_group is not None:
            self.remove_vm_from_groups(_host.host_group, orch_id, uuid)
        elif isinstance(_host, HostGroup) and \
                _host.parent_resource is not None:
            self.remove_vm_from_groups(_host.parent_resource, orch_id, uuid)

    def remove_vm_from_groups_of_host(self, _host, orch_id=None, uuid=None):
        """Remove vm from related groups of the host."""

        for lgk in _host.memberships.keys():
            if lgk not in self.groups.keys():
                LOG.warning("group (" + lgk + ") already removed")
                continue
            lg = self.groups[lgk]

            if isinstance(_host, Host):
                if lg.remove_vm_from_host(_host.name, orch_id, uuid) is True:
                    lg.last_update = time.time()

                if _host.remove_membership(lg) is True:
                    _host.last_update = time.time()

            elif isinstance(_host, HostGroup):
                if self._check_group_type(lg.group_type):
                    if lgk.split(":")[0] == _host.host_type:
                        if lg.remove_vm_from_host(_host.name,
                                                  orch_id, uuid) is True:
                            lg.last_update = time.time()

                        if _host.remove_membership(lg) is True:
                            _host.last_update = time.time()

        if isinstance(_host, Host) and _host.host_group is not None:
            self.remove_vm_from_groups_of_host(_host.host_group, orch_id, uuid)
        elif isinstance(_host, HostGroup) and \
                _host.parent_resource is not None:
            self.remove_vm_from_groups_of_host(_host.parent_resource,
                                               orch_id, uuid)

    def update_uuid_in_groups(self, _orch_id, _uuid, _host):
        """Update physical uuid."""

        for lgk in _host.memberships.keys():
            lg = self.groups[lgk]

            if isinstance(_host, Host):
                if lg.update_uuid(_orch_id, _uuid, _host.name) is True:
                    lg.last_update = time.time()
            elif isinstance(_host, HostGroup):
                if self._check_group_type(lg.group_type):
                    if lgk.split(":")[0] == _host.host_type:
                        if lg.update_uuid(_orch_id, _uuid, _host.name) is True:
                            lg.last_update = time.time()

        if isinstance(_host, Host) and _host.host_group is not None:
            self.update_uuid_in_groups(_orch_id, _uuid, _host.host_group)
        elif isinstance(_host, HostGroup) and \
                _host.parent_resource is not None:
            self.update_uuid_in_groups(_orch_id, _uuid, _host.parent_resource)

    def update_orch_id_in_groups(self, _orch_id, _uuid, _host):
        """Update orch_id."""

        for lgk in _host.memberships.keys():
            lg = self.groups[lgk]

            if isinstance(_host, Host):
                if lg.update_orch_id(_orch_id, _uuid, _host.name) is True:
                    lg.last_update = time.time()
            elif isinstance(_host, HostGroup):
                if self._check_group_type(lg.group_type):
                    if lgk.split(":")[0] == _host.host_type:
                        if (lg.update_orch_id(_orch_id, _uuid, _host.name) is
                           True):
                            lg.last_update = time.time()

        if isinstance(_host, Host) and _host.host_group is not None:
            self.update_orch_id_in_groups(_orch_id, _uuid, _host.host_group)
        elif (isinstance(_host, HostGroup) and
              _host.parent_resource is not None):
            self.update_orch_id_in_groups(_orch_id, _uuid,
                                          _host.parent_resource)

    def compute_avail_resources(self, hk, host):
        """Compute the available amount of resources with oversubsription ratios.

        """

        ram_allocation_ratio_list = []
        cpu_allocation_ratio_list = []
        disk_allocation_ratio_list = []
        static_ram_standby_ratio = 0.0
        static_cpu_standby_ratio = 0.0
        static_disk_standby_ratio = 0.0

        for _, lg in host.memberships.iteritems():
            if lg.group_type == "AGGR":
                if "ram_allocation_ratio" in lg.metadata.keys():
                    ram_allocation_ratio_list.append(
                        float(lg.metadata["ram_allocation_ratio"]))
                if "cpu_allocation_ratio" in lg.metadata.keys():
                    cpu_allocation_ratio_list.append(
                        float(lg.metadata["cpu_allocation_ratio"]))
                if "disk_allocation_ratio" in lg.metadata.keys():
                    disk_allocation_ratio_list.append(
                        float(lg.metadata["disk_allocation_ratio"]))

        ram_allocation_ratio = 1.0
        if len(ram_allocation_ratio_list) > 0:
            ram_allocation_ratio = min(ram_allocation_ratio_list)
        else:
            if self.config.default_ram_allocation_ratio > 0:
                ram_allocation_ratio = self.config.default_ram_allocation_ratio

        if self.config.static_mem_standby_ratio > 0:
            static_ram_standby_ratio = (
                float(self.config.static_mem_standby_ratio) / float(100))

        host.compute_avail_mem(ram_allocation_ratio, static_ram_standby_ratio)

        cpu_allocation_ratio = 1.0
        if len(cpu_allocation_ratio_list) > 0:
            cpu_allocation_ratio = min(cpu_allocation_ratio_list)
        else:
            if self.config.default_cpu_allocation_ratio > 0:
                cpu_allocation_ratio = self.config.default_cpu_allocation_ratio

        if self.config.static_cpu_standby_ratio > 0:
            static_cpu_standby_ratio = (
                float(self.config.static_cpu_standby_ratio) / float(100))

        host.compute_avail_vCPUs(
            cpu_allocation_ratio, static_cpu_standby_ratio)

        disk_allocation_ratio = 1.0
        if len(disk_allocation_ratio_list) > 0:
            disk_allocation_ratio = min(disk_allocation_ratio_list)
        else:
            if self.config.default_disk_allocation_ratio > 0:
                disk_allocation_ratio = \
                    self.config.default_disk_allocation_ratio

        if self.config.static_local_disk_standby_ratio > 0:
            static_disk_standby_ratio = (
                float(self.config.static_local_disk_standby_ratio) / float(100)
            )

        host.compute_avail_disk(
            disk_allocation_ratio, static_disk_standby_ratio)

    def get_flavor(self, _id):
        """Get a flavor info."""

        flavor_id = None
        if isinstance(_id, six.string_types):
            flavor_id = _id
        else:
            flavor_id = str(_id)

        flavor = None

        if flavor_id in self.flavors.keys():
            flavor = self.flavors[flavor_id]
        else:
            for _, f in self.flavors.iteritems():
                if f.flavor_id == flavor_id:
                    flavor = f
                    break

        if flavor is not None:
            if flavor.status is not "enabled":
                flavor = None

        return flavor

    def _check_group_type(self, type):
        return type in ['EX', 'AFF', 'DIV']
