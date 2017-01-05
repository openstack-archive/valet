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

"""Conf."""

from oslo_config import cfg
import sys
from valet.common import logger_conf, conf as common

CONF = cfg.CONF

ostro_cli_opts = [
    cfg.StrOpt('command',
               short='c',
               default='status',
               help='engine command.'),
]

engine_group = cfg.OptGroup(name='engine', title='Valet Engine conf')
engine_opts = [
    cfg.StrOpt('pid', default='/var/run/valet/ostro-daemon.pid'),
    cfg.StrOpt('mode', default='live', help='sim will let Ostro simulate datacenter, while live will let it handle a real datacenter'),
    cfg.StrOpt('sim_cfg_loc', default='/etc/valet/engine/ostro_sim.cfg'),
    cfg.BoolOpt('network_control', default=False, help='whether network controller (i.e., Tegu) has been deployed'),
    cfg.StrOpt('network_control_url', default='http://network_control:29444/tegu/api'),
    cfg.StrOpt('ip', default='localhost'),
    cfg.IntOpt('health_timeout', default=10, help='health check grace period (seconds, default=10)'),
    cfg.IntOpt('priority', default=1, help='this instance priority (master=1)'),
    cfg.StrOpt('rpc_server_ip', default='localhost',
               help='Set RPC server ip and port if used. Otherwise, ignore these parameters'),
    cfg.StrOpt('rpc_server_port', default='8002'),
    cfg.StrOpt('datacenter_name', default='bigsite',
               help='Inform the name of datacenter (region name), where Valet/Ostro is deployed.'),
    cfg.IntOpt('num_of_region_chars', default='3', help='number of chars that indicates the region code'),
    cfg.StrOpt('rack_code_list', default='r', help='rack indicator.'),
    cfg.ListOpt('node_code_list', default='a,c,u,f,o,p,s',
                help='indicates the node type. a: network, c KVM compute, u: ESXi compute, f: ?, o: operation, '
                     'p: power, s: storage.'),
    cfg.StrOpt('compute_trigger_time', default='1:00',
               help='trigger time or frequency for checking compute hosting server status (i.e., call Nova)'),
    cfg.IntOpt('compute_trigger_frequency', default=3600,
               help='trigger time or frequency for checking compute hosting server status (i.e., call Nova)'),
    cfg.StrOpt('topology_trigger_time', default='2:00',
               help='Set trigger time or frequency for checking datacenter topology (i.e., call AIC Formation)'),
    cfg.IntOpt('topology_trigger_frequency', default=3600,
               help='Set trigger time or frequency for checking datacenter topology (i.e., call AIC Formation)'),
    cfg.IntOpt('default_cpu_allocation_ratio', default=16, help='Set default overbooking ratios. '
                                                                'Note that each compute node can have its own ratios'),
    cfg.IntOpt('default_ram_allocation_ratio', default=1.5, help='Set default overbooking ratios. '
                                                                 'Note that each compute node can have its own ratios'),
    cfg.IntOpt('default_disk_allocation_ratio', default=1, help='Set default overbooking ratios. '
                                                                'Note that each compute node can have its own ratios'),
    cfg.IntOpt('static_cpu_standby_ratio', default=20, help='unused percentages of resources (i.e. standby) '
                                                            'that are set aside for applications workload spikes.'),
    cfg.IntOpt('static_mem_standby_ratio', default=20, help='unused percentages of resources (i.e. standby) '
                                                            'that are set aside for applications workload spikes.'),
    cfg.IntOpt('static_local_disk_standby_ratio', default=20, help='unused percentages of resources (i.e. standby) '
                                                                   'that are set aside for applications workload spikes.'),
] + logger_conf("engine")

listener_group = cfg.OptGroup(name='events_listener',
                              title='Valet Engine listener')
listener_opts = [
    cfg.StrOpt('exchange', default='nova'),
    cfg.StrOpt('exchange_type', default='topic'),
    cfg.BoolOpt('auto_delete', default=False),
    cfg.BoolOpt('store', default=True),
] + logger_conf("ostro_listener")


def init_engine(default_config_files=None):
    """ register the engine and the listener groups """
    common.init_conf("engine.log", args=sys.argv[1:],
                     grp2opt={engine_group: engine_opts,
                     listener_group: listener_opts},
                     cli_opts=[ostro_cli_opts],
                     default_config_files=default_config_files)
