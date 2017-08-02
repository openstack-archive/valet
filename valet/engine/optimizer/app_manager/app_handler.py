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

from oslo_log import log

from valet.engine.optimizer.app_manager.app_topology import AppTopology

LOG = log.getLogger(__name__)


class AppHistory(object):
    """Data container for scheduling decisions."""

    def __init__(self, _key):
        self.decision_key = _key
        self.host = None
        self.result = None
        self.timestamp = None


class AppHandler(object):
    """
    App Handler Class.

    This class handles operations for the management of applications.
    Functions related to adding apps and adding/removing them from
    placement and updating topology info.
    """

    def __init__(self, _placement_handler, _metadata, _resource, _db, _config):
        """Init App Handler Class."""

        self.phandler = _placement_handler
        self.resource = _resource
        self.db = _db
        self.config = _config

        self.metadata = _metadata

        # current app requested, a temporary copy
        # key= stack_id, value = AppTopology instance
        self.apps = {}
        self.max_app_cache = 500
        self.min_app_cache = 100

        self.decision_history = {}
        self.max_decision_history = 5000
        self.min_decision_history = 1000

    def set_app(self, _app):
        """
        Validate app placement request and extract info for placement
        decision.
        """

        app_topology = AppTopology(self.phandler, self.resource, self.db)
        app_topology.init_app(_app)
        if app_topology.status != "success":
            LOG.error(app_topology.status)
            return app_topology

        LOG.info("Received {} for app {} ".format(app_topology.action,
                                                  app_topology.app_id))

        if app_topology.action == "create":
            return self._set_app_for_create(_app, app_topology)
        elif app_topology.action == "replan":
            return self._set_app_for_replan(_app, app_topology)
        elif app_topology.action == "migrate":
            return self._set_app_for_replan(_app, app_topology)
        elif app_topology.action == "identify":
            return self._set_app_for_identify(_app, app_topology)
        elif app_topology.action == "update":
            return self._set_app_for_update(_app, app_topology)

        return app_topology

    def _set_app_for_create(self, _app, _app_topology):
        """
        Set for stack-creation or single server creation (ad-hoc) requests.
        """

        if self._set_flavor_properties(_app_topology) is False:
            LOG.error(_app_topology.status)
            return _app_topology

        LOG.debug("done setting flavor properties")

        if _app_topology.set_app_topology_properties(_app) is False:
            if _app_topology.status == "success":
                return None
            else:
                LOG.error(_app_topology.status)
                return _app_topology

        # for case of ad-hoc create or update
        if len(_app_topology.candidate_list_map) > 0:
            # FIXME(gjung): the key might not be the uuid, but orch_id
            uuid = _app_topology.candidate_list_map.keys()[0]

            placement = self.phandler.get_placement(uuid)
            if placement is None:
                return None

            if placement.uuid != "none":
                LOG.info("change 'ad-hoc' to 'replan'")

                # FIXME(gjung):
                # if placement.stack_id and placement.orch_id
                #     if placement.stack_id == _app_topology.app_id
                #         then, this should be merged into the original stack
                #     otherwise, a seperate stack
                #         update placement.stack_id
                #         remove it from the original stack?
                #         update orch_id in resource status
                # else (i.e., pre-valet placement)

                self._set_app_for_ad_hoc_update(placement, _app_topology)
                if _app_topology.status is None:
                    return None
                elif _app_topology.status != "success":
                    LOG.error(_app_topology.status)
                    return _app_topology

            # NOTE(gjung): if placement does not exist,
            #    check if _app_topology.app_id exists
            #    then merge into the stack
            #    otherwise, a seperate stack

        LOG.debug("done setting app properties")

        if _app_topology.parse_app_topology() is False:
            if _app_topology.status == "success":
                return None
            else:
                LOG.error(_app_topology.status)
                return _app_topology

        LOG.debug("done parsing app")

        return _app_topology

    def _set_app_for_ad_hoc_update(self, _placement, _app_topology):
        "Set prior allocation info."

        if _placement.uuid not in _app_topology.stack["placements"].keys():
            _app_topology.status = "find unknown orch_id while ad-hoc update"
            return

        _app_topology.stack["placements"][_placement.uuid]["properties"]["host"] = _placement.host
        _app_topology.stack["placements"][_placement.uuid]["resource_id"] = _placement.uuid
        _app_topology.id_map[_placement.uuid] = _placement.uuid

        _app_topology.action = "replan"

        flavor_id = None
        if _placement.stack_id is None or _placement.stack_id == "none":
            if _placement.host in self.resource.hosts.keys():
                host = self.resource.hosts[_placement.host]
                vm_info = host.get_vm_info(uuid=_placement.uuid)
                if vm_info is not None:
                    if "flavor_id" in vm_info.keys():
                        flavor_id = vm_info["flavor_id"]
                else:
                    _app_topology.status = "missing vm while ad-hoc update"
                    return
            else:
                _app_topology.status = "missing host while ad-hoc update"
                return
        else:
            (old_placements, old_groups) = self.get_stack(_placement.stack_id)
            if old_placements is None:
                _app_topology.status = None
                return
            elif len(old_placements) == 0:
                _app_topology.status = "missing prior stack while ad-hoc updt."
                return

            flavor_id = old_placements[_placement.orch_id]["properties"]["flavor"]

        if flavor_id is None:
            _app_topology.status = "missing vm flavor info  while ad-hoc updt."
            return

        old_vm_alloc = {}
        old_vm_alloc["host"] = _placement.host

        (flavor, status) = self._get_flavor(flavor_id)
        if flavor is None:
            _app_topology.status = status
            return

        old_vm_alloc["vcpus"] = flavor.vCPUs
        old_vm_alloc["mem"] = flavor.mem_cap
        old_vm_alloc["local_volume"] = flavor.disk_cap

        _app_topology.old_vm_map[_placement.uuid] = old_vm_alloc

        self.phandler.update_placement(_placement.uuid,
                                       stack_id=_app_topology.app_id,
                                       orch_id=_placement.uuid,
                                       state='rebuilding')
        self.phandler.set_original_host(_placement.uuid)

    def _set_app_for_replan(self, _app, _app_topology):
        """
        Set for migration request or re-scheduling prior placement due to
        conflict.
        """

        (placements, groups) = self.get_placements(_app_topology)
        if placements is None:
            return None
        elif len(placements) == 0:
            return _app_topology

        _app_topology.stack["placements"] = placements
        _app_topology.stack["groups"] = groups

        LOG.debug("done getting stack")

        # check if mock id was used, then change to the real orch_id
        if "mock_id" in _app.keys():
            if _app["mock_id"] is not None and _app["mock_id"] != "none":
                status = self._change_orch_id(_app, _app_topology)
                if status != "success":
                    return _app_topology

                LOG.debug("done replacing mock id")

        if _app_topology.set_app_topology_properties(_app) is False:
            if _app_topology.status == "success":
                return None
            else:
                LOG.error(_app_topology.status)
                return _app_topology

        LOG.debug("done setting stack properties")

        if _app_topology.parse_app_topology() is False:
            if _app_topology.status == "success":
                return None
            else:
                LOG.error(_app_topology.status)
                return _app_topology

        LOG.debug("done parsing stack")

        return _app_topology

    def _set_app_for_identify(self, _app, _app_topology):
        """Set for the confirmation with physical uuid of scheduling decision
        match.
        """

        (placements, groups) = self.get_placements(_app_topology)
        if placements is None:
            return None
        elif len(placements) == 0:
            return _app_topology

        _app_topology.stack["placements"] = placements
        _app_topology.stack["groups"] = groups

        LOG.debug("done getting stack")

        # check if mock id was used, then change to the real orch_id
        if "mock_id" in _app.keys():
            if _app["mock_id"] is not None and _app["mock_id"] != "none":
                status = self._change_orch_id(_app, _app_topology)
                if status != "success":
                    return _app_topology

                LOG.debug("done replacing mock id")

        return _app_topology

    def _set_app_for_update(self, _app, _app_topology):
        """Set for stack-update request."""

        if self._set_flavor_properties(_app_topology) is False:
            LOG.error(_app_topology.status)
            return _app_topology

        LOG.debug("done setting vm properties")

        (old_placements, old_groups) = self.get_placements(_app_topology)
        if old_placements is None:
            return None

        if "original_resources" in _app.keys():
            if len(old_placements) == 0:
                old_placements = _app["original_resources"]

        if len(old_placements) == 0:
            if _app_topology.status == "success":
                _app_topology.status = "cannot find prior stack for update"
            return _app_topology

        LOG.debug("done getting old stack")

        # NOTE(gjung): old placements info can be stale.
        for rk, r in old_placements.iteritems():
            if r["type"] == "OS::Nova::Server":
                if "resource_id" in r.keys():
                    uuid = r["resource_id"]

                    placement = self.phandler.get_placement(uuid)
                    if placement is None:
                        return None
                    elif placement.uuid == "none":
                        LOG.warn("vm (" + rk + ") in original stack missing. "
                                 "Perhaps it was deleted?")

                        if rk in _app_topology.stack["placements"].keys():
                            del _app_topology.stack["placements"][rk]
                        continue

                    if rk in _app_topology.stack["placements"].keys():
                        if placement.stack_id is None or \
                           placement.stack_id == "none" or \
                           placement.stack_id != _app_topology.app_id:

                            if placement.stack_id is None or \
                               placement.stack_id == "none":
                                LOG.warn("stack id in valet record is unknown")
                            else:
                                LOG.warn("stack id in valet record is "
                                         "different")

                            curr_state = None
                            if placement.state is None or \
                               placement.state == "none":
                                curr_state = "created"
                            else:
                                curr_state = placement.state

                            self.phandler.update_placement(uuid,
                                                           stack_id=_app_topology.app_id,
                                                           orch_id=rk,
                                                           state=curr_state)

                        self._apply_meta_change(rk, r, _app_topology.stack["placements"])

                        _app_topology.update_placement_vm_host(rk,
                                                               placement.host)

                        if "resource_id" not in _app_topology.stack["placements"][rk].keys():
                            _app_topology.stack["placements"][rk]["resource_id"] = uuid

                    else:
                        if placement.stack_id is not None and \
                           placement.stack_id != "none":
                            self.phandler.update_placement(uuid,
                                                           stack_id="none",
                                                           orch_id="none")

                        host = self.resource.hosts[placement.host]
                        vm_info = host.get_vm_info(uuid=placement.uuid)
                        if "flavor_id" not in vm_info.keys():
                            (flavor, status) = self._get_flavor(r["properties"]["flavor"])
                            if flavor is not None:
                                vm_info["flavor_id"] = flavor.flavor_id
                            else:
                                _app_topology.status = status
                                return _app_topology

                else:
                    LOG.warn("vm (" + rk + ") in original stack does not have"
                             " uuid")

        if old_groups is not None and len(old_groups) > 0:
            for gk, g in old_groups.iteritems():
                if "host" in g.keys():
                    _app_topology.update_placement_group_host(gk, g["host"])

        LOG.debug("done setting stack update")

        if _app_topology.set_app_topology_properties(_app) is False:
            if _app_topology.status == "success":
                return None
            else:
                LOG.error(_app_topology.status)
                return _app_topology

        for rk, vm_alloc in _app_topology.old_vm_map.iteritems():
            old_r = old_placements[rk]

            vcpus = 0
            mem = 0
            local_volume = 0
            if "vcpus" not in old_r["properties"].keys():
                (flavor, status) = self._get_flavor(old_r["properties"]["flavor"])
                if flavor is None:
                    _app_topology.status = status
                    return _app_topology
                else:
                    vcpus = flavor.vCPUs
                    mem = flavor.mem_cap
                    local_volume = flavor.disk_cap
            else:
                vcpus = old_r["properties"]["vcpus"]
                mem = old_r["properties"]["mem"]
                local_volume = old_r["properties"]["local_volume"]

            if vm_alloc["vcpus"] != vcpus or \
               vm_alloc["mem"] != mem or \
               vm_alloc["local_volume"] != local_volume:
                old_vm_alloc = {}
                old_vm_alloc["host"] = vm_alloc["host"]
                old_vm_alloc["vcpus"] = vcpus
                old_vm_alloc["mem"] = mem
                old_vm_alloc["local_volume"] = local_volume

                _app_topology.old_vm_map[rk] = old_vm_alloc

        # FIXME(gjung): the case of that vms seen in new stack but not in old
        # stack

        LOG.debug("done setting stack properties")

        if _app_topology.parse_app_topology() is False:
            if _app_topology.status == "success":
                return None
            else:
                LOG.error(_app_topology.status)
                return _app_topology

        LOG.debug("done getting stack")

        return _app_topology

    def _set_flavor_properties(self, _app_topology):
        """Set flavor's properties."""

        for rk, r in _app_topology.stack["placements"].iteritems():
            if r["type"] == "OS::Nova::Server":
                (flavor, status) = self._get_flavor(r["properties"]["flavor"])
                if flavor is None:
                    _app_topology.status = status
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

    def _change_orch_id(self, _app, _app_topology):
        """Replace mock orch_id before setting application."""

        m_id = _app["mock_id"]
        o_id = _app["orchestration_id"]
        u_id = _app["resource_id"]

        if not _app_topology.change_orch_id(m_id, o_id):
            LOG.error(_app_topology.status)
            return _app_topology.status

        host_name = _app_topology.get_placement_host(o_id)
        if host_name == "none":
            _app_topology.status = "allocated host not found while changing mock id"
            LOG.error(_app_topology.status)
            return _app_topology.status
        else:
            if host_name in self.resource.hosts.keys():
                host = self.resource.hosts[host_name]
                vm_info = host.get_vm_info(orch_id=m_id)
                if vm_info is None:
                    _app_topology.status = "vm not found while changing mock id"
                    LOG.error(_app_topology.status)
                    return _app_topology.status
                else:
                    vm_info["orch_id"] = o_id

                self.resource.update_orch_id_in_groups(o_id, u_id, host)
            else:
                _app_topology.status = "host is not found while changing mock id"
                LOG.error(_app_topology.status)
                return _app_topology.status

        placement = self.phandler.get_placement(u_id)
        if placement is None:
            return None

        if placement.uuid != "none":
            if placement.orch_id is not None and placement.orch_id != "none":
                if placement.orch_id == m_id:
                    placement.orch_id = o_id
                    if not self.phandler.store_placement(u_id, placement):
                        return None

        return "success"

    def _get_flavor(self, _flavor_name):
        """Get flavor."""

        status = "success"

        flavor = self.resource.get_flavor(_flavor_name)

        if flavor is None:
            LOG.warn("not exist flavor (" + _flavor_name + ") and try to "
                     "refetch")

            if not self.metadata.set_flavors():
                status = "failed to read flavors from nova"
                return (None, status)

            flavor = self.resource.get_flavor(_flavor_name)
            if flavor is None:
                status = "net exist flavor (" + _flavor_name + ")"
                return (None, status)

        return (flavor, status)

    def _apply_meta_change(self, _rk, _r, _placements):
        """Check if image or flavor is changed in the update request."""

        if _rk in _placements.keys():
            r = _placements[_rk]

            if r["properties"]["flavor"] != _r["properties"]["flavor"]:
                self.phandler.update_placement(_r["resource_id"],
                                               state="rebuilding")
                self.phandler.set_original_host(_r["resource_id"])

            # NOTE(gjung): Nova & Heat does not re-schedule if image is changed
            if r["properties"]["image"] != _r["properties"]["image"]:
                self.phandler.update_placement(_r["resource_id"],
                                               state="rebuild")

    def get_placements(self, _app_topology):
        """Get prior stack/app placements info from db or cache."""

        (placements, groups) = self.get_stack(_app_topology.app_id)

        if placements is None:
            return (None, None)
        elif len(placements) == 0:
            _app_topology.status = "no app/stack record"
            return ({}, {})

        return (placements, groups)

    def get_stack(self, _stack_id):
        """Get stack info from db or cache."""

        placements = {}
        groups = {}

        if _stack_id in self.apps.keys():
            placements = self.apps[_stack_id].stack["placements"]
            groups = self.apps[_stack_id].stack["groups"]
            LOG.debug("hit stack cache")
        else:
            stack = self.db.get_stack(_stack_id)
            if stack is None:
                return (None, None)
            elif len(stack) == 0:
                return ({}, {})

            placements = stack["resources"]
            if "groups" in stack.keys() and stack["groups"] is not None:
                groups = stack["groups"]

        return (placements, groups)

    def store_app(self, _app_topology):
        """Store and cache app placement results."""

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
        """Update the uuid or host of vm in stack in db and cache."""

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

            if not self.db.update_stack(_stack_id, orch_id=orch_id, uuid=uuid,
                                        host=host, time=time.time()):
                return (None, None)

            return (placement["resource_id"], placement["properties"]["host"])
        else:
            return ("none", "none")

    def delete_from_stack(self, _stack_id, orch_id=None, uuid=None):
        """Delete a placement from stack in db and cache."""

        if _stack_id in self.apps.keys():
            app_topology = self.apps[_stack_id]

            if orch_id is not None:
                del app_topology.stack["placements"][orch_id]
                app_topology.timestamp_scheduled = time.time()
            elif uuid is not None:
                pk = None
                for rk, r in app_topology.stack["placements"].iteritems():
                    if "resource_id" in r.keys() and uuid == r["resource_id"]:
                        pk = rk
                        break
                if pk is not None:
                    del app_topology.stack["placements"][pk]
                    app_topology.timestamp_scheduled = time.time()

        if not self.db.delete_placement_from_stack(_stack_id,
                                                   orch_id=orch_id,
                                                   uuid=uuid,
                                                   time=time.time()):
            return False
        return True

    def check_history(self, _app):
        """Check if 'create' or 'replan' is determined already."""

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
        """Record an app placement decision."""

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
        """Unload app placement decisions."""

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
            del self.decision_history[dk]

    def _flush_app_cache(self):
        """Unload app topologies."""

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
