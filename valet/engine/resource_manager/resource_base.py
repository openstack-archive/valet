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

"""Resource Base.

File contains resource datatype objects from base type of a flavor and
builds all the way up to a datacenter object.
"""

from valet.engine.optimizer.app_manager.app_topology_base import LEVELS


class Datacenter(object):
    """Datacenter Class.

    This object represents a datacenter. It contains all memberships or
    logical groups in the datacenter, all resources available, placed vms,
    and more throughout the datacenter.
    """

    def __init__(self, _name):
        """Init Datacenter object."""
        self.name = _name

        self.region_code_list = []

        self.status = "enabled"

        # all available logical groups (e.g., aggregate) in the datacenter
        self.memberships = {}

        self.vCPUs = 0
        self.original_vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0                 # MB
        self.original_mem_cap = 0
        self.avail_mem_cap = 0
        self.local_disk_cap = 0          # GB, ephemeral
        self.original_local_disk_cap = 0
        self.avail_local_disk_cap = 0

        self.root_switches = {}
        self.storages = {}

        self.resources = {}

        # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)
        self.vm_list = []

        # a list of placed volumes
        self.volume_list = []

        self.last_update = 0
        self.last_link_update = 0

    def init_resources(self):
        """Init datacenter resources to 0."""
        self.vCPUs = 0
        self.original_vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0                 # MB
        self.original_mem_cap = 0
        self.avail_mem_cap = 0
        self.local_disk_cap = 0          # GB, ephemeral
        self.original_local_disk_cap = 0
        self.avail_local_disk_cap = 0

    def get_json_info(self):
        """Return JSON info for datacenter object."""
        membership_list = []
        for lgk in self.memberships.keys():
            membership_list.append(lgk)

        switch_list = []
        for sk in self.root_switches.keys():
            switch_list.append(sk)

        storage_list = []
        for shk in self.storages.keys():
            storage_list.append(shk)

        child_list = []
        for ck in self.resources.keys():
            child_list.append(ck)

        return {'status': self.status,
                'name': self.name,
                'region_code_list': self.region_code_list,
                'membership_list': membership_list,
                'vCPUs': self.vCPUs,
                'original_vCPUs': self.original_vCPUs,
                'avail_vCPUs': self.avail_vCPUs,
                'mem': self.mem_cap,
                'original_mem': self.original_mem_cap,
                'avail_mem': self.avail_mem_cap,
                'local_disk': self.local_disk_cap,
                'original_local_disk': self.original_local_disk_cap,
                'avail_local_disk': self.avail_local_disk_cap,
                'switch_list': switch_list,
                'storage_list': storage_list,
                'children': child_list,
                'vm_list': self.vm_list,
                'volume_list': self.volume_list,
                'last_update': self.last_update,
                'last_link_update': self.last_link_update}


