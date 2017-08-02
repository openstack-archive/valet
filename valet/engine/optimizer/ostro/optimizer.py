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
from oslo_log import log

from valet.engine.optimizer.app_manager.group import Group
from valet.engine.optimizer.app_manager.vm import VM
from valet.engine.optimizer.ostro.search import Search

LOG = log.getLogger(__name__)


class Optimizer(object):
    """Optimizer to compute the optimal placements."""

    def __init__(self):
        self.resource = None
        self.search = Search()

    def plan(self, _app_topology):
        """Scheduling placements of given app."""

        self.resource = _app_topology.resource

        if _app_topology.action != "ping" and \
           _app_topology.action != "identify":
            _app_topology.set_weight()
            _app_topology.set_optimization_priority()

        if _app_topology.action == "create":
            if self.search.plan(_app_topology) is True:
                LOG.debug("done search")

                if len(_app_topology.candidate_list_map) > 0:  # ad-hoc
                    self._update_placement_states(_app_topology)
                    LOG.debug("done update states")

                if _app_topology.status == "success":
                    self._update_placement_hosts(_app_topology)
                    LOG.debug("done update hosts")

                    self._update_resource_status(_app_topology)
                    LOG.debug("done update resource status")
            else:
                if _app_topology.status == "success":
                    _app_topology.status = "failed"

        elif _app_topology.action == "update":
            if self.search.re_plan(_app_topology) is True:
                LOG.debug("done search")

                self._update_placement_states(_app_topology)
                if _app_topology.status == "success":
                    LOG.debug("done update states")

                    self._update_placement_hosts(_app_topology)
                    LOG.debug("done update hosts")

                    self._delete_old_placements(_app_topology.old_vm_map)
                    self._update_resource_status(_app_topology)
                    LOG.debug("done update resource status")
            else:
                if _app_topology.status == "success":
                    _app_topology.status = "failed"

        elif _app_topology.action == "replan":
            orch_id = _app_topology.id_map.keys()[0]
            host_name = _app_topology.get_placement_host(orch_id)

            if host_name != "none" and \
               host_name in _app_topology.candidate_list_map[orch_id]:
                LOG.warn("vm is already placed in one of candidate hosts")

                if not _app_topology.update_placement_state(orch_id,
                                                            host=host_name):
                    LOG.error(_app_topology.status)
                else:
                    LOG.debug("done update state")

                    uuid = _app_topology.get_placement_uuid(orch_id)

                    host = self.resource.hosts[host_name]
                    if not host.exist_vm(uuid=uuid):
                        self._update_uuid(orch_id, uuid, host_name)
                        LOG.debug("done update uuid in host")

            elif self.search.re_plan(_app_topology) is True:
                LOG.debug("done search")

                self._update_placement_states(_app_topology)
                if _app_topology.status == "success":
                    LOG.debug("done update states")

                    self._update_placement_hosts(_app_topology)
                    LOG.debug("done update hosts")

                    self._delete_old_placements(_app_topology.old_vm_map)
                    self._update_resource_status(_app_topology)
                    LOG.debug("done update resource status")
            else:
                # FIXME(gjung): if 'replan' fails, remove all pending vms?

                if _app_topology.status == "success":
                    _app_topology.status = "failed"

        elif _app_topology.action == "identify":
            if not _app_topology.update_placement_state(_app_topology.id_map.keys()[0]):
                LOG.error(_app_topology.status)
            else:
                LOG.debug("done update state")

                orch_id = _app_topology.id_map.keys()[0]
                uuid = _app_topology.get_placement_uuid(orch_id)
                host_name = _app_topology.get_placement_host(orch_id)
                self._update_uuid(orch_id, uuid, host_name)
                LOG.debug("done update uuid in host")

        elif _app_topology.action == "migrate":
            if self.search.re_plan(_app_topology) is True:
                self._update_placement_states(_app_topology)
                if _app_topology.status == "success":
                    self._update_placement_hosts(_app_topology)
                    self._delete_old_placements(_app_topology.old_vm_map)
                    self._update_resource_status(_app_topology)
            else:
                if _app_topology.status == "success":
                    _app_topology.status = "failed"

    def _update_placement_states(self, _app_topology):
        """Update state of each placement."""
        for v, p in self.search.node_placements.iteritems():
            if isinstance(v, VM):
                if not _app_topology.update_placement_state(v.orch_id,
                                                            host=p.host_name):
                    LOG.error(_app_topology.status)
                    break

    def _update_placement_hosts(self, _app_topology):
        """Update stack with assigned hosts."""

        for v, p in self.search.node_placements.iteritems():
            if isinstance(v, VM):
                host = p.host_name
                _app_topology.update_placement_vm_host(v.orch_id, host)
                LOG.debug(" vm: " + v.orch_id + " placed in " + host)
            elif isinstance(v, Group):
                host = None
                if v.level == "host":
                    host = p.host_name
                elif v.level == "rack":
                    host = p.rack_name
                elif v.level == "cluster":
                    host = p.cluster_name
                _app_topology.update_placement_group_host(v.orch_id, host)
                LOG.debug(" affinity: " + v.orch_id + " placed in " + host)

    def _delete_old_placements(self, _old_placements):
        """Delete old placements from host and groups."""

        for _v_id, vm_alloc in _old_placements.iteritems():
            self.resource.remove_vm_from_host(vm_alloc, orch_id=_v_id,
                                              uuid=_v_id)
            self.resource.update_host_time(vm_alloc["host"])

            host = self.resource.hosts[vm_alloc["host"]]
            self.resource.remove_vm_from_groups(host, orch_id=_v_id,
                                                uuid=_v_id)

        self.resource.update_topology(store=False)

    def _update_resource_status(self, _app_topology):
        """Update resource status based on placements."""

        for v, np in self.search.node_placements.iteritems():
            if isinstance(v, VM):
                vm_info = {}
                vm_info["stack_id"] = _app_topology.app_id
                vm_info["orch_id"] = v.orch_id
                vm_info["uuid"] = _app_topology.get_placement_uuid(v.orch_id)
                vm_info["name"] = v.name

                vm_alloc = {}
                vm_alloc["host"] = np.host_name
                vm_alloc["vcpus"] = v.vCPUs
                vm_alloc["mem"] = v.mem
                vm_alloc["local_volume"] = v.local_volume_size

                if self.resource.add_vm_to_host(vm_alloc, vm_info) is True:
                    self.resource.update_host_time(np.host_name)

                self._update_grouping(v,
                                      self.search.avail_hosts[np.host_name],
                                      vm_info)

        self.resource.update_topology(store=False)

    def _update_grouping(self, _v, _host, _vm_info):
        """Update group status in resource."""

        for lgk, lg in _host.host_memberships.iteritems():
            if lg.group_type == "EX" or \
               lg.group_type == "AFF" or \
               lg.group_type == "DIV":
                lg_name = lgk.split(":")
                if lg_name[0] == "host" and lg_name[1] != "any":
                    self.resource.add_group(_host.host_name,
                                            lgk, lg.group_type)

        if _host.rack_name != "any":
            for lgk, lg in _host.rack_memberships.iteritems():
                if lg.group_type == "EX" or \
                   lg.group_type == "AFF" or \
                   lg.group_type == "DIV":
                    lg_name = lgk.split(":")
                    if lg_name[0] == "rack" and lg_name[1] != "any":
                        self.resource.add_group(_host.rack_name,
                                                lgk, lg.group_type)

        if _host.cluster_name != "any":
            for lgk, lg in _host.cluster_memberships.iteritems():
                if lg.group_type == "EX" or \
                   lg.group_type == "AFF" or \
                   lg.group_type == "DIV":
                    lg_name = lgk.split(":")
                    if lg_name[0] == "cluster" and lg_name[1] != "any":
                        self.resource.add_group(_host.cluster_name,
                                                lgk, lg.group_type)

        vm_groups = []
        self._collect_groups_of_vm(_v, vm_groups)

        host = self.resource.hosts[_host.host_name]
        self.resource.add_vm_to_groups(host, _vm_info, vm_groups)

    def _collect_groups_of_vm(self, _v, _vm_groups):
        """Collect all groups of the vm of its parent (affinity)."""

        if isinstance(_v, VM):
            for es in _v.extra_specs_list:
                if "host_aggregates" in es.keys():
                    lg_list = es["host_aggregates"]
                    for lgk in lg_list:
                        if lgk not in _vm_groups:
                            _vm_groups.append(lgk)

            if _v.availability_zone is not None:
                az = _v.availability_zone.split(":")[0]
                if az not in _vm_groups:
                    _vm_groups.append(az)

        for _, g in _v.exclusivity_groups.iteritems():
            if g not in _vm_groups:
                _vm_groups.append(g)

        for _, g in _v.diversity_groups.iteritems():
            if g not in _vm_groups:
                _vm_groups.append(g)

        if isinstance(_v, Group):
            name = _v.level + ":" + _v.name
            if name not in _vm_groups:
                _vm_groups.append(name)

        if _v.surgroup is not None:
            self._collect_groups_of_vm(_v.surgroup, _vm_groups)

    def _update_uuid(self, _orch_id, _uuid, _host_name):
        """Update physical uuid of placement in host."""

        host = self.resource.hosts[_host_name]
        if host.update_uuid(_orch_id, _uuid) is True:
            self.resource.update_host_time(_host_name)
        else:
            LOG.warn("fail to update uuid in host = " + host.name)

        self.resource.update_uuid_in_groups(_orch_id, _uuid, host)

        self.resource.update_topology(store=False)

    def _delete_placement_in_host(self, _orch_id, _vm_alloc):
        self.resource.remove_vm_from_host(_vm_alloc, orch_id=_orch_id)
        self.resource.update_host_time(_vm_alloc["host"])

        host = self.resource.hosts[_vm_alloc["host"]]
        self.resource.remove_vm_from_groups(host, orch_id=_orch_id)

        self.resource.update_topology(store=False)
