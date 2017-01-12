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

LEVELS = ["host", "rack", "cluster"]


class VGroup(object):

    def __init__(self, _app_uuid, _uuid):
        self.app_uuid = _app_uuid
        self.uuid = _uuid
        self.name = None

        self.status = "requested"

        self.vgroup_type = "AFF"       # Support Affinity group at this version
        self.level = None              # host, rack, or cluster

        self.survgroup = None          # where this vgroup belong to
        self.subvgroups = {}           # child vgroups

        self.vgroup_list = []          # a list of links to VMs or Volumes

        self.diversity_groups = {}     # cumulative diversity/exclusivity group
        self.exclusivity_groups = {}   # over this level. key=name, value=level

        self.availability_zone_list = []
        self.extra_specs_list = []     # cumulative extra_specs

        self.vCPUs = 0
        self.mem = 0                   # MB
        self.local_volume_size = 0     # GB
        self.volume_sizes = {}         # key = volume_class_name, value = size
        self.nw_bandwidth = 0          # Mbps
        self.io_bandwidth = 0          # Mbps

        self.vCPU_weight = -1
        self.mem_weight = -1
        self.local_volume_weight = -1
        self.volume_weight = -1        # averge of all storage classes
        self.bandwidth_weight = -1

        self.host = None

    def get_json_info(self):
        survgroup_id = None
        if self.survgroup is None:
            survgroup_id = "none"
        else:
            survgroup_id = self.survgroup.uuid

        subvgroup_list = []
        for vk in self.subvgroups.keys():
            subvgroup_list.append(vk)

        link_list = []
        for l in self.vgroup_list:
            link_list.append(l.get_json_info())

        return {'name': self.name,
                'status': self.status,
                'vgroup_type': self.vgroup_type,
                'level': self.level,
                'survgroup': survgroup_id,
                'subvgroup_list': subvgroup_list,
                'link_list': link_list,
                'diversity_groups': self.diversity_groups,
                'exclusivity_groups': self.exclusivity_groups,
                'availability_zones': self.availability_zone_list,
                'extra_specs_list': self.extra_specs_list,
                'cpus': self.vCPUs,
                'mem': self.mem,
                'local_volume': self.local_volume_size,
                'volumes': self.volume_sizes,
                'nw_bandwidth': self.nw_bandwidth,
                'io_bandwidth': self.io_bandwidth,
                'cpu_weight': self.vCPU_weight,
                'mem_weight': self.mem_weight,
                'local_volume_weight': self.local_volume_weight,
                'volume_weight': self.volume_weight,
                'bandwidth_weight': self.bandwidth_weight,
                'host': self.host}


class VM(object):

    def __init__(self, _app_uuid, _uuid):
        self.app_uuid = _app_uuid
        self.uuid = _uuid
        self.name = None

        self.status = "requested"

        self.survgroup = None          # VGroup where this vm belongs to

        self.volume_list = []          # a list of links to Volumes
        self.vm_list = []              # a list of links to VMs

        self.diversity_groups = {}
        self.exclusivity_groups = {}

        self.availability_zone = None
        self.extra_specs_list = []

        self.flavor = None
        self.vCPUs = 0
        self.mem = 0                  # MB
        self.local_volume_size = 0    # GB
        self.nw_bandwidth = 0
        self.io_bandwidth = 0

        self.vCPU_weight = -1
        self.mem_weight = -1
        self.local_volume_weight = -1
        self.bandwidth_weight = -1

        self.host = None              # where this vm is placed

    def get_json_info(self):
        survgroup_id = None
        if self.survgroup is None:
            survgroup_id = "none"
        else:
            survgroup_id = self.survgroup.uuid

        vm_list = []
        for vml in self.vm_list:
            vm_list.append(vml.get_json_info())

        vol_list = []
        for voll in self.volume_list:
            vol_list.append(voll.get_json_info())

        availability_zone = None
        if self.availability_zone is None:
            availability_zone = "none"
        else:
            availability_zone = self.availability_zone

        return {'name': self.name,
                'status': self.status,
                'survgroup': survgroup_id,
                'vm_list': vm_list,
                'volume_list': vol_list,
                'diversity_groups': self.diversity_groups,
                'exclusivity_groups': self.exclusivity_groups,
                'availability_zones': availability_zone,
                'extra_specs_list': self.extra_specs_list,
                'flavor': self.flavor,
                'cpus': self.vCPUs,
                'mem': self.mem,
                'local_volume': self.local_volume_size,
                'nw_bandwidth': self.nw_bandwidth,
                'io_bandwidth': self.io_bandwidth,
                'cpu_weight': self.vCPU_weight,
                'mem_weight': self.mem_weight,
                'local_volume_weight': self.local_volume_weight,
                'bandwidth_weight': self.bandwidth_weight,
                'host': self.host}


class Volume(object):

    def __init__(self, _app_uuid, _uuid):
        self.app_uuid = _app_uuid
        self.uuid = _uuid
        self.name = None

        self.status = "requested"

        self.volume_class = None

        self.survgroup = None         # where this vm belongs to

        self.vm_list = []             # a list of links to VMs

        self.diversity_groups = {}
        self.exclusivity_groups = {}

        self.volume_size = 0          # GB
        self.io_bandwidth = 0

        self.volume_weight = -1
        self.bandwidth_weight = -1

        self.storage_host = None

    def get_json_info(self):
        survgroup_id = None
        if self.survgroup is None:
            survgroup_id = "none"
        else:
            survgroup_id = self.survgroup.uuid

        volume_class = None
        if self.volume_class is None:
            volume_class = "none"
        else:
            volume_class = self.volume_class

        vm_list = []
        for vml in self.vm_list:
            vm_list.append(vml.get_json_info())

        return {'name': self.name,
                'status': self.status,
                'class': volume_class,
                'survgroup': survgroup_id,
                'vm_list': vm_list,
                'diversity_groups': self.diversity_groups,
                'exclusivity_groups': self.exclusivity_groups,
                'volume': self.volume_size,
                'io_bandwidth': self.io_bandwidth,
                'volume_weight': self.volume_weight,
                'bandwidth_weight': self.bandwidth_weight,
                'host': self.storage_host}


class VGroupLink(object):

    def __init__(self, _n):
        self.node = _n                # target VM or Volume
        self.nw_bandwidth = 0
        self.io_bandwidth = 0

    def get_json_info(self):
        return {'target': self.node.uuid,
                'nw_bandwidth': self.nw_bandwidth,
                'io_bandwidth': self.io_bandwidth}


class VMLink(object):

    def __init__(self, _n):
        self.node = _n                # target VM
        self.nw_bandwidth = 0         # Mbps

    def get_json_info(self):
        return {'target': self.node.uuid,
                'nw_bandwidth': self.nw_bandwidth}


class VolumeLink(object):

    def __init__(self, _n):
        self.node = _n                # target Volume
        self.io_bandwidth = 0         # Mbps

    def get_json_info(self):
        return {'target': self.node.uuid,
                'io_bandwidth': self.io_bandwidth}
