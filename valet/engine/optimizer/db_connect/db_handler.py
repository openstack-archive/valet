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

"""Music Handler."""

import json
import operator

from oslo_log import log

from valet.common.music import Music
from valet.engine.optimizer.db_connect.event import Event
# from valet.engine.optimizer.simulator.workload_generator import WorkloadGen

LOG = log.getLogger(__name__)


class DBHandler(object):
    """
    This Class consists of functions that interact with the music
    database for valet and returns/deletes/updates objects within it.
    """

    def __init__(self, _config):
        """Init Music Handler."""
        self.config = _config

        # self.db = WorkloadGen(self.config, LOG)
        self.db = Music(hosts=self.config.hosts, port=self.config.port,
                        replication_factor=self.config.replication_factor,
                        music_server_retries=self.config.music_server_retries,
                        logger=LOG)

    def get_events(self):
        """
        Get events from nova

        This function obtains all events from the database and then
        iterates through all of them to check the method and perform the
        corresponding action on them. Return Event list.
        """
        event_list = []

        events = {}
        try:
            events = self.db.read_all_rows(self.config.db_keyspace, self.config.db_event_table)
        except Exception as e:
            LOG.error("DB: miss events: " + str(e))
            return []

        if len(events) > 0:
            for _, row in events.iteritems():
                event_id = row['timestamp']
                exchange = row['exchange']
                method = row['method']
                args_data = row['args']

                LOG.debug("MusicHandler.get_events: event (" +
                          event_id + ") is entered")

                if exchange != "nova":
                    if self.delete_event(event_id) is False:
                        return None
                    LOG.debug(
                        "MusicHandler.get_events: event exchange "
                        "(" + exchange + ") is not supported")
                    continue

                if method != 'object_action' and method != 'build_and_run_' \
                                                           'instance':
                    if self.delete_event(event_id) is False:
                        return None
                    LOG.debug("MusicHandler.get_events: event method "
                              "(" + method + ") is not considered")
                    continue

                if len(args_data) == 0:
                    if self.delete_event(event_id) is False:
                        return None
                    LOG.debug("MusicHandler.get_events: "
                              "event does not have args")
                    continue

                try:
                    args = json.loads(args_data)
                except (ValueError, KeyError, TypeError):
                    LOG.warn("DB: while decoding to json event = " + method +
                             ":" + event_id)
                    continue

                # TODO(lamt) this block of code can use refactoring
                if method == 'object_action':
                    if 'objinst' in args.keys():
                        objinst = args['objinst']
                        if 'nova_object.name' in objinst.keys():
                            nova_object_name = objinst['nova_object.name']
                            if nova_object_name == 'Instance':
                                if 'nova_object.changes' in objinst.keys() and \
                                   'nova_object.data' in objinst.keys():
                                    change_list = objinst[
                                        'nova_object.changes']
                                    change_data = objinst['nova_object.data']
                                    if 'vm_state' in change_list and \
                                       'vm_state' in change_data.keys():
                                        if (change_data['vm_state'] ==
                                                'deleted' or
                                                change_data['vm_state'] ==
                                                'active'):
                                            e = Event(event_id)
                                            e.exchange = exchange
                                            e.method = method
                                            e.args = args
                                            event_list.append(e)
                                        else:
                                            msg = "unknown vm_state = %s"
                                            LOG.warning(
                                                msg % change_data["vm_state"])
                                            if 'uuid' in change_data.keys():
                                                msg = "    uuid = %s"
                                                LOG.warning(
                                                    msg % change_data['uuid'])
                                            if not self.delete_event(event_id):
                                                return None
                                    else:
                                        if not self.delete_event(event_id):
                                            return None
                                else:
                                    if self.delete_event(event_id) is False:
                                        return None
                            elif nova_object_name == 'ComputeNode':
                                if 'nova_object.changes' in objinst.keys() and \
                                   'nova_object.data' in objinst.keys():
                                    e = Event(event_id)
                                    e.exchange = exchange
                                    e.method = method
                                    e.args = args
                                    event_list.append(e)
                                else:
                                    if self.delete_event(event_id) is False:
                                        return None
                            else:
                                if self.delete_event(event_id) is False:
                                    return None
                        else:
                            if self.delete_event(event_id) is False:
                                return None
                    else:
                        if self.delete_event(event_id) is False:
                            return None
                elif method == 'build_and_run_instance':
                    if 'filter_properties' not in args.keys():
                        if self.delete_event(event_id) is False:
                            return None
                        continue

                    # NOTE(GJ): do not check the existance of scheduler_hints
                    if 'instance' not in args.keys():
                        if self.delete_event(event_id) is False:
                            return None
                        continue
                    else:
                        instance = args['instance']
                        if 'nova_object.data' not in instance.keys():
                            if self.delete_event(event_id) is False:
                                return None
                            continue

                    e = Event(event_id)
                    e.exchange = exchange
                    e.method = method
                    e.args = args
                    event_list.append(e)

        error_event_list = []
        for e in event_list:
            e.set_data()

            if e.method == "object_action":
                if e.object_name == 'Instance':
                    if e.uuid is None or e.uuid == "none" or \
                       e.host is None or e.host == "none" or \
                       e.vcpus == -1 or e.mem == -1:
                        error_event_list.append(e)
                        LOG.warn("DB: data missing in instance object event")
                elif e.object_name == 'ComputeNode':
                    if e.host is None or e.host == "none":
                        error_event_list.append(e)
                        LOG.warn("DB: data missing in compute object event")
            elif e.method == "build_and_run_instance":
                if e.uuid is None or e.uuid == "none":
                    error_event_list.append(e)
                    LOG.warning("MusicHandler.get_events: data missing "
                                "in build event")

        if len(error_event_list) > 0:
            event_list[:] = [e for e in event_list if e not in error_event_list]
        if len(event_list) > 0:
            # event_id is timestamp
            event_list.sort(key=operator.attrgetter('event_id'))

        return event_list

    def delete_event(self, _e):
        """Delete event."""
        try:
            self.db.delete_row_eventually(self.config.db_keyspace,
                                          self.config.db_event_table,
                                          'timestamp', _e)
        except Exception as e:
            LOG.error("DB: while deleting event: " + str(e))
            return False
        return True

    def get_requests(self):
        """Get requests from valet-api."""

        request_list = []

        requests = {}
        try:
            requests = self.db.read_all_rows(self.config.db_keyspace,
                                             self.config.db_request_table)
        except Exception as e:
            LOG.error("DB: miss requests: " + str(e))
            return []

        if len(requests) > 0:
            for _, row in requests.iteritems():
                r_list = json.loads(row['request'])

                LOG.debug("*** input = " + json.dumps(r_list, indent=4))

                for r in r_list:
                    request_list.append(r)

        return request_list

    def put_result(self, _result):
        """Return result and delete handled request."""

        for rk, r in _result.iteritems():

            LOG.debug("*** output = " + json.dumps(r, indent=4))

            data = {
                'stack_id': rk,
                'placement': json.dumps(r)
            }
            try:
                self.db.create_row(self.config.db_keyspace,
                                   self.config.db_response_table, data)
            except Exception as e:
                LOG.error("DB: while putting placement result: " + str(e))
                return False

        return True

    def delete_requests(self, _result):
        """Delete finished requests."""

        for rk in _result.keys():
            try:
                self.db.delete_row_eventually(self.config.db_keyspace,
                                              self.config.db_request_table,
                                              'stack_id', rk)
            except Exception as e:
                LOG.error("DB: while deleting handled request: " + str(e))
                return False

        return True

    def get_stack(self, _stack_id):
        """Get stack info."""

        json_app = {}

        row = {}
        try:
            row = self.db.read_row(self.config.db_keyspace,
                                   self.config.db_app_table,
                                   'stack_id', _stack_id)
        except Exception as e:
            LOG.error("DB: while getting stack info: " + str(e))
            return None

        if len(row) > 0:
            str_app = row[row.keys()[0]]['app']
            json_app = json.loads(str_app)

        return json_app

    def store_stack(self, _stack_data):
        """Store stack info."""

        stack_id = _stack_data["stack_id"]

        if not self.delete_stack(stack_id):
            return False

        LOG.debug("store stack = " + json.dumps(_stack_data, indent=4))

        data = {
            'stack_id': stack_id,
            'app': json.dumps(_stack_data)
        }
        try:
            self.db.create_row(self.config.db_keyspace,
                               self.config.db_app_table, data)
        except Exception as e:
            LOG.error("DB: while storing app: " + str(e))
            return False

        return True

    def delete_stack(self, _s_id):
        """Delete stack."""
        try:
            self.db.delete_row_eventually(self.config.db_keyspace,
                                          self.config.db_app_table,
                                          'stack_id', _s_id)
        except Exception as e:
            LOG.error("DB: while deleting app: " + str(e))
            return False
        return True

    def delete_placement_from_stack(self, _stack_id, orch_id=None, uuid=None,
                                    time=None):
        """Update stack by removing a placement from stack resources."""

        stack = self.get_stack(_stack_id)
        if stack is None:
            return False

        if len(stack) > 0:
            if orch_id is not None:
                del stack["resources"][orch_id]
            elif uuid is not None:
                pk = None
                for rk, r in stack["resources"].iteritems():
                    if "resource_id" in r.keys() and uuid == r["resource_id"]:
                        pk = rk
                        break
                if pk is not None:
                    del stack["resources"][pk]

            if time is not None:
                stack["timestamp"] = time

            if not self.store_stack(stack):
                return False

        return True

    def update_stack(self, _stack_id, orch_id=None, uuid=None, host=None,
                     time=None):
        """
        Update stack by changing host and/or uuid of vm in stack resources.
        """

        stack = self.get_stack(_stack_id)
        if stack is None:
            return False

        if len(stack) > 0:
            if orch_id is not None:
                if orch_id in stack["resources"].keys():
                    if uuid is not None:
                        stack["resources"][orch_id]["resource_id"] = uuid
                    if host is not None:
                        stack["resources"][orch_id]["properties"]["host"] = host
            elif uuid is not None:
                for rk, r in stack["resources"].iteritems():
                    if "resource_id" in r.keys() and uuid == r["resource_id"]:
                        if host is not None:
                            r["properties"]["host"] = host
                        break

            if time is not None:
                stack["timestamp"] = time

            if not self.store_stack(stack):
                return False

        return True

    def get_placement(self, _uuid):
        """Get placement info of given vm."""

        row = {}
        try:
            row = self.db.read_row(self.config.db_keyspace,
                                   self.config.db_uuid_table, 'uuid', _uuid)
        except Exception as e:
            LOG.error("DB: while getting vm placement info: " + str(e))
            return None

        if len(row) > 0:
            str_data = row[row.keys()[0]]['metadata']
            json_data = json.loads(str_data)
            return json_data
        else:
            return {}

    def get_placements(self):
        """Get all placements."""

        placement_list = []

        results = {}
        try:
            results = self.db.read_all_rows(self.config.db_keyspace,
                                            self.config.db_uuid_table)
        except Exception as e:
            LOG.error("DB: while getting all placements: " + str(e))
            return None

        if len(results) > 0:
            for _, row in results.iteritems():
                placement_list.append(json.loads(row['metadata']))

        return placement_list

    def store_placement(self, _placement_data):
        """Store placement info of given vm."""

        uuid = _placement_data["uuid"]

        if not self.delete_placement(uuid):
            return False

        LOG.debug("store placement = " + json.dumps(_placement_data, indent=4))

        data = {
            'uuid': uuid,
            'metadata': json.dumps(_placement_data)
        }
        try:
            self.db.create_row(self.config.db_keyspace,
                               self.config.db_uuid_table, data)
        except Exception as e:
            LOG.error("DB: while inserting placement: " + str(e))
            return False

        return True

    def delete_placement(self, _uuid):
        """Delete placement."""
        try:
            self.db.delete_row_eventually(self.config.db_keyspace,
                                          self.config.db_uuid_table,
                                          'uuid', _uuid)
        except Exception as e:
            LOG.error("DB: while deleting vm placement info: " + str(e))
            return False
        return True

    def get_resource_status(self, _k):
        """Get resource status."""

        json_resource = {}

        row = {}
        try:
            row = self.db.read_row(self.config.db_keyspace,
                                   self.config.db_resource_table,
                                   'site_name', _k, log=LOG)
        except Exception as e:
            LOG.error("MUSIC error while reading resource status: " +
                      str(e))
            return None

        if len(row) > 0:
            str_resource = row[row.keys()[0]]['resource']
            json_resource = json.loads(str_resource)

        return json_resource

    def update_resource_status(self, _k, _status):
        """Update resource status."""

        row = {}
        try:
            row = self.db.read_row(self.config.db_keyspace,
                                   self.config.db_resource_table,
                                   'site_name', _k)
        except Exception as e:
            LOG.error("MUSIC error while reading resource status: " + str(e))
            return False

        json_resource = {}

        if len(row) > 0:
            str_resource = row[row.keys()[0]]['resource']
            json_resource = json.loads(str_resource)

            if 'flavors' in _status.keys():
                for fk, f in _status['flavors'].iteritems():
                    if 'flavors' not in json_resource.keys():
                        json_resource['flavors'] = {}
                    json_resource['flavors'][fk] = f

            if 'groups' in _status.keys():
                for lgk, lg in _status['groups'].iteritems():
                    if 'groups' not in json_resource.keys():
                        json_resource['groups'] = {}
                    json_resource['groups'][lgk] = lg

            if 'hosts' in _status.keys():
                for hk, h in _status['hosts'].iteritems():
                    if 'hosts' not in json_resource.keys():
                        json_resource['hosts'] = {}
                    json_resource['hosts'][hk] = h

            if 'host_groups' in _status.keys():
                for hgk, hg in _status['host_groups'].iteritems():
                    if 'host_groups' not in json_resource.keys():
                        json_resource['host_groups'] = {}
                    json_resource['host_groups'][hgk] = hg

            if 'datacenter' in _status.keys():
                json_resource['datacenter'] = _status['datacenter']

            json_resource['timestamp'] = _status['timestamp']

            try:
                self.db.delete_row_eventually(self.config.db_keyspace,
                                              self.config.db_resource_table,
                                              'site_name', _k)
            except Exception as e:
                LOG.error("MUSIC error while deleting resource "
                          "status: " + str(e))
                return False
        else:
            json_resource = _status

        LOG.debug("store resource status = " + json.dumps(json_resource,
                                                          indent=4))

        data = {
            'site_name': _k,
            'resource': json.dumps(json_resource)
        }
        try:
            self.db.create_row(self.config.db_keyspace,
                               self.config.db_resource_table, data)
        except Exception as e:
            LOG.error("DB could not create row in resource table: " + str(e))
            return False

        return True

    def get_group(self, _g_id):
        """Get valet group info of given group identifier."""

        group_info = {}

        row = self._get_group_by_name(_g_id)
        if row is None:
            return None

        if len(row) > 0:
            group_info["id"] = row[row.keys()[0]]['id']
            group_info["level"] = row[row.keys()[0]]['level']
            group_info["type"] = row[row.keys()[0]]['type']
            group_info["members"] = json.loads(row[row.keys()[0]]['members'])
            group_info["name"] = row[row.keys()[0]]['name']
            return group_info
        else:
            row = self._get_group_by_id(_g_id)
            if row is None:
                return None

            if len(row) > 0:
                group_info["id"] = row[row.keys()[0]]['id']
                group_info["level"] = row[row.keys()[0]]['level']
                group_info["type"] = row[row.keys()[0]]['type']
                group_info["members"] = json.loads(row[row.keys()[0]]['members'])
                group_info["name"] = row[row.keys()[0]]['name']
                return group_info
            else:
                return {}

    def _get_group_by_name(self, _name):
        """Get valet group info of given group name."""

        row = {}

        try:
            row = self.db.read_row(self.config.db_keyspace,
                                   self.config.db_group_table,
                                   'name', _name)
        except Exception as e:
            LOG.error("DB: while getting group info by name: " + str(e))
            return None

        return row

    def _get_group_by_id(self, _id):
        """Get valet group info of given group id."""

        row = {}

        try:
            row = self.db.read_row(self.config.db_keyspace,
                                   self.config.db_group_table, 'id', _id)
        except Exception as e:
            LOG.error("DB: while getting group info by id: " + str(e))
            return None

        return row
