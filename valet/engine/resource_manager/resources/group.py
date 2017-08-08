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


class Group(object):
    '''Container for groups.'''

    def __init__(self, _name):
        self.name = _name
        self.group_type = "AGGR"         # AGGR, AZ, INTG, EX, DIV, or AFF

        self.status = "enabled"

        # any metadata to be matched when placing nodes
        self.metadata = {}

        self.vm_list = []                # a list of placed vms

        # key = host_name, value = a list of placed vms
        self.vms_per_host = {}

        self.last_update = 0

    def exist_vm(self, orch_id=None, uuid=None):
        '''Check if the vm exists in this group.'''

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

    def exist_vm_in_host(self, _host_name, orch_id=None, uuid=None):
        '''Check if the vm exists in the host in this group.'''

        exist = False

        if _host_name in self.vms_per_host.keys():
            vm_list = self.vms_per_host[_host_name]

            if orch_id is not None and orch_id != "none":
                for vm_info in vm_list:
                    if vm_info["orch_id"] == orch_id:
                        exist = True
                        break

            if not exist:
                if uuid is not None and uuid != "none":
                    for vm_info in vm_list:
                        if vm_info["uuid"] == uuid:
                            exist = True
                            break

        return exist

    def update_uuid(self, _orch_id, _uuid, _host_name):
        '''Update a vm with uuid.'''

        success = False

        for vm_info in self.vm_list:
            if vm_info["orch_id"] == _orch_id:
                vm_info["uuid"] = _uuid
                success = True
                break

        if _host_name in self.vms_per_host.keys():
            for host_vm_info in self.vms_per_host[_host_name]:
                if host_vm_info["orch_id"] == _orch_id:
                    host_vm_info["uuid"] = _uuid
                    success = True
                    break

        return success

    def update_orch_id(self, _orch_id, _uuid, _host_name):
        '''Update a vm with orch_id.'''

        success = False

        for vm_info in self.vm_list:
            if vm_info["uuid"] == _uuid:
                vm_info["orch_id"] = _orch_id
                success = True
                break

        if _host_name in self.vms_per_host.keys():
            for host_vm_info in self.vms_per_host[_host_name]:
                if host_vm_info["uuid"] == _uuid:
                    host_vm_info["orch_id"] = _orch_id
                    success = True
                    break

        return success

    def add_vm(self, _vm_info, _host_name):
        '''Add vm to this group.'''

        if self.exist_vm(orch_id=_vm_info["orch_id"], uuid=_vm_info["uuid"]):
            self._remove_vm(orch_id=_vm_info["orch_id"], uuid=_vm_info["uuid"])

        self.vm_list.append(_vm_info)

        if self.exist_vm_in_host(_host_name, orch_id=_vm_info["orch_id"],
                                 uuid=_vm_info["uuid"]):
            self.remove_vm_from_host(_host_name, orch_id=_vm_info["orch_id"],
                                     uuid=_vm_info["uuid"])

        if (self.group_type == "EX" or self.group_type == "AFF" or
           self.group_type == "DIV"):
            if _host_name not in self.vms_per_host.keys():
                self.vms_per_host[_host_name] = []

        self.vms_per_host[_host_name].append(_vm_info)

        return True

    def remove_vm(self, _host_name, orch_id=None, uuid=None):
        '''Remove vm from this group.'''

        success = False

        success = self._remove_vm(orch_id, uuid)

        success = self.remove_vm_from_host(_host_name, orch_id, uuid)

        return success

    def _remove_vm(self, orch_id=None, uuid=None):
        '''Remove vm from this group.'''

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

    def remove_vm_from_host(self, _host_name, orch_id=None, uuid=None):
        '''Remove vm from the host of this group.'''

        success = False

        if orch_id is not None and orch_id != "none":
            if _host_name in self.vms_per_host.keys():
                for host_vm_info in self.vms_per_host[_host_name]:
                    if host_vm_info["orch_id"] == orch_id:
                        self.vms_per_host[_host_name].remove(host_vm_info)
                        success = True
                        break

        if not success:
            if uuid is not None and uuid != "none":
                if _host_name in self.vms_per_host.keys():
                    for host_vm_info in self.vms_per_host[_host_name]:
                        if host_vm_info["uuid"] == uuid:
                            self.vms_per_host[_host_name].remove(host_vm_info)
                            success = True
                            break

        if (self.group_type == "EX" or self.group_type == "AFF" or
           self.group_type == "DIV"):
            if ((_host_name in self.vms_per_host.keys()) and
               len(self.vms_per_host[_host_name]) == 0):
                del self.vms_per_host[_host_name]

        return success

    def get_json_info(self):
        '''Get group info as JSON format.'''

        return {'status': self.status,
                'group_type': self.group_type,
                'metadata': self.metadata,
                'vm_list': self.vm_list,
                'vms_per_host': self.vms_per_host,
                'last_update': self.last_update}
