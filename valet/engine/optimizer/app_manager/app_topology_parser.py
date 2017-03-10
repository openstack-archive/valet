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

import six
from valet.engine.optimizer.app_manager.app_topology_base \
    import VGroup, VGroupLink, VM, VMLink, LEVELS


class Parser(object):
    """Parser Class.

    This class handles parsing out the data related to the desired
    topology from a template.
    not supported OS::Nova::ServerGroup OS::Heat::AutoScalingGroup OS::Heat::Stack OS::Heat::ResourceGroup
    """

    def __init__(self, _high_level_allowed, _logger):
        """Init Parser Class."""
        self.logger = _logger

        self.high_level_allowed = _high_level_allowed

        self.format_version = None
        self.stack_id = None          # used as application id
        self.application_name = None
        self.action = None            # [create|update|ping]

        self.candidate_list_map = {}

        self.status = "success"

    def set_topology(self, _graph):
        """Return result of set_topology which parses input to get topology."""
        if "version" in _graph.keys():
            self.format_version = _graph["version"]
        else:
            self.format_version = "0.0"

        if "stack_id" in _graph.keys():
            self.stack_id = _graph["stack_id"]
        else:
            self.stack_id = "none"

        if "application_name" in _graph.keys():
            self.application_name = _graph["application_name"]
        else:
            self.application_name = "none"

        if "action" in _graph.keys():
            self.action = _graph["action"]
        else:
            self.action = "any"

        if "locations" in _graph.keys() and len(_graph["locations"]) > 0:
            if len(_graph["resources"]) == 1:
                v_uuid = _graph["resources"].keys()[0]
                self.candidate_list_map[v_uuid] = _graph["locations"]

        return self._set_topology(_graph["resources"])

    def _set_topology(self, _elements):
        vgroups = {}
        vms = {}

        for rk, r in _elements.iteritems():
            if r["type"] == "OS::Nova::Server":
                vm = VM(self.stack_id, rk)
                if "name" in r.keys():
                    vm.name = r["name"]
                else:
                    vm.name = vm.uuid
                flavor_id = r["properties"]["flavor"]
                if isinstance(flavor_id, six.string_types):
                    vm.flavor = flavor_id
                else:
                    vm.flavor = str(flavor_id)
                if "availability_zone" in r["properties"].keys():
                    az = r["properties"]["availability_zone"]
                    # NOTE: do not allow to specify a certain host name
                    vm.availability_zone = az.split(":")[0]
                if "locations" in r.keys():
                    if len(r["locations"]) > 0:
                        self.candidate_list_map[rk] = r["locations"]
                vms[vm.uuid] = vm
                self.logger.info("vm = " + vm.uuid)
            elif r["type"] == "OS::Cinder::Volume":
                self.logger.warn("Parser: do nothing for volume at this "
                                 "version")

            elif r["type"] == "ATT::Valet::GroupAssignment":
                vgroup = VGroup(self.stack_id, rk)
                vgroup.vgroup_type = None
                if "group_type" in r["properties"].keys():
                    if r["properties"]["group_type"] == "affinity":
                        vgroup.vgroup_type = "AFF"
                    elif r["properties"]["group_type"] == "diversity":
                        vgroup.vgroup_type = "DIV"
                    elif r["properties"]["group_type"] == "exclusivity":
                        vgroup.vgroup_type = "EX"
                    else:
                        self.status = "unknown group = " + \
                                      r["properties"]["group_type"]
                        return {}, {}
                else:
                    self.status = "no group type"
                    return {}, {}

                if "group_name" in r["properties"].keys():
                    vgroup.name = r["properties"]["group_name"]
                else:
                    if vgroup.vgroup_type == "EX":
                        self.status = "no exclusivity group identifier"
                        return {}, {}
                    else:
                        vgroup.name = "any"

                if "level" in r["properties"].keys():
                    vgroup.level = r["properties"]["level"]
                    if vgroup.level != "host":
                        if self.high_level_allowed is False:
                            self.status = "only host level of affinity group allowed " + \
                                          "due to the mis-match of host naming convention"
                            return {}, {}
                else:
                    self.status = "no grouping level"
                    return {}, {}
                vgroups[vgroup.uuid] = vgroup
                self.logger.info("group = " + vgroup.name + vgroup.name + ", type = " + vgroup.vgroup_type)

        if self._merge_diversity_groups(_elements, vgroups, vms) is False:
            return {}, {}
        if self._merge_exclusivity_groups(_elements, vgroups, vms) is False:
            return {}, {}
        if self._merge_affinity_groups(_elements, vgroups, vms) is False:
            return {}, {}

        """ delete all EX and DIV vgroups after merging """
        for vgk in vgroups.keys():
            vg = vgroups[vgk]
            if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                del vgroups[vgk]

        return vgroups, vms

    def _merge_diversity_groups(self, _elements, _vgroups, _vms):
        for level in LEVELS:
            for rk, r in _elements.iteritems():
                if r["type"] == "ATT::Valet::GroupAssignment" and \
                   r["properties"]["group_type"] == "diversity" and \
                   r["properties"]["level"] == level:
                    vgroup = _vgroups[rk]
                    for vk in r["properties"]["resources"]:
                        if vk in _vms.keys():
                            vgroup.subvgroups[vk] = _vms[vk]
                            _vms[vk].diversity_groups[rk] = vgroup.level + ":" + vgroup.name
                        elif vk in _vgroups.keys():
                            vg = _vgroups[vk]
                            if LEVELS.index(vg.level) > LEVELS.index(level):
                                self.status = "grouping scope: nested " \
                                              "group's level is higher"
                                return False
                            if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                                self.status = vg.vgroup_type + " not allowd to be nested in diversity group"
                                return False
                            vgroup.subvgroups[vk] = vg
                            vg.diversity_groups[rk] = vgroup.level + ":" + \
                                vgroup.name
                        else:
                            self.status = "invalid resource = " + vk
                            return False
        return True

    def _merge_exclusivity_groups(self, _elements, _vgroups, _vms):
        for level in LEVELS:
            for rk, r in _elements.iteritems():
                if r["type"] == "ATT::Valet::GroupAssignment" and \
                   r["properties"]["group_type"] == "exclusivity" and \
                   r["properties"]["level"] == level:
                    vgroup = _vgroups[rk]
                    for vk in r["properties"]["resources"]:
                        if vk in _vms.keys():
                            vgroup.subvgroups[vk] = _vms[vk]
                            _vms[vk].exclusivity_groups[rk] = vgroup.level + ":" + vgroup.name
                        elif vk in _vgroups.keys():
                            vg = _vgroups[vk]
                            if LEVELS.index(vg.level) > LEVELS.index(level):
                                self.status = "grouping scope: nested " \
                                              "group's level is higher"
                                return False
                            if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                                self.status = vg.vgroup_type + ") not allowd to be nested in exclusivity group"
                                return False
                            vgroup.subvgroups[vk] = vg
                            vg.exclusivity_groups[rk] = vgroup.level + ":" + \
                                vgroup.name
                        else:
                            self.status = "invalid resource = " + vk
                            return False
        return True

    def _merge_affinity_groups(self, _elements, _vgroups, _vms):
        # key is uuid of vm or vgroup & value is its parent vgroup
        affinity_map = {}
        for level in LEVELS:
            for rk, r in _elements.iteritems():
                if r["type"] == "ATT::Valet::GroupAssignment" and \
                   r["properties"]["group_type"] == "affinity" and \
                   r["properties"]["level"] == level:
                    vgroup = None
                    if rk in _vgroups.keys():
                        vgroup = _vgroups[rk]
                    else:
                        continue

                    for vk in r["properties"]["resources"]:
                        if vk in _vms.keys():
                            vgroup.subvgroups[vk] = _vms[vk]
                            _vms[vk].survgroup = vgroup
                            affinity_map[vk] = vgroup
                            self._add_implicit_diversity_groups(vgroup, _vms[vk].diversity_groups)
                            self._add_implicit_exclusivity_groups(vgroup, _vms[vk].exclusivity_groups)
                            self._add_memberships(vgroup, _vms[vk])
                            del _vms[vk]
                        elif vk in _vgroups.keys():
                            vg = _vgroups[vk]
                            if LEVELS.index(vg.level) > LEVELS.index(level):
                                self.status = "grouping scope: nested " \
                                              "group's level is higher"
                                return False
                            if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                                if self._merge_subgroups(vgroup, vg.subvgroups, _vms, _vgroups,
                                                         _elements, affinity_map) is False:
                                    return False
                                del _vgroups[vk]
                            else:
                                if self._exist_in_subgroups(vk, vgroup) is None:
                                    if self._get_subgroups(vg, _elements,
                                                           _vgroups, _vms,
                                                           affinity_map) is False:
                                        return False
                                    vgroup.subvgroups[vk] = vg
                                    vg.survgroup = vgroup
                                    affinity_map[vk] = vgroup
                                    self._add_implicit_diversity_groups(vgroup, vg.diversity_groups)
                                    self._add_implicit_exclusivity_groups(vgroup, vg.exclusivity_groups)
                                    self._add_memberships(vgroup, vg)
                                    del _vgroups[vk]
                        else:
                            # vk belongs to the other vgroup already
                            # or refer to invalid resource
                            if vk not in affinity_map.keys():
                                self.status = "invalid resource = " + vk
                                return False
                            if affinity_map[vk].uuid != vgroup.uuid:
                                if self._exist_in_subgroups(vk, vgroup) is None:
                                    self._set_implicit_grouping(
                                        vk, vgroup, affinity_map, _vgroups)

        return True

    def _merge_subgroups(self, _vgroup, _subgroups, _vms, _vgroups, _elements, _affinity_map):
        for vk, _ in _subgroups.iteritems():
            if vk in _vms.keys():
                _vgroup.subvgroups[vk] = _vms[vk]
                _vms[vk].survgroup = _vgroup
                _affinity_map[vk] = _vgroup
                self._add_implicit_diversity_groups(_vgroup, _vms[vk].diversity_groups)
                self._add_implicit_exclusivity_groups(_vgroup, _vms[vk].exclusivity_groups)
                self._add_memberships(_vgroup, _vms[vk])
                del _vms[vk]
            elif vk in _vgroups.keys():
                vg = _vgroups[vk]
                if LEVELS.index(vg.level) > LEVELS.index(_vgroup.level):
                    self.status = "grouping scope: nested group's level is " \
                                  "higher"
                    return False
                if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                    if self._merge_subgroups(_vgroup, vg.subvgroups,
                                             _vms, _vgroups,
                                             _elements, _affinity_map) is False:
                        return False
                    del _vgroups[vk]
                else:
                    if self._exist_in_subgroups(vk, _vgroup) is None:
                        if self._get_subgroups(vg, _elements, _vgroups, _vms, _affinity_map) is False:
                            return False
                        _vgroup.subvgroups[vk] = vg
                        vg.survgroup = _vgroup
                        _affinity_map[vk] = _vgroup
                        self._add_implicit_diversity_groups(_vgroup, vg.diversity_groups)
                        self._add_implicit_exclusivity_groups(_vgroup, vg.exclusivity_groups)
                        self._add_memberships(_vgroup, vg)
                        del _vgroups[vk]
            else:
                # vk belongs to the other vgroup already
                # or refer to invalid resource
                if vk not in _affinity_map.keys():
                    self.status = "invalid resource = " + vk
                    return False
                if _affinity_map[vk].uuid != _vgroup.uuid:
                    if self._exist_in_subgroups(vk, _vgroup) is None:
                        self._set_implicit_grouping(vk, _vgroup, _affinity_map, _vgroups)
        return True

    def _get_subgroups(self, _vgroup, _elements, _vgroups, _vms, _affinity_map):
        for vk in _elements[_vgroup.uuid]["properties"]["resources"]:
            if vk in _vms.keys():
                _vgroup.subvgroups[vk] = _vms[vk]
                _vms[vk].survgroup = _vgroup
                _affinity_map[vk] = _vgroup
                self._add_implicit_diversity_groups(_vgroup, _vms[vk].diversity_groups)
                self._add_implicit_exclusivity_groups(_vgroup, _vms[vk].exclusivity_groups)
                self._add_memberships(_vgroup, _vms[vk])
                del _vms[vk]
            elif vk in _vgroups.keys():
                vg = _vgroups[vk]
                if LEVELS.index(vg.level) > LEVELS.index(_vgroup.level):
                    self.status = "grouping scope: nested group's level is " \
                                  "higher"
                    return False
                if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                    if self._merge_subgroups(_vgroup, vg.subvgroups,
                                             _vms, _vgroups,
                                             _elements, _affinity_map) is False:
                        return False
                    del _vgroups[vk]
                else:
                    if self._exist_in_subgroups(vk, _vgroup) is None:
                        if self._get_subgroups(vg, _elements, _vgroups, _vms, _affinity_map) is False:
                            return False
                        _vgroup.subvgroups[vk] = vg
                        vg.survgroup = _vgroup
                        _affinity_map[vk] = _vgroup
                        self._add_implicit_diversity_groups(_vgroup, vg.diversity_groups)
                        self._add_implicit_exclusivity_groups(_vgroup, vg.exclusivity_groups)
                        self._add_memberships(_vgroup, vg)
                        del _vgroups[vk]
            else:
                if vk not in _affinity_map.keys():
                    self.status = "invalid resource = " + vk
                    return False
                if _affinity_map[vk].uuid != _vgroup.uuid:
                    if self._exist_in_subgroups(vk, _vgroup) is None:
                        self._set_implicit_grouping(vk, _vgroup, _affinity_map, _vgroups)
        return True

    def _add_implicit_diversity_groups(self, _vgroup, _diversity_groups):
        for dz, level in _diversity_groups.iteritems():
            l = level.split(":", 1)[0]
            if LEVELS.index(l) >= LEVELS.index(_vgroup.level):
                _vgroup.diversity_groups[dz] = level

    def _add_implicit_exclusivity_groups(self, _vgroup, _exclusivity_groups):
        for ex, level in _exclusivity_groups.iteritems():
            l = level.split(":", 1)[0]
            if LEVELS.index(l) >= LEVELS.index(_vgroup.level):
                _vgroup.exclusivity_groups[ex] = level

    def _add_memberships(self, _vgroup, _v):
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

    ''' take vk's most top parent as a s_vg's child vgroup '''
    def _set_implicit_grouping(self, _vk, _s_vg, _affinity_map, _vgroups):
        t_vg = _affinity_map[_vk]  # where _vk currently belongs to

        if t_vg.uuid in _affinity_map.keys():
            # if the parent belongs to the other parent vgroup
            self._set_implicit_grouping(t_vg.uuid, _s_vg, _affinity_map, _vgroups)
        else:
            if LEVELS.index(t_vg.level) > LEVELS.index(_s_vg.level):
                t_vg.level = _s_vg.level
            if self._exist_in_subgroups(t_vg.uuid, _s_vg) is None:
                _s_vg.subvgroups[t_vg.uuid] = t_vg
                t_vg.survgroup = _s_vg
                _affinity_map[t_vg.uuid] = _s_vg
                self._add_implicit_diversity_groups(_s_vg, t_vg.diversity_groups)
                self._add_implicit_exclusivity_groups(_s_vg, t_vg.exclusivity_groups)
                self._add_memberships(_s_vg, t_vg)
                del _vgroups[t_vg.uuid]

    def _exist_in_subgroups(self, _vk, _vg):
        containing_vg_uuid = None
        for vk, v in _vg.subvgroups.iteritems():
            if vk == _vk:
                containing_vg_uuid = _vg.uuid
                break
            else:
                if isinstance(v, VGroup):
                    containing_vg_uuid = self._exist_in_subgroups(_vk, v)
                    if containing_vg_uuid is not None:
                        break
        return containing_vg_uuid
