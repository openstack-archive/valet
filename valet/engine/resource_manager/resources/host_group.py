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

# from valet.engine.optimizer.app_manager.group import LEVEL
from valet.engine.optimizer.app_manager.app_topology_base import LEVELS


class HostGroup(object):
    '''Container for host group (rack).'''

    def __init__(self, _id):
        self.name = _id

        # rack or cluster(e.g., power domain, zone)
        self.host_type = "rack"

        self.status = "enabled"

        # all available groups (e.g., aggregate) in this group
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

        self.parent_resource = None      # e.g., datacenter
        self.child_resources = {}        # e.g., hosting servers

        # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)
        self.vm_list = []

        self.last_update = 0

    def init_resources(self):
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
        for lgk in self.memberships.keys():
            lg = self.memberships[lgk]
            if (lg.group_type == "EX" or lg.group_type == "AFF" or
               lg.group_type == "DIV"):
                level = lg.name.split(":")[0]
                if (LEVELS.index(level) < LEVELS.index(self.host_type) or
                   self.name not in lg.vms_per_host.keys()):
                    del self.memberships[lgk]
            else:
                del self.memberships[lgk]

    def remove_membership(self, _lg):
        cleaned = False

        if (_lg.group_type == "EX" or _lg.group_type == "AFF" or
           _lg.group_type == "DIV"):
            if self.name not in _lg.vms_per_host.keys():
                del self.memberships[_lg.name]
                cleaned = True

        return cleaned

    def check_availability(self):
        if self.status == "enabled":
            return True
        else:
            return False

    def get_json_info(self):
        membership_list = []
        for lgk in self.memberships.keys():
            membership_list.append(lgk)

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
                'parent': self.parent_resource.name,
                'children': child_list,
                'vm_list': self.vm_list,
                'last_update': self.last_update}