# data container for rack or cluster
class HostGroup(object):
    """Class for Host Group Object.

    This Class represents a group of hosts. If a single host is a single server
    then host group is a rack or cluster of servers. This class contains all
    memberships and resources for the group of hosts.
    """

    def __init__(self, _id):
        """Init for Host Group Class."""
        self.name = _id

        # rack or cluster(e.g., power domain, zone)
        self.host_type = "rack"

        self.status = "enabled"

        # all available logical groups (e.g., aggregate) in this group
        self.memberships = {}

        self.vCPUs = 0
        self.original_vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0                 # MB
        self.original_mem_cap = 0
        self.avail_mem_cap = 0
        self.local_disk_cap = 0          # GB, ephemeral
        self.original_local_disk_cap = 0
        self.avail_local_disk_cap = 0

        self.switches = {}               # ToRs
        self.storages = {}

        self.parent_resource = None      # e.g., datacenter
        self.child_resources = {}        # e.g., hosting servers

        # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)
        self.vm_list = []

        # a list of placed volumes
        self.volume_list = []

        self.last_update = 0
        self.last_link_update = 0

    def init_resources(self):
        """Init all host group resources to 0."""
        self.vCPUs = 0
        self.original_vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0                 # MB
        self.original_mem_cap = 0
        self.avail_mem_cap = 0
        self.local_disk_cap = 0          # GB, ephemeral
        self.original_local_disk_cap = 0
        self.avail_local_disk_cap = 0

    def init_memberships(self):
        """Init Host Group memberships."""
        for lgk in self.memberships.keys():
            lg = self.memberships[lgk]
            if lg.group_type == "EX" or lg.group_type == "AFF" or \
                lg.group_type == "DIV":
                level = lg.name.split(":")[0]
                if LEVELS.index(level) < LEVELS.index(self.host_type) or \
                    self.name not in lg.vms_per_host.keys():
                    del self.memberships[lgk]
            else:
                del self.memberships[lgk]

    def remove_membership(self, _lg):
        """Return True if membership to group _lg removed."""
        cleaned = False

        if _lg.group_type == "EX" or _lg.group_type == "AFF" or \
            _lg.group_type == "DIV":
            if self.name not in _lg.vms_per_host.keys():
                del self.memberships[_lg.name]
                cleaned = True

        return cleaned

    def check_availability(self):
        """Return True if Host Group status is 'enabled'."""
        if self.status == "enabled":
            return True
        else:
            return False

    def get_json_info(self):
        """Return JSON info for Host Group object."""
        membership_list = []
        for lgk in self.memberships.keys():
            membership_list.append(lgk)

        switch_list = []
        for sk in self.switches.keys():
            switch_list.append(sk)

        storage_list = []
        for shk in self.storages.keys():
            storage_list.append(shk)

        child_list = []
        for ck in self.child_resources.keys():
            child_list.append(ck)

        return {'status': self.status,
                'host_type': self.host_type,
                'membership_list': membership_list,
                'vCPUs': self.vCPUs,
                'original_vCPUs': self.original_vCPUs,
                'avail_vCPUs': self.avail_vCPUs,
                'mem': self.mem_cap,
                'original_mem': self.original_mem_cap,
                'avail_mem': self.avail_mem_cap,
                'local_disk': self.local_disk_cap,
                'original_local_disk': self.original_local_disk_cap,
                'avail_local_disk': self.avail_local_disk_cap,
                'switch_list': switch_list,
                'storage_list': storage_list,
                'parent': self.parent_resource.name,
                'children': child_list,
                'vm_list': self.vm_list,
                'volume_list': self.volume_list,
                'last_update': self.last_update,
                'last_link_update': self.last_link_update}


