#!/bin/python

from valet.engine.optimizer.app_manager.app_topology_parser import Parser
from valet.engine.optimizer.app_manager.vgroup import VGroup
from valet.engine.optimizer.app_manager.vm import VM


class AppTopology(object):
    '''Container to deliver the status of request.'''

    def __init__(self, _placement_handler, _resource, _db, _logger):
        self.app_id = None           # stack_id
        self.app_name = None
        self.action = None           # create, update, identify, replan, migrate, ping
        self.timestamp_scheduled = 0

        # stack resources
        self.placements = None
        self.groups = None

        self.phandler = _placement_handler
        self.resource = _resource
        self.db = _db

        # For search
        self.vgroups = {}              # key = orch_id, value = VGroup instance containing sub-groups
        self.vms = {}                  # key = orch_id, value = VM instance
        self.old_vm_map = {}           # key = orch_id, value = current placement info
        self.planned_vm_map = {}       # key = orch_id, value = current host
        self.candidate_list_map = {}   # key = orch_id, value = candidate hosts
        self.id_map = {}               # key = orch_id, value = physical uuid

        self.parser = Parser()

        # For placement optimization
        self.total_CPU = 0
        self.total_mem = 0
        self.total_local_vol = 0
        self.optimization_priority = None

        self.logger = _logger

        self.status = "success"

    def init_app(self, _app):
        '''Validate and init app request info.'''

        if "action" in _app.keys():
            self.action = _app["action"]
        else:
            self.status = "no action type in request"
            return

        if "stack_id" in _app.keys():
            self.app_id = _app["stack_id"]
        else:
            self.status = "no id in request"
            return

        if "application_name" in _app.keys():
            self.app_name = _app["application_name"]
        else:
            self.app_name = "none"

        if self.action == "create" or self.action == "update":
            if "resources" in _app.keys():
                self.placements = _app["resources"]
            else:
                self.status = "no resources in request action = " + self.action
                return
            if "groups" in _app.keys():
                self.groups = _app["groups"]

        if self.action in ("identify", "replan", "migrate"):
            if "resource_id" in _app.keys():
                if "orchestration_id" in _app.keys():
                    self.id_map[_app["orchestration_id"]] = _app["resource_id"]
                else:
                    self.id_map[_app["resource_id"]] = _app["resource_id"]
            else:
                self.status = "no physical uuid in request action = " + self.action
                return

    def set_app_topology_properties(self, _app):
        '''Set app properties.'''

        if self.action == "create" and "locations" in _app.keys() and len(_app["locations"]) > 0:
            if len(_app["resources"]) == 1:
                # Indicate this is an ad-hoc request
                self.candidate_list_map[_app["resources"].keys()[0]] = _app["locations"]

        for rk, r in self.placements.iteritems():
            if r["type"] == "OS::Nova::Server":
                if self.action == "replan":
                    if rk == _app["orchestration_id"]:
                        self.candidate_list_map[rk] = _app["locations"]
                    else:
                        if "resource_id" in r.keys():
                            placement = self.phandler.get_placement(r["resource_id"])
                            if placement is None:
                                return False
                            elif placement.uuid == "none":
                                self.status = "no record for placement for vm = " + rk
                                return False
                            if placement.state not in ("rebuilding", "migrating"):
                                self.planned_vm_map[rk] = r["properties"]["host"]

                elif self.action == "update":
                    if "resource_id" in r.keys():
                        placement = self.phandler.get_placement(r["resource_id"])
                        if placement is None:
                            return False
                        elif placement.uuid == "none":
                            self.status = "no record for placement for vm = " + rk
                            return False
                        if placement.state not in ("rebuilding", "migrating"):
                            self.planned_vm_map[rk] = r["properties"]["host"]

                elif self.action == "create":
                    if "locations" in r.keys() and len(r["locations"]) > 0:
                        # Indicate this is an ad-hoc request
                        self.candidate_list_map[rk] = r["locations"]

                elif self.action == "migrate":
                    if "resource_id" in r.keys():
                        if r["resource_id"] == _app["resource_id"]:
                            not_candidate_list = []
                            not_candidate_list.append(r["properties"]["host"])
                            if "excluded_hosts" in _app.keys():
                                for h in _app["excluded_hosts"]:
                                    if h != r["properties"]["host"]:
                                        not_candidate_list.append(h)
                            candidate_list = [hk for hk in self.resource.hosts.keys()
                                              if hk not in not_candidate_list]
                            self.candidate_list_map[rk] = candidate_list
                        else:
                            self.planned_vm_map[rk] = r["properties"]["host"]

                if "host" in r["properties"].keys():
                    host = r["properties"]["host"]
                    vcpus = 0
                    mem = 0
                    local_volume = 0
                    if "vcpus" in r["properties"].keys():
                        vcpus = int(r["properties"]["vcpus"])
                    if "mem" in r["properties"].keys():
                        mem = int(r["properties"]["mem"])
                    if "local_volume" in r["properties"].keys():
                        local_volume = int(r["properties"]["local_volume"])
                    self.old_vm_map[rk] = (host, vcpus, mem, local_volume)

        if self.action == "replan" or self.action == "migrate":
            if len(self.candidate_list_map) == 0:
                self.status = "no target vm found for " + self.action
                return False

        return True

    def parse_app_topology(self):
        '''Extract info from stack input for search.'''

        (self.vgroups, self.vms) = self.parser.set_topology(self.app_id, self.placements, self.groups)
        if len(self.vgroups) == 0 and len(self.vms) == 0:
            self.status = "parse error while " + self.action + " for " + self.app_id + ": " + self.parser.status
            return False

        return True

    def set_weight(self):
        '''Set relative weight of each vms and groups.'''

        for _, vm in self.vms.iteritems():
            self._set_vm_weight(vm)
        for _, vg in self.vgroups.iteritems():
            self._set_vm_weight(vg)

        for _, vg in self.vgroups.iteritems():
            self._set_vgroup_resource(vg)

        for _, vg in self.vgroups.iteritems():
            self._set_vgroup_weight(vg)

    def _set_vm_weight(self, _v):
        '''Set relative weight of each vm against available resource amount.'''

        if isinstance(_v, VGroup):
            for _, sg in _v.subvgroups.iteritems():
                self._set_vm_weight(sg)
        else:
            if self.resource.CPU_avail > 0:
                _v.vCPU_weight = float(_v.vCPUs) / float(self.resource.CPU_avail)
            else:
                _v.vCPU_weight = 1.0
            self.total_CPU += _v.vCPUs

            if self.resource.mem_avail > 0:
                _v.mem_weight = float(_v.mem) / float(self.resource.mem_avail)
            else:
                _v.mem_weight = 1.0
            self.total_mem += _v.mem

            if self.resource.local_disk_avail > 0:
                _v.local_volume_weight = float(_v.local_volume_size) / float(self.resource.local_disk_avail)
            else:
                if _v.local_volume_size > 0:
                    _v.local_volume_weight = 1.0
                else:
                    _v.local_volume_weight = 0.0
            self.total_local_vol += _v.local_volume_size

    def _set_vgroup_resource(self, _vg):
        '''Sum up amount of resources of vms for each affinity group.'''
        if isinstance(_vg, VM):
            return
        for _, sg in _vg.subvgroups.iteritems():
            self._set_vgroup_resource(sg)
            _vg.vCPUs += sg.vCPUs
            _vg.mem += sg.mem
            _vg.local_volume_size += sg.local_volume_size

    def _set_vgroup_weight(self, _vgroup):
        '''Set relative weight of each affinity group against available resource amount.'''

        if self.resource.CPU_avail > 0:
            _vgroup.vCPU_weight = float(_vgroup.vCPUs) / float(self.resource.CPU_avail)
        else:
            if _vgroup.vCPUs > 0:
                _vgroup.vCPU_weight = 1.0
            else:
                _vgroup.vCPU_weight = 0.0

        if self.resource.mem_avail > 0:
            _vgroup.mem_weight = float(_vgroup.mem) / float(self.resource.mem_avail)
        else:
            if _vgroup.mem > 0:
                _vgroup.mem_weight = 1.0
            else:
                _vgroup.mem_weight = 0.0

        if self.resource.local_disk_avail > 0:
            _vgroup.local_volume_weight = float(_vgroup.local_volume_size) / float(self.resource.local_disk_avail)
        else:
            if _vgroup.local_volume_size > 0:
                _vgroup.local_volume_weight = 1.0
            else:
                _vgroup.local_volume_weight = 0.0

        for _, svg in _vgroup.subvgroups.iteritems():
            if isinstance(svg, VGroup):
                self._set_vgroup_weight(svg)

    def set_optimization_priority(self):
        '''Determine the optimization priority among different types of resources.'''

        if len(self.vgroups) == 0 and len(self.vms) == 0:
            return

        app_CPU_weight = -1
        if self.resource.CPU_avail > 0:
            app_CPU_weight = float(self.total_CPU) / float(self.resource.CPU_avail)
        else:
            if self.total_CPU > 0:
                app_CPU_weight = 1.0
            else:
                app_CPU_weight = 0.0

        app_mem_weight = -1
        if self.resource.mem_avail > 0:
            app_mem_weight = float(self.total_mem) / float(self.resource.mem_avail)
        else:
            if self.total_mem > 0:
                app_mem_weight = 1.0
            else:
                app_mem_weight = 0.0

        app_local_vol_weight = -1
        if self.resource.local_disk_avail > 0:
            app_local_vol_weight = float(self.total_local_vol) / float(self.resource.local_disk_avail)
        else:
            if self.total_local_vol > 0:
                app_local_vol_weight = 1.0
            else:
                app_local_vol_weight = 0.0

        opt = [("cpu", app_CPU_weight),
               ("mem", app_mem_weight),
               ("lvol", app_local_vol_weight)]

        self.optimization_priority = sorted(opt, key=lambda resource: resource[1], reverse=True)

    def get_placement_uuid(self, _orch_id):
        '''Get the physical uuid for vm if available.'''
        if "resource_id" in self.placements[_orch_id].keys():
            return self.placements[_orch_id]["resource_id"]
        else:
            return "none"

    def get_placement_host(self, _orch_id):
        '''Get the determined host name for vm if available.'''
        if "host" in self.placements[_orch_id]["properties"].keys():
            return self.placements[_orch_id]["properties"]["host"]
        else:
            return "none"

    def delete_placement(self, _orch_id):
        '''Delete the placement from stack.'''

        uuid = self.get_placement_uuid(_orch_id)
        if uuid != "none":
            if not self.phandler.delete_placement(uuid):
                return False

        if _orch_id in self.placements.keys():
            del self.placements[_orch_id]

        return True

    def update_placement_vm_host(self, _v_id, _host):
        '''Update host info for vm.'''
        if _v_id in self.placements.keys():
            self.placements[_v_id]["properties"]["host"] = _host
            if "locations" in self.placements[_v_id].keys():
                del self.placements[_v_id]["locations"]

    def update_placement_group_host(self, _g_id, _host):
        '''Update host info in affinity group.'''
        if _g_id in self.groups.keys():
            self.groups[_g_id]["host"] = _host

    def update_placement_state(self, _v_id, host=None):
        '''Update state and host of vm deployment.'''

        placement = self.placements[_v_id]

        self.logger.debug("TEST: update state of orch_id = " + _v_id)

        if self.action == "replan":
            if _v_id == self.id_map.keys()[0]:
                uuid = self.id_map[_v_id]
                if "resource_id" in placement.keys():
                    if not self._update_placement_state(uuid, host, "planned", self.action):
                        return False
                else:
                    placement["resource_id"] = uuid
                    if self.phandler.insert_placement(uuid, self.app_id, host, _v_id, "planned") is None:
                        return False
            else:
                if _v_id not in self.planned_vm_map.keys():
                    if "resource_id" in placement.keys():
                        uuid = placement["resource_id"]
                        if not self._update_placement_state(uuid, host, "planning", self.action):
                            return False

        elif self.action == "identify":
            uuid = self.id_map[_v_id]
            host = placement["properties"]["host"]
            if "resource_id" in placement.keys():
                if not self._update_placement_state(uuid, host, "planned", self.action):
                    return False
            else:
                placement["resource_id"] = uuid
                if self.phandler.insert_placement(uuid, self.app_id, host, _v_id, "planned") is None:
                    return False

        elif self.action == "update":
            if _v_id not in self.planned_vm_map.keys():
                if "resource_id" in placement.keys():
                    uuid = placement["resource_id"]
                    if not self._update_placement_state(uuid, host, "planning", self.action):
                        return False

        elif self.action == "create" and len(self.candidate_list_map) > 0:  # ad-hoc
            placement["resource_id"] = _v_id
            if self.phandler.insert_placement(_v_id, self.app_id, host, _v_id, "planned") is None:
                return False

        elif self.action == "migrate":
            if _v_id not in self.planned_vm_map.keys():
                if "resource_id" in placement.keys():
                    uuid = placement["resource_id"]
                    if not self._update_placement_state(uuid, host, "planning", self.action):
                        return False

        return True

    def _update_placement_state(self, _uuid, _host, _phase, _action):
        '''Determine new state depending on phase (scheduling, confirmed) and action.'''

        placement = self.phandler.get_placement(_uuid)
        if placement is None or placement.uuid == "none":
            self.status = "no placement found for update"
            return False

        new_state = None
        if _phase == "planning":
            if _action == "migrate":
                new_state = "migrating"
                self.phandler.set_original_host(_uuid)
            else:
                if placement.state in ("rebuilding", "migrating"):
                    if placement.original_host != _host:
                        new_state = "migrating"
                    else:
                        new_state = "rebuilding"
        elif _phase == "planned":
            if placement.state in ("rebuilding", "migrating"):
                if placement.original_host != _host:
                    new_state = "migrate"
                else:
                    new_state = "rebuild"
            else:
                if _action == "identify":
                    new_state = "rebuild"
                elif _action == "replan":
                    new_state = "migrate"

        self.phandler.update_placement(_uuid, host=_host, state=new_state)

        return True

    def store_app(self):
        '''Store this app to db with timestamp.'''

        stack_data = {}
        stack_data["stack_id"] = self.app_id
        stack_data["timestamp"] = self.timestamp_scheduled
        stack_data["action"] = self.action
        stack_data["resources"] = self.placements
        stack_data["groups"] = self.groups

        if not self.db.store_stack(stack_data):
            return False

        return True
