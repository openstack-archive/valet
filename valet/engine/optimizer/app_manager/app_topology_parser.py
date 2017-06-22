#!/bin/python


import six

from valet.engine.optimizer.app_manager.vgroup import VGroup, LEVEL
from valet.engine.optimizer.app_manager.vm import VM


class Parser(object):

    def __init__(self):
        self.status = "success"

    def set_topology(self, _app_id, _elements, _groups):
        '''Parse stack resources to set info for search.'''

        vgroups = {}
        vms = {}

        if _groups is not None:
            vgroups = self._set_vgroups(_app_id, _groups)
            if vgroups is None:
                return {}, {}

        vgroup_assignments = {}
        for rk, r in _elements.iteritems():
            if r["type"] == "OS::Nova::Server":
                vm = VM(_app_id, rk)

                if "name" in r.keys():
                    vm.name = r["name"]
                if "resource_id" in r.keys():
                    vm.uuid = r["resource_id"]

                flavor_id = r["properties"]["flavor"]
                if isinstance(flavor_id, six.string_types):
                    vm.flavor = flavor_id
                else:
                    vm.flavor = str(flavor_id)
                image_id = r["properties"]["image"]
                if isinstance(image_id, six.string_types):
                    vm.image = image_id
                else:
                    vm.image = str(image_id)

                if "host" in r["properties"].keys():
                    vm.host = r["properties"]["host"]

                if "vcpus" in r["properties"].keys():
                    vm.vCPUs = int(r["properties"]["vcpus"])
                if "mem" in r["properties"].keys():
                    vm.mem = int(r["properties"]["mem"])
                if "local_volume" in r["properties"].keys():
                    vm.local_volume_size = int(r["properties"]["local_volume"])
                if "extra_specs" in r["properties"].keys():
                    extra_specs = {}
                    for mk, mv in r["properties"]["extra_specs"].iteritems():
                        extra_specs[mk] = mv
                    vm.extra_specs_list.append(extra_specs)

                if "availability_zone" in r["properties"].keys():
                    az = r["properties"]["availability_zone"]
                    # NOTE: do not allow to specify a certain host name
                    vm.availability_zone = az.split(":")[0]

                if "metadata" in r["properties"].keys():
                    if "valet" in r["properties"]["metadata"].keys():
                        if "groups" in r["properties"]["metadata"]["valet"].keys():
                            group_list = r["properties"]["metadata"]["valet"]["groups"]
                            self._assign_groups(rk, group_list, vgroup_assignments)

                vms[vm.orch_id] = vm
            elif r["type"] == "OS::Cinder::Volume":
                pass
            elif r["type"] == "OS::Valet::GroupAssignment":
                vgroup_assignments[rk] = r

        if self._merge_diversity_groups(vgroup_assignments, vgroups, vms) is False:
            return {}, {}
        if self._merge_exclusivity_groups(vgroup_assignments, vgroups, vms) is False:
            return {}, {}
        if self._merge_affinity_groups(vgroup_assignments, vgroups, vms) is False:
            return {}, {}

        # Delete all EX and DIV vgroups after merging
        vgroups = {vgk: vg for vgk, vg in vgroups.iteritems()
                   if vg.vgroup_type != "DIV" and vg.vgroup_type != "EX"}

        if len(vgroups) == 0 and len(vms) == 0:
            self.status = "no vms found in stack"

        return vgroups, vms

    def _set_vgroups(self, _app_id, _groups):
        ''' to parse valet groups for search '''

        vgroups = {}

        for gk, g in _groups.iteritems():
            vgroup = VGroup(_app_id, gk)

            vgroup.vgroup_type = None
            if "type" in g.keys():
                if g["type"] == "affinity":
                    vgroup.vgroup_type = "AFF"
                elif g["type"] == "diversity":
                    vgroup.vgroup_type = "DIV"
                elif g["type"] == "exclusivity":
                    vgroup.vgroup_type = "EX"
                else:
                    self.status = "unknown group type = " + g["type"] + " for group = " + gk
                    return None
            else:
                self.status = "no group type for group = " + gk
                return None

            if "name" in g.keys():
                vgroup.name = g["name"]
            else:
                if vgroup.vgroup_type == "EX":
                    self.status = "no exclusivity group name for group = " + gk
                    return None
                else:
                    vgroup.name = "any"

            if "level" in g.keys():
                vgroup.level = g["level"]
            else:
                self.status = "no grouping level for group = " + gk
                return None

            if "host" in g.keys():
                vgroup.host = g["host"]

            vgroups[vgroup.orch_id] = vgroup

        return vgroups

    def _assign_groups(self, _rk, _group_list, _vgroup_assignments):
        count = 0
        for g_id in _group_list:
            rk = _rk + "_" + str(count)
            count += 1
            properties = {}
            properties["group"] = g_id
            properties["resources"] = []
            properties["resources"].append(_rk)
            assignment = {}
            assignment["properties"] = properties
            _vgroup_assignments[rk] = assignment

    def _merge_diversity_groups(self, _elements, _vgroups, _vms):
        ''' to merge diversity sub groups '''

        for level in LEVEL:
            for rk, r in _elements.iteritems():
                vgroup = None
                if "group" in r["properties"].keys():
                    if r["properties"]["group"] in _vgroups.keys():
                        if _vgroups[r["properties"]["group"]].level == level and \
                           _vgroups[r["properties"]["group"]].vgroup_type == "DIV":
                            vgroup = _vgroups[r["properties"]["group"]]
                        else:
                            continue
                if vgroup is None:
                    self.status = "no diversity group reference in assignment = " + rk
                    return False

                for vk in r["properties"]["resources"]:
                    if vk in _vms.keys():
                        vgroup.subvgroups[vk] = _vms[vk]
                        _vms[vk].diversity_groups[vgroup.orch_id] = vgroup.level + ":" + vgroup.name
                    elif vk in _vgroups.keys():
                        vg = _vgroups[vk]
                        if LEVEL.index(vg.level) > LEVEL.index(level):
                            self.status = "grouping scope: nested group's level is higher"
                            return False
                        if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                            self.status = vg.vgroup_type + " not allowd to be nested in diversity group"
                            return False
                        vgroup.subvgroups[vk] = vg
                        vg.diversity_groups[vgroup.orch_id] = vgroup.level + ":" + vgroup.name
                    else:
                        self.status = "invalid resource = " + vk + " in assignment = " + rk
                        return False
        return True

    def _merge_exclusivity_groups(self, _elements, _vgroups, _vms):
        ''' to merge exclusivity sub groups '''

        for level in LEVEL:
            for rk, r in _elements.iteritems():
                vgroup = None
                if "group" in r["properties"].keys():
                    if r["properties"]["group"] in _vgroups.keys():
                        if _vgroups[r["properties"]["group"]].level == level and \
                           _vgroups[r["properties"]["group"]].vgroup_type == "EX":
                            vgroup = _vgroups[r["properties"]["group"]]
                        else:
                            continue
                if vgroup is None:
                    self.status = "no group reference in exclusivity assignment = " + rk
                    return False

                for vk in r["properties"]["resources"]:
                    if vk in _vms.keys():
                        vgroup.subvgroups[vk] = _vms[vk]
                        _vms[vk].exclusivity_groups[vgroup.orch_id] = vgroup.level + ":" + vgroup.name
                    elif vk in _vgroups.keys():
                        vg = _vgroups[vk]
                        if LEVEL.index(vg.level) > LEVEL.index(level):
                            self.status = "grouping scope: nested group's level is higher"
                            return False
                        if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                            self.status = vg.vgroup_type + ") not allowd to be nested in exclusivity group"
                            return False
                        vgroup.subvgroups[vk] = vg
                        vg.exclusivity_groups[vgroup.orch_id] = vgroup.level + ":" + vgroup.name
                    else:
                        self.status = "invalid resource = " + vk + " in assignment = " + rk
                        return False
        return True

    def _merge_affinity_groups(self, _elements, _vgroups, _vms):
        ''' to merge affinity sub groups '''

        affinity_map = {}  # key is orch_id of vm or vgroup & value is its parent vgroup

        for level in LEVEL:
            for rk, r in _elements.iteritems():
                vgroup = None
                if "group" in r["properties"].keys():
                    if r["properties"]["group"] in _vgroups.keys():
                        if _vgroups[r["properties"]["group"]].level == level and \
                           _vgroups[r["properties"]["group"]].vgroup_type == "AFF":
                            vgroup = _vgroups[r["properties"]["group"]]
                        else:
                            continue
                    else:
                        continue
                if vgroup is None:
                    self.status = "no group reference in affinity assignment = " + rk
                    return False

                for vk in r["properties"]["resources"]:
                    if vk in _vms.keys():
                        self._merge_vm(vgroup, vk, _vms, affinity_map)
                    elif vk in _vgroups.keys():
                        if not self._merge_vgroup(vgroup, vk, _vgroups, _vms, _elements, affinity_map):
                            return False
                    else:  # vk belongs to the other vgroup already or refer to invalid resource
                        if vk not in affinity_map.keys():
                            self.status = "invalid resource = " + vk + " in assignment = " + rk
                            return False
                        if affinity_map[vk].orch_id != vgroup.orch_id:
                            if self._exist_in_subgroups(vk, vgroup) is None:
                                self._set_implicit_grouping(vk, vgroup, affinity_map, _vgroups)

        return True

    def _merge_subgroups(self, _vgroup, _subgroups, _vms, _vgroups, _elements, _affinity_map):
        ''' to merge recursive affinity sub groups '''

        for vk, _ in _subgroups.iteritems():
            if vk in _vms.keys():
                self._merge_vm(_vgroup, vk, _vms, _affinity_map)
            elif vk in _vgroups.keys():
                if not self._merge_vgroup(_vgroup, vk, _vgroups, _vms, _elements, _affinity_map):
                    return False
            else:  # vk belongs to the other vgroup already or refer to invalid resource
                if vk not in _affinity_map.keys():
                    self.status = "invalid resource = " + vk
                    return False
                if _affinity_map[vk].orch_id != _vgroup.orch_id:
                    if self._exist_in_subgroups(vk, _vgroup) is None:
                        self._set_implicit_grouping(vk, _vgroup, _affinity_map, _vgroups)
        return True

    def _merge_vm(self, _vgroup, _vk, _vms, _affinity_map):
        ''' to merge a vm into the vgroup '''
        _vgroup.subvgroups[_vk] = _vms[_vk]
        _vms[_vk].survgroup = _vgroup
        _affinity_map[_vk] = _vgroup
        self._add_implicit_diversity_groups(_vgroup, _vms[_vk].diversity_groups)
        self._add_implicit_exclusivity_groups(_vgroup, _vms[_vk].exclusivity_groups)
        self._add_memberships(_vgroup, _vms[_vk])
        del _vms[_vk]

    def _merge_vgroup(self, _vgroup, _vk, _vgroups, _vms, _elements, _affinity_map):
        ''' to merge a vgroup into the vgroup '''
        vg = _vgroups[_vk]
        if LEVEL.index(vg.level) > LEVEL.index(_vgroup.level):
            self.status = "grouping scope: nested group's level is higher"
            return False
        if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
            if not self._merge_subgroups(_vgroup, vg.subvgroups, _vms, _vgroups, _elements, _affinity_map):
                return False
            del _vgroups[_vk]
        else:
            if self._exist_in_subgroups(_vk, _vgroup) is None:
                if not self._get_subgroups(vg, _elements, _vgroups, _vms, _affinity_map):
                    return False
                _vgroup.subvgroups[_vk] = vg
                vg.survgroup = _vgroup
                _affinity_map[_vk] = _vgroup
                self._add_implicit_diversity_groups(_vgroup, vg.diversity_groups)
                self._add_implicit_exclusivity_groups(_vgroup, vg.exclusivity_groups)
                self._add_memberships(_vgroup, vg)
                del _vgroups[_vk]
        return True

    def _get_subgroups(self, _vgroup, _elements, _vgroups, _vms, _affinity_map):
        ''' to merge all deeper subgroups '''
        for rk, r in _elements.iteritems():
            if r["properties"]["group"] == _vgroup.orch_id:
                for vk in r["properties"]["resources"]:
                    if vk in _vms.keys():
                        self._merge_vm(_vgroup, vk, _vms, _affinity_map)
                    elif vk in _vgroups.keys():
                        if not self._merge_vgroup(_vgroup, vk, _vgroups, _vms, _elements, _affinity_map):
                            return False
                    else:
                        if vk not in _affinity_map.keys():
                            self.status = "invalid resource = " + vk
                            return False
                        if _affinity_map[vk].orch_id != _vgroup.orch_id:
                            if self._exist_in_subgroups(vk, _vgroup) is None:
                                self._set_implicit_grouping(vk, _vgroup, _affinity_map, _vgroups)
                return True
        return False

    def _add_implicit_diversity_groups(self, _vgroup, _diversity_groups):
        ''' to add subgroup's diversity groups '''
        for dz, level in _diversity_groups.iteritems():
            l = level.split(":", 1)[0]
            if LEVEL.index(l) >= LEVEL.index(_vgroup.level):
                _vgroup.diversity_groups[dz] = level

    def _add_implicit_exclusivity_groups(self, _vgroup, _exclusivity_groups):
        ''' to add subgroup's exclusivity groups '''
        for ex, level in _exclusivity_groups.iteritems():
            l = level.split(":", 1)[0]
            if LEVEL.index(l) >= LEVEL.index(_vgroup.level):
                _vgroup.exclusivity_groups[ex] = level

    def _add_memberships(self, _vgroup, _v):
        ''' to add subgroups's host-aggregates and AZs '''
        if isinstance(_v, VM) or isinstance(_v, VGroup):
            for extra_specs in _v.extra_specs_list:
                _vgroup.extra_specs_list.append(extra_specs)
            if isinstance(_v, VM) and _v.availability_zone is not None:
                if _v.availability_zone not in _vgroup.availability_zone_list:
                    _vgroup.availability_zone_list.append(_v.availability_zone)
            if isinstance(_v, VGroup):
                for az in _v.availability_zone_list:
                    if az not in _vgroup.availability_zone_list:
                        _vgroup.availability_zone_list.append(az)

    def _set_implicit_grouping(self, _vk, _s_vg, _affinity_map, _vgroups):
        ''' take vk's most top parent as a s_vg's child vgroup '''

        t_vg = _affinity_map[_vk]  # where _vk currently belongs to

        if t_vg.orch_id in _affinity_map.keys():  # if the parent belongs to the other parent vgroup
            self._set_implicit_grouping(t_vg.orch_id, _s_vg, _affinity_map, _vgroups)
        else:
            if LEVEL.index(t_vg.level) > LEVEL.index(_s_vg.level):
                t_vg.level = _s_vg.level
            if self._exist_in_subgroups(t_vg.orch_id, _s_vg) is None:
                _s_vg.subvgroups[t_vg.orch_id] = t_vg
                t_vg.survgroup = _s_vg
                _affinity_map[t_vg.orch_id] = _s_vg
                self._add_implicit_diversity_groups(_s_vg, t_vg.diversity_groups)
                self._add_implicit_exclusivity_groups(_s_vg, t_vg.exclusivity_groups)
                self._add_memberships(_s_vg, t_vg)
                del _vgroups[t_vg.orch_id]

    def _exist_in_subgroups(self, _vk, _vg):
        ''' to check if vk exists in a vgroup recursively '''
        containing_vg_id = None
        for vk, v in _vg.subvgroups.iteritems():
            if vk == _vk:
                containing_vg_id = _vg.orch_id
                break
            else:
                if isinstance(v, VGroup):
                    containing_vg_id = self._exist_in_subgroups(_vk, v)
                    if containing_vg_id is not None:
                        break
        return containing_vg_id