class Host(object):
    """Class for Host Object.

    This class is for a Host Object, imagine a server. This means
    information about the groups the host is a part of, all the hardware
    parameters (vCPUs, local disk, memory) as well as the list of vms and
    volumes placed on the host.
    """

    def __init__(self, _name):
        """Init for Host object."""
        self.name = _name

        # mark if this is synch'ed by multiple sources
        self.tag = []
        self.status = "enabled"
        self.state = "up"

        # logical group (e.g., aggregate) this hosting server is involved in
        self.memberships = {}

        self.vCPUs = 0
        self.original_vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0                 # MB
        self.original_mem_cap = 0
        self.avail_mem_cap = 0
        self.local_disk_cap = 0          # GB, ephemeral
        self.original_local_disk_cap = 0
        self.avail_local_disk_cap = 0

        self.vCPUs_used = 0
        self.free_mem_mb = 0
        self.free_disk_gb = 0
        self.disk_available_least = 0

        self.switches = {}               # leaf
        self.storages = {}

        self.host_group = None           # e.g., rack

        # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)
        self.vm_list = []

        # a list of placed volumes
        self.volume_list = []

        self.last_update = 0
        self.last_link_update = 0

    def clean_memberships(self):
        """Return True if host cleaned from logical group membership."""
        cleaned = False

        for lgk in self.memberships.keys():
            lg = self.memberships[lgk]
            if self.name not in lg.vms_per_host.keys():
                del self.memberships[lgk]
                cleaned = True

        return cleaned

    def remove_membership(self, _lg):
        """Return True if host removed from logical group _lg passed in."""
        cleaned = False

        if _lg.group_type == "EX" or _lg.group_type == "AFF" or \
            _lg.group_type == "DIV":
            if self.name not in _lg.vms_per_host.keys():
                del self.memberships[_lg.name]
                cleaned = True

        return cleaned

    def check_availability(self):
        """Return True if host is up, enabled and tagged as nova infra."""
        if self.status == "enabled" and self.state == "up" and \
                ("nova" in self.tag) and ("infra" in self.tag):
            return True
        else:
            return False

    def get_uuid(self, _h_uuid):
        """Return uuid of vm with matching orchestration id(_h_uuid)."""
        uuid = None

        for vm_id in self.vm_list:
            if vm_id[0] == _h_uuid:
                uuid = vm_id[2]
                break

        return uuid

    def exist_vm_by_h_uuid(self, _h_uuid):
        """Return True if vm with orchestration id(_h_uuid) exists on host."""
        exist = False

        for vm_id in self.vm_list:
            if vm_id[0] == _h_uuid:
                exist = True
                break

        return exist

    def exist_vm_by_uuid(self, _uuid):
        """Return True if vm with physical id(_uuid) exists on host."""
        exist = False

        for vm_id in self.vm_list:
            if vm_id[2] == _uuid:
                exist = True
                break

        return exist

    def remove_vm_by_h_uuid(self, _h_uuid):
        """Return True if vm removed with matching _h_uuid."""
        success = False

        for vm_id in self.vm_list:
            if vm_id[0] == _h_uuid:
                self.vm_list.remove(vm_id)
                success = True
                break

        return success

    def remove_vm_by_uuid(self, _uuid):
        """Return True if vm removed with matching _uuid."""
        success = False

        for vm_id in self.vm_list:
            if vm_id[2] == _uuid:
                self.vm_list.remove(vm_id)
                success = True
                break

        return success

    def update_uuid(self, _h_uuid, _uuid):
        """Return True if vm physical id updated."""
        success = False

        vm_name = "none"
        for vm_id in self.vm_list:
            if vm_id[0] == _h_uuid:
                vm_name = vm_id[1]
                self.vm_list.remove(vm_id)
                success = True
                break

        if success is True:
            vm_id = (_h_uuid, vm_name, _uuid)
            self.vm_list.append(vm_id)

        return success

    def update_h_uuid(self, _h_uuid, _uuid):
        """Return True if vm orchestration id (_h_uuid) updated."""
        success = False

        vm_name = "none"
        for vm_id in self.vm_list:
            if vm_id[2] == _uuid:
                vm_name = vm_id[1]
                self.vm_list.remove(vm_id)
                success = True
                break

        if success is True:
            vm_id = (_h_uuid, vm_name, _uuid)
            self.vm_list.append(vm_id)

        return success

    def compute_avail_vCPUs(self, _overcommit_ratio, _standby_ratio):
        """Calc avail_vCPUs by calculating vCPUs and subtracting in use."""
        self.vCPUs = \
            self.original_vCPUs * _overcommit_ratio * (1.0 - _standby_ratio)

        self.avail_vCPUs = self.vCPUs - self.vCPUs_used

    def compute_avail_mem(self, _overcommit_ratio, _standby_ratio):
        """Calc avail_mem by calculating mem_cap and subtract used mem."""
        self.mem_cap = \
            self.original_mem_cap * _overcommit_ratio * (1.0 - _standby_ratio)

        used_mem_mb = self.original_mem_cap - self.free_mem_mb

        self.avail_mem_cap = self.mem_cap - used_mem_mb

    def compute_avail_disk(self, _overcommit_ratio, _standby_ratio):
        """Calc avail_disk by calc local_disk_cap and subtract used disk."""
        self.local_disk_cap = \
            self.original_local_disk_cap * \
            _overcommit_ratio * \
            (1.0 - _standby_ratio)

        free_disk_cap = self.free_disk_gb
        if self.disk_available_least > 0:
            free_disk_cap = min(self.free_disk_gb, self.disk_available_least)

        used_disk_cap = self.original_local_disk_cap - free_disk_cap

        self.avail_local_disk_cap = self.local_disk_cap - used_disk_cap

    def get_json_info(self):
        """Return JSON info for Host object."""
        membership_list = []
        for lgk in self.memberships.keys():
            membership_list.append(lgk)

        switch_list = []
        for sk in self.switches.keys():
            switch_list.append(sk)

        storage_list = []
        for shk in self.storages.keys():
            storage_list.append(shk)

        return {'tag': self.tag, 'status': self.status, 'state': self.state,
                'membership_list': membership_list,
                'vCPUs': self.vCPUs,
                'original_vCPUs': self.original_vCPUs,
                'avail_vCPUs': self.avail_vCPUs,
                'mem': self.mem_cap,
                'original_mem': self.original_mem_cap,
                'avail_mem': self.avail_mem_cap,
                'local_disk': self.local_disk_cap,
                'original_local_disk': self.original_local_disk_cap,
                'avail_local_disk': self.avail_local_disk_cap,
                'vCPUs_used': self.vCPUs_used,
                'free_mem_mb': self.free_mem_mb,
                'free_disk_gb': self.free_disk_gb,
                'disk_available_least': self.disk_available_least,
                'switch_list': switch_list,
                'storage_list': storage_list,
                'parent': self.host_group.name,
                'vm_list': self.vm_list,
                'volume_list': self.volume_list,
                'last_update': self.last_update,
                'last_link_update': self.last_link_update}


