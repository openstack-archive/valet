#!/bin/python

import operator
import time


class Placement(object):
    '''Container to hold a placement info.'''

    def __init__(self, _uuid):
        self.uuid = _uuid
        self.stack_id = None
        self.host = None
        self.orch_id = None
        self.state = None
        self.original_host = None
        self.dirty = False
        self.status = None
        self.timestamp = 0

    def get_json_info(self):
        return {'uuid': self.uuid,
                'stack_id': self.stack_id,
                'host': self.host,
                'orch_id': self.orch_id,
                'state': self.state,
                'original_host': self.original_host,
                'dirty': self.dirty,
                'status': self.status,
                'timestamp': self.timestamp}


class PlacementHandler(object):
    '''Placement handler to cache and store placements.'''

    def __init__(self, _db, _logger):
        self.placements = {}  # key = uuid, value = Placement instance
        self.max_cache = 5000
        self.min_cache = 1000

        self.db = _db
        self.logger = _logger

    def flush_cache(self):
        '''Unload placements from cache based on LRU.'''

        if len(self.placements) > self.max_cache:
            count = 0
            num_of_removes = len(self.placements) - self.min_cache

            remove_item_list = []
            for placement in (sorted(self.placements.values(),
                                     key=operator.attrgetter('timestamp'))):
                remove_item_list.append(placement.uuid)
                count += 1
                if count == num_of_removes:
                    break

            for uuid in remove_item_list:
                self.unload_placement(uuid)

    def load_placement(self, _uuid):
        '''Patch to cache from db.'''

        p = self.db.get_placement(_uuid)
        if p is None:
            return None
        elif len(p) == 0:
            return Placement("none")

        placement = Placement(_uuid)
        placement.uuid = p["uuid"]
        placement.stack_id = p["stack_id"]
        placement.host = p["host"]
        placement.orch_id = p["orch_id"]
        placement.state = p["state"]
        placement.original_host = p["original_host"]
        placement.dirty = p["dirty"]
        placement.status = p["status"]
        placement.timestamp = float(p["timestamp"])
        self.placements[_uuid] = placement

        return placement

    def unload_placement(self, _uuid):
        '''Remove from cache.'''
        if _uuid in self.placements.keys():
            placement = self.placements[_uuid]
            if placement.dirty is False:
                del self.placements[_uuid]

    def store_placement(self, _uuid, _placement):
        '''Store changed placement to db.'''

        placement_data = {}
        placement_data["uuid"] = _uuid
        placement_data["stack_id"] = _placement.stack_id
        placement_data["host"] = _placement.host
        placement_data["orch_id"] = _placement.orch_id
        placement_data["state"] = _placement.state
        placement_data["original_host"] = _placement.original_host
        placement_data["dirty"] = _placement.dirty
        placement_data["status"] = _placement.status
        placement_data["timestamp"] = _placement.timestamp

        if not self.db.store_placement(placement_data):
            return False
        return True

    def get_placement(self, _uuid):
        '''Get placement info from db or cache.'''

        if _uuid not in self.placements.keys():
            placement = self.load_placement(_uuid)
            if placement is None:
                return None
            elif placement.uuid == "none":
                return placement
        else:
            self.logger.debug("hit placement cache")

        return self.placements[_uuid]

    def get_placements(self):
        '''Get all placements from db.'''

        placement_list = self.db.get_placements()
        if placement_list is None:
            return None

        return placement_list

    def delete_placement(self, _uuid):
        '''Delete placement from cache and db.'''

        if _uuid in self.placements.keys():
            del self.placements[_uuid]

        if not self.db.delete_placement(_uuid):
            return False

        return True

    def insert_placement(self, _uuid, _stack_id, _host, _orch_id, _state):
        '''Insert (Update) new (existing) placement into cache and db.'''

        placement = Placement(_uuid)
        placement.stack_id = _stack_id
        placement.host = _host
        placement.orch_id = _orch_id
        placement.state = _state
        placement.original_host = None
        placement.timestamp = time.time()
        placement.status = "verified"
        placement.dirty = True
        self.placements[_uuid] = placement

        if not self.store_placement(_uuid, placement):
            return None

        return placement

    def update_placement(self, _uuid, stack_id=None, host=None, orch_id=None, state=None):
        '''Update exsiting placement info in cache.'''

        placement = self.get_placement(_uuid)
        if placement is None or placement.uuid == "none":
            return False

        if stack_id is not None:
            if placement.stack_id is None or placement.stack_id == "none" or placement.stack_id != stack_id:
                placement.stack_id = stack_id
                placement.timestamp = time.time()
                placement.dirty = True
        if host is not None:
            if placement.host != host:
                placement.host = host
                placement.timestamp = time.time()
                placement.dirty = True
        if orch_id is not None:
            if placement.orch_id is None or placement.orch_id == "none" or placement.orch_id != orch_id:
                placement.orch_id = orch_id
                placement.timestamp = time.time()
                placement.dirty = True
        if state is not None:
            if placement.state is None or placement.state == "none" or placement.state != state:
                placement.state = state
                placement.timestamp = time.time()
                placement.dirty = True

        if not self.store_placement(_uuid, placement):
            return False

        return True

    def set_original_host(self, _uuid):
        '''Set the original host before migration.'''

        placement = self.get_placement(_uuid)
        if placement is None or placement.uuid == "none":
            return False

        placement.original_host = placement.host
        placement.timestamp = time.time()
        placement.dirty = True

        if not self.store_placement(_uuid, placement):
            return False

        return True

    def set_verified(self, _uuid):
        '''Mark this vm as verified.'''

        placement = self.get_placement(_uuid)
        if placement is None or placement.uuid == "none":
            return False

        if placement.status != "verified":
            self.logger.info("this vm is just verified")
            placement.status = "verified"
            placement.timestamp = time.time()
            placement.dirty = True

            if not self.store_placement(_uuid, placement):
                return False

        return True

    def set_unverified(self, _uuid):
        '''Mark this vm as not verified yet.'''

        placement = self.get_placement(_uuid)
        if placement is None or placement.uuid == "none":
            return False

        self.logger.info("this vm is not verified yet")
        placement.status = "none"
        placement.timestamp = time.time()
        placement.dirty = True

        if not self.store_placement(_uuid, placement):
            return False

        return True
