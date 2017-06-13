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
import time
import traceback

from valet.engine.optimizer.app_manager.app_topology_base import LEVELS
from valet.engine.resource_manager.resource_base import Datacenter
from valet.engine.resource_manager.resource_base import Flavor
from valet.engine.resource_manager.resource_base import Host
from valet.engine.resource_manager.resource_base import HostGroup
from valet.engine.resource_manager.resource_base import LogicalGroup


class Resource(object):
    """Resource Class.

    This class bootsraps the resources from the database and initializes
    them using base resources (datacenter, host group, host, logical group).
    Also manages aggregate status of resources and metadata and handles
    updates to base resource types.
    """

    def __init__(self, _db, _config, _logger):
        """Init Resource Class."""
        self.db = _db

        self.config = _config
        self.logger = _logger

        """ resource data """
        self.datacenter = Datacenter(self.config.datacenter_name)
        self.host_groups = {}
        self.hosts = {}

        """ metadata """
        self.logical_groups = {}
        self.flavors = {}

        self.current_timestamp = 0
        self.curr_db_timestamp = 0

        self.resource_updated = False

        """ resource status aggregation """
        self.CPU_avail = 0
        self.mem_avail = 0
        self.local_disk_avail = 0
        self.disk_avail = 0
        self.nw_bandwidth_avail = 0

    # FIXME(GJ): should check invalid return here?
    def bootstrap_from_db(self, _resource_status):
        """Return True if bootsrap resource from database successful."""
        try:
            self.logger.info("Resource status from DB = %s", _resource_status)
            logical_groups = _resource_status.get("logical_groups")
            if logical_groups:
                for lgk, lg in logical_groups.iteritems():
                    logical_group = LogicalGroup(lgk)
                    logical_group.group_type = lg.get("group_type")
                    logical_group.status = lg.get("status")
                    logical_group.metadata = lg.get("metadata")
                    logical_group.vm_list = lg.get("vm_list")
                    logical_group.vms_per_host = lg.get("vms_per_host")

                    self.logical_groups[lgk] = logical_group

            if len(self.logical_groups) == 0:
                self.logger.warn("no logical_groups")

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
                self.logger.error("fail loading flavors")

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
                        host.memberships[lgk] = self.logical_groups[lgk]

                    self.hosts[hk] = host

                if len(self.hosts) == 0:
                    self.logger.error("fail loading hosts")

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
                        host_group.memberships[lgk] = self.logical_groups[lgk]

                    self.host_groups[hgk] = host_group

                if len(self.host_groups) == 0:
                    self.logger.warn("fail loading host_groups")

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
                    self.datacenter.memberships[lgk] = self.logical_groups[lgk]

                for ck in dc.get("children"):
                    if ck in self.host_groups.keys():
                        self.datacenter.resources[ck] = self.host_groups[ck]
                    elif ck in self.hosts.keys():
                        self.datacenter.resources[ck] = self.hosts[ck]

                if len(self.datacenter.resources) == 0:
                    self.logger.error("fail loading datacenter")

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
            self.logger.error("while bootstrap_from_db: ",
                              traceback.format_exc())

        return True

    def update_topology(self, store=True):
        """Update Topology and return True, if store True then store update."""
        self._update_topology()

        self._update_compute_avail()

        if store is False:
            return True

        return self.store_topology_updates()

    def _update_topology(self):
        updated = False
        for level in LEVELS:
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

                for vm_id in host.vm_list:
                    _host_group.vm_list.append(vm_id)

        _host_group.init_memberships()

        for _, host in _host_group.child_resources.iteritems():
            if host.check_availability() is True:
                for mk in host.memberships.keys():
                    _host_group.memberships[mk] = host.memberships[mk]

    def _update_datacenter_topology(self):
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
        self.CPU_avail = self.datacenter.avail_vCPUs
        self.mem_avail = self.datacenter.avail_mem_cap
        self.local_disk_avail = self.datacenter.avail_local_disk_cap

    def store_topology_updates(self):
        updated = False
        flavor_updates = {}
        logical_group_updates = {}
        host_updates = {}
        host_group_updates = {}
        datacenter_update = None

        self.logger.info("check and store resource status")

        for fk, flavor in self.flavors.iteritems():
            if flavor.last_update >= self.curr_db_timestamp:
                flavor_updates[fk] = flavor.get_json_info()
                updated = True

        for lgk, lg in self.logical_groups.iteritems():
            if lg.last_update >= self.curr_db_timestamp:
                logical_group_updates[lgk] = lg.get_json_info()
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

        # NOTE(GJ): do not track resource change histroy in this version

        if updated is True:
            json_logging = {}
            json_logging['timestamp'] = self.curr_db_timestamp

            if len(flavor_updates) > 0:
                json_logging['flavors'] = flavor_updates
            if len(logical_group_updates) > 0:
                json_logging['logical_groups'] = logical_group_updates
            if len(host_updates) > 0:
                json_logging['hosts'] = host_updates
            if len(host_group_updates) > 0:
                json_logging['host_groups'] = host_group_updates
            if datacenter_update is not None:
                json_logging['datacenter'] = datacenter_update

            if not self.db.update_resource_status(
                    self.datacenter.name, json_logging):
                return None

            self.curr_db_timestamp = time.time()

        return True

    def show_current_logical_groups(self):
        self.logger.debug("--- track logical groups info ---")
        for lgk, lg in self.logical_groups.iteritems():
            if lg.status == "enabled":
                self.logger.debug("lg name = " + lgk)
                self.logger.debug("    type = " + lg.group_type)
                if lg.group_type == "AGGR":
                    for k in lg.metadata.keys():
                        self.logger.debug("        metadata key = " + k)
                self.logger.debug("    vms")
                debug_msg = "        orch_id = %s uuid = %s"
                for v in lg.vm_list:
                    LOG.debug(debug_msg % (v[0], v[2]))
                LOG.debug("    hosts")
                for h, v in lg.vms_per_host.iteritems():
                    LOG.debug("        host = %s" % h)
                    LOG.debug("        vms = %s" %
                              str(len(lg.vms_per_host[h])))
                    host = None
                    if h in self.hosts.keys():
                        host = self.hosts[h]
                    elif h in self.host_groups.keys():
                        host = self.host_groups[h]
                    else:
                        self.logger.error("TEST: lg member not exist")
                    if host is not None:
                        self.logger.debug("        status = " + host.status)
                        if lgk not in host.memberships.keys():
                            self.logger.error("TEST: membership missing")

    def show_current_host_status(self):
        self.logger.debug("--- track host info ---")
        for hk, h in self.hosts.iteritems():
            self.logger.debug("host name = " + hk)
            self.logger.debug("    status = " + h.status + ", " + h.state)
            self.logger.debug("    vms = " + str(len(h.vm_list)))
            self.logger.debug("    resources (org, total, avail, used)")
            cpu_org = str(h.original_vCPUs)
            cpu_tot = str(h.vCPUs)
            cpu_avail = str(h.avail_vCPUs)
            cpu_used = str(h.vCPUs_used)
            msg = "      {0} = {1}, {2}, {3}, {4}"
            self.logger.debug(
                msg.format('cpu', cpu_org, cpu_tot, cpu_avail, cpu_used))
            mem_org = str(h.original_mem_cap)
            mem_tot = str(h.mem_cap)
            mem_avail = str(h.avail_mem_cap)
            mem_used = str(h.free_mem_mb)
            self.logger.debug(
                msg.format('mem', mem_org, mem_tot, mem_avail, mem_used))
            dsk_org = str(h.original_local_disk_cap)
            dsk_tot = str(h.local_disk_cap)
            dsk_avail = str(h.avail_local_disk_cap)
            dsk_used = str(h.free_disk_gb)
            self.logger.debug(
                msg.format('disk', dsk_org, dsk_tot, dsk_avail, dsk_used))
            self.logger.debug("    memberships")
            for mk in h.memberships.keys():
                self.logger.debug("        " + mk)
                if mk not in self.logical_groups.keys():
                    self.logger.error("TEST: lg missing")

    def update_rack_resource(self, _host):
        """Update resources for rack (host), then update cluster."""
        rack = _host.host_group

        if rack is not None:
            rack.last_update = time.time()

            if isinstance(rack, HostGroup):
                self.update_cluster_resource(rack)

    def update_cluster_resource(self, _rack):
        """Update cluster rack belonged to, then update datacenter."""
        cluster = _rack.parent_resource

        if cluster is not None:
            cluster.last_update = time.time()

            if isinstance(cluster, HostGroup):
                self.datacenter.last_update = time.time()

    def get_uuid(self, _h_uuid, _host_name):
        """Return host uuid."""
        host = self.hosts[_host_name]

        return host.get_uuid(_h_uuid)

    def add_vm_to_host(self, _host_name, _vm_id, _vcpus, _mem, _ldisk):
        """Add vm to host and adjust compute resources for host."""
        host = self.hosts[_host_name]

        host.vm_list.append(_vm_id)

        host.avail_vCPUs -= _vcpus
        host.avail_mem_cap -= _mem
        host.avail_local_disk_cap -= _ldisk

        host.vCPUs_used += _vcpus
        host.free_mem_mb -= _mem
        host.free_disk_gb -= _ldisk
        host.disk_available_least -= _ldisk

    def remove_vm_by_h_uuid_from_host(self, _host_name, _h_uuid, _vcpus, _mem,
                                      _ldisk):
        """Remove vm from host by h_uuid, adjust compute resources for host."""
        host = self.hosts[_host_name]

        host.remove_vm_by_h_uuid(_h_uuid)

        host.avail_vCPUs += _vcpus
        host.avail_mem_cap += _mem
        host.avail_local_disk_cap += _ldisk

        host.vCPUs_used -= _vcpus
        host.free_mem_mb += _mem
        host.free_disk_gb += _ldisk
        host.disk_available_least += _ldisk

    def remove_vm_by_uuid_from_host(self, _host_name, _uuid, _vcpus, _mem,
                                    _ldisk):
        """Remove vm from host by uuid, adjust compute resources for host."""
        host = self.hosts[_host_name]

        host.remove_vm_by_uuid(_uuid)

        host.avail_vCPUs += _vcpus
        host.avail_mem_cap += _mem
        host.avail_local_disk_cap += _ldisk

        host.vCPUs_used -= _vcpus
        host.free_mem_mb += _mem
        host.free_disk_gb += _ldisk
        host.disk_available_least += _ldisk

    # called from handle_events
    def update_host_resources(self, _hn, _st, _vcpus, _vcpus_used, _mem, _fmem,
                              _ldisk, _fldisk, _avail_least):
        updated = False

        host = self.hosts[_hn]

        if host.status != _st:
            host.status = _st
            LOG.warning(
                "Resource.update_host_resources: host(%s) status changed" %
                _hn)
            updated = True

        # FIXME(GJ): should check cpu, memm and disk here?

        if updated is True:
            self.compute_avail_resources(_hn, host)

        return updated

    def update_host_time(self, _host_name):
        """Update last host update time."""
        host = self.hosts[_host_name]

        host.last_update = time.time()
        self.update_rack_resource(host)

    def add_logical_group(self, _host_name, _lg_name, _lg_type):
        """Add logical group to host memberships and update host resource."""
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
        """Add vm to logical group and update corresponding lg."""
        for lgk in _host.memberships.keys():
            if lgk in _logical_groups_of_vm:
                lg = self.logical_groups[lgk]

                if isinstance(_host, Host):
                    if lg.add_vm_by_h_uuid(_vm_id, _host.name) is True:
                        lg.last_update = time.time()
                elif isinstance(_host, HostGroup):
                    if self._check_group_type(lg.group_type):
                        if lgk.split(":")[0] == _host.host_type:
                            if lg.add_vm_by_h_uuid(_vm_id, _host.name) is True:
                                lg.last_update = time.time()

        if isinstance(_host, Host) and _host.host_group is not None:
            self.add_vm_to_logical_groups(_host.host_group, _vm_id,
                                          _logical_groups_of_vm)
        elif (isinstance(_host, HostGroup) and
              _host.parent_resource is not None):
            self.add_vm_to_logical_groups(_host.parent_resource, _vm_id,
                                          _logical_groups_of_vm)

    def remove_vm_by_h_uuid_from_logical_groups(self, _host, _h_uuid):
        """Remove vm by orchestration id from lgs. Update host and lgs."""
        for lgk in _host.memberships.keys():
            if lgk not in self.logical_groups.keys():
                LOG.warning("logical group (%s) missing while "
                            "removing %s" % (lgk, _h_uuid))
                continue
            lg = self.logical_groups[lgk]

            if isinstance(_host, Host):
                # Remove host from lg's membership if the host
                # has no vms of lg
                if lg.remove_vm_by_h_uuid(_h_uuid, _host.name) is True:
                    lg.last_update = time.time()

                # Remove lg from host's membership if lg does not have the host
                if _host.remove_membership(lg) is True:
                    _host.last_update = time.time()

            elif isinstance(_host, HostGroup):
                if self._check_group_type(lg.group_type):
                    if lgk.split(":")[0] == _host.host_type:
                        if lg.remove_vm_by_h_uuid(_h_uuid, _host.name):
                            lg.last_update = time.time()

                        if _host.remove_membership(lg):
                            _host.last_update = time.time()

            if self._check_group_type(lg.group_type):
                if len(lg.vm_list) == 0:
                    del self.logical_groups[lgk]

        if isinstance(_host, Host) and _host.host_group is not None:
            self.remove_vm_by_h_uuid_from_logical_groups(_host.host_group,
                                                         _h_uuid)
        elif (isinstance(_host, HostGroup) and
              _host.parent_resource is not None):
            self.remove_vm_by_h_uuid_from_logical_groups(
                _host.parent_resource, _h_uuid)

    def remove_vm_by_uuid_from_logical_groups(self, _host, _uuid):
        """Remove vm by uuid from lgs and update proper host and lgs."""
        for lgk in _host.memberships.keys():
            if lgk not in self.logical_groups.keys():
                LOG.warning("logical group (%s) missing while "
                            "removing %s" % (lgk, _uuid))
                continue
            lg = self.logical_groups[lgk]

            if isinstance(_host, Host):
                # Remove host from lg's membership if the host has
                # no vms of lg
                if lg.remove_vm_by_uuid(_uuid, _host.name) is True:
                    lg.last_update = time.time()

                # Remove lg from host's membership if lg does not
                # have the host
                if _host.remove_membership(lg) is True:
                    _host.last_update = time.time()

            elif isinstance(_host, HostGroup):
                if self._check_group_type(lg.group_type):
                    if lgk.split(":")[0] == _host.host_type:
                        if lg.remove_vm_by_uuid(_uuid, _host.name) is True:
                            lg.last_update = time.time()

                        if _host.remove_membership(lg) is True:
                            _host.last_update = time.time()

            if self._check_group_type(lg.group_type):
                if len(lg.vm_list) == 0:
                    del self.logical_groups[lgk]

        if isinstance(_host, Host) and _host.host_group is not None:
            self.remove_vm_by_uuid_from_logical_groups(_host.host_group, _uuid)
        elif (isinstance(_host, HostGroup) and
              _host.parent_resource is not None):
            self.remove_vm_by_uuid_from_logical_groups(_host.parent_resource,
                                                       _uuid)

    def clean_none_vms_from_logical_groups(self, _host):
        """Clean vms with status none from logical groups."""
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
                if self._check_group_type(lg.group_type):
                    if lgk.split(":")[0] == _host.host_type:
                        if lg.clean_none_vms(_host.name) is True:
                            lg.last_update = time.time()

                        if _host.remove_membership(lg) is True:
                            _host.last_update = time.time()

            if self._check_group_type(lg.group_type):
                if len(lg.vm_list) == 0:
                    del self.logical_groups[lgk]

        if isinstance(_host, Host) and _host.host_group is not None:
            self.clean_none_vms_from_logical_groups(_host.host_group)
        elif (isinstance(_host, HostGroup) and
              _host.parent_resource is not None):
            self.clean_none_vms_from_logical_groups(_host.parent_resource)

    def update_uuid_in_logical_groups(self, _h_uuid, _uuid, _host):
        """Update uuid in lgs and update lg last update time."""
        for lgk in _host.memberships.keys():
            lg = self.logical_groups[lgk]

            if isinstance(_host, Host):
                if lg.update_uuid(_h_uuid, _uuid, _host.name) is True:
                    lg.last_update = time.time()
            elif isinstance(_host, HostGroup):
                if self._check_group_type(lg.group_type):
                    if lgk.split(":")[0] == _host.host_type:
                        if lg.update_uuid(_h_uuid, _uuid, _host.name) is True:
                            lg.last_update = time.time()

        if isinstance(_host, Host) and _host.host_group is not None:
            self.update_uuid_in_logical_groups(
                _h_uuid, _uuid, _host.host_group)
        elif (isinstance(_host, HostGroup) and
              _host.parent_resource is not None):
            self.update_uuid_in_logical_groups(_h_uuid, _uuid,
                                               _host.parent_resource)

    def update_h_uuid_in_logical_groups(self, _h_uuid, _uuid, _host):
        """Update orchestration id in lgs and update lg last update time."""
        for lgk in _host.memberships.keys():
            lg = self.logical_groups[lgk]

            if isinstance(_host, Host):
                if lg.update_h_uuid(_h_uuid, _uuid, _host.name):
                    lg.last_update = time.time()
            elif isinstance(_host, HostGroup):
                if self._check_group_type(lg.group_type):
                    if lgk.split(":")[0] == _host.host_type:
                        if lg.update_h_uuid(_h_uuid, _uuid, _host.name):
                            lg.last_update = time.time()

        if isinstance(_host, Host) and _host.host_group is not None:
            self.update_h_uuid_in_logical_groups(_h_uuid, _uuid,
                                                 _host.host_group)
        elif (isinstance(_host, HostGroup) and
              _host.parent_resource is not None):
            self.update_h_uuid_in_logical_groups(_h_uuid, _uuid,
                                                 _host.parent_resource)

    def compute_avail_resources(self, hk, host):
        """Compute avail resources for host.

        This function computes ram, cpu and disk allocation ratios for
        the passed in host. Then uses data to compute avail memory, disk
        and vCPUs.
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
        """Return flavor according to name passed in."""
        flavor = None

        if _id in self.flavors.keys():
            flavor = self.flavors[_id]
        else:
            for _, f in self.flavors.iteritems():
                if f.flavor_id == _id:
                    flavor = f
                    break

        if flavor is not None:
            if flavor.status != "enabled":
                flavor = None

        return flavor

    def _check_group_type(self, type):
        return type in ['EX', 'AFF', 'DIV']
