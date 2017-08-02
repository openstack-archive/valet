#!/bin/python

import filter_utils
import six

_SCOPE = 'aggregate_instance_extra_specs'


class AggregateInstanceExtraSpecsFilter(object):
    """AggregateInstanceExtraSpecsFilter works with InstanceType records."""

    def __init__(self):
        self.name = "aggregate-instance-extra-specs"

        self.status = None

    def init_condition(self):
        self.status = None

    def check_pre_condition(self, _level, _v, _node_placements, _avail_groups):
        if len(_v.extra_specs_list) > 0:
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
        """Check given candidate host if instance's  extra specs matches to metadata."""

        extra_specs_list = []
        for extra_specs in _v.extra_specs_list:
            if "valet" not in extra_specs.keys() and "host_aggregates" not in extra_specs.keys():
                extra_specs_list.append(extra_specs)

        if len(extra_specs_list) == 0:
            return True

        metadatas = filter_utils.aggregate_metadata_get_by_host(_level, _candidate)

        matched_group_list = []
        for extra_specs in extra_specs_list:
            for lgk, metadata in metadatas.iteritems():
                if self._match_metadata(_candidate.get_resource_name(_level), lgk, extra_specs, metadata):
                    matched_group_list.append(lgk)
                    break
            else:
                return False

        for extra_specs in _v.extra_specs_list:
            if "host_aggregates" in extra_specs.keys():
                extra_specs["host_aggregates"] = matched_group_list
                break
        else:
            host_aggregate_extra_specs = {}
            host_aggregate_extra_specs["host_aggregates"] = matched_group_list
            _v.extra_specs_list.append(host_aggregate_extra_specs)

        return True

    def _match_metadata(self, _h_name, _lg_name, _extra_specs, _metadata):
        for key, req in six.iteritems(_extra_specs):
            # Either not scope format, or aggregate_instance_extra_specs scope
            scope = key.split(':', 1)
            if len(scope) > 1:
                if scope[0] != _SCOPE:
                    continue
                else:
                    del scope[0]
            key = scope[0]

            if key == "host_aggregates":
                continue

            aggregate_vals = _metadata.get(key, None)
            if not aggregate_vals:
                return False
            for aggregate_val in aggregate_vals:
                if filter_utils.match(aggregate_val, req):
                    break
            else:
                return False

        return True
