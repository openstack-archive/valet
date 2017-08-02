#!/bin/python


class CPUFilter(object):

    def __init__(self):
        self.name = "cpu"

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
        """Return True if host has sufficient CPU cores."""

        (vCPUs, avail_vCPUs) = _candidate.get_vCPUs(_level)

        instance_vCPUs = _v.vCPUs

        # Do not allow an instance to overcommit against itself, only against other instances.
        if instance_vCPUs > vCPUs:
            return False

        if avail_vCPUs < instance_vCPUs:
            return False

        return True