class LogicalGroup(object):
    """Logical Group class.

    This class contains info about grouped vms, such as metadata when placing
    nodes, list of placed vms, list of placed volumes and group type.
    """

    def __init__(self, _name):
        """Init Logical Group object."""
        self.name = _name

        # AGGR, AZ, INTG, EX, DIV, or AFF
        self.group_type = "AGGR"

        self.status = "enabled"

        # any metadata to be matched when placing nodes
        self.metadata = {}

        # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)
        self.vm_list = []

        # a list of placed volumes
        self.volume_list = []

        # key = host_id, value = a list of placed vms
        self.vms_per_host = {}

        self.last_update = 0

    def exist_vm_by_h_uuid(self, _h_uuid):
        """Return True if h_uuid exist in vm_list as an orchestration_uuid."""
        exist = False

        for vm_id in self.vm_list:
            if vm_id[0] == _h_uuid:
                exist = True
                break

        return exist

    def exist_vm_by_uuid(self, _uuid):
        """Return True if uuid exist in vm_list as physical_uuid."""
        exist = False

        for vm_id in self.vm_list:
            if vm_id[2] == _uuid:
                exist = True
                break

        return exist

    def update_uuid(self, _h_uuid, _uuid, _host_id):
        """Return True if _uuid and/or _host_id successfully updated."""
        success = False

        vm_name = "none"
        for vm_id in self.vm_list:
            if vm_id[0] == _h_uuid:
                vm_name = vm_id[1]
                self.vm_list.remove(vm_id)
                success = True
                break

        if _host_id in self.vms_per_host.keys():
            for host_vm_id in self.vms_per_host[_host_id]:
                if host_vm_id[0] == _h_uuid:
                    self.vms_per_host[_host_id].remove(host_vm_id)
                    success = True
                    break

        if success is True:
            vm_id = (_h_uuid, vm_name, _uuid)
            self.vm_list.append(vm_id)
            if _host_id in self.vms_per_host.keys():
                self.vms_per_host[_host_id].append(vm_id)

        return success

    def update_h_uuid(self, _h_uuid, _uuid, _host_id):
        """Return True physical_uuid and/or _host_id successfully updated."""
        success = False

        vm_name = "none"
        for vm_id in self.vm_list:
            if vm_id[2] == _uuid:
                vm_name = vm_id[1]
                self.vm_list.remove(vm_id)
                success = True
                break

        if _host_id in self.vms_per_host.keys():
            for host_vm_id in self.vms_per_host[_host_id]:
                if host_vm_id[2] == _uuid:
                    self.vms_per_host[_host_id].remove(host_vm_id)
                    success = True
                    break

        if success is True:
            vm_id = (_h_uuid, vm_name, _uuid)
            self.vm_list.append(vm_id)
            if _host_id in self.vms_per_host.keys():
                self.vms_per_host[_host_id].append(vm_id)

        return success

    def add_vm_by_h_uuid(self, _vm_id, _host_id):
        """Return True if vm added with id _vm_id(orchestration id)."""
        success = False

        if self.exist_vm_by_h_uuid(_vm_id[0]) is False:
            self.vm_list.append(_vm_id)

            if self.group_type == "EX" or self.group_type == "AFF" or \
                self.group_type == "DIV":
                if _host_id not in self.vms_per_host.keys():
                    self.vms_per_host[_host_id] = []
            self.vms_per_host[_host_id].append(_vm_id)

            success = True

        return success

    def remove_vm_by_h_uuid(self, _h_uuid, _host_id):
        """Return True if vm removed with id _h_uuid(orchestration id)."""
        success = False

        for vm_id in self.vm_list:
            if vm_id[0] == _h_uuid:
                self.vm_list.remove(vm_id)
                success = True
                break

        if _host_id in self.vms_per_host.keys():
            for host_vm_id in self.vms_per_host[_host_id]:
                if host_vm_id[0] == _h_uuid:
                    self.vms_per_host[_host_id].remove(host_vm_id)
                    success = True
                    break

        if self.group_type == "EX" or self.group_type == "AFF" or \
            self.group_type == "DIV":
            if (_host_id in self.vms_per_host.keys()) and \
                len(self.vms_per_host[_host_id]) == 0:
                del self.vms_per_host[_host_id]

        return success

    def remove_vm_by_uuid(self, _uuid, _host_id):
        """Return True if vm with matching uuid found and removed."""
        success = False

        for vm_id in self.vm_list:
            if vm_id[2] == _uuid:
                self.vm_list.remove(vm_id)
                success = True
                break

        if _host_id in self.vms_per_host.keys():
            for host_vm_id in self.vms_per_host[_host_id]:
                if host_vm_id[2] == _uuid:
                    self.vms_per_host[_host_id].remove(host_vm_id)
                    success = True
                    break

        if self.group_type == "EX" or self.group_type == "AFF" or \
            self.group_type == "DIV":
            if (_host_id in self.vms_per_host.keys()) and \
                len(self.vms_per_host[_host_id]) == 0:
                del self.vms_per_host[_host_id]

        return success

    def clean_none_vms(self, _host_id):
        """Return True if vm's or host vm's removed with physical id none."""
        success = False

        for vm_id in self.vm_list:
            if vm_id[2] == "none":
                self.vm_list.remove(vm_id)
                success = True

        if _host_id in self.vms_per_host.keys():
            for vm_id in self.vms_per_host[_host_id]:
                if vm_id[2] == "none":
                    self.vms_per_host[_host_id].remove(vm_id)
                    success = True

        if self.group_type == "EX" or self.group_type == "AFF" or \
            self.group_type == "DIV":
            if (_host_id in self.vms_per_host.keys()) and \
                len(self.vms_per_host[_host_id]) == 0:
                del self.vms_per_host[_host_id]

        return success

    def get_json_info(self):
        """Return JSON info for Logical Group object."""
        return {'status': self.status,
                'group_type': self.group_type,
                'metadata': self.metadata,
                'vm_list': self.vm_list,
                'volume_list': self.volume_list,
                'vms_per_host': self.vms_per_host,
                'last_update': self.last_update}


