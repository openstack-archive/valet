#!/bin/python


class DiskFilter(object):

    def __init__(self):
        self.name = "disk"

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
        """Filter based on disk usage."""

        requested_disk = _v.local_volume_size
        (_, usable_disk) = _candidate.get_local_disk(_level)

        if not usable_disk >= requested_disk:
            return False

        return True
