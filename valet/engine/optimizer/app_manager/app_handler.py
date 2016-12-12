# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Modified: Sep. 27, 2016


import json

from valet.engine.optimizer.app_manager.app_topology import AppTopology
from valet.engine.optimizer.app_manager.app_topology_base import VM
from valet.engine.optimizer.app_manager.application import App
from valet.engine.optimizer.util import util as util


class AppHandler(object):

    def __init__(self, _resource, _db, _config, _logger):
        self.resource = _resource
        self.db = _db
        self.config = _config
        self.logger = _logger

        ''' current app requested, a temporary copy '''
        self.apps = {}

        self.last_log_index = 0

        self.status = "success"

    def add_app(self, _app_data):
        self.apps.clear()

        app_topology = AppTopology(self.resource, self.logger)

        for app in _app_data:
            self.logger.debug("AppHandler: parse app")

            stack_id = None
            if "stack_id" in app.keys():
                stack_id = app["stack_id"]
            else:
                stack_id = "none"

            application_name = None
            if "application_name" in app.keys():
                application_name = app["application_name"]
            else:
                application_name = "none"

            action = app["action"]
            if action == "ping":
                self.logger.debug("AppHandler: got ping")
            elif action == "replan" or action == "migrate":
                re_app = self._regenerate_app_topology(stack_id, app, app_topology, action)
                if re_app is None:
                    self.apps[stack_id] = None
                    self.status = "cannot locate the original plan for stack = " + stack_id
                    return None

                if action == "replan":
                    self.logger.debug("AppHandler: got replan: " + stack_id)
                elif action == "migrate":
                    self.logger.debug("AppHandler: got migration: " + stack_id)

                app_id = app_topology.set_app_topology(re_app)

                if app_id is None:
                    self.logger.error("AppHandler: " + app_topology.status)
                    self.status = app_topology.status
                    self.apps[stack_id] = None
                    return None
            else:
                app_id = app_topology.set_app_topology(app)

                if app_id is None:
                    self.logger.error("AppHandler: " + app_topology.status)
                    self.status = app_topology.status
                    self.apps[stack_id] = None
                    return None

            new_app = App(stack_id, application_name, action)
            self.apps[stack_id] = new_app

        return app_topology

    def add_placement(self, _placement_map, _timestamp):
        for v in _placement_map.keys():
            if self.apps[v.app_uuid].status == "requested":
                self.apps[v.app_uuid].status = "scheduled"
                self.apps[v.app_uuid].timestamp_scheduled = _timestamp

            if isinstance(v, VM):
                self.apps[v.app_uuid].add_vm(v, _placement_map[v])
            # elif isinstance(v, Volume):
            #     self.apps[v.app_uuid].add_volume(v, _placement_map[v])
            else:
                if _placement_map[v] in self.resource.hosts.keys():
                    host = self.resource.hosts[_placement_map[v]]
                    if v.level == "host":
                        self.apps[v.app_uuid].add_vgroup(v, host.name)
                else:
                    hg = self.resource.host_groups[_placement_map[v]]
                    if v.level == hg.host_type:
                        self.apps[v.app_uuid].add_vgroup(v, hg.name)

        if self._store_app_placements() is False:
            # NOTE: ignore?
            pass

    def _store_app_placements(self):
        (app_logfile, last_index, mode) = util.get_last_logfile(
            self.config.app_log_loc, self.config.max_log_size, self.config.max_num_of_logs,
            self.resource.datacenter.name, self.last_log_index)
        self.last_log_index = last_index

        # TODO(GJ): error handling

        logging = open(self.config.app_log_loc + app_logfile, mode)

        for appk, app in self.apps.iteritems():
            json_log = app.log_in_info()
            log_data = json.dumps(json_log)

            logging.write(log_data)
            logging.write("\n")

        logging.close()

        self.logger.info("AppHandler: log app in " + app_logfile)

        if self.db is not None:
            for appk, app in self.apps.iteritems():
                json_info = app.get_json_info()
                if self.db.add_app(appk, json_info) is False:
                    return False

            if self.db.update_app_log_index(self.resource.datacenter.name, self.last_log_index) is False:
                return False

        return True

    def remove_placement(self):
        if self.db is not None:
            for appk, _ in self.apps.iteritems():
                if self.db.add_app(appk, None) is False:
                    self.logger.error("AppHandler: error while adding app info to MUSIC")
                    # NOTE: ignore?

    def get_vm_info(self, _s_uuid, _h_uuid, _host):
        vm_info = {}

        if _h_uuid is not None and _h_uuid != "none" and \
           _s_uuid is not None and _s_uuid != "none":
            vm_info = self.db.get_vm_info(_s_uuid, _h_uuid, _host)

        return vm_info

    def update_vm_info(self, _s_uuid, _h_uuid):
        s_uuid_exist = bool(_s_uuid is not None and _s_uuid != "none")
        h_uuid_exist = bool(_h_uuid is not None and _h_uuid != "none")
        if s_uuid_exist and h_uuid_exist:
            return self.db.update_vm_info(_s_uuid, _h_uuid)
        return True

    def _regenerate_app_topology(self, _stack_id, _app, _app_topology, _action):
        re_app = {}

        old_app = self.db.get_app_info(_stack_id)
        if old_app is None:
            self.status = "error while getting old_app from MUSIC"
            self.logger.error("AppHandler: " + self.status)
            return None
        elif len(old_app) == 0:
            self.status = "cannot find the old app in MUSIC"
            self.logger.error("AppHandler: " + self.status)
            return None

        re_app["action"] = "create"
        re_app["stack_id"] = _stack_id

        resources = {}
        diversity_groups = {}
        exclusivity_groups = {}

        if "VMs" in old_app.keys():
            for vmk, vm in old_app["VMs"].iteritems():
                resources[vmk] = {}
                resources[vmk]["name"] = vm["name"]
                resources[vmk]["type"] = "OS::Nova::Server"
                properties = {}
                properties["flavor"] = vm["flavor"]
                if vm["availability_zones"] != "none":
                    properties["availability_zone"] = vm["availability_zones"]
                resources[vmk]["properties"] = properties

                if len(vm["diversity_groups"]) > 0:
                    for divk, level_name in vm["diversity_groups"].iteritems():
                        div_id = divk + ":" + level_name
                        if div_id not in diversity_groups.keys():
                            diversity_groups[div_id] = []
                        diversity_groups[div_id].append(vmk)

                if len(vm["exclusivity_groups"]) > 0:
                    for exk, level_name in vm["exclusivity_groups"].iteritems():
                        ex_id = exk + ":" + level_name
                        if ex_id not in exclusivity_groups.keys():
                            exclusivity_groups[ex_id] = []
                        exclusivity_groups[ex_id].append(vmk)

                if _action == "replan":
                    if vmk == _app["orchestration_id"]:
                        _app_topology.candidate_list_map[vmk] = _app["locations"]

                        self.logger.debug("AppHandler: re-requested vm = " + vm["name"] + " in")
                        for hk in _app["locations"]:
                            self.logger.debug("    " + hk)

                    elif vmk in _app["exclusions"]:
                        _app_topology.planned_vm_map[vmk] = vm["host"]

                        self.logger.debug("AppHandler: exception from replan = " + vm["name"])

                elif _action == "migrate":
                    if vmk == _app["orchestration_id"]:
                        _app_topology.exclusion_list_map[vmk] = _app["excluded_hosts"]
                        if vm["host"] not in _app["excluded_hosts"]:
                            _app_topology.exclusion_list_map[vmk].append(vm["host"])
                    else:
                        _app_topology.planned_vm_map[vmk] = vm["host"]

                _app_topology.old_vm_map[vmk] = (vm["host"], vm["cpus"], vm["mem"], vm["local_volume"])

        if "VGroups" in old_app.keys():
            for gk, affinity in old_app["VGroups"].iteritems():
                resources[gk] = {}
                resources[gk]["type"] = "ATT::Valet::GroupAssignment"
                properties = {}
                properties["group_type"] = "affinity"
                properties["group_name"] = affinity["name"]
                properties["level"] = affinity["level"]
                properties["resources"] = []
                for r in affinity["subvgroup_list"]:
                    properties["resources"].append(r)
                resources[gk]["properties"] = properties

                if len(affinity["diversity_groups"]) > 0:
                    for divk, level_name in affinity["diversity_groups"].iteritems():
                        div_id = divk + ":" + level_name
                        if div_id not in diversity_groups.keys():
                            diversity_groups[div_id] = []
                        diversity_groups[div_id].append(gk)

                if len(affinity["exclusivity_groups"]) > 0:
                    for exk, level_name in affinity["exclusivity_groups"].iteritems():
                        ex_id = exk + ":" + level_name
                        if ex_id not in exclusivity_groups.keys():
                            exclusivity_groups[ex_id] = []
                        exclusivity_groups[ex_id].append(gk)

        # NOTE: skip pipes in this version

        for div_id, resource_list in diversity_groups.iteritems():
            divk_level_name = div_id.split(":")
            resources[divk_level_name[0]] = {}
            resources[divk_level_name[0]]["type"] = "ATT::Valet::GroupAssignment"
            properties = {}
            properties["group_type"] = "diversity"
            properties["group_name"] = divk_level_name[2]
            properties["level"] = divk_level_name[1]
            properties["resources"] = resource_list
            resources[divk_level_name[0]]["properties"] = properties

        for ex_id, resource_list in exclusivity_groups.iteritems():
            exk_level_name = ex_id.split(":")
            resources[exk_level_name[0]] = {}
            resources[exk_level_name[0]]["type"] = "ATT::Valet::GroupAssignment"
            properties = {}
            properties["group_type"] = "exclusivity"
            properties["group_name"] = exk_level_name[2]
            properties["level"] = exk_level_name[1]
            properties["resources"] = resource_list
            resources[exk_level_name[0]]["properties"] = properties

        re_app["resources"] = resources

        return re_app
