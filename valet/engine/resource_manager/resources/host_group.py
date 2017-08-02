#!/bin/python


from valet.engine.optimizer.app_manager.group import LEVEL


class HostGroup(object):
    '''Container for host group (rack).'''

    def __init__(self, _id):
        self.name = _id
        self.host_type = "rack"          # rack or cluster(e.g., power domain, zone)

        self.status = "enabled"

        self.memberships = {}            # all available groups (e.g., aggregate) in this group

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

        self.vm_list = []                # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)

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
            if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                level = lg.name.split(":")[0]
                if LEVEL.index(level) < LEVEL.index(self.host_type) or self.name not in lg.vms_per_host.keys():
                    del self.memberships[lgk]
            else:
                del self.memberships[lgk]

    def remove_membership(self, _lg):
        cleaned = False

        if _lg.group_type == "EX" or _lg.group_type == "AFF" or _lg.group_type == "DIV":
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
