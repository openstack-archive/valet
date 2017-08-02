#!/bin/python


class Host(object):
    '''Container for compute host.'''

    def __init__(self, _name):
        self.name = _name

        self.tag = []                    # mark if this is synch'ed by multiple sources
        self.status = "enabled"
        self.state = "up"

        self.memberships = {}            # group (e.g., aggregate) this hosting server is involved in

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

        self.host_group = None           # e.g., rack

        self.vm_list = []                # a list of placed vms

        self.last_update = 0

    def clean_memberships(self):
        '''Remove from memberships.'''

        cleaned = False

        for lgk in self.memberships.keys():
            lg = self.memberships[lgk]
            if self.name not in lg.vms_per_host.keys():
                del self.memberships[lgk]
                cleaned = True

        return cleaned

    def remove_membership(self, _lg):
        '''Remove a membership. '''

        cleaned = False

        if _lg.group_type == "EX" or _lg.group_type == "AFF" or _lg.group_type == "DIV":
            if self.name not in _lg.vms_per_host.keys():
                del self.memberships[_lg.name]
                cleaned = True

        return cleaned

    def check_availability(self):
        '''Check if host is available.'''
        if self.status == "enabled" and self.state == "up" and ("nova" in self.tag) and ("infra" in self.tag):
            return True
        else:
            return False

    def get_vm_info(self, orch_id=None, uuid=None):
        '''Get vm info.'''

        vm_info = None

        if orch_id is not None and orch_id != "none":
            for v_info in self.vm_list:
                if v_info["orch_id"] == orch_id:
                    vm_info = v_info
                    break

        if vm_info is None:
            if uuid is not None and uuid != "none":
                for v_info in self.vm_list:
                    if v_info["uuid"] == uuid:
                        vm_info = v_info
                        break

        return vm_info

    def get_uuid(self, _orch_id):
        uuid = None

        for vm_info in self.vm_list:
            if vm_info["orch_id"] == _orch_id:
                uuid = vm_info["uuid"]
                break

        return uuid

    def exist_vm(self, orch_id=None, uuid=None):
        '''Check if vm is located in this host.'''

        exist = False

        if orch_id is not None and orch_id != "none":
            for vm_info in self.vm_list:
                if vm_info["orch_id"] == orch_id:
                    exist = True
                    break

        if not exist:
            if uuid is not None and uuid != "none":
                for vm_info in self.vm_list:
                    if vm_info["uuid"] == uuid:
                        exist = True
                        break

        return exist

    def remove_vm(self, orch_id=None, uuid=None):
        '''Remove vm from this host.'''

        success = False

        if orch_id is not None and orch_id != "none":
            for vm_info in self.vm_list:
                if vm_info["orch_id"] == orch_id:
                    self.vm_list.remove(vm_info)
                    success = True
                    break

        if not success:
            if uuid is not None and uuid != "none":
                for vm_info in self.vm_list:
                    if vm_info["uuid"] == uuid:
                        self.vm_list.remove(vm_info)
                        success = True
                        break

        return success

    def update_uuid(self, _orch_id, _uuid):
        '''Update a vm to include uuid.'''

        success = False

        for vm_info in self.vm_list:
            if vm_info["orch_id"] == _orch_id:
                vm_info["uuid"] = _uuid
                success = True
                break

        return success

    def update_orch_id(self, _orch_id, _uuid):
        success = False

        for vm_info in self.vm_list:
            if vm_info["uuid"] == _uuid:
                vm_info["orch_id"] = _orch_id
                success = True
                break

        return success

    def compute_avail_vCPUs(self, _overcommit_ratio, _standby_ratio):
        self.vCPUs = self.original_vCPUs * _overcommit_ratio * (1.0 - _standby_ratio)

        self.avail_vCPUs = self.vCPUs - self.vCPUs_used

    def compute_avail_mem(self, _overcommit_ratio, _standby_ratio):
        self.mem_cap = self.original_mem_cap * _overcommit_ratio * (1.0 - _standby_ratio)

        used_mem_mb = self.original_mem_cap - self.free_mem_mb

        self.avail_mem_cap = self.mem_cap - used_mem_mb

    def compute_avail_disk(self, _overcommit_ratio, _standby_ratio):
        self.local_disk_cap = self.original_local_disk_cap * _overcommit_ratio * (1.0 - _standby_ratio)

        free_disk_cap = self.free_disk_gb
        if self.disk_available_least > 0:
            free_disk_cap = min(self.free_disk_gb, self.disk_available_least)

        used_disk_cap = self.original_local_disk_cap - free_disk_cap

        self.avail_local_disk_cap = self.local_disk_cap - used_disk_cap

    def get_json_info(self):
        membership_list = []
        for lgk in self.memberships.keys():
            membership_list.append(lgk)

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
                'parent': self.host_group.name,
                'vm_list': self.vm_list,
                'last_update': self.last_update}
