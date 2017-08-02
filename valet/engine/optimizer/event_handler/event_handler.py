#!/bin/python

import time
from valet.engine.optimizer.app_manager.placement_handler import Placement


class EventHandler(object):
    '''Handler to apply events to resource status and placements.'''

    def __init__(self, _placement_handler, _app_handler, _resource, _db, _logger):
        self.logger = _logger

        self.phandler = _placement_handler
        self.ahandler = _app_handler
        self.resource = _resource
        self.db = _db

    def handle_events(self, _event_list, _data_lock):
        '''Deal with events (vm create and delete, host status).'''

        _data_lock.acquire()

        for e in _event_list:
            if e.host is not None and e.host != "none":
                if e.host not in self.resource.hosts.keys():
                    self.logger.warn("EVENT: host (" + e.host + ") not exists")
                    continue

            if e.method == "build_and_run_instance":
                if not self._handle_build_and_run_event(e):
                    _data_lock.release()
                    return False
            elif e.method == "object_action":
                if e.object_name == 'Instance':
                    if e.vm_state == "active":
                        if not self._handle_active_instance_event(e):
                            _data_lock.release()
                            return False
                    elif e.vm_state == "deleted":
                        if not self._handle_delete_instance_event(e):
                            _data_lock.release()
                            return False
                    else:
                        self.logger.warn("EVENT: unknown event vm_state = " + e.vm_state)
                elif e.object_name == 'ComputeNode':
                    self._handle_compute_event(e)
                else:
                    self.logger.warn("EVENT: unknown object_name = " + e.object_name)
            else:
                self.logger.warn("EVENT: unknown method = " + e.method)

        for e in _event_list:
            if not self.db.delete_event(e.event_id):
                _data_lock.release()
                return False

        _data_lock.release()

        return True

    def _handle_build_and_run_event(self, e):
        '''Handle 'build-and-run' event to relate stack_id.'''

        self.logger.info("EVENT: got 'build_and_run' for " + e.uuid)

        stack_id = None
        if e.heat_root_stack_id is not None and e.heat_root_stack_id != "none":
            stack_id = e.heat_root_stack_id
        else:
            self.logger.warn("EVENT: stack_id is none")

        orch_id = None
        if e.heat_resource_uuid is not None and e.heat_resource_uuid != "none":
            orch_id = e.heat_resource_uuid
        else:
            self.logger.warn("EVENT: orch_id is none")

        if stack_id is not None and orch_id is not None:
            placement = self.phandler.get_placement(e.uuid)
            if placement is None:
                return False

            elif placement.uuid == "none":
                self.logger.warn("miss 'identify' or 'replan' step?")

                (vid, host_name) = self.ahandler.update_stack(stack_id, orch_id=orch_id, uuid=e.uuid)

                if host_name is not None and host_name != "none":
                    placement = Placement(e.uuid)
                    placement.stack_id = stack_id
                    placement.host = host_name
                    placement.orch_id = orch_id
                    placement.state = "building"
                    placement.timestamp = time.time()
                    placement.status = "verified"

                    if not self.phandler.store_placement(e.uuid, placement):
                        return False

                    self._update_uuid(orch_id, e.uuid, host_name)
                    self.resource.update_topology(store=False)
                else:
                    self.logger.warn("EVENT: unknown vm instance!")
            else:
                if placement.stack_id is not None and placement.stack_id != "none":
                    if placement.stack_id != stack_id:
                        self.logger.debug("recorded stack_id = " + placement.stack_id)
                        self.logger.warn("EVENT: stack_id(" + stack_id + ") is different!")

                        # FIXME(gjung): update stack_id in placement handler, resource, stack?
                else:
                    self.logger.warn("EVENT: stack_id is missing")

        return True

    def _handle_active_instance_event(self, e):
        '''Handle event for vm activation confirmation.'''

        self.logger.info("EVENT: got instance_active for " + e.uuid)

        placement = self.phandler.get_placement(e.uuid)
        if placement is None:
            return False

        elif placement.uuid == "none":
            self.logger.warn("EVENT: unknown instance!")

            placement = Placement(e.uuid)
            placement.host = e.host
            placement.state = "created"
            placement.timestamp = time.time()
            placement.status = "verified"

            vm_info = {}
            vm_info["uuid"] = e.uuid
            vm_info["stack_id"] = "none"
            vm_info["orch_id"] = "none"
            vm_info["name"] = "none"

            vm_alloc = {}
            vm_alloc["host"] = e.host
            vm_alloc["vcpus"] = e.vcpus
            vm_alloc["mem"] = e.mem
            vm_alloc["local_volume"] = e.local_disk

            if self._add_vm_to_host(vm_info, vm_alloc) is True:
                self.resource.update_topology(store=False)

            if not self.phandler.store_placement(e.uuid, placement):
                return False

            return True

        if placement.host != e.host:
            self.logger.warn("EVENT: vm activated in the different host!")

            vm_info = {}
            vm_info["uuid"] = e.uuid
            vm_info["stack_id"] = placement.stack_id
            vm_info["orch_id"] = placement.orch_id
            vm_info["name"] = "none"

            vm_alloc = {}
            vm_alloc["host"] = e.host
            vm_alloc["vcpus"] = e.vcpus
            vm_alloc["mem"] = e.mem
            vm_alloc["local_volume"] = e.local_disk

            if self._add_vm_to_host(vm_info, vm_alloc) is True:
                vm_alloc["host"] = placement.host

                self._remove_vm_from_host(e.uuid, vm_alloc)
                self._remove_vm_from_groups_of_host(e.uuid, placement.host)
                self.resource.update_topology(store=False)

                placement.host = e.host

                if placement.stack_id is not None or placement.stack_id != "none":
                    (vid, hk) = self.ahandler.update_stack(placement.stack_id, uuid=e.uuid, host=e.host)
                    if vid is None:
                        return False

        new_state = None
        if placement.state == "planned":
            new_state = "created"
        elif placement.state == "rebuild":
            new_state = "rebuilt"
        elif placement.state == "migrate":
            new_state = "migrated"
        else:
            self.logger.warn("EVENT: vm is in incomplete state = " + placement.state)
            new_state = "created"

        curr_state = "none"
        if placement.state is not None:
            curr_state = placement.state
        self.logger.info("EVENT: state changed from '" + curr_state + "' to '" + new_state + "'")

        placement.state = new_state

        if not self.phandler.store_placement(e.uuid, placement):
            return False

        return True

    def _handle_delete_instance_event(self, e):
        '''Handle event for vm deletion notification.'''

        self.logger.info("EVENT: got instance_delete for " + e.uuid)

        placement = self.phandler.get_placement(e.uuid)
        if placement is None:
            return False
        elif placement.uuid == "none":
            self.logger.warn("EVENT: unknown vm instance!")
            return True

        if placement.host != e.host:
            self.logger.warn("EVENT: vm activated in the different host!")
            return True

        if placement.state is None or placement.state == "none" or \
           placement.state in ("created", "rebuilt", "migrated"):
            if placement.stack_id is not None and placement.stack_id != "none":
                if not self.ahandler.delete_from_stack(placement.stack_id, uuid=e.uuid):
                    return False
            else:
                self.logger.warn("EVENT: stack_id is unknown")

            if not self.phandler.delete_placement(e.uuid):
                return False

            vm_alloc = {}
            vm_alloc["host"] = e.host
            vm_alloc["vcpus"] = e.vcpus
            vm_alloc["mem"] = e.mem
            vm_alloc["local_volume"] = e.local_disk

            self._remove_vm_from_host(e.uuid, vm_alloc)
            self._remove_vm_from_groups(e.uuid, e.host)
            self.resource.update_topology(store=False)
        else:
            self.logger.warn("EVENT: vm is incomplete state for deletion = " + placement.state)

        return True

    def _handle_compute_event(self, e):
        '''Handle event about compute resource change.'''
        self.logger.info("EVENT: got compute for " + e.host)
        if self.resource.update_host_resources(e.host, e.status) is True:
            self.resource.update_host_time(e.host)
            self.resource.update_topology(store=False)

    def _add_vm_to_host(self, _vm_info, _vm_alloc):
        '''Add vm to host.'''
        if self.resource.add_vm_to_host(_vm_alloc, _vm_info) is True:
            self.resource.update_host_time(_vm_alloc["host"])
            return True
        return False

    def _remove_vm_from_host(self, _uuid, _vm_alloc):
        '''Remove deleted vm from host.'''
        if self.resource.remove_vm_from_host(_vm_alloc, uuid=_uuid) is True:
            self.resource.update_host_time(_vm_alloc["host"])
        else:
            self.logger.warn("vm (" + _uuid + ") is missing in host while removing")

    def _remove_vm_from_groups(self, _uuid, _host_name):
        '''Remove deleted vm from groups.'''
        host = self.resource.hosts[_host_name]
        self.resource.remove_vm_from_groups(host, uuid=_uuid)

    def _remove_vm_from_groups_of_host(self, _uuid, _host_name):
        '''Remove deleted vm from host of the group.'''
        host = self.resource.hosts[_host_name]
        self.resource.remove_vm_from_groups_of_host(host, uuid=_uuid)

    def _update_uuid(self, _orch_id, _uuid, _host_name):
        '''Update physical uuid of placement.'''

        host = self.resource.hosts[_host_name]
        if host.update_uuid(_orch_id, _uuid) is True:
            self.resource.update_host_time(_host_name)
        else:
            self.logger.warn("fail to update uuid in host = " + host.name)

        self.resource.update_uuid_in_groups(_orch_id, _uuid, host)
