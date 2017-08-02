#!/bin/python


class NamedDiversityFilter(object):

    def __init__(self):
        self.name = "named-diversity"

        self.diversity_list = []

        self.status = None

    def init_condition(self):
        self.diversity_list = []
        self.status = None

    def check_pre_condition(self, _level, _v, _node_placements, _avail_groups):
        if len(_v.diversity_groups) > 0:
            for _, diversity_id in _v.diversity_groups.iteritems():
                if diversity_id.split(":")[0] == _level:
                    if diversity_id in _avail_groups.keys():
                        self.diversity_list.append(diversity_id)

        if len(self.diversity_list) > 0:
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
        """Filter based on named diversity groups."""

        for diversity_id in self.diversity_list:
            memberships = _candidate.get_memberships(_level)

            for lgk, lgr in memberships.iteritems():
                if lgr.group_type == "DIV" and lgk == diversity_id:
                    return False

        return True
