#!/bin/python

# Modified: Sep. 27, 2016

import time

from valet.engine.optimizer.app_manager.app_topology_base import VGroup, VM, Volume
from valet.engine.optimizer.ostro.search import Search


class Optimizer(object):

    def __init__(self, _resource, _logger):
        self.resource = _resource
        self.logger = _logger

        self.search = Search(self.logger)

        self.status = "success"

    def place(self, _app_topology):
        success = False

        uuid_map = None
        place_type = None

        start_ts = time.time()

        if len(_app_topology.candidate_list_map) > 0:
            place_type = "replan"
        elif len(_app_topology.exclusion_list_map) > 0:
            place_type = "migration"
        else:
            place_type = "create"

        if place_type == "migration":
            vm_id = _app_topology.exclusion_list_map.keys()[0]
            candidate_host_list = []
            for hk in self.resource.hosts.keys():
                if hk not in _app_topology.exclusion_list_map[vm_id]:
                    candidate_host_list.append(hk)
            _app_topology.candidate_list_map[vm_id] = candidate_host_list

        if place_type == "replan" or place_type == "migration":
            success = self.search.re_place_nodes(_app_topology, self.resource)
            if success is True:
                if len(_app_topology.old_vm_map) > 0:
                    uuid_map = self._delete_old_vms(_app_topology.old_vm_map)
                    self.resource.update_topology(store=False)

                    self.logger.debug("Optimizer: remove old placements for replan")
        else:
            success = self.search.place_nodes(_app_topology, self.resource)

        end_ts = time.time()

        if success is True:

            self.logger.debug("Optimizer: search running time = " + str(end_ts - start_ts) + " sec")
            self.logger.debug("Optimizer: total bandwidth = " + str(self.search.bandwidth_usage))
            self.logger.debug("Optimizer: total number of hosts = " + str(self.search.num_of_hosts))

            placement_map = {}
            for v in self.search.node_placements.keys():
                if isinstance(v, VM):
                    placement_map[v] = self.search.node_placements[v].host_name
                elif isinstance(v, Volume):
                    placement_map[v] = self.search.node_placements[v].host_name + "@"
                    placement_map[v] += self.search.node_placements[v].storage.storage_name
                elif isinstance(v, VGroup):
                    if v.level == "host":
                        placement_map[v] = self.search.node_placements[v].host_name
                    elif v.level == "rack":
                        placement_map[v] = self.search.node_placements[v].rack_name
                    elif v.level == "cluster":
                        placement_map[v] = self.search.node_placements[v].cluster_name

                self.logger.debug("    " + v.name + " placed in " + placement_map[v])

            self._update_resource_status(uuid_map)

            return placement_map

        else:
            self.status = self.search.status
            return None

    def _delete_old_vms(self, _old_vm_map):
        uuid_map = {}

        for h_uuid, info in _old_vm_map.iteritems():
            uuid = self.resource.get_uuid(h_uuid, info[0])
            if uuid is not None:
                uuid_map[h_uuid] = uuid

            self.resource.remove_vm_by_h_uuid_from_host(info[0], h_uuid, info[1], info[2], info[3])
            self.resource.update_host_time(info[0])

            host = self.resource.hosts[info[0]]
            self.resource.remove_vm_by_h_uuid_from_logical_groups(host, h_uuid)

        return uuid_map

    def _update_resource_status(self, _uuid_map):
        for v, np in self.search.node_placements.iteritems():

            if isinstance(v, VM):
                uuid = "none"
                if _uuid_map is not None:
                    if v.uuid in _uuid_map.keys():
                        uuid = _uuid_map[v.uuid]

                self.resource.add_vm_to_host(np.host_name,
                                             (v.uuid, v.name, uuid),
                                             v.vCPUs, v.mem, v.local_volume_size)

                for vl in v.vm_list:
                    tnp = self.search.node_placements[vl.node]
                    placement_level = np.get_common_placement(tnp)
                    self.resource.deduct_bandwidth(np.host_name, placement_level, vl.nw_bandwidth)

                for voll in v.volume_list:
                    tnp = self.search.node_placements[voll.node]
                    placement_level = np.get_common_placement(tnp)
                    self.resource.deduct_bandwidth(np.host_name, placement_level, voll.io_bandwidth)

                self._update_logical_grouping(v, self.search.avail_hosts[np.host_name], uuid)

                self.resource.update_host_time(np.host_name)

            elif isinstance(v, Volume):
                self.resource.add_vol_to_host(np.host_name, np.storage.storage_name, v.name, v.volume_size)

                for vl in v.vm_list:
                    tnp = self.search.node_placements[vl.node]
                    placement_level = np.get_common_placement(tnp)
                    self.resource.deduct_bandwidth(np.host_name, placement_level, vl.io_bandwidth)

                self.resource.update_storage_time(np.storage.storage_name)

    def _update_logical_grouping(self, _v, _avail_host, _uuid):
        for lgk, lg in _avail_host.host_memberships.iteritems():
            if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                lg_name = lgk.split(":")
                if lg_name[0] == "host" and lg_name[1] != "any":
                    self.resource.add_logical_group(_avail_host.host_name, lgk, lg.group_type)

        if _avail_host.rack_name != "any":
            for lgk, lg in _avail_host.rack_memberships.iteritems():
                if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                    lg_name = lgk.split(":")
                    if lg_name[0] == "rack" and lg_name[1] != "any":
                        self.resource.add_logical_group(_avail_host.rack_name, lgk, lg.group_type)

        if _avail_host.cluster_name != "any":
            for lgk, lg in _avail_host.cluster_memberships.iteritems():
                if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                    lg_name = lgk.split(":")
                    if lg_name[0] == "cluster" and lg_name[1] != "any":
                        self.resource.add_logical_group(_avail_host.cluster_name, lgk, lg.group_type)

        vm_logical_groups = []
        self._collect_logical_groups_of_vm(_v, vm_logical_groups)

        host = self.resource.hosts[_avail_host.host_name]
        self.resource.add_vm_to_logical_groups(host, (_v.uuid, _v.name, _uuid), vm_logical_groups)

    def _collect_logical_groups_of_vm(self, _v, _vm_logical_groups):
        if isinstance(_v, VM):
            for es in _v.extra_specs_list:
                if "host_aggregates" in es.keys():
                    lg_list = es["host_aggregates"]
                    for lgk in lg_list:
                        if lgk not in _vm_logical_groups:
                            _vm_logical_groups.append(lgk)

            if _v.availability_zone is not None:
                az = _v.availability_zone.split(":")[0]
                if az not in _vm_logical_groups:
                    _vm_logical_groups.append(az)

        for _, level in _v.exclusivity_groups.iteritems():
            if level not in _vm_logical_groups:
                _vm_logical_groups.append(level)

        for _, level in _v.diversity_groups.iteritems():
            if level not in _vm_logical_groups:
                _vm_logical_groups.append(level)

        if isinstance(_v, VGroup):
            name = _v.level + ":" + _v.name
            if name not in _vm_logical_groups:
                _vm_logical_groups.append(name)

        if _v.survgroup is not None:
            self._collect_logical_groups_of_vm(_v.survgroup, _vm_logical_groups)
