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

from oslo_config import cfg

engine_opts = [
    cfg.StrOpt(
        'pid',
        default='/var/run/valet/valet-engine.pid',
        help='''

'''),
    cfg.StrOpt(
        'mode',
        default='mode',
        help='''

'''),
    cfg.StrOpt(
        'ip',
        default='localhost',
        help='''

'''),
    cfg.IntOpt(
        'health_timeout',
        default=10,
        help='''
The grace period, in seconds, for health check.
'''),
    cfg.IntOpt(
        'priority',
        default=1,
        help='''
The priority of the instance.  The priority is a positive integer.
A lower value indicates higher priority.  The master instance should have
the value of 1.
'''),
    cfg.StrOpt(
        'datacenter_name',
        default='RegionOne',
        help='''
'''),
    cfg.IntOpt(
        'compute_trigger_frequency',
        default=1800,
        help='''
Frequency, in seconds, for checking compute host status.
'''),
    cfg.IntOpt(
        'topology_trigger_frequency',
        default=1800,
        help='''
Frequency, in seconds, for checking datacenter toplogy.
'''),
    cfg.FloatOpt(
        'default_cpu_allocation_ratio',
        default=16,
        help='''
'''),
    cfg.FloatOpt(
        'default_ram_allocation_ratio',
        default=1.5,
        help='''
'''),
    cfg.FloatOpt(
        'default_disk_allocation_ratio',
        default=1,
        help='''
'''),
    cfg.FloatOpt(
        'static_cpu_standby_ratio',
        default=20,
        help='''
'''),
    cfg.FloatOpt(
        'static_mem_standby_ratio',
        default=20,
        help='''
'''),
    cfg.FloatOpt(
        'static_local_disk_standby_ratio',
        default=20,
        help='''
'''),
]


def register_opts(conf):
    conf.register_opts(engine_opts)


def list_opts():
    return {'engine': engine_opts}
