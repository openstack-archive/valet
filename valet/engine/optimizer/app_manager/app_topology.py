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

"""App Topology."""

from valet.engine.optimizer.app_manager.app_topology_base import VM, VGroup
from valet.engine.optimizer.app_manager.app_topology_parser import Parser


class AppTopology(object):
    """App Topology Class.

    This class contains functions for parsing and setting each app, as well as
    calculating and setting optimization.
    """

    def __init__(self, _resource, _logger):
        """Init App Topology Class."""
        self.vgroups = {}
        self.vms = {}

        # for replan
        self.old_vm_map = {}
        self.planned_vm_map = {}
        self.candidate_list_map = {}

        # for migration-tip
        self.exclusion_list_map = {}

        self.resource = _resource
        self.logger = _logger

        # restriction of host naming convention
        high_level_allowed = True
        if "none" in self.resource.datacenter.region_code_list:
            high_level_allowed = False

        self.parser = Parser(high_level_allowed, self.logger)

        self.total_CPU = 0
        self.total_mem = 0
        self.total_local_vol = 0
        self.optimization_priority = None

        self.status = "success"

    def set_app_topology(self, _app_graph):
        """Set app topology (Parse and set each app).

        Set app topology by calling parser to determine vgroups,
        vms and volumes. Then return parsed stack_id, app_name and action.
        """
        (vgroups, vms) = self.parser.set_topology(_app_graph)

        if len(self.parser.candidate_list_map) > 0:
            self.candidate_list_map = self.parser.candidate_list_map

        if len(vgroups) == 0 and len(vms) == 0:
            self.status = self.parser.status
            return None

        # cumulate virtual resources
        for _, vgroup in vgroups.iteritems():
            self.vgroups[vgroup.uuid] = vgroup
        for _, vm in vms.iteritems():
            self.vms[vm.uuid] = vm

        return self.parser.stack_id, self.parser.application_name, \
            self.parser.action

    def set_weight(self):
        """Set weight of vms and vgroups."""
        for _, vm in self.vms.iteritems():
            self._set_vm_weight(vm)
        for _, vg in self.vgroups.iteritems():
            self._set_vm_weight(vg)

        for _, vg in self.vgroups.iteritems():
            self._set_vgroup_resource(vg)

        for _, vg in self.vgroups.iteritems():
            self._set_vgroup_weight(vg)

    def _set_vm_weight(self, _v):
        if isinstance(_v, VGroup):
            for _, sg in _v.subvgroups.iteritems():
                self._set_vm_weight(sg)
        else:
            if self.resource.CPU_avail > 0:
                _v.vCPU_weight = float(_v.vCPUs) / \
                    float(self.resource.CPU_avail)
            else:
                _v.vCPU_weight = 1.0
            self.total_CPU += _v.vCPUs

            if self.resource.mem_avail > 0:
                _v.mem_weight = float(_v.mem) / \
                    float(self.resource.mem_avail)
            else:
                _v.mem_weight = 1.0
            self.total_mem += _v.mem

            if self.resource.local_disk_avail > 0:
                _v.local_volume_weight = float(_v.local_volume_size) / \
                    float(self.resource.local_disk_avail)
            else:
                if _v.local_volume_size > 0:
                    _v.local_volume_weight = 1.0
                else:
                    _v.local_volume_weight = 0.0
            self.total_local_vol += _v.local_volume_size

    def _set_vgroup_resource(self, _vg):
        if isinstance(_vg, VM):
            return
        for _, sg in _vg.subvgroups.iteritems():
            self._set_vgroup_resource(sg)
            _vg.vCPUs += sg.vCPUs
            _vg.mem += sg.mem
            _vg.local_volume_size += sg.local_volume_size

    def _set_vgroup_weight(self, _vgroup):
        """Calculate weights for vgroup."""
        if self.resource.CPU_avail > 0:
            _vgroup.vCPU_weight = float(_vgroup.vCPUs) / \
                float(self.resource.CPU_avail)
        else:
            if _vgroup.vCPUs > 0:
                _vgroup.vCPU_weight = 1.0
            else:
                _vgroup.vCPU_weight = 0.0

        if self.resource.mem_avail > 0:
            _vgroup.mem_weight = float(_vgroup.mem) / \
                float(self.resource.mem_avail)
        else:
            if _vgroup.mem > 0:
                _vgroup.mem_weight = 1.0
            else:
                _vgroup.mem_weight = 0.0

        if self.resource.local_disk_avail > 0:
            _vgroup.local_volume_weight = float(_vgroup.local_volume_size) / \
                float(self.resource.local_disk_avail)
        else:
            if _vgroup.local_volume_size > 0:
                _vgroup.local_volume_weight = 1.0
            else:
                _vgroup.local_volume_weight = 0.0

        for _, svg in _vgroup.subvgroups.iteritems():
            if isinstance(svg, VGroup):
                self._set_vgroup_weight(svg)

    def set_optimization_priority(self):
        """Set Optimization Priority.

        This function calculates weights for bandwidth, cpu, memory, local
        and overall volume for an app. Then Sorts the results and sets
        optimization order accordingly.
        """
        if len(self.vgroups) == 0 and len(self.vms) == 0:
            return

        app_CPU_weight = -1
        if self.resource.CPU_avail > 0:
            app_CPU_weight = float(self.total_CPU) / \
                float(self.resource.CPU_avail)
        else:
            if self.total_CPU > 0:
                app_CPU_weight = 1.0
            else:
                app_CPU_weight = 0.0

        app_mem_weight = -1
        if self.resource.mem_avail > 0:
            app_mem_weight = float(self.total_mem) / \
                float(self.resource.mem_avail)
        else:
            if self.total_mem > 0:
                app_mem_weight = 1.0
            else:
                app_mem_weight = 0.0

        app_local_vol_weight = -1
        if self.resource.local_disk_avail > 0:
            app_local_vol_weight = float(self.total_local_vol) / \
                float(self.resource.local_disk_avail)
        else:
            if self.total_local_vol > 0:
                app_local_vol_weight = 1.0
            else:
                app_local_vol_weight = 0.0

        opt = [("cpu", app_CPU_weight),
               ("mem", app_mem_weight),
               ("lvol", app_local_vol_weight)]

        self.optimization_priority = sorted(opt,
                                            key=lambda resource: resource[1],
                                            reverse=True)
