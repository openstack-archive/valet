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
#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
# Modified: Sep. 16, 2016
#
# Functions
# - Set all configurations to run Ostro
#
#################################################################################################################

import os
from oslo_config import cfg
from valet.engine.conf import register_conf


CONF = cfg.CONF


class Config(object):

    def __init__(self, *default_config_files):

        register_conf()
        if default_config_files:
            CONF(default_config_files=default_config_files)
        else:
            CONF(project='valet')

        # System parameters
        self.root_loc = os.path.dirname(CONF.default_config_files[0])

        self.mode = None

        self.command = 'status'

        self.process = None

        self.control_loc = None

        self.api_protocol = 'http://'

        self.network_control = False
        self.network_control_api = None

        self.db_keyspace = None
        self.db_request_table = None
        self.db_response_table = None
        self.db_event_table = None
        self.db_resource_table = None
        self.db_app_table = None
        self.db_resource_index_table = None
        self.db_app_index_table = None
        self.db_uuid_table = None
        self.replication_factor = 3
        self.db_hosts = []

        self.ip = None

        self.priority = 0

        self.rpc_server_ip = None
        self.rpc_server_port = 0

        # Logging parameters
        self.logger_name = None
        self.logging_level = None
        self.logging_loc = None

        self.resource_log_loc = None
        self.app_log_loc = None
        self.max_main_log_size = 0
        self.max_log_size = 0
        self.max_num_of_logs = 0

        # Management parameters
        self.datacenter_name = None

        self.num_of_region_chars = 0
        self.rack_code_list = []
        self.node_code_list = []

        self.topology_trigger_time = None
        self.topology_trigger_freq = 0
        self.compute_trigger_time = None
        self.compute_trigger_freq = 0

        self.default_cpu_allocation_ratio = 1
        self.default_ram_allocation_ratio = 1
        self.default_disk_allocation_ratio = 1

        self.static_cpu_standby_ratio = 0
        self.static_mem_standby_ratio = 0
        self.static_local_disk_standby_ratio = 0

        # Authentication parameters
        self.project_name = None
        self.user_name = None
        self.pw = None

        # Simulation parameters
        self.sim_cfg_loc = None

        self.num_of_hosts_per_rack = 0
        self.num_of_racks = 0
        self.num_of_spine_switches = 0
        self.num_of_aggregates = 0
        self.aggregated_ratio = 0

        self.cpus_per_host = 0
        self.mem_per_host = 0
        self.disk_per_host = 0
        self.bandwidth_of_spine = 0
        self.bandwidth_of_rack = 0
        self.bandwidth_of_host = 0

        self.num_of_basic_flavors = 0
        self.base_flavor_cpus = 0
        self.base_flavor_mem = 0
        self.base_flavor_disk = 0

    def configure(self):

        status = self._init_system()
        if status != "success":
            return status

        self.sim_cfg_loc = self.root_loc + self.sim_cfg_loc
        self.process = self.process
        self.logging_loc = self.logging_loc
        self.resource_log_loc = self.logging_loc
        self.app_log_loc = self.logging_loc
        self.eval_log_loc = self.logging_loc

        if self.mode.startswith("live") is False:
            status = self._set_simulation()
            if status != "success":
                return status

        return "success"

    def _init_system(self):

        self.command = CONF.command

        self.mode = CONF.engine.mode

        self.priority = CONF.engine.priority

        self.logger_name = CONF.engine.logger_name

        self.logging_level = CONF.engine.logging_level

        self.logging_loc = CONF.engine.logging_dir

        self.resource_log_loc = CONF.engine.logging_dir + 'resources'

        self.app_log_loc = CONF.engine.logging_dir + 'app'

        self.eval_log_loc = CONF.engine.logging_dir

        self.max_log_size = CONF.engine.max_log_size

        self.max_num_of_logs = CONF.engine.max_num_of_logs

        self.process = CONF.engine.pid

        self.rpc_server_ip = CONF.engine.rpc_server_ip

        self.rpc_server_port = CONF.engine.rpc_server_port

        self.datacenter_name = CONF.engine.datacenter_name

        self.network_control = CONF.engine.network_control

        self.network_control_url = CONF.engine.network_control_url

        self.default_cpu_allocation_ratio = CONF.engine.default_cpu_allocation_ratio

        self.default_ram_allocation_ratio = CONF.engine.default_ram_allocation_ratio

        self.default_disk_allocation_ratio = CONF.engine.default_disk_allocation_ratio

        self.static_cpu_standby_ratio = CONF.engine.static_cpu_standby_ratio

        self.static_mem_standby_ratio = CONF.engine.static_mem_standby_ratio

        self.static_local_disk_standby_ratio = CONF.engine.static_local_disk_standby_ratio

        self.topology_trigger_time = CONF.engine.topology_trigger_time

        self.topology_trigger_freq = CONF.engine.topology_trigger_frequency

        self.compute_trigger_time = CONF.engine.compute_trigger_time

        self.compute_trigger_freq = CONF.engine.compute_trigger_frequency

        self.db_keyspace = CONF.music.keyspace

        self.db_request_table = CONF.music.request_table

        self.db_response_table = CONF.music.response_table

        self.db_event_table = CONF.music.event_table

        self.db_resource_table = CONF.music.resource_table

        self.db_app_table = CONF.music.app_table

        self.db_resource_index_table = CONF.music.resource_index_table

        self.db_app_index_table = CONF.music.app_index_table

        self.db_uuid_table = CONF.music.uuid_table

        self.replication_factor = CONF.music.replication_factor

        self.db_host = CONF.music.host

        self.ip = CONF.engine.ip

        self.num_of_region_chars = CONF.engine.num_of_region_chars

        self.rack_code_list = CONF.engine.rack_code_list

        self.node_code_list = CONF.engine.node_code_list

        self.sim_cfg_loc = CONF.engine.sim_cfg_loc

        self.project_name = CONF.identity.project_name

        self.user_name = CONF.identity.username

        self.pw = CONF.identity.password

        return "success"

    def _set_simulation(self):

        self.num_of_spine_switches = CONF.engine.num_of_spine_switches

        self.num_of_hosts_per_rack = CONF.engine.num_of_hosts_per_rack

        self.num_of_racks = CONF.engine.num_of_racks

        self.num_of_aggregates = CONF.engine.num_of_aggregates

        self.aggregated_ratio = CONF.engine.aggregated_ratio

        self.cpus_per_host = CONF.engine.cpus_per_host

        self.mem_per_host = CONF.engine.mem_per_host

        self.disk_per_host = CONF.engine.disk_per_host

        self.bandwidth_of_spine = CONF.engine.bandwidth_of_spine

        self.bandwidth_of_rack = CONF.engine.bandwidth_of_rack

        self.bandwidth_of_host = CONF.engine.bandwidth_of_host

        self.num_of_basic_flavors = CONF.engine.num_of_basic_flavors

        self.base_flavor_cpus = CONF.engine.base_flavor_cpus

        self.base_flavor_mem = CONF.engine.base_flavor_mem

        self.base_flavor_disk = CONF.engine.base_flavor_disk
