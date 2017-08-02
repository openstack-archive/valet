#!/bin/python


class MemFilter(object):

    def __init__(self):
        self.name = "mem"

        self.status = None

    def init_condition(self):
        self.status = None

    def check_pre_condition(self, _level, _v, _node_placements, _avail_groups):
        return True

    def filter_candidates(self, _level, _v, _candidate_list):
        candidate_list = []

        for c in _candidate_list:
            if self._check_candidate(_level, _v, c):
                candidate_list.append(c)

        return candidate_list

    def _check_candidate(self, _level, _v, _candidate):
        """Only return hosts with sufficient available RAM."""

        requested_ram = _v.mem   # MB
        (total_ram, usable_ram) = _candidate.get_mem(_level)

        # Do not allow an instance to overcommit against itself, only against other instances.
        if not total_ram >= requested_ram:
            return False

        if not usable_ram >= requested_ram:
            return False

        return True
