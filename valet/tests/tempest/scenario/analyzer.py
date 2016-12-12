# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
'''
Created on Nov 8, 2016

@author: Yael
'''

from collections import defaultdict
import os
from tempest import config
import traceback

CONF = config.CONF


class Analyzer(object):

    def __init__(self, logger, stack_id, heat, nova):
        ''' initializing the analyzer - connecting to nova '''
        self.heat_client = heat
        self.nova_client = nova
        self.possible_topdir = os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir))
        self.stack_identifier = stack_id
        self.log = logger
        self.resource_name = {}
        self.instance_on_server = {}
        self.group_instance_name = {}

    def check(self, resources):
        ''' Checking if all instances are on the Appropriate hosts and racks '''
        self.log.log_info("Starting to check instances location")
        result = True

        self.init_servers_list()
        self.init_resources(resources)
        ins_group = self.init_instances_for_group(resources)

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
            self.log.log_error("Exception at method check: %s" % ex, traceback.format_exc())
            result = False

        return result

    def init_instances_for_group(self, resources):
        ins_group = defaultdict(list)

        for grp in resources.groups.keys():
            self.group_instance_name[grp] = resources.groups[grp].group_resources
            resources.groups[grp].group_resources.append(resources.groups[grp].level)
            ins_group[resources.groups[grp].group_type].append(resources.groups[grp].group_resources)

        # replacing group for it's instances
        ins_group = self.organize(ins_group)

        return ins_group

    def init_resources(self, resources):
        for ins in resources.instances:
            self.resource_name[ins.resource_name] = ins.name

    def init_servers_list(self):
        servers_list = self.nova_client.list_servers()

        for i in range(len(servers_list["servers"])):
            server = self.nova_client.show_server(servers_list["servers"][i]["id"])
            self.instance_on_server[servers_list["servers"][i]["name"]] = server["server"]["OS-EXT-SRV-ATTR:host"]

    def get_instance_name(self, res_name):
        return self.resource_name[res_name]

    def get_instance_host(self, res_name):
        hosts = []

        if len(self.instance_on_server) == 0:
            self.init_servers_list()
            self.log.log_info("instance_on_server: %s" % self.instance_on_server)

        for res in res_name:
            name = self.get_instance_name(res)
            hosts.append(self.instance_on_server[name])

        return hosts

    def are_the_same(self, res_name, level):
        self.log.log_info("are_the_same")
        hosts_list = self.get_instance_host(res_name)
        self.log.log_info(hosts_list)

        try:
            for h in hosts_list:
                if self.compare_host(self.get_host_or_rack(level, h), self.get_host_or_rack(level, hosts_list[0])) is False:
                    return False
            return True

        except Exception as ex:
            self.log.log_error("Exception at method are_the_same: %s" % ex, traceback.format_exc())
            return False

    def are_different(self, res_name, level):
        ''' Checking if all hosts (and racks) are different for all instances '''
        self.log.log_info("are_different")
        diction = {}
        hosts_list = self.get_instance_host(res_name)
        self.log.log_info(hosts_list)

        try:
            for h in hosts_list:
                if self.is_already_exists(diction, self.get_host_or_rack(level, h)):
                    return False
            return True

        except Exception as ex:
            self.log.log_error("Exception at method are_all_hosts_different: %s" % ex, traceback.format_exc())
            return False

    def are_we_alone(self, ins_for_group, level):
        self.log.log_info("are_we_alone ")
        self.log.log_info(ins_for_group)

        instances = self.instance_on_server.keys()
        if level == "rack":
            instances = self.get_rack_instances(set(self.instance_on_server.values()))

        # instance_on_server should be all the instances on the rack
        if len(instances) < 1:
            return False

        for instance in ins_for_group:
            if self.resource_name[instance] in instances:
                instances.remove(self.resource_name[instance])

        return not instances

    def organize(self, ins_group):
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

    def get_group_instances(self, resources, group_ins):
        ''' gets the instance object according to the group_ins

        group_ins - the group_resources name of the instances belong to this group (['my-instance-1', 'my-instance-2'])
        '''
        ins_for_group = []
        try:
            for instance in resources.instances:
                if instance.resource_name in group_ins:
                    ins_for_group.append(instance)
            return ins_for_group

        except Exception as ex:
            self.log.log_error("Exception at method get_group_instances: %s" % ex, traceback.format_exc())
            return None

    def get_rack_instances(self, hosts):
        racks = []
        for host in hosts:
            racks.append(self.get_rack(host))

        instances = []
        for x in self.instance_on_server:
            if self.get_rack(self.instance_on_server[x]) in racks:
                instances.append(x)
        return instances

    def is_already_exists(self, diction, item):
        if item in diction:
            return True

        diction[item] = 1
        return False

    def compare_rack(self, current_host, first_host):
        self.log.log_debug(current_host)
        return self.get_rack(current_host) == self.get_rack(first_host)

    def compare_host(self, current_host, first_host):
        self.log.log_debug(current_host)
        return current_host == first_host

    def get_rack(self, host):
        return (host.split("r")[1])[:2]

    def get_host_or_rack(self, level, host):
        return host if level == "host" else self.get_rack(host)
