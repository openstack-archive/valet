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

"""Analyzer."""

from novaclient import client
import traceback
from valet.tests.functional.valet_validator.common import Result, GeneralLogger
from valet.tests.functional.valet_validator.common.auth import Auth
from valet.tests.functional.valet_validator.common.init import CONF


class Analyzer(object):
    """Methods to perform analysis on hosts, vms, racks."""

    def __init__(self):
        """Initializing the analyzer - connecting to nova."""
        GeneralLogger.log_info("Initializing Analyzer")
        self.nova = client.Client(CONF.nova.VERSION,
                                  session=Auth.get_auth_session())

    def get_host_name(self, instance_name):
        """Returning host by instance name."""
        serv = self.nova.servers.find(name=instance_name)
        return self.get_hostname(serv)

    def get_all_hosts(self, instances_list):
        """Returning all hosts of all instances."""
        GeneralLogger.log_debug("Getting hosts names")
        return [self.get_host_name(instance.name)
                for instance in instances_list]

    def check(self, resources):
        """Check if all instances are on the Appropriate hosts and racks."""
        GeneralLogger.log_debug("Starting to check instances location")
        result = True

        try:
            for key in resources.groups:
                group = resources.groups[key]

                resources_to_compare = self.get_resources_to_compare(
                    resources, group.group_resources) or group.group_resources
                instances_for_group = self.get_group_instances(
                    resources, resources_to_compare)
                hosts_list = self.get_all_hosts(instances_for_group)

                # switch case
                result = result and \
                    {
                        "affinity": self.are_the_same(hosts_list,
                                                      group.level),
                        "diversity": self.are_different(hosts_list,
                                                        group.level),
                        "exclusivity": self.are_we_alone(hosts_list,
                                                         instances_for_group)
                    }[group.group_type]

        except Exception as ex:
            GeneralLogger.log_error("Exception at method check: %s" % ex,
                                    traceback.format_exc())
            result = False

        return Result(result)

    def get_resources_to_compare(self, resources, group_resources):
        """Return resources to compare."""
        resources_to_compare = []

        try:
            # ['test-affinity-group1', 'test-affinity-group2']
            for group_name in group_resources:
                if "test" in group_name:
                    resources_to_compare.append(
                        resources.groups[group_name].group_resources)
                else:
                    return None
            return resources_to_compare

        except Exception as ex:
            GeneralLogger.log_error("Exception at method "
                                    "get_resources_to_compare: %s"
                                    % ex, traceback.format_exc())

    def are_we_alone(self, hosts_list, ins_for_group):
        """Return result of whether any instances on host."""
        try:
            # instances is all the instances on this host
            all_instances_on_host = self.get_instances_per_host(hosts_list)
            for instance in ins_for_group:
                if instance.name in all_instances_on_host:
                    all_instances_on_host.remove(instance.name)
            return not all_instances_on_host

        except Exception as ex:
            GeneralLogger.log_error("Exception at method are_we_alone: %s"
                                    % ex, traceback.format_exc())

    def get_instances_per_host(self, hosts_list):
        """Get number of instances per host."""
        instances = []
        try:
            for host in set(hosts_list):
                for items in self.get_vms_by_hypervisor(host):
                    instances.append(items.name)

            return instances
        except Exception as ex:
            GeneralLogger.log_error("Exception at method "
                                    "get_instances_per_host: %s"
                                    % ex, traceback.format_exc())

    def are_different(self, hosts_list, level):
        """Check if all hosts (and racks) are different for all instances."""
        diction = {}

        try:
            for h in hosts_list:
                if self.is_already_exists(diction,
                                          self.get_host_or_rack(level, h)):
                    return False
            return True

        except Exception as ex:
            GeneralLogger.log_error("Exception at method "
                                    "are_all_hosts_different: %s"
                                    % ex, traceback.format_exc())
            return False

    def are_the_same(self, hosts_list, level):
        """Check if all hosts (and racks) are the same for all instances."""
        GeneralLogger.log_debug("Hosts are:")
        try:
            for h in hosts_list:
                if self.compare_host(
                        self.get_host_or_rack(level, h),
                        self.get_host_or_rack(level, hosts_list[0])) is False:
                    return False
            return True

        except Exception as ex:
            GeneralLogger.log_error("Exception at method "
                                    "are_all_hosts_different: %s"
                                    % ex, traceback.format_exc())
            return False

    def get_group_instances(self, resources, group_ins):
        """Get the instance object according to the group_ins.

        group_ins - the group_resources name of the instances belong to
        this group (['my-instance-1', 'my-instance-2']).
        """
        ins_for_group = []
        try:
            for instance in resources.instances:
                if instance.resource_name in group_ins:
                    ins_for_group.append(instance)
            return ins_for_group

        except Exception as ex:
            GeneralLogger.log_error("Exception at method "
                                    "get_group_instances: %s"
                                    % ex, traceback.format_exc())
            return None

    def get_hostname(self, vm):
        """Get hostname of vm."""
        return str(getattr(vm, CONF.nova.ATTR))

    def is_already_exists(self, diction, item):
        """If item exists, return True, otherwise return False."""
        if item in diction:
            return True

        diction[item] = 1
        return False

    def compare_rack(self, current_host, first_host):
        """Return True if racks of current and first host are equal."""
        GeneralLogger.log_debug(current_host)
        return self.get_rack(current_host) == self.get_rack(first_host)

    def compare_host(self, current_host, first_host):
        """Compare current host to first host."""
        GeneralLogger.log_debug(current_host)
        return current_host == first_host

    def get_rack(self, host):
        """Get rack from host."""
        return (host.split("r")[1])[:2]

    def get_host_or_rack(self, level, host):
        """Return host if current level is host, otherwise return rack."""
        return host if level == "host" else self.get_rack(host)

    def get_vms_by_hypervisor(self, host):
        """Return vms based on hypervisor(host)."""
        return [vm for vm in self.nova.servers.list(
            search_opts={"all_tenants": True}) if self.get_hostname(vm) == host]
