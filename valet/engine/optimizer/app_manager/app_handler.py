#!/bin/python


import json
import operator
import time

from valet.engine.optimizer.app_manager.app_topology import AppTopology


class AppHistory(object):
    '''Data container for scheduling decisions.'''

    def __init__(self, _key):
        self.decision_key = _key
        self.host = None
        self.result = None
        self.timestamp = None


class AppHandler(object):
    '''Handler class for all requested applications.'''

    def __init__(self, _placement_handler, _metadata, _resource, _db, _config, _logger):
        self.phandler = _placement_handler
        self.resource = _resource
        self.db = _db

        self.metadata = _metadata

        self.config = _config
        self.logger = _logger

        self.apps = {}   # key= stack_id, value = Contain AppTopology instance
        self.max_app_cache = 500
        self.min_app_cache = 100

        self.decision_history = {}
        self.max_decision_history = 5000
        self.min_decision_history = 1000

    def check_history(self, _app):
        '''Check if 'create' or 'replan' is determined already.'''

        stack_id = _app["stack_id"]
        action = _app["action"]

        decision_key = None
        if action == "create":
            decision_key = stack_id + ":" + action + ":none"
        elif action == "replan":
            decision_key = stack_id + ":" + action + ":" + _app["resource_id"]
        else:
            return (None, None)

        if decision_key in self.decision_history.keys():
            return (decision_key, self.decision_history[decision_key].result)
        else:
            return (decision_key, None)

    def record_history(self, _decision_key, _result):
        '''Record an app placement decision.'''

        decision_key_element_list = _decision_key.split(":")

        action = decision_key_element_list[1]
        if action == "create" or action == "replan":
            if len(self.decision_history) > self.max_decision_history:
                self._flush_decision_history()
            app_history = AppHistory(_decision_key)
            app_history.result = _result
            app_history.timestamp = time.time()
            self.decision_history[_decision_key] = app_history

    def _flush_decision_history(self):
        '''Unload app placement decisions.'''

        count = 0
        num_of_removes = len(self.decision_history) - self.min_decision_history

        remove_item_list = []
        for decision in (sorted(self.decision_history.values(), key=operator.attrgetter('timestamp'))):
            remove_item_list.append(decision.decision_key)
            count += 1
            if count == num_of_removes:
                break

        for dk in remove_item_list:
            del self.decision_history[dk]

    def _flush_app_cache(self):
        '''Unload app topologies.'''

        count = 0
        num_of_removes = len(self.apps) - self.min_app_cache

        remove_item_list = []
        for app in (sorted(self.apps.values(), key=operator.attrgetter('timestamp_scheduled'))):
            remove_item_list.append(app.app_id)
            count += 1
            if count == num_of_removes:
                break

        for appk in remove_item_list:
            del self.apps[appk]

    def set_app(self, _app):
        '''Validate app placement request and extract info for placement decision.'''

        app_topology = AppTopology(self.phandler, self.resource, self.db, self.logger)
        app_topology.init_app(_app)
        if app_topology.status != "success":
            self.logger.error(app_topology.status)
            return app_topology

        self.logger.info("got '" + app_topology.action + "' for app = " + app_topology.app_id)

        if app_topology.action == "ping":
            pass

        # For stack-creation or single vm creation (ad-hoc) requests
        elif app_topology.action == "create":
            if self._set_vm_flavor_properties(app_topology) is False:
                self.logger.error(app_topology.status)
                return app_topology

            if app_topology.set_app_topology_properties(_app) is False:
                if app_topology.status == "success":
                    return None
                else:
                    self.logger.error(app_topology.status)
                    return app_topology

            self.logger.debug("TEST: done setting stack properties")

            if app_topology.parse_app_topology() is False:
                self.logger.error(app_topology.status)
                return app_topology

            self.logger.debug("TEST: done parsing stack")

        # For migration recommandation request or re-scheduling prior placement due to conflict
        elif app_topology.action == "replan" or app_topology.action == "migrate":
            (placements, groups) = self.get_placements(app_topology)
            if placements is None:
                return None
            elif len(placements) == 0:
                return app_topology
            app_topology.placements = placements
            app_topology.groups = groups

            self.logger.debug("TEST: done getting stack")

            if app_topology.set_app_topology_properties(_app) is False:
                if app_topology.status == "success":
                    return None
                else:
                    self.logger.error(app_topology.status)
                    return app_topology

            self.logger.debug("TEST: done setting stack properties")

            if app_topology.parse_app_topology() is False:
                self.logger.error(app_topology.status)
                return app_topology

            self.logger.debug("TEST: done parsing stack")

        # For the confirmation with physical uuid of scheduling decision match
        elif app_topology.action == "identify":
            (placements, groups) = self.get_placements(app_topology)
            if placements is None:
                return None
            elif len(placements) == 0:
                return app_topology
            app_topology.placements = placements
            app_topology.groups = groups

            self.logger.debug("TEST: done getting stack")

        # For stack-update request
        elif app_topology.action == "update":
            if self._set_vm_flavor_properties(app_topology) is False:
                self.logger.error(app_topology.status)
                return app_topology

            (old_placements, old_groups) = self.get_placements(app_topology)
            if old_placements is None:
                return None

            if "original_resources" in _app.keys():
                if len(old_placements) > 0:
                    self.logger.warn("original stack info already exists")
                else:
                    old_placements = _app["original_resources"]

            if len(old_placements) == 0:
                if app_topology.status == "success":
                    app_topology.status = "failed"
                return app_topology

            self.logger.debug("TEST: done getting old stack")

            for rk, r in old_placements.iteritems():
                if r["type"] == "OS::Nova::Server":
                    if "resource_id" in r.keys():
                        uuid = r["resource_id"]
                        placement = self.phandler.get_placement(uuid)
                        if placement is None:
                            return None
                        elif placement.uuid == "none":
                            self.logger.warn("vm (" + rk + ") in original stack missing (deleted?)")
                            app_topology.delete_placement(rk)
                            continue

                        if placement.stack_id is None or placement.stack_id == "none" or \
                           placement.stack_id != app_topology.app_id:
                            self.logger.warn("unknown stack in valet record")
                            self.phandler.update_placement(uuid, stack_id=app_topology.app_id, orch_id=rk)

                        if self._change_meta(rk, r, app_topology.placements) is True:
                            self.phandler.update_placement(uuid, state="rebuilding")
                            self.phandler.set_original_host(uuid)

                        app_topology.update_placement_vm_host(rk, placement.host)
                    else:
                        self.logger.warn("vm (" + rk + ") in original stack does not have id")

            if old_groups is not None and len(old_groups) > 0:
                for gk, g in old_groups.iteritems():
                    if "host" in g.keys():
                        app_topology.update_placement_group_host(gk, g["host"])

            self.logger.debug("TEST: done setting stack update")

            if app_topology.set_app_topology_properties(_app) is False:
                if app_topology.status == "success":
                    return None
                else:
                    self.logger.error(app_topology.status)
                    return app_topology

            for rk, host_info in app_topology.old_vm_map.iteritems():
                old = old_placements[rk]
                vcpus = old["properties"]["vcpus"]
                mem = old["properties"]["mem"]
                local_volume = old["properties"]["local_volume"]
                if host_info[1] != vcpus or host_info[2] != mem or host_info[3] != local_volume:
                    app_topology.old_vm_map[rk] = (host_info[0], vcpus, mem, local_volume)

            self.logger.debug("TEST: done setting stack properties")

            if app_topology.parse_app_topology() is False:
                self.logger.error(app_topology.status)
                return app_topology

            self.logger.debug("TEST: done getting stack")

        return app_topology

    def _set_vm_flavor_properties(self, _app_topology):
        '''Set flavor's properties.'''

        for rk, r in _app_topology.placements.iteritems():
            if r["type"] == "OS::Nova::Server":
                flavor = self.resource.get_flavor(r["properties"]["flavor"])
                if flavor is None:
                    self.logger.warn("not exist flavor (" + r["properties"]["flavor"] + ") and try to refetch")

                    if not self.metadata.set_flavors():
                        _app_topology.status = "failed to read flavors from nova"
                        return False
                    flavor = self.resource.get_flavor(r["properties"]["flavor"])
                    if flavor is None:
                        _app_topology.status = "net exist flavor (" + r["properties"]["flavor"] + ")"
                        return False

                r["properties"]["vcpus"] = flavor.vCPUs
                r["properties"]["mem"] = flavor.mem_cap
                r["properties"]["local_volume"] = flavor.disk_cap

                if len(flavor.extra_specs) > 0:
                    extra_specs = {}
                    for mk, mv in flavor.extra_specs.iteritems():
                        extra_specs[mk] = mv
                    r["properties"]["extra_specs"] = extra_specs

        return True

    def _change_meta(self, _rk, _r, _placements):
        '''Check if image or flavor is changed in the update request.'''
        if _rk in _placements.keys():
            r = _placements[_rk]
            if r["properties"]["flavor"] != _r["properties"]["flavor"]:
                if "vcpus" not in r["properties"].keys():
                    flavor = self.resource.get_flavor(r["properties"]["flavor"])
                    r["properties"]["vcpus"] = flavor.vCPUs
                    r["properties"]["mem"] = flavor.mem_cap
                    r["properties"]["local_volume"] = flavor.disk_cap
                return True
            if r["properties"]["image"] != _r["properties"]["image"]:
                return True
        return False

    def get_placements(self, _app_topology):
        '''Get prior stack/app placements info from db or cache.'''

        (placements, groups) = self.get_stack(_app_topology.app_id)

        if placements is None:
            return (None, None)
        elif len(placements) == 0:
            _app_topology.status = "no app/stack record"
            return ({}, {})

        return (placements, groups)

    def get_stack(self, _stack_id):
        '''Get stack info from db or cache.'''

        placements = {}
        groups = {}

        if _stack_id in self.apps.keys():
            placements = self.apps[_stack_id].placements
            groups = self.apps[_stack_id].groups
            self.logger.debug("hit stack cache")
        else:
            stack = self.db.get_stack(_stack_id)
            if stack is None:
                return (None, None)
            elif len(stack) == 0:
                return ({}, {})
            placements = stack["resources"]
            if "groups" in stack.keys() and stack["groups"] is not None:
                groups = stack["groups"]

        self.logger.debug("TEST: current placements")
        self.logger.debug(json.dumps(placements, indent=4))
        if groups is not None and len(groups) > 0:
            self.logger.debug("TEST: current groups")
            self.logger.debug(json.dumps(groups, indent=4))

        return (placements, groups)

    def store_app(self, _app_topology):
        '''Store and cache app placement results.'''

        if _app_topology.action == "ping":
            return True

        _app_topology.timestamp_scheduled = self.resource.current_timestamp

        if not _app_topology.store_app():
            return False

        if len(self.apps) > self.max_app_cache:
            self._flush_app_cache()
        self.apps[_app_topology.app_id] = _app_topology

        self.phandler.flush_cache()

        return True

    def update_stack(self, _stack_id, orch_id=None, uuid=None, host=None):
        '''Update the uuid or host of vm in stack in db and cache.'''

        (placements, groups) = self.get_stack(_stack_id)
        if placements is None:
            return (None, None)
        elif len(placements) == 0:
            return ("none", "none")

        placement = None
        if orch_id is not None:
            if orch_id in placements.keys():
                placement = placements[orch_id]
        elif uuid is not None:
            for rk, r in placements.iteritems():
                if "resource_id" in r.keys() and uuid == r["resource_id"]:
                    placement = r
                    break

        if placement is not None:
            if uuid is not None:
                placement["resource_id"] = uuid
            if host is not None:
                placement["properties"]["host"] = host

            if not self.db.update_stack(_stack_id, orch_id=orch_id, uuid=uuid, host=host, time=time.time()):
                return (None, None)

            return (placement["resource_id"], placement["properties"]["host"])
        else:
            return ("none", "none")

    def delete_from_stack(self, _stack_id, orch_id=None, uuid=None):
        '''Delete a placement from stack in db and cache.'''

        if _stack_id in self.apps.keys():
            app_topology = self.apps[_stack_id]

            if orch_id is not None:
                del app_topology.placements[orch_id]
                app_topology.timestamp_scheduled = time.time()
            elif uuid is not None:
                pk = None
                for rk, r in app_topology.placements.iteritems():
                    if "resource_id" in r.keys() and uuid == r["resource_id"]:
                        pk = rk
                        break
                if pk is not None:
                    del app_topology.placements[pk]
                    app_topology.timestamp_scheduled = time.time()

        if not self.db.delete_placement_from_stack(_stack_id, orch_id=orch_id, uuid=uuid, time=time.time()):
            return False
        return True
