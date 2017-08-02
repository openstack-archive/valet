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

# - Set all configurations to run Ostro

"""Valet Engine Server Configuration."""

from oslo_config import cfg
from valet.engine.conf import init_engine


CONF = cfg.CONF


class Config(object):
    """Valet Engine Server Configuration."""

    def __init__(self, *default_config_files):
        init_engine(default_config_files=default_config_files)

        self.command = 'status'
        self.process = None
        self.control_loc = None
        self.api_protocol = 'http://'

        self.db_keyspace = None
        self.db_request_table = None
        self.db_response_table = None
        self.db_event_table = None
        self.db_resource_table = None
        self.db_app_table = None
        self.db_uuid_table = None
        self.db_group_table = None
        self.replication_factor = 3
        self.hosts = ['localhost']
        self.port = 8080

        self.ip = None
        self.priority = 0

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

        self.topology_trigger_freq = 0
        self.compute_trigger_freq = 0
        self.metadata_trigger_freq = 0
        self.update_batch_wait = 0

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

        # Music HA paramater
        self.music_server_retries = 3

    def configure(self):
        """Store config info extracted from oslo."""
        status = self._init_system()
        if status != "success":
            return status

        self.process = self.process
        self.logging_loc = self.logging_loc
        self.resource_log_loc = self.logging_loc
        self.app_log_loc = self.logging_loc
        self.eval_log_loc = self.logging_loc

        return "success"

    def _init_system(self):

        self.command = CONF.command

        self.logger_name = CONF.engine.logger_name
        self.logging_level = CONF.engine.logging_level
        self.logging_loc = CONF.engine.logging_dir
        self.resource_log_loc = CONF.engine.logging_dir + 'resources'
        self.app_log_loc = CONF.engine.logging_dir + 'app'
        self.eval_log_loc = CONF.engine.logging_dir
        self.max_log_size = CONF.engine.max_log_size
        self.max_num_of_logs = CONF.engine.max_num_of_logs

        self.process = CONF.engine.pid
        self.datacenter_name = CONF.engine.datacenter_name

        self.default_cpu_allocation_ratio = \
            CONF.engine.default_cpu_allocation_ratio

        self.default_ram_allocation_ratio = \
            CONF.engine.default_ram_allocation_ratio

        self.default_disk_allocation_ratio = \
            CONF.engine.default_disk_allocation_ratio

        self.static_cpu_standby_ratio = CONF.engine.static_cpu_standby_ratio
        self.static_mem_standby_ratio = CONF.engine.static_mem_standby_ratio

        self.static_local_disk_standby_ratio = \
            CONF.engine.static_local_disk_standby_ratio

        self.topology_trigger_freq = CONF.engine.topology_trigger_frequency
        self.compute_trigger_freq = CONF.engine.compute_trigger_frequency
        self.metadata_trigger_freq = CONF.engine.metadata_trigger_frequency
        self.update_batch_wait = CONF.engine.update_batch_wait

        self.db_keyspace = CONF.music.keyspace
        self.db_request_table = CONF.music.request_table
        self.db_response_table = CONF.music.response_table
        self.db_event_table = CONF.music.event_table
        self.db_resource_table = CONF.music.resource_table
        self.db_app_table = CONF.music.app_table
        self.db_uuid_table = CONF.music.uuid_table
        self.db_group_table = CONF.music.group_table

        self.music_server_retries = CONF.music.music_server_retries
        self.replication_factor = CONF.music.replication_factor

        self.hosts = CONF.music.hosts
        self.port = CONF.music.port

        self.priority = CONF.engine.priority
        self.ip = CONF.engine.ip

        self.num_of_region_chars = CONF.engine.num_of_region_chars
        self.rack_code_list = CONF.engine.rack_code_list
        self.node_code_list = CONF.engine.node_code_list

        self.project_name = CONF.identity.project_name
        self.user_name = CONF.identity.username
        self.pw = CONF.identity.password

        return "success"
