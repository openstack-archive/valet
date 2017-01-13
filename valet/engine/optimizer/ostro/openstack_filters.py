#
# Copyright 2014-2017 AT&T Intellectual Property
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AggregateInstanceExtraSpecsFilter."""

import six

from valet.engine.optimizer.app_manager.app_topology_base import VM
from valet.engine.optimizer.ostro import openstack_utils

_SCOPE = 'aggregate_instance_extra_specs'


class AggregateInstanceExtraSpecsFilter(object):
    """AggregateInstanceExtraSpecsFilter works with InstanceType records."""

    # Aggregate data and instance type does not change within a request
    run_filter_once_per_request = True

    def __init__(self, _logger):
        """Initialization."""
        self.logger = _logger

    def host_passes(self, _level, _host, _v):
        """Return a list of hosts that can create instance_type."""
        """Check that the extra specs associated with the instance type match
        the metadata provided by aggregates.  If not present return False."""

        # If 'extra_specs' is not present or extra_specs are empty then we
        # need not proceed further
        extra_specs_list = []
        for extra_specs in _v.extra_specs_list:
            if "host_aggregates" not in extra_specs.keys():
                extra_specs_list.append(extra_specs)

        if len(extra_specs_list) == 0:
            return True

        metadatas = openstack_utils.aggregate_metadata_get_by_host(_level,
                                                                   _host)

        matched_logical_group_list = []
        for extra_specs in extra_specs_list:
            for lgk, metadata in metadatas.iteritems():
                if self._match_metadata(_host.get_resource_name(_level), lgk,
                                        extra_specs, metadata) is True:
                    matched_logical_group_list.append(lgk)
                    break
            else:
                return False

        for extra_specs in _v.extra_specs_list:
            if "host_aggregates" in extra_specs.keys():
                extra_specs["host_aggregates"] = matched_logical_group_list
                break
        else:
            host_aggregate_extra_specs = {}
            host_aggregate_extra_specs["host_aggregates"] = \
                matched_logical_group_list
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
                self.logger.debug("key (" + key + ") not exists in logical_"
                                  "group (" + _lg_name + ") " +
                                  " of host (" + _h_name + ")")
                return False
            for aggregate_val in aggregate_vals:
                if openstack_utils.match(aggregate_val, req):
                    break
            else:
                self.logger.debug("key (" + key + ")'s value (" + req + ") not "
                                  "exists in logical_group " + "(" + _lg_name +
                                  ") " + " of host (" + _h_name + ")")
                return False

        return True


# NOTE: originally, OpenStack used the metadata of host_aggregate
class AvailabilityZoneFilter(object):
    """AvailabilityZoneFilter filters Hosts by availability zone."""

    """Work with aggregate metadata availability zones, using the key
    'availability_zone'
    Note: in theory a compute node can be part of multiple availability_zones
    """

    # Availability zones do not change within a request
    run_filter_once_per_request = True

    def __init__(self, _logger):
        """Initialization."""
        self.logger = _logger

    def host_passes(self, _level, _host, _v):
        """Return True if all availalibility zones in _v exist in the host."""
        az_request_list = []
        if isinstance(_v, VM):
            az_request_list.append(_v.availability_zone)
        else:
            for az in _v.availability_zone_list:
                az_request_list.append(az)

        if len(az_request_list) == 0:
            return True

        availability_zone_list = \
            openstack_utils.availability_zone_get_by_host(_level, _host)

        for azr in az_request_list:
            if azr not in availability_zone_list:
                self.logger.debug("AZ (" + azr + ") not exists in host " + "(" +
                                  _host.get_resource_name(_level) + ")")
                return False

        return True


class RamFilter(object):
    """RamFilter."""

    def __init__(self, _logger):
        """Initialization."""
        self.logger = _logger

    def host_passes(self, _level, _host, _v):
        """Return True if host has sufficient available RAM."""
        requested_ram = _v.mem   # MB
        (total_ram, usable_ram) = _host.get_mem(_level)

        # Do not allow an instance to overcommit against itself, only against
        # other instances.
        if not total_ram >= requested_ram:
            self.logger.debug("requested mem (" + str(requested_ram) +
                              ") more than total mem (" +
                              str(total_ram) + ") in host (" +
                              _host.get_resource_name(_level) + ")")
            return False

        if not usable_ram >= requested_ram:
            self.logger.debug("requested mem (" + str(requested_ram) +
                              ") more than avail mem (" +
                              str(usable_ram) + ") in host (" +
                              _host.get_resource_name(_level) + ")")
            return False

        return True


class CoreFilter(object):
    """CoreFilter."""

    def __init__(self, _logger):
        """Initialization."""
        self.logger = _logger

    def host_passes(self, _level, _host, _v):
        """Return True if host has sufficient CPU cores."""
        (vCPUs, avail_vCPUs) = _host.get_vCPUs(_level)

        instance_vCPUs = _v.vCPUs

        # Do not allow an instance to overcommit against itself, only against
        # other instances.
        if instance_vCPUs > vCPUs:
            self.logger.debug("requested vCPUs (" + str(instance_vCPUs) +
                              ") more than total vCPUs (" +
                              str(vCPUs) + ") in host (" +
                              _host.get_resource_name(_level) + ")")
            return False

        if avail_vCPUs < instance_vCPUs:
            self.logger.debug("requested vCPUs (" + str(instance_vCPUs) +
                              ") more than avail vCPUs (" +
                              str(avail_vCPUs) + ") in host (" +
                              _host.get_resource_name(_level) + ")")
            return False

        return True


class DiskFilter(object):
    """DiskFilter."""

    def __init__(self, _logger):
        """Initialization."""
        self.logger = _logger

    def host_passes(self, _level, _host, _v):
        """Return True if the requested disk is less than the available disk."""
        requested_disk = _v.local_volume_size
        (_, usable_disk) = _host.get_local_disk(_level)

        if not usable_disk >= requested_disk:
            self.logger.debug("requested disk (" + str(requested_disk) +
                              ") more than avail disk (" +
                              str(usable_disk) + ") in host (" +
                              _host.get_resource_name(_level) + ")")
            return False

        return True
