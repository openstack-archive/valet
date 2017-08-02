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

"""App Topology Parser.
- Restrictions of nested groups: EX in EX, EX in DIV, DIV in EX, DIV in DIV
- VM/group cannot exist in multiple EX groups
- Nested group's level cannot be higher than nesting group
- No supporting the following Heat components
    OS::Nova::ServerGroup
    OS::Heat::AutoScalingGroup
    OS::Heat::Stack
    OS::Heat::ResourceGroup
    OS::Heat::ResourceGroup
"""

import json
import six
import traceback

from oslo_log import log

from valet.engine.optimizer.app_manager.group import Group
from valet.engine.optimizer.app_manager.group import LEVEL
from valet.engine.optimizer.app_manager.vm import VM

LOG = log.getLogger(__name__)


class Parser(object):
    """This class handles parsing out the data related to the desired
    topology from a template.
    """

    def __init__(self, _db):
        self.db = _db

        self.status = "success"

    def set_topology(self, _app_id, _stack):
        """Parse stack resources to set info for search."""

        groups = {}
        vms = {}

        group_assignments = {}

        for rk, r in _stack["placements"].iteritems():
            if r["type"] == "OS::Nova::Server":
                vm = VM(_app_id, rk)

                if "name" in r.keys():
                    vm.name = r["name"]

                if "resource_id" in r.keys():
                    vm.uuid = r["resource_id"]

                if "flavor" in r["properties"].keys():
                    flavor_id = r["properties"]["flavor"]
                    if isinstance(flavor_id, six.string_types):
                        vm.flavor = flavor_id
                    else:
                        vm.flavor = str(flavor_id)
                else:
                    self.status = "flavor attribute is missing in "
                                  "OS::Nova::Server"
                    return {}, {}

                if "image" in r["properties"].keys():
                    image_id = r["properties"]["image"]
                    if isinstance(image_id, six.string_types):
                        vm.image = image_id
                    else:
                        vm.image = str(image_id)
                else:
                    self.status = "image attribute is missing in "
                                  "OS::Nova::Server"
                    return {}, {}

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

                    for mk, mv in extra_specs.iteritems():
                        if mk == "valet":
                            group_list = []

                            if isinstance(mv, six.string_types):
                                try:
                                    groups_dict = json.loads(mv)
                                    if "groups" in groups_dict.keys():
                                        group_list = groups_dict["groups"]
                                except Exception:
                                    LOG.error("valet metadata parsing: " +
                                              traceback.format_exc())
                                    self.status = "wrong valet metadata format"
                                    return {}, {}
                            else:
                                if "groups" in mv.keys():
                                    group_list = mv["groups"]

                            self._assign_groups(rk, "flavor",
                                                group_list, group_assignments)

                    vm.extra_specs_list.append(extra_specs)

                if "metadata" in r["properties"].keys():
                    if "valet" in r["properties"]["metadata"].keys():
                        if "groups" in r["properties"]["metadata"]["valet"].keys():
                            group_list = r["properties"]["metadata"]["valet"]["groups"]
                            self._assign_groups(rk, "meta", group_list, group_assignments)

                if "availability_zone" in r["properties"].keys():
                    az = r["properties"]["availability_zone"]
                    # NOTE: do not allow to specify a certain host name
                    vm.availability_zone = az.split(":")[0]

                vms[vm.orch_id] = vm
            elif r["type"] == "OS::Cinder::Volume":
                pass
            elif r["type"] == "OS::Valet::GroupAssignment":
                group_assignments[rk] = r

        if len(group_assignments) > 0:
            groups = self._set_groups(group_assignments, _app_id, _stack)
            if groups is None:
                return None, None
            if len(groups) == 0:
                return {}, {}

        if self._merge_diversity_groups(group_assignments, groups,
                                        vms) is False:
            return {}, {}
        if self._merge_exclusivity_groups(group_assignments, groups,
                                          vms) is False:
            return {}, {}
        if self._merge_affinity_groups(group_assignments, groups,
                                       vms) is False:
            return {}, {}

        # Delete all EX and DIV groups after merging
        groups = {vgk: vg for vgk, vg in groups.iteritems() \
                 if vg.group_type != "DIV" and vg.group_type != "EX"}

        if len(groups) == 0 and len(vms) == 0:
            self.status = "no vms found in stack"

        return groups, vms

    def _assign_groups(self, _rk, _tag, _group_list, _group_assignments):
        """Create group assignment."""

        count = 0
        for g_id in _group_list:
            rk = _rk + "_" + _tag + "_" + str(count)
            count += 1
            properties = {}
            properties["group"] = g_id
            properties["resources"] = []
            properties["resources"].append(_rk)
            assignment = {}
            assignment["properties"] = properties
            _group_assignments[rk] = assignment

    def _set_groups(self, _group_assignments, _app_id, _stack):
        """Parse valet groups for search."""

        if _stack["groups"] is None:
            _stack["groups"] = {}

        groups = {}

        for rk, assignment in _group_assignments.iteritems():
            if "group" in assignment["properties"].keys():
                g_id = assignment["properties"]["group"]
                if g_id in _stack["groups"].keys():
                    group = self._make_group(_app_id, g_id, _stack["groups"][g_id])
                    if group is not None:
                        groups[group.orch_id] = group
                    else:
                        return {}
                else:
                    group_info = self.db.get_group(g_id)
                    if group_info is None:
                        return None
                    elif len(group_info) == 0:
                        self.status = "no group found"
                        return {}

                    g = {}
                    g["type"] = group_info["type"]
                    g["name"] = group_info["name"]
                    g["level"] = group_info["level"]

                    _stack["groups"][group_info["id"]] = g

                    assignment["properties"]["group"] = group_info["id"]

                    group = self._make_group(_app_id, group_info["id"], g)
                    if group is not None:
                        groups[group.orch_id] = group
                    else:
                        return {}
            else:
                self.status = "group assignment format error"
                return {}

        return groups

    def _make_group(self, _app_id, _gk, _g):
        """Make a group object."""

        group = Group(_app_id, _gk)

        group.group_type = None
        if "type" in _g.keys():
            if _g["type"] == "affinity":
                group.group_type = "AFF"
            elif _g["type"] == "diversity":
                group.group_type = "DIV"
            elif _g["type"] == "exclusivity":
                group.group_type = "EX"
            else:
                self.status = "unknown group type = " + _g["type"] +
                              " for group = " + _gk
                return None
        else:
            self.status = "no group type for group = " + _gk
            return None

        if "name" in _g.keys():
            group.name = _g["name"]
        else:
            if group.group_type == "EX":
                self.status = "no exclusivity group name for group = " + _gk
                return None
            else:
                group.name = "any"

        if "level" in _g.keys():
            group.level = _g["level"]
        else:
            self.status = "no grouping level for group = " + _gk
            return None

        if "host" in _g.keys():
            group.host = _g["host"]

        return group

    def _merge_diversity_groups(self, _elements, _groups, _vms):
        """ to merge diversity sub groups """

        for level in LEVEL:
            for rk, r in _elements.iteritems():
                group = None

                if "group" in r["properties"].keys():
                    if _groups[r["properties"]["group"]].level == level and \
                       _groups[r["properties"]["group"]].group_type == "DIV":
                        group = _groups[r["properties"]["group"]]
                    else:
                        continue

                if group is None:
                    self.status = "no diversity group reference in assignment"
                                  " = " + rk
                    return False

                if "resources" not in r["properties"].keys():
                    self.status = "group assignment format error"
                    return False

                for vk in r["properties"]["resources"]:
                    if vk in _vms.keys():
                        group.subgroups[vk] = _vms[vk]
                        _vms[vk].diversity_groups[group.orch_id] = group.level
                                                            + ":" + group.name
                    elif vk in _groups.keys():

                        # FIXME(gjung): vk refers to GroupAssignment
                        # orch_id -> uuid of group

                        vg = _groups[vk]
                        if LEVEL.index(vg.level) > LEVEL.index(level):
                            self.status = "grouping scope: nested group's"
                                          " level is higher"
                            return False
                        if vg.group_type == "DIV" or vg.group_type == "EX":
                            self.status = vg.group_type + " not allowd to be "
                                          "nested in diversity group"
                            return False
                        group.subgroups[vk] = vg
                        vg.diversity_groups[group.orch_id] = group.level + ":"
                                                             + group.name
                    else:
                        self.status = "invalid resource = " + vk +
                                      " in assignment = " + rk
                        return False

        return True

    def _merge_exclusivity_groups(self, _elements, _groups, _vms):
        """ to merge exclusivity sub groups """

        for level in LEVEL:
            for rk, r in _elements.iteritems():
                group = None

                if "group" in r["properties"].keys():
                    if _groups[r["properties"]["group"]].level == level and \
                       _groups[r["properties"]["group"]].group_type == "EX":
                        group = _groups[r["properties"]["group"]]
                    else:
                        continue

                if group is None:
                    self.status = "no group reference in exclusivity"
                                  " assignment = " + rk
                    return False

                if "resources" not in r["properties"].keys():
                    self.status = "group assignment format error"
                    return False

                for vk in r["properties"]["resources"]:
                    if vk in _vms.keys():
                        group.subgroups[vk] = _vms[vk]
                        _vms[vk].exclusivity_groups[group.orch_id] = group.level + ":" + group.name
                    elif vk in _groups.keys():
                        vg = _groups[vk]
                        if LEVEL.index(vg.level) > LEVEL.index(level):
                            self.status = "grouping scope: nested group's level is higher"
                            return False
                        if vg.group_type == "DIV" or vg.group_type == "EX":
                            self.status = vg.group_type + ") not allowd to be"
                                          " nested in exclusivity group"
                            return False
                        group.subgroups[vk] = vg
                        vg.exclusivity_groups[group.orch_id] = group.level +
                                                               ":" + group.name
                    else:
                        self.status = "invalid resource = " + vk +
                                      " in assignment = " + rk
                        return False

        return True

    def _merge_affinity_groups(self, _elements, _groups, _vms):
        # key is orch_id of vm or group & value is its parent group
        affinity_map = {}

        for level in LEVEL:
            for rk, r in _elements.iteritems():
                group = None

                if "group" in r["properties"].keys():
                    if r["properties"]["group"] in _groups.keys():
                        if _groups[r["properties"]["group"]].level == level and \
                           _groups[r["properties"]["group"]].group_type == "AFF":
                            group = _groups[r["properties"]["group"]]
                        else:
                            continue
                    else:
                        continue

                if group is None:
                    self.status = "no group reference in affinity assignment "
                                  "= " + rk
                    return False

                if "resources" not in r["properties"].keys():
                    self.status = "group assignment format error"
                    return False

                for vk in r["properties"]["resources"]:
                    if vk in _vms.keys():
                        self._merge_vm(group, vk, _vms, affinity_map)
                    elif vk in _groups.keys():
                        if not self._merge_group(group, vk, _groups, _vms,
                                                 _elements, affinity_map):
                            return False
                    else:
                        # vk belongs to the other group already or
                        # refer to invalid resource
                        if vk not in affinity_map.keys():
                            self.status = "invalid resource = " + vk +
                                          " in assignment = " + rk
                            return False
                        if affinity_map[vk].orch_id != group.orch_id:
                            if self._exist_in_subgroups(vk, group) is None:
                                self._set_implicit_grouping(vk,
                                                            group,
                                                            affinity_map,
                                                            _groups)

        return True

    def _merge_subgroups(self, _group, _subgroups, _vms, _groups, _elements,
                         _affinity_map):
        """To merge recursive affinity sub groups"""

        for vk, _ in _subgroups.iteritems():
            if vk in _vms.keys():
                self._merge_vm(_group, vk, _vms, _affinity_map)
            elif vk in _groups.keys():
                if not self._merge_group(_group, vk, _groups, _vms,
                                         _elements, _affinity_map):
                    return False
            else:
                # vk belongs to the other group already or
                # refer to invalid resource
                if vk not in _affinity_map.keys():
                    self.status = "invalid resource = " + vk
                    return False
                if _affinity_map[vk].orch_id != _group.orch_id:
                    if self._exist_in_subgroups(vk, _group) is None:
                        self._set_implicit_grouping(vk, _group, _affinity_map,
                                                    _groups)

        return True

    def _merge_vm(self, _group, _vk, _vms, _affinity_map):
        """ to merge a vm into the group """
        _group.subgroups[_vk] = _vms[_vk]
        _vms[_vk].surgroup = _group
        _affinity_map[_vk] = _group
        self._add_implicit_diversity_groups(_group,
                                            _vms[_vk].diversity_groups)
        self._add_implicit_exclusivity_groups(_group,
                                              _vms[_vk].exclusivity_groups)
        self._add_memberships(_group, _vms[_vk])
        del _vms[_vk]

    def _merge_group(self, _group, _vk, _groups, _vms, _elements,
                     _affinity_map):
        """ to merge a group into the group """

        vg = _groups[_vk]

        if LEVEL.index(vg.level) > LEVEL.index(_group.level):
            self.status = "grouping scope: nested group's level is higher"
            return False

        if vg.group_type == "DIV" or vg.group_type == "EX":
            if not self._merge_subgroups(_group, vg.subgroups, _vms, _groups,
                                         _elements, _affinity_map):
                return False
            del _groups[_vk]
        else:
            if self._exist_in_subgroups(_vk, _group) is None:
                if not self._get_subgroups(vg, _elements, _groups, _vms,
                                           _affinity_map):
                    return False

                _group.subgroups[_vk] = vg
                vg.surgroup = _group
                _affinity_map[_vk] = _group
                self._add_implicit_diversity_groups(_group,
                                                    vg.diversity_groups)
                self._add_implicit_exclusivity_groups(_group,
                                                      vg.exclusivity_groups)
                self._add_memberships(_group, vg)
                del _groups[_vk]

        return True

    def _get_subgroups(self, _group, _elements, _groups, _vms, _affinity_map):
        """ to merge all deeper subgroups """

        for rk, r in _elements.iteritems():
            if r["properties"]["group"] == _group.orch_id:
                for vk in r["properties"]["resources"]:
                    if vk in _vms.keys():
                        self._merge_vm(_group, vk, _vms, _affinity_map)
                    elif vk in _groups.keys():
                        if not self._merge_group(_group, vk, _groups, _vms,
                                                 _elements, _affinity_map):
                            return False
                    else:
                        if vk not in _affinity_map.keys():
                            self.status = "invalid resource = " + vk
                            return False

                        if _affinity_map[vk].orch_id != _group.orch_id:
                            if self._exist_in_subgroups(vk, _group) is None:
                                self._set_implicit_grouping(vk,
                                                            _group,
                                                            _affinity_map,
                                                            _groups)
                return True

        return False

    def _add_implicit_diversity_groups(self, _group, _diversity_groups):
        """ to add subgroup's diversity groups """
        for dz, level in _diversity_groups.iteritems():
            l = level.split(":", 1)[0]
            if LEVEL.index(l) >= LEVEL.index(_group.level):
                _group.diversity_groups[dz] = level

    def _add_implicit_exclusivity_groups(self, _group, _exclusivity_groups):
        """ to add subgroup's exclusivity groups """
        for ex, level in _exclusivity_groups.iteritems():
            l = level.split(":", 1)[0]
            if LEVEL.index(l) >= LEVEL.index(_group.level):
                _group.exclusivity_groups[ex] = level

    def _add_memberships(self, _group, _v):
        """ to add subgroups's host-aggregates and AZs """
        if isinstance(_v, VM) or isinstance(_v, Group):
            for extra_specs in _v.extra_specs_list:
                _group.extra_specs_list.append(extra_specs)
            if isinstance(_v, VM) and _v.availability_zone is not None:
                if _v.availability_zone not in _group.availability_zone_list:
                    _group.availability_zone_list.append(_v.availability_zone)
            if isinstance(_v, Group):
                for az in _v.availability_zone_list:
                    if az not in _group.availability_zone_list:
                        _group.availability_zone_list.append(az)

    def _set_implicit_grouping(self, _vk, _s_vg, _affinity_map, _groups):
        """ take vk's most top parent as a s_vg's child group """

        t_vg = _affinity_map[_vk]  # where _vk currently belongs to

        if t_vg.orch_id in _affinity_map.keys():
            # if the parent belongs to the other parent group
            self._set_implicit_grouping(t_vg.orch_id, _s_vg,
                                        _affinity_map, _groups)
        else:
            if LEVEL.index(t_vg.level) > LEVEL.index(_s_vg.level):
                t_vg.level = _s_vg.level
            if self._exist_in_subgroups(t_vg.orch_id, _s_vg) is None:
                _s_vg.subgroups[t_vg.orch_id] = t_vg
                t_vg.surgroup = _s_vg
                _affinity_map[t_vg.orch_id] = _s_vg
                self._add_implicit_diversity_groups(_s_vg,
                                                    t_vg.diversity_groups)
                self._add_implicit_exclusivity_groups(_s_vg,
                                                      t_vg.exclusivity_groups)
                self._add_memberships(_s_vg, t_vg)
                del _groups[t_vg.orch_id]

    def _exist_in_subgroups(self, _vk, _vg):
        """ to check if vk exists in a group recursively """
        containing_vg_id = None
        for vk, v in _vg.subgroups.iteritems():
            if vk == _vk:
                containing_vg_id = _vg.orch_id
                break
            else:
                if isinstance(v, Group):
                    containing_vg_id = self._exist_in_subgroups(_vk, v)
                    if containing_vg_id is not None:
                        break
        return containing_vg_id
