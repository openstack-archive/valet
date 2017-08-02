#!/bin/python


class NoExclusivityFilter(object):

    def __init__(self):
        self.name = "no-exclusivity"

        self.status = None

    def init_condition(self):
        self.status = None

    def check_pre_condition(self, _level, _v, _node_placements, _avail_groups):
        exclusivities = _v.get_exclusivities(_level)

        if len(exclusivities) == 0:
            return True
        else:
            return False

    def filter_candidates(self, _level, _v, _candidate_list):
        candidate_list = []

        for c in _candidate_list:
            if self._check_candidate(_level, c):
                candidate_list.append(c)

        return candidate_list

    def _check_candidate(self, _level, _candidate):
        memberships = _candidate.get_memberships(_level)

        for mk in memberships.keys():
            if memberships[mk].group_type == "EX" and mk.split(":")[0] == _level:
                return False

        return True
