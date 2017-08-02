#!/bin/python

from valet.engine.optimizer.app_manager.group import Group


class NamedAffinityFilter(object):

    def __init__(self):
        self.name = "named-affinity"

        self.affinity_id = None

        self.status = None

    def init_condition(self):
        self.affinity_id = None
        self.status = None

    def check_pre_condition(self, _level, _v, _node_placements, _avail_groups):
        if isinstance(_v, Group):
            affinity_id = _v.get_affinity_id()  # level:name, except name == "any"
            if affinity_id is not None:
                # NOTE(gjung): do not depend on _level not like exclusivity
                if affinity_id in _avail_groups.keys():
                    self.affinity_id = affinity_id

        if self.affinity_id is not None:
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
        """Filter based on named affinity group."""

        # NOTE(gjung): do not depend on _level not like exclusivity
        memberships = _candidate.get_all_memberships(_level)
        for lgk, lgr in memberships.iteritems():
            if lgr.group_type == "AFF" and lgk == self.affinity_id:
                return True

        return False
