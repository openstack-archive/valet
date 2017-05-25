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

"""App Handler."""

import operator
import time

from valet.engine.optimizer.app_manager.app_topology import AppTopology
from valet.engine.optimizer.app_manager.app_topology_base import VM
from valet.engine.optimizer.app_manager.application import App


class AppHistory(object):

    def __init__(self, _key):
        self.decision_key = _key
        self.host = None
        self.result = None
        self.timestamp = None


class AppHandler(object):
    """App Handler Class.

    This class handles operations for the management of applications.
    Functions related to adding apps and adding/removing them from
    placement and updating topology info.
    """

    def __init__(self, _resource, _db, _config, _logger):
        """Init App Handler Class."""
        self.resource = _resource
        self.db = _db
        self.config = _config
        self.logger = _logger

        """ current app requested, a temporary copy """
        self.apps = {}

        self.decision_history = {}
        self.max_decision_history = 5000
        self.min_decision_history = 1000

        self.status = "success"

    # NOTE(GJ): do not cache migration decision
    def check_history(self, _app):
        stack_id = _app["stack_id"]
        action = _app["action"]

        if action == "create":
            decision_key = stack_id + ":" + action + ":none"
            if decision_key in self.decision_history.keys():
                return (decision_key,
                        self.decision_history[decision_key].result)
            else:
                return (decision_key, None)
        elif action == "replan":
            decision_key = stack_id + ":" + action + ":" + _app["orchestration_id"]
            if decision_key in self.decision_history.keys():
                return (decision_key,
                        self.decision_history[decision_key].result)
            else:
                return (decision_key, None)
        else:
            return (None, None)

    def put_history(self, _decision_key, _result):
        decision_key_list = _decision_key.split(":")
        action = decision_key_list[1]
        if action == "create" or action == "replan":
            app_history = AppHistory(_decision_key)
            app_history.result = _result
            app_history.timestamp = time.time()
            self.decision_history[_decision_key] = app_history

            if len(self.decision_history) > self.max_decision_history:
                self._clean_decision_history()

    def _clean_decision_history(self):
        count = 0
        num_of_removes = len(self.decision_history) - self.min_decision_history
        remove_item_list = []
        for decision in (sorted(self.decision_history.values(),
                         key=operator.attrgetter('timestamp'))):
            remove_item_list.append(decision.decision_key)
            count += 1
            if count == num_of_removes:
                break
        for dk in remove_item_list:
            if dk in self.decision_history.keys():
                del self.decision_history[dk]

    def add_app(self, _app):
        """Add app and set or regenerate topology, return updated topology."""
        self.apps.clear()

        app_topology = AppTopology(self.resource, self.logger)

        stack_id = None
        if "stack_id" in _app.keys():
            stack_id = _app["stack_id"]
        else:
            stack_id = "none"

        application_name = None
        if "application_name" in _app.keys():
            application_name = _app["application_name"]
        else:
            application_name = "none"

        action = _app["action"]
        if action == "ping":
            self.logger.info("got ping")
        elif action == "replan" or action == "migrate":
            re_app = self._regenerate_app_topology(stack_id, _app,
                                                   app_topology, action)
            if re_app is None:
                self.apps[stack_id] = None
                self.status = "cannot locate the original plan for stack = " + stack_id
                return None

            if action == "replan":
                self.logger.info("got replan: " + stack_id)
            elif action == "migrate":
                self.logger.info("got migration: " + stack_id)

            app_id = app_topology.set_app_topology(re_app)

            if app_id is None:
                self.logger.error(app_topology.status)
                self.status = app_topology.status
                self.apps[stack_id] = None
                return None
        else:
            app_id = app_topology.set_app_topology(_app)

            if len(app_topology.candidate_list_map) > 0:
                self.logger.info("got ad-hoc placement: " + stack_id)
            else:
                self.logger.info("got placement: " + stack_id)

            if app_id is None:
                self.logger.error(app_topology.status)
                self.status = app_topology.status
                self.apps[stack_id] = None
                return None

        new_app = App(stack_id, application_name, action)
        self.apps[stack_id] = new_app

        return app_topology

    def add_placement(self, _placement_map, _app_topology, _timestamp):
        """Change requested apps to scheduled and place them."""
        for v in _placement_map.keys():
            if self.apps[v.app_uuid].status == "requested":
                self.apps[v.app_uuid].status = "scheduled"
                self.apps[v.app_uuid].timestamp_scheduled = _timestamp

            if isinstance(v, VM):
                if self.apps[v.app_uuid].request_type == "replan":
                    if v.uuid in _app_topology.planned_vm_map.keys():
                        self.apps[v.app_uuid].add_vm(
                            v, _placement_map[v], "replanned")
                    else:
                        self.apps[v.app_uuid].add_vm(
                            v, _placement_map[v], "scheduled")
                    if v.uuid == _app_topology.candidate_list_map.keys()[0]:
                        self.apps[v.app_uuid].add_vm(
                            v, _placement_map[v], "replanned")
                else:
                    self.apps[v.app_uuid].add_vm(
                        v, _placement_map[v], "scheduled")
            # NOTE(GJ): do not handle Volume in this version
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
            pass

    def _store_app_placements(self):
        # NOTE(GJ): do not track application history in this version

        for appk, app in self.apps.iteritems():
            json_info = app.get_json_info()
            if self.db.add_app(appk, json_info) is False:
                return False

        return True

    def remove_placement(self):
        """Remove App from placement."""
        if self.db is not None:
            for appk, _ in self.apps.iteritems():
                if self.db.add_app(appk, None) is False:
                    self.logger.error("AppHandler: error while adding app "
                                      "info to MUSIC")

    def get_vm_info(self, _s_uuid, _h_uuid, _host):
        """Return vm_info from database."""
        vm_info = {}

        if _h_uuid is not None and _h_uuid != "none" and \
           _s_uuid is not None and _s_uuid != "none":
            vm_info = self.db.get_vm_info(_s_uuid, _h_uuid, _host)

        return vm_info

    def update_vm_info(self, _s_uuid, _h_uuid):
        if _h_uuid and _h_uuid != "none" and _s_uuid and _s_uuid != "none":
            return self.db.update_vm_info(_s_uuid, _h_uuid)

        return True

    def _regenerate_app_topology(self, _stack_id, _app, _app_topology, _action):
        re_app = {}

        old_app = self.db.get_app_info(_stack_id)
        if old_app is None:
            self.status = "error while getting old_app from MUSIC"
            self.logger.error(self.status)
            return None
        elif len(old_app) == 0:
            self.status = "cannot find the old app in MUSIC"
            self.logger.error(self.status)
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
                    elif vmk in _app["exclusions"]:
                        _app_topology.planned_vm_map[vmk] = vm["host"]
                    if vm["status"] == "replanned":
                        _app_topology.planned_vm_map[vmk] = vm["host"]
                elif _action == "migrate":
                    if vmk == _app["orchestration_id"]:
                        _app_topology.exclusion_list_map[vmk] = _app[
                            "excluded_hosts"]
                        if vm["host"] not in _app["excluded_hosts"]:
                            _app_topology.exclusion_list_map[vmk].append(
                                vm["host"])
                    else:
                        _app_topology.planned_vm_map[vmk] = vm["host"]

                _app_topology.old_vm_map[vmk] = (vm["host"], vm["cpus"],
                                                 vm["mem"], vm["local_volume"])

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
                    for divk, level_name in \
                            affinity["diversity_groups"].iteritems():
                        div_id = divk + ":" + level_name
                        if div_id not in diversity_groups.keys():
                            diversity_groups[div_id] = []
                        diversity_groups[div_id].append(gk)

                if len(affinity["exclusivity_groups"]) > 0:
                    for exk, level_name in \
                            affinity["exclusivity_groups"].iteritems():
                        ex_id = exk + ":" + level_name
                        if ex_id not in exclusivity_groups.keys():
                            exclusivity_groups[ex_id] = []
                        exclusivity_groups[ex_id].append(gk)

        for div_id, resource_list in diversity_groups.iteritems():
            divk_level_name = div_id.split(":")
            resources[divk_level_name[0]] = {}
            resources[divk_level_name[0]]["type"] = \
                "ATT::Valet::GroupAssignment"
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
