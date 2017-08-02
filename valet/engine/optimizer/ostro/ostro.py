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

import threading
import time

from oslo_config import cfg
from oslo_log import log

from valet.engine.listener.listener_manager import ListenerManager
from valet.engine.optimizer.app_manager.app_handler import AppHandler
from valet.engine.optimizer.app_manager.placement_handler \
        import PlacementHandler
from valet.engine.optimizer.db_connect.db_handler import DBHandler
from valet.engine.optimizer.event_handler.event_handler import EventHandler
from valet.engine.optimizer.ostro.bootstrapper import Bootstrapper
from valet.engine.optimizer.ostro.optimizer import Optimizer
from valet.engine.resource_manager.compute_manager import ComputeManager
from valet.engine.resource_manager.metadata_manager import MetadataManager
from valet.engine.resource_manager.resource import Resource
from valet.engine.resource_manager.topology_manager import TopologyManager

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class Ostro(object):
    """Main class for placement scheduling."""

    def __init__(self, _config):
        """Initialization."""
        self.config = _config
        self.end_of_process = False
        self.batch_store_trigger = 10  # sec

        self.data_lock = threading.Lock()
        self.thread_list = []

        self.db = DBHandler(self.config)
        self.resource = Resource(self.db, self.config)

        self.compute = ComputeManager(1, "Compute", self.resource,
                                      self.data_lock, self.config)
        self.topology = TopologyManager(2, "Topology", self.resource,
                                        self.data_lock, self.config)
        self.metadata = MetadataManager(3, "Metadata", self.resource,
                                        self.data_lock, self.config)
        self.listener = ListenerManager(4, "Listener", CONF)

        self.phandler = PlacementHandler(self.db)
        self.ahandler = AppHandler(self.phandler, self.metadata, self.resource,
                                   self.db, self.config)

        self.compute.set_handlers(self.phandler, self.ahandler)

        self.optimizer = Optimizer()

        self.ehandler = EventHandler(self.phandler, self.ahandler,
                                     self.resource, self.db)

        self.bootstrapper = Bootstrapper(self.resource, self.db)
        self.bootstrapper.set_handlers(self.phandler)


    def bootstrap(self):
        """Load all required datacenter resource information."""

        if not self.bootstrapper.load_data(self.compute, self.topology, self.metadata):
            return False

        if not self.bootstrapper.verify_pre_valet_placements():
            return False

        return True

    def run_ostro(self):
        """Run main valet-engine (ostro) loop."""

        LOG.info("start ostro ......")

        self.compute.start()
        self.topology.start()
        self.metadata.start()
        self.listener.start()

        self.thread_list.append(self.compute)
        self.thread_list.append(self.topology)
        self.thread_list.append(self.metadata)
        self.thread_list.append(self.listener)

        while self.end_of_process is False:
            request_list = self.db.get_requests()
            if len(request_list) > 0:
                if self._handle_requests(request_list) is False:
                    break
            else:
                event_list = self.db.get_events()
                if event_list is None:
                    break
                if len(event_list) > 0:
                    if self.ehandler.handle_events(event_list,
                                                   self.data_lock) is False:
                        break
                else:
                    now_time = (time.time() - self.resource.current_timestamp)
                    if now_time >= self.batch_store_trigger:
                        self.data_lock.acquire()
                        if self.resource.store_topology_updates() is False:
                            self.data_lock.release()
                            break
                        self.data_lock.release()
                    else:
                        time.sleep(0.1)

        self.compute.end_of_process = True
        self.topology.end_of_process = True
        self.metadata.end_of_process = True

        for t in self.thread_list:
            t.join()

        LOG.info("exit ostro")

    def _handle_requests(self, _req_list):
        """Deal with all requests.

        Request types are 'query', 'create', 'replan', 'identify', 'update',
        'migrate', 'ping'.
        """

        for req in _req_list:
            if req["action"] == "query":
                query_result = self._query(req)
                if query_result is None:
                    LOG.error("valet-engine exits due to the error")
                    return False

                result = self._get_json_query_result(req["stack_id"],
                                                     query_result)

                if not self.db.put_result(result):
                    return False

            else:
                # FIXME(gjung): history check not works & due to update,
                # ad-hoc and replan with the same key
                # result = None
                # (decision_key, old_decision) = \
                #        self.ahandler.check_history(req)

                # if old_decision is None:

                app_topology = self._plan_app(req)
                if app_topology is None:
                    LOG.error("valet-engine exits due to the error")
                    return False

                LOG.info("plan result status: " + app_topology.status)

                result = self._get_json_result(app_topology)

                #     if decision_key is not None:
                #         self.ahandler.record_history(decision_key, result)
                # else:
                #     LOG.warn("decision(" + decision_key + ") already made")
                #     result = old_decision

                if app_topology.action in ("ping", "create", "replan",
                                           "update", "migrate"):
                    if not self.db.put_result(result):
                        return False

            if not self.db.delete_requests(result):
                return False

        return True

    def _query(self, _q):
        """Get placements information of valet group (affinity, diversity,
        exclusivity).
        """

        LOG.info("got query")

        query_result = {}
        query_result["result"] = None
        query_result["status"] = "ok"

        if "type" in _q.keys():
            if _q["type"] == "group_vms":
                if "parameters" in _q.keys():
                    params = _q["parameters"]
                    if "group_name" in params.keys():
                        self.data_lock.acquire()
                        placement_list = self._get_placements_from_group(params["group_name"])
                        self.data_lock.release()
                        query_result["result"] = placement_list
                    else:
                        query_result["status"] = "unknown paramenter in query"
                else:
                    query_result["status"] = "no paramenter in query"
            elif _q["type"] == "invalid_placements":
                self.data_lock.acquire()
                result = self._get_invalid_placements()
                if result is None:
                    self.data_lock.release()
                    return None
                query_result["result"] = result
                self.data_lock.release()
            else:
                query_result["status"] = "unknown query type"
        else:
            query_result["status"] = "no type in query"

        if query_result["status"] != "ok":
            LOG.warn(query_result["status"])
            query_result["result"] = None

        return query_result

    def _get_placements_from_group(self, _group_name):
        """Get all placements information of given valet group."""

        placement_list = []

        vm_info_list = []
        for lgk, lg in self.resource.groups.iteritems():
            if lg.group_type == "EX" or \
               lg.group_type == "AFF" or \
               lg.group_type == "DIV":
                lg_id = lgk.split(":")
                if lg_id[1] == _group_name:
                    vm_info_list = lg.vm_list
                    break

        for vm_info in vm_info_list:
            if vm_info["uuid"] != "none":
                placement_list.append(vm_info["uuid"])
            else:
                LOG.warning("found pending vms in this group while query")

        return placement_list

    def _get_invalid_placements(self):
        """Get all invalid placements."""

        if not self.bootstrapper.verify_pre_valet_placements():
            return None

        vms = {}

        placement_list = self.phandler.get_placements()

        for p in placement_list:
            if p["status"] is not None and p["status"] != "verified":
                status = {}
                status["status"] = p["status"]
                vms[p["uuid"]] = status

        return vms

    def _plan_app(self, _app):
        """Deal with app placement request.

        Validate the request, extract info, search placements, and store/cache results.
        """

        self.data_lock.acquire()
        app_topology = self.ahandler.set_app(_app)
        if app_topology is None:
            self.data_lock.release()
            return None
        elif app_topology.status != "success":
            self.data_lock.release()
            return app_topology

        self.optimizer.plan(app_topology)
        if app_topology.status != "success":
            self.data_lock.release()
            return app_topology

        if not self.ahandler.store_app(app_topology):
            self.data_lock.release()
            return None
        self.data_lock.release()

        return app_topology

    def _get_json_query_result(self, _stack_id, _result):
        """Set query result format as JSON."""

        result = {}
        result[_stack_id] = {}

        result[_stack_id]["action"] = "query"
        result[_stack_id]["stack_id"] = _stack_id

        query_status = {}
        if _result["status"] != "ok":
            query_status['type'] = "error"
            query_status['message'] = _result["status"]
        else:
            query_status['type'] = "ok"
            query_status['message'] = "success"
        result[_stack_id]['status'] = query_status

        if _result["result"] is not None:
            result[_stack_id]['resources'] = _result["result"]

        return result

    def _get_json_result(self, _app_topology):
        """Set request result format as JSON."""

        result = {}
        result[_app_topology.app_id] = {}

        result[_app_topology.app_id]["action"] = _app_topology.action
        result[_app_topology.app_id]["stack_id"] = _app_topology.app_id

        if _app_topology.action == "ping":
            app_status = {}
            if _app_topology.status != "success":
                app_status['type'] = "error"
                app_status['message'] = _app_topology.status
                result[_app_topology.app_id]['status'] = app_status
                result[_app_topology.app_id]['resources'] = {}
            else:
                app_status['type'] = "ok"
                app_status['message'] = _app_topology.status
                result[_app_topology.app_id]['status'] = app_status
                result[_app_topology.app_id]['resources'] = {
                        "ip": self.config.ip, "id": self.config.priority}
        elif _app_topology.action in ("create", "replan", "update", "migrate"):
            app_status = {}
            if _app_topology.status != "success":
                app_status['type'] = "error"
                app_status['message'] = _app_topology.status
                result[_app_topology.app_id]['status'] = app_status
                result[_app_topology.app_id]['resources'] = {}
            else:
                app_status['type'] = "ok"
                app_status['message'] = _app_topology.status
                result[_app_topology.app_id]['status'] = app_status
                resources = {}
                for rk, r in _app_topology.stack["placements"].iteritems():
                    if r["type"] == "OS::Nova::Server":
                        resources[rk] = {"properties": {
                                            "host": r["properties"]["host"]}}
                result[_app_topology.app_id]['resources'] = resources

        return result
