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

from collections import defaultdict
import os
from tempest import config
import time
import traceback

CONF = config.CONF


class Analyzer(object):
    """Class to analyze groups/racks/instances."""

    def __init__(self, logger, stack_id, heat, nova):
        """Initializing the analyzer - connecting to Nova."""
        self.heat_client = heat
        self.nova_client = nova
        self.possible_topdir = os.path.normpath(os.path.join(
            os.path.abspath(__file__), os.pardir))
        self.stack_identifier = stack_id
        self.log = logger
        self.resource_name = {}
        self.host_instance_dict = {}
        self.group_instance_name = {}
        self.instances_on_host = defaultdict(list)
        self.tries = CONF.valet.TRIES_TO_SHOW_SERVER

    def check(self, resources, levels, group_types):
        """Checking if all instances are on the Appropriate hosts and racks """
        self.log.log_info("Starting to check instances location")
        result = True

        self.init_servers_list()
        self.init_resources(resources)
        ins_group = self.init_instances_for_group(resources,
                                                  levels, group_types)

        try:
            for group_type in ins_group:
                for group_resource in ins_group[group_type]:
                    instances = group_resource[:2]
                    level = group_resource[2]

                    fn = \
                        {
                            "affinity": self.are_the_same,
                            "diversity": self.are_different,
                            "exclusivity": self.are_we_alone
                        }[group_type]

                    result = result and fn(instances, level)

        except Exception as ex:
            self.log.log_error("Exception at method check: %s" % ex,
                               traceback.format_exc())
            result = False

        return result

    def init_instances_for_group(self, resources, levels, group_types):
        self.log.log_info("initializing instances for groups")
        ins_group = defaultdict(list)
        index = 0

        for grp in resources.groups.keys():
            self.group_instance_name[grp] = resources.groups[grp].group_resources
            resources.groups[grp].group_resources.append(levels[index])
            ins_group[group_types[index]].append(
                    resources.groups[grp].group_resources)
            ++index

        # replacing group for it's instances
        ins_group = self.organize(ins_group)

        return ins_group

    def init_resources(self, resources):
        """Init resources."""
        for ins in resources.instances:
            self.resource_name[ins.resource_name] = ins.name

    def init_servers_list(self):
        """Init server list from nova client."""
        self.log.log_info("initializing the servers list")
        servers_list = self.nova_client.list_servers()

        try:
            for i in range(len(servers_list["servers"])):
                server = self.nova_client.show_server(
                    servers_list["servers"][i]["id"])
                host_name = server["server"]["OS-EXT-SRV-ATTR:host"]
                instance_name = servers_list["servers"][i]["name"]

                self.host_instance_dict[instance_name] = host_name
                self.instances_on_host[host_name].append(instance_name)

        except Exception:
            self.log.log_error(
                "Exception trying to show_server: %s" % traceback.format_exc())
            if self.tries > 0:
                time.sleep(CONF.valet.PAUSE)
                self.tries -= 1
                self.init_servers_list()

        for host in self.instances_on_host:
            self.instances_on_host[host] = set(self.instances_on_host[host])

    def get_instance_name(self, res_name):
        """Return instance name (resource name)."""
        return self.resource_name[res_name]

    def get_instance_host(self, res_name):
        """Return host of instance with matching name."""
        hosts = []

        self.log.log_debug(
            "host - instance dictionary is: %s" % self.host_instance_dict)

        for res in res_name:
            name = self.get_instance_name(res)
            hosts.append(self.host_instance_dict[name])

        return hosts

    def are_the_same(self, res_name, level):
        """Return true if host aren't the same otherwise return False."""
        self.log.log_info("verifying instances are on the same host/racks")
        hosts_list = self.get_instance_host(res_name)
        self.log.log_debug("hosts to compare: %s" % hosts_list)

        try:
            for h in hosts_list:
                if self.compare_host(
                        self.get_host_or_rack(level, h),
                        self.get_host_or_rack(level, hosts_list[0])) is False:
                    return False

        except Exception as ex:
            self.log.log_error("Exception while verifying instances are on "
                               "different hosts/racks: "
                               "%s" % ex, traceback.format_exc())
            return False
        return True

    def are_different(self, res_name, level):
        """Check if all hosts (and racks) are different for all instances."""
        self.log.log_info("verifying instances are on different hosts/racks")
        diction = {}
        hosts_list = self.get_instance_host(res_name)
        self.log.log_debug("hosts to compare: %s" % hosts_list)

        try:
            for h in hosts_list:
                if self.is_already_exists(diction, self.get_host_or_rack(level,
                                                                         h)):
                    return False

        except Exception as ex:
            self.log.log_error("Exception while verifying instances are on "
                               "different hosts/racks: "
                               "%s" % ex, traceback.format_exc())
            return False
        return True

    def are_we_alone(self, ins_for_group, level):
        """Return True if no other instances in group on server."""
        self.log.log_info("verifying instances are on the "
                          "same group hosts/racks")

        exclusivity_group_hosts = self.get_exclusivity_group_hosts()

        self.log.log_debug(
            "exclusivity group hosts are: %s " % exclusivity_group_hosts)
        self.log.log_debug(
            "instances on host are: %s " % self.instances_on_host)

        # instances - all the instances on the exclusivity group hosts
        for host in exclusivity_group_hosts:
            instances = self.instances_on_host[host]

        self.log.log_debug("exclusivity group instances are: %s " % instances)

        if level == "rack":
            instances = self.get_rack_instances(
                set(self.host_instance_dict.values()))

        # host_instance_dict should be all the instances on the rack
        if len(instances) < 1:
            return False

        for instance in ins_for_group:
            if self.resource_name[instance] in instances:
                instances.remove(self.resource_name[instance])

        return not instances

    def organize(self, ins_group):
        """Organize internal groups, return ins_group."""
        internal_ins = []
        for x in ins_group:
            for y in ins_group[x]:
                if y[0] in self.group_instance_name.keys():
                    internal_ins.append(self.group_instance_name[y[0]][0])
                    internal_ins.append(self.group_instance_name[y[1]][0])
                    internal_ins.append(y[2])
                    ins_group.pop(x)
                    ins_group[x].append(internal_ins)
        return ins_group

    def get_exclusivity_group_hosts(self):
        """Get all hosts that exclusivity group instances are located on """
        servers_list = self.nova_client.list_servers()
        exclusivity_hosts = []
        for serv in servers_list["servers"]:
            if "exclusivity" in serv["name"]:
                server = self.nova_client.show_server(serv["id"])
                exclusivity_hosts.append(
                    server["server"]["OS-EXT-SRV-ATTR:host"])
        return set(exclusivity_hosts)

    def get_group_instances(self, resources, group_ins):
        """Get the instance object according to the group_ins.

        group_ins - the group_resources name of the instances belong to this
        group (['my-instance-1', 'my-instance-2'])
        """
        ins_for_group = []
        try:
            for instance in resources.instances:
                if instance.resource_name in group_ins:
                    ins_for_group.append(instance)
            return ins_for_group

        except Exception as ex:
            self.log.log_error(
                "Exception at method get_group_instances: %s" % ex,
                traceback.format_exc())
            return None

    def get_rack_instances(self, hosts):
        """Get instances on racks, return list of instances."""
        racks = []
        for host in hosts:
            racks.append(self.get_rack(host))

        instances = []
        for x in self.host_instance_dict:
            if self.get_rack(self.host_instance_dict[x]) in racks:
                instances.append(x)
        return instances

    def is_already_exists(self, diction, item):
        """Return true if item exists in diction."""
        if item in diction:
            return True

        diction[item] = 1
        return False

    def compare_rack(self, current_host, first_host):
        """Compare racks for hosts, return true if racks equal."""
        return self.get_rack(current_host) == self.get_rack(first_host)

    def compare_host(self, current_host, first_host):
        """Compare current to first host, return True if equal."""
        return current_host == first_host

    def get_rack(self, host):
        """Get rack for current host."""
        return (host.split("r")[1])[:2]

    def get_host_or_rack(self, level, host):
        """Return host or rack based on level."""
        return host if level == "host" else self.get_rack(host)
