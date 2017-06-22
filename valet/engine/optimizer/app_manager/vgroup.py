#!/bin/python


LEVEL = ["host", "rack", "cluster"]


class VGroup(object):

    def __init__(self, _app_id, _orch_id):
        self.app_id = _app_id          # stack_id
        self.orch_id = _orch_id        # consistent and permanent key
        self.name = None

        self.vgroup_type = "AFF"
        self.level = None              # host, rack, or cluster

        self.survgroup = None          # where this vgroup belong to
        self.subvgroups = {}           # child vgroups

        self.diversity_groups = {}     # cumulative diversity/exclusivity group
        self.exclusivity_groups = {}   # over this level. key=name, value=level

        self.availability_zone_list = []
        self.extra_specs_list = []     # cumulative extra_specs

        self.vCPUs = 0
        self.mem = 0                   # MB
        self.local_volume_size = 0     # GB

        self.vCPU_weight = -1
        self.mem_weight = -1
        self.local_volume_weight = -1

        self.host = None

        self.sort_base = -1

    def get_common_diversity(self, _diversity_groups):
        common_level = "ANY"

        for dk in self.diversity_groups.keys():
            if dk in _diversity_groups.keys():
                level = self.diversity_groups[dk].split(":")[0]
                if common_level != "ANY":
                    if LEVEL.index(level) > LEVEL.index(common_level):
                        common_level = level
                else:
                    common_level = level

        return common_level

    def get_affinity_id(self):
        aff_id = None

        if self.vgroup_type == "AFF" and self.name != "any":
            aff_id = self.level + ":" + self.name

        return aff_id

    def get_exclusivities(self, _level):
        exclusivities = {}

        for exk, level in self.exclusivity_groups.iteritems():
            if level.split(":")[0] == _level:
                exclusivities[exk] = level

        return exclusivities

    def get_json_info(self):
        survgroup_id = None
        if self.survgroup is None:
            survgroup_id = "none"
        else:
            survgroup_id = self.survgroup.orch_id

        subvgroup_list = []
        for vk in self.subvgroups.keys():
            subvgroup_list.append(vk)

        return {'name': self.name,
                'vgroup_type': self.vgroup_type,
                'level': self.level,
                'survgroup': survgroup_id,
                'subvgroup_list': subvgroup_list,
                'diversity_groups': self.diversity_groups,
                'exclusivity_groups': self.exclusivity_groups,
                'availability_zones': self.availability_zone_list,
                'extra_specs_list': self.extra_specs_list,
                'cpus': self.vCPUs,
                'mem': self.mem,
                'local_volume': self.local_volume_size,
                'cpu_weight': self.vCPU_weight,
                'mem_weight': self.mem_weight,
                'local_volume_weight': self.local_volume_weight,
                'host': self.host}
