#!/bin/python

from valet.engine.optimizer.app_manager.group import LEVEL, Group
from valet.engine.optimizer.ostro.search_helper import check_vm_grouping


class DiversityFilter(object):

    def __init__(self):
        self.name = "diversity"

        self.node_placements = None

        self.status = None

    def init_condition(self):
        self.node_placements = None
        self.status = None

    def check_pre_condition(self, _level, _v, _node_placements, _avail_groups):
        if len(_v.diversity_groups) > 0:
            self.node_placements = _node_placements
            return True
        else:
            return False

    def filter_candidates(self, _level, _v, _candidate_list):
        candidate_list = []

        for c in _candidate_list:
            if self._check_candidate(_level, _v, c):
                candidate_list.append(c)

        return candidate_list

    def _check_candidate(self, _level, _v, _candidate):
        """Filter based on diversity groups."""

        for v in self.node_placements.keys():
            if isinstance(v, Group):
                if check_vm_grouping(v, _v.orch_id) is True:
                    continue

            diversity_level = _v.get_common_diversity(v.diversity_groups)

            if diversity_level != "ANY" and LEVEL.index(diversity_level) >= LEVEL.index(_level):
                if diversity_level == "host":
                    if _candidate.cluster_name == self.node_placements[v].cluster_name and \
                       _candidate.rack_name == self.node_placements[v].rack_name and  \
                       _candidate.host_name == self.node_placements[v].host_name:
                        return False
                elif diversity_level == "rack":
                    if _candidate.cluster_name == self.node_placements[v].cluster_name and \
                       _candidate.rack_name == self.node_placements[v].rack_name:
                        return False
                elif diversity_level == "cluster":
                    if _candidate.cluster_name == self.node_placements[v].cluster_name:
                        return False

        return True
