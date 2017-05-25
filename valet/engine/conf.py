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

import sys

from oslo_config import cfg

from valet.common import logger_conf
from valet.common import conf as common

CONF = cfg.CONF

ostro_cli_opts = [
    cfg.StrOpt('command',
               short='c',
               default='status',
               help='engine command.'),
]

engine_group = cfg.OptGroup(name='engine', title='Valet Engine conf')
engine_opts = [
    cfg.StrOpt('pid',
               default='/var/run/valet/valet-engine.pid'),
    cfg.StrOpt('mode',
               default='live',
               help='run as actual or simulation for test'),
    cfg.StrOpt('sim_cfg_loc',
               default='/etc/valet/engine/ostro_sim.cfg'),
    cfg.StrOpt('ip',
               default='localhost'),
    cfg.IntOpt('health_timeout',
               default=10,
               help='health check grace period (seconds, default=10)'),
    cfg.IntOpt('priority',
               default=1,
               help='this instance priority (master=1)'),
    cfg.StrOpt('datacenter_name',
               default='aic',
               help='The name of region'),
    cfg.IntOpt('num_of_region_chars',
               default='3',
               help='number of chars that indicates the region code'),
    cfg.StrOpt('rack_code_list',
               default='r',
               help='rack indicator.'),
    cfg.ListOpt('node_code_list',
                default='a,c,u,f,o,p,s',
                help='Indicates the node type'),
    cfg.IntOpt('compute_trigger_frequency',
               default=1800,
               help='Frequency for checking compute hosting status'),
    cfg.IntOpt('topology_trigger_frequency',
               default=3600,
               help='Frequency for checking datacenter topology'),
    cfg.IntOpt('update_batch_wait',
               default=600,
               help='Wait time before start resource synch from Nova'),
    cfg.FloatOpt('default_cpu_allocation_ratio',
                 default=16,
                 help='Default CPU overbooking ratios'),
    cfg.FloatOpt('default_ram_allocation_ratio',
                 default=1.5, help='Default mem overbooking ratios'),
    cfg.FloatOpt('default_disk_allocation_ratio',
                 default=1,
                 help='Default disk overbooking ratios'),
    cfg.FloatOpt('static_cpu_standby_ratio',
                 default=20,
                 help='Percentages of standby cpu resources'),
    cfg.FloatOpt('static_mem_standby_ratio',
                 default=20,
                 help='Percentages of standby mem resources'),
    cfg.FloatOpt('static_local_disk_standby_ratio',
                 default=20,
                 help='Percentages of disk standby  esources'),
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
    """Register the engine and the listener groups """
    common.init_conf("engine.log", args=sys.argv[1:],
                     grp2opt={engine_group: engine_opts,
                     listener_group: listener_opts},
                     cli_opts=[ostro_cli_opts],
                     default_config_files=default_config_files)
