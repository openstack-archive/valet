# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Modified: Sep. 27, 2016

from valet.engine.optimizer.app_manager.app_topology_base import VGroup, VGroupLink, VM, VMLink, LEVELS


'''
- Restrictions of nested groups: EX in EX, EX in DIV, DIV in EX, DIV in DIV
- VM/group cannot exist in multiple EX groups
- Nested group's level cannot be higher than nesting group
- No supporting the following Heat components
    OS::Nova::ServerGroup
    OS::Heat::AutoScalingGroup
    OS::Heat::Stack
    OS::Heat::ResourceGroup
    OS::Heat::ResourceGroup
'''


class Parser(object):

    def __init__(self, _high_level_allowed, _logger):
        self.logger = _logger

        self.high_level_allowed = _high_level_allowed

        self.format_version = None
        self.stack_id = None          # used as application id
        self.application_name = None
        self.action = None            # [create|update|ping]

        self.status = "success"

    def set_topology(self, _graph):
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

        return self._set_topology(_graph["resources"])

    def _set_topology(self, _elements):
        vgroups = {}
        vgroup_captured = False
        vms = {}

        ''' empty at this version '''
        volumes = {}

        for rk, r in _elements.iteritems():

            if r["type"] == "OS::Nova::Server":
                vm = VM(self.stack_id, rk)

                if "name" in r.keys():
                    vm.name = r["name"]
                else:
                    vm.name = vm.uuid

                vm.flavor = r["properties"]["flavor"]

                if "availability_zone" in r["properties"].keys():
                    az = r["properties"]["availability_zone"]
                    # NOTE: do not allow to specify a certain host name
                    vm.availability_zone = az.split(":")[0]

                vms[vm.uuid] = vm

                self.logger.debug("Parser: get a vm = " + vm.name)

            elif r["type"] == "OS::Cinder::Volume":
                self.logger.warn("Parser: do nothing for volume at this version")

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
                        self.status = "unknown group = " + r["properties"]["group_type"]
                        return {}, {}, {}
                else:
                    self.status = "no group type"
                    return {}, {}, {}

                if "group_name" in r["properties"].keys():
                    vgroup.name = r["properties"]["group_name"]
                else:
                    if vgroup.vgroup_type == "EX":
                        self.status = "no exclusivity group identifier"
                        return {}, {}, {}
                    else:
                        vgroup.name = "any"

                if "level" in r["properties"].keys():
                    vgroup.level = r["properties"]["level"]
                    if vgroup.level != "host":
                        if self.high_level_allowed is False:
                            self.status = "only host level of affinity group allowed " + \
                                          "due to the mis-match of host naming convention"
                            return {}, {}, {}
                else:
                    self.status = "no grouping level"
                    return {}, {}, {}

                vgroups[vgroup.uuid] = vgroup

                self.logger.debug("Parser: get a group = " + vgroup.name)
                vgroup_captured = True

        self._set_vm_links(_elements, vms)

        if self._set_volume_links(_elements, vms, volumes) is False:
            return {}, {}, {}

        self._set_total_link_capacities(vms, volumes)

        self.logger.debug("Parser: all vms parsed")

        if self._merge_diversity_groups(_elements, vgroups, vms, volumes) is False:
            return {}, {}, {}

        if self._merge_exclusivity_groups(_elements, vgroups, vms, volumes) is False:
            return {}, {}, {}

        if self._merge_affinity_groups(_elements, vgroups, vms, volumes) is False:
            return {}, {}, {}

        ''' delete all EX and DIV vgroups after merging '''
        for vgk in vgroups.keys():
            vg = vgroups[vgk]
            if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                del vgroups[vgk]

        for vgk in vgroups.keys():
            vgroup = vgroups[vgk]
            self._set_vgroup_links(vgroup, vgroups, vms, volumes)

        if vgroup_captured is True:
            self.logger.debug("Parser: all groups resolved")

        return vgroups, vms, volumes

    def _set_vm_links(self, _elements, _vms):
        for _, r in _elements.iteritems():
            if r["type"] == "ATT::CloudQoS::Pipe":
                resources = r["properties"]["resources"]
                for vk1 in resources:
                    if vk1 in _vms.keys():
                        vm = _vms[vk1]
                        for vk2 in resources:
                            if vk2 != vk1:
                                if vk2 in _vms.keys():
                                    link = VMLink(_vms[vk2])
                                    if "bandwidth" in r["properties"].keys():
                                        link.nw_bandwidth = r["properties"]["bandwidth"]["min"]
                                    vm.vm_list.append(link)

    def _set_volume_links(self, _elements, _vms, _volumes):
        for rk, r in _elements.iteritems():
            if r["type"] == "OS::Cinder::VolumeAttachment":
                self.logger.warn("Parser: do nothing for volume attachment at this version")

        return True

    def _set_total_link_capacities(self, _vms, _volumes):
        for _, vm in _vms.iteritems():
            for vl in vm.vm_list:
                vm.nw_bandwidth += vl.nw_bandwidth
            for voll in vm.volume_list:
                vm.io_bandwidth += voll.io_bandwidth

        for _, volume in _volumes.iteritems():
            for vl in volume.vm_list:
                volume.io_bandwidth += vl.io_bandwidth

    def _merge_diversity_groups(self, _elements, _vgroups, _vms, _volumes):
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
                        elif vk in _volumes.keys():
                            vgroup.subvgroups[vk] = _volumes[vk]
                            _volumes[vk].diversity_groups[rk] = vgroup.level + ":" + vgroup.name
                        elif vk in _vgroups.keys():
                            vg = _vgroups[vk]

                            if LEVELS.index(vg.level) > LEVELS.index(level):
                                self.status = "grouping scope: nested group's level is higher"
                                return False

                            if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                                self.status = "group type (" + vg.vgroup_type + ") not allowd to be nested in diversity group at this version"
                                return False

                            vgroup.subvgroups[vk] = vg
                            vg.diversity_groups[rk] = vgroup.level + ":" + vgroup.name
                        else:
                            self.status = "invalid resource = " + vk
                            return False

        return True

    def _merge_exclusivity_groups(self, _elements, _vgroups, _vms, _volumes):
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
                        elif vk in _volumes.keys():
                            vgroup.subvgroups[vk] = _volumes[vk]
                            _volumes[vk].exclusivity_groups[rk] = vgroup.level + ":" + vgroup.name
                        elif vk in _vgroups.keys():
                            vg = _vgroups[vk]

                            if LEVELS.index(vg.level) > LEVELS.index(level):
                                self.status = "grouping scope: nested group's level is higher"
                                return False

                            if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                                self.status = "group type (" + vg.vgroup_type + ") not allowd to be nested in exclusivity group at this version"
                                return False

                            vgroup.subvgroups[vk] = vg
                            vg.exclusivity_groups[rk] = vgroup.level + ":" + vgroup.name
                        else:
                            self.status = "invalid resource = " + vk
                            return False

        return True

    def _merge_affinity_groups(self, _elements, _vgroups, _vms, _volumes):
        affinity_map = {}  # key is uuid of vm, volume, or vgroup & value is its parent vgroup

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

                    self.logger.debug("Parser: merge for affinity = " + vgroup.name)

                    for vk in r["properties"]["resources"]:

                        if vk in _vms.keys():
                            vgroup.subvgroups[vk] = _vms[vk]
                            _vms[vk].survgroup = vgroup

                            affinity_map[vk] = vgroup

                            self._add_implicit_diversity_groups(vgroup, _vms[vk].diversity_groups)
                            self._add_implicit_exclusivity_groups(vgroup, _vms[vk].exclusivity_groups)
                            self._add_memberships(vgroup, _vms[vk])

                            del _vms[vk]

                        elif vk in _volumes.keys():
                            vgroup.subvgroups[vk] = _volumes[vk]
                            _volumes[vk].survgroup = vgroup

                            affinity_map[vk] = vgroup

                            self._add_implicit_diversity_groups(vgroup, _volumes[vk].diversity_groups)
                            self._add_implicit_exclusivity_groups(vgroup, _volumes[vk].exclusivity_groups)
                            self._add_memberships(vgroup, _volumes[vk])

                            del _volumes[vk]

                        elif vk in _vgroups.keys():
                            vg = _vgroups[vk]

                            if LEVELS.index(vg.level) > LEVELS.index(level):
                                self.status = "grouping scope: nested group's level is higher"
                                return False

                            if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                                if self._merge_subgroups(vgroup, vg.subvgroups, _vms, _volumes, _vgroups,
                                                         _elements, affinity_map) is False:
                                    return False
                                del _vgroups[vk]
                            else:
                                if self._exist_in_subgroups(vk, vgroup) is None:
                                    if self._get_subgroups(vg, _elements,
                                                           _vgroups, _vms, _volumes,
                                                           affinity_map) is False:
                                        return False

                                    vgroup.subvgroups[vk] = vg
                                    vg.survgroup = vgroup

                                    affinity_map[vk] = vgroup

                                    self._add_implicit_diversity_groups(vgroup, vg.diversity_groups)
                                    self._add_implicit_exclusivity_groups(vgroup, vg.exclusivity_groups)
                                    self._add_memberships(vgroup, vg)

                                    del _vgroups[vk]

                        else:  # vk belongs to the other vgroup already or refer to invalid resource
                            if vk not in affinity_map.keys():
                                self.status = "invalid resource = " + vk
                                return False

                            if affinity_map[vk].uuid != vgroup.uuid:
                                if self._exist_in_subgroups(vk, vgroup) is None:
                                    self._set_implicit_grouping(vk, vgroup, affinity_map, _vgroups)

        return True

    def _merge_subgroups(self, _vgroup, _subgroups, _vms, _volumes, _vgroups, _elements, _affinity_map):
        for vk, _ in _subgroups.iteritems():
            if vk in _vms.keys():
                _vgroup.subvgroups[vk] = _vms[vk]
                _vms[vk].survgroup = _vgroup

                _affinity_map[vk] = _vgroup

                self._add_implicit_diversity_groups(_vgroup, _vms[vk].diversity_groups)
                self._add_implicit_exclusivity_groups(_vgroup, _vms[vk].exclusivity_groups)
                self._add_memberships(_vgroup, _vms[vk])

                del _vms[vk]

            elif vk in _volumes.keys():
                _vgroup.subvgroups[vk] = _volumes[vk]
                _volumes[vk].survgroup = _vgroup

                _affinity_map[vk] = _vgroup

                self._add_implicit_diversity_groups(_vgroup, _volumes[vk].diversity_groups)
                self._add_implicit_exclusivity_groups(_vgroup, _volumes[vk].exclusivity_groups)
                self._add_memberships(_vgroup, _volumes[vk])

                del _volumes[vk]

            elif vk in _vgroups.keys():
                vg = _vgroups[vk]

                if LEVELS.index(vg.level) > LEVELS.index(_vgroup.level):
                    self.status = "grouping scope: nested group's level is higher"
                    return False

                if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                    if self._merge_subgroups(_vgroup, vg.subvgroups,
                                             _vms, _volumes, _vgroups,
                                             _elements, _affinity_map) is False:
                        return False
                    del _vgroups[vk]
                else:
                    if self._exist_in_subgroups(vk, _vgroup) is None:
                        if self._get_subgroups(vg, _elements, _vgroups, _vms, _volumes, _affinity_map) is False:
                            return False

                        _vgroup.subvgroups[vk] = vg
                        vg.survgroup = _vgroup

                        _affinity_map[vk] = _vgroup

                        self._add_implicit_diversity_groups(_vgroup, vg.diversity_groups)
                        self._add_implicit_exclusivity_groups(_vgroup, vg.exclusivity_groups)
                        self._add_memberships(_vgroup, vg)

                        del _vgroups[vk]

            else:  # vk belongs to the other vgroup already or refer to invalid resource
                if vk not in _affinity_map.keys():
                    self.status = "invalid resource = " + vk
                    return False

                if _affinity_map[vk].uuid != _vgroup.uuid:
                    if self._exist_in_subgroups(vk, _vgroup) is None:
                        self._set_implicit_grouping(vk, _vgroup, _affinity_map, _vgroups)

        return True

    def _get_subgroups(self, _vgroup, _elements, _vgroups, _vms, _volumes, _affinity_map):

        for vk in _elements[_vgroup.uuid]["properties"]["resources"]:

            if vk in _vms.keys():
                _vgroup.subvgroups[vk] = _vms[vk]
                _vms[vk].survgroup = _vgroup

                _affinity_map[vk] = _vgroup

                self._add_implicit_diversity_groups(_vgroup, _vms[vk].diversity_groups)
                self._add_implicit_exclusivity_groups(_vgroup, _vms[vk].exclusivity_groups)
                self._add_memberships(_vgroup, _vms[vk])

                del _vms[vk]

            elif vk in _volumes.keys():
                _vgroup.subvgroups[vk] = _volumes[vk]
                _volumes[vk].survgroup = _vgroup

                _affinity_map[vk] = _vgroup

                self._add_implicit_diversity_groups(_vgroup, _volumes[vk].diversity_groups)
                self._add_implicit_exclusivity_groups(_vgroup, _volumes[vk].exclusivity_groups)
                self._add_memberships(_vgroup, _volumes[vk])

                del _volumes[vk]

            elif vk in _vgroups.keys():
                vg = _vgroups[vk]

                if LEVELS.index(vg.level) > LEVELS.index(_vgroup.level):
                    self.status = "grouping scope: nested group's level is higher"
                    return False

                if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                    if self._merge_subgroups(_vgroup, vg.subvgroups,
                                             _vms, _volumes, _vgroups,
                                             _elements, _affinity_map) is False:
                        return False
                    del _vgroups[vk]
                else:
                    if self._exist_in_subgroups(vk, _vgroup) is None:
                        if self._get_subgroups(vg, _elements, _vgroups, _vms, _volumes, _affinity_map) is False:
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

            '''
            for hgk, hg in _v.host_aggregates.iteritems():
                _vgroup.host_aggregates[hgk] = hg
            '''

    ''' take vk's most top parent as a s_vg's child vgroup '''
    def _set_implicit_grouping(self, _vk, _s_vg, _affinity_map, _vgroups):
        t_vg = _affinity_map[_vk]  # where _vk currently belongs to

        if t_vg.uuid in _affinity_map.keys():  # if the parent belongs to the other parent vgroup
            self._set_implicit_grouping(t_vg.uuid, _s_vg, _affinity_map, _vgroups)

        else:
            if LEVELS.index(t_vg.level) > LEVELS.index(_s_vg.level):
                t_vg.level = _s_vg.level

                '''
                self.status = "Grouping scope: sub-group's level is larger"
                return False
                '''

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

    def _set_vgroup_links(self, _vgroup, _vgroups, _vms, _volumes):
        for _, svg in _vgroup.subvgroups.iteritems():  # currently, not define vgroup itself in pipe
            if isinstance(svg, VM):
                for vml in svg.vm_list:
                    found = False
                    for _, tvgroup in _vgroups.iteritems():
                        containing_vg_uuid = self._exist_in_subgroups(vml.node.uuid, tvgroup)
                        if containing_vg_uuid is not None:
                            found = True
                            if containing_vg_uuid != _vgroup.uuid and \
                               self._exist_in_subgroups(containing_vg_uuid, _vgroup) is None:
                                self._add_nw_link(vml, _vgroup)
                            break
                    if found is False:
                        for tvk in _vms.keys():
                            if tvk == vml.node.uuid:
                                self._add_nw_link(vml, _vgroup)
                                break
                for voll in svg.volume_list:
                    found = False
                    for _, tvgroup in _vgroups.iteritems():
                        containing_vg_uuid = self._exist_in_subgroups(voll.node.uuid, tvgroup)
                        if containing_vg_uuid is not None:
                            found = True
                            if containing_vg_uuid != _vgroup.uuid and \
                               self._exist_in_subgroups(containing_vg_uuid, _vgroup) is None:
                                self._add_io_link(voll, _vgroup)
                            break
                    if found is False:
                        for tvk in _volumes.keys():
                            if tvk == voll.node.uuid:
                                self._add_io_link(voll, _vgroup)
                                break
            # elif isinstance(svg, Volume):
            #     for vml in svg.vm_list:
            #         found = False
            #         for _, tvgroup in _vgroups.iteritems():
            #             containing_vg_uuid = self._exist_in_subgroups(vml.node.uuid, tvgroup)
            #             if containing_vg_uuid is not None:
            #                 found = True
            #                 if containing_vg_uuid != _vgroup.uuid and \
            #                    self._exist_in_subgroups(containing_vg_uuid, _vgroup) is None:
            #                     self._add_io_link(vml, _vgroup)
            #                 break
            #         if found is False:
            #             for tvk in _vms.keys():
            #                 if tvk == vml.node.uuid:
            #                     self._add_io_link(vml, _vgroup)
            #                     break
            elif isinstance(svg, VGroup):
                self._set_vgroup_links(svg, _vgroups, _vms, _volumes)

                for svgl in svg.vgroup_list:  # svgl is a link to VM or Volume
                    if self._exist_in_subgroups(svgl.node.uuid, _vgroup) is None:
                        self._add_nw_link(svgl, _vgroup)
                        self._add_io_link(svgl, _vgroup)

    def _add_nw_link(self, _link, _vgroup):
        _vgroup.nw_bandwidth += _link.nw_bandwidth
        vgroup_link = self._get_vgroup_link(_link, _vgroup.vgroup_list)
        if vgroup_link is not None:
            vgroup_link.nw_bandwidth += _link.nw_bandwidth
        else:
            link = VGroupLink(_link.node)  # _link.node is VM
            link.nw_bandwidth = _link.nw_bandwidth
            _vgroup.vgroup_list.append(link)

    def _add_io_link(self, _link, _vgroup):
        _vgroup.io_bandwidth += _link.io_bandwidth
        vgroup_link = self._get_vgroup_link(_link, _vgroup.vgroup_list)
        if vgroup_link is not None:
            vgroup_link.io_bandwidth += _link.io_bandwidth
        else:
            link = VGroupLink(_link.node)
            link.io_bandwidth = _link.io_bandwidth
            _vgroup.vgroup_list.append(link)

    def _get_vgroup_link(self, _link, _vgroup_link_list):
        vgroup_link = None
        for vgl in _vgroup_link_list:
            if vgl.node.uuid == _link.node.uuid:
                vgroup_link = vgl
                break
        return vgroup_link
