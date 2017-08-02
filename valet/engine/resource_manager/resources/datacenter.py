#!/bin/python


class Datacenter(object):
    '''Container for datacenter resource.'''

    def __init__(self, _name):
        self.name = _name

        self.status = "enabled"

        self.memberships = {}            # all available groups (e.g., aggregate) in the datacenter

        self.vCPUs = 0
        self.original_vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0                 # MB
        self.original_mem_cap = 0
        self.avail_mem_cap = 0
        self.local_disk_cap = 0          # GB, ephemeral
        self.original_local_disk_cap = 0
        self.avail_local_disk_cap = 0

        self.resources = {}

        self.vm_list = []                # a list of placed vms

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

    def get_json_info(self):
        membership_list = []
        for lgk in self.memberships.keys():
            membership_list.append(lgk)

        child_list = []
        for ck in self.resources.keys():
            child_list.append(ck)

        return {'status': self.status,
                'name': self.name,
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
                'children': child_list,
                'vm_list': self.vm_list,
                'last_update': self.last_update}