class Switch(object):
    """Switch class."""

    def __init__(self, _switch_id):
        """Init Switch object."""
        self.name = _switch_id
        self.switch_type = "ToR"         # root, spine, ToR, or leaf

        self.status = "enabled"

        self.up_links = {}
        self.down_links = {}             # currently, not used
        self.peer_links = {}

        self.last_update = 0

    def get_json_info(self):
        """Return JSON info on Switch object."""
        ulinks = {}
        for ulk, ul in self.up_links.iteritems():
            ulinks[ulk] = ul.get_json_info()

        plinks = {}
        for plk, pl in self.peer_links.iteritems():
            plinks[plk] = pl.get_json_info()

        return {'status': self.status,
                'switch_type': self.switch_type,
                'up_links': ulinks,
                'peer_links': plinks,
                'last_update': self.last_update}


class Link(object):
    """Link class."""

    def __init__(self, _name):
        """Init Link object."""
        self.name = _name                # format: source + "-" + target
        self.resource = None             # switch beging connected to

        self.nw_bandwidth = 0            # Mbps
        self.avail_nw_bandwidth = 0

    def get_json_info(self):
        """Return JSON info on Link object."""
        return {'resource': self.resource.name,
                'bandwidth': self.nw_bandwidth,
                'avail_bandwidth': self.avail_nw_bandwidth}


class StorageHost(object):
    """Storage Host class."""

    def __init__(self, _name):
        """Init Storage Host object."""
        self.name = _name
        self.storage_class = None   # tiering, e.g., platinum, gold, silver

        self.status = "enabled"
        self.host_list = []

        self.disk_cap = 0   # GB
        self.avail_disk_cap = 0

        self.volume_list = []   # list of volume names placed in this host

        self.last_update = 0
        self.last_cap_update = 0

    def get_json_info(self):
        """Return JSON info on Storage Host object."""
        return {'status': self.status,
                'class': self.storage_class,
                'host_list': self.host_list,
                'disk': self.disk_cap,
                'avail_disk': self.avail_disk_cap,
                'volume_list': self.volume_list,
                'last_update': self.last_update,
                'last_cap_update': self.last_cap_update}


class Flavor(object):
    """Flavor class."""

    def __init__(self, _name):
        """Init flavor object."""
        self.name = _name
        self.flavor_id = None

        self.status = "enabled"

        self.vCPUs = 0
        self.mem_cap = 0        # MB
        self.disk_cap = 0       # including ephemeral (GB) and swap (MB)

        self.extra_specs = {}

        self.last_update = 0

    def get_json_info(self):
        """Return JSON info of Flavor Object."""
        return {'status': self.status,
                'flavor_id': self.flavor_id,
                'vCPUs': self.vCPUs,
                'mem': self.mem_cap,
                'disk': self.disk_cap,
                'extra_specs': self.extra_specs,
                'last_update': self.last_update}
