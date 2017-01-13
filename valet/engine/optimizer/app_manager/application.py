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

"""App."""


class App(object):
    """App Class.

    This class represents an app object that consists of the name and id of
    the app, as well as the status and vms/volumes/vgroups it belogns to.
    """

    def __init__(self, _app_id, _app_name, _action):
        """Init App."""
        self.app_id = _app_id
        self.app_name = _app_name

        self.request_type = _action   # create, update, or ping

        self.timestamp_scheduled = 0

        self.vgroups = {}
        self.vms = {}
        self.volumes = {}

        self.status = 'requested'  # Moved to "scheduled" (and then "placed")

    def add_vm(self, _vm, _host_name):
        """Add vm to app, set status to scheduled."""
        self.vms[_vm.uuid] = _vm
        self.vms[_vm.uuid].status = "scheduled"
        self.vms[_vm.uuid].host = _host_name

    def add_volume(self, _vol, _host_name):
        """Add volume to app, set status to scheduled."""
        self.vms[_vol.uuid] = _vol
        self.vms[_vol.uuid].status = "scheduled"
        self.vms[_vol.uuid].storage_host = _host_name

    def add_vgroup(self, _vg, _host_name):
        """Add vgroup to app, set status to scheduled."""
        self.vgroups[_vg.uuid] = _vg
        self.vgroups[_vg.uuid].status = "scheduled"
        self.vgroups[_vg.uuid].host = _host_name

    def get_json_info(self):
        """Return JSON info of App including vms, vols and vgs."""
        vms = {}
        for vmk, vm in self.vms.iteritems():
            vms[vmk] = vm.get_json_info()

        vols = {}
        for volk, vol in self.volumes.iteritems():
            vols[volk] = vol.get_json_info()

        vgs = {}
        for vgk, vg in self.vgroups.iteritems():
            vgs[vgk] = vg.get_json_info()

        return {'action': self.request_type,
                'timestamp': self.timestamp_scheduled,
                'stack_id': self.app_id,
                'name': self.app_name,
                'VMs': vms,
                'Volumes': vols,
                'VGroups': vgs}

    def log_in_info(self):
        """Return in info related to login (time of login, app name, etc)."""
        return {'action': self.request_type,
                'timestamp': self.timestamp_scheduled,
                'stack_id': self.app_id,
                'name': self.app_name}
