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
        help='Set path to Valet Engine runing process pid.'
    ),
    cfg.StrOpt(
        'datacenter_name',
        default='Region1',
        help="""
            Inform the name of datacenter (region name),
            where Valet is deployed.
    """),
    cfg.IntOpt(
        'compute_trigger_frequency',
        default=1800,
        help='Set frequency, in seconds, for checking compute host status.'
    ),
    cfg.IntOpt(
        'topology_trigger_frequency',
        default=1800,
        help="""
            Set trigger time or frequency, in seconds,
            for checking datacenter toplogy.
    """),
    cfg.FloatOpt(
        'default_cpu_allocation_ratio',
        default=16,
        help="""
            Set default overbooking ratios.
            Note that each compute node can have its own ratios.
    """),
    cfg.FloatOpt(
        'default_ram_allocation_ratio',
        default=1.5,
        help='Set default mem overbooking ratios.'
    ),
    cfg.FloatOpt(
        'default_disk_allocation_ratio',
        default=1,
        help='Set default disk overbooking ratios.'
    ),
    cfg.FloatOpt(
        'static_cpu_standby_ratio',
        default=20,
        help='Set percentages of standby CPU resources.'
    ),
    cfg.FloatOpt(
        'static_mem_standby_ratio',
        default=20,
        help='Set percentages of standby mem resources.'
    ),
    cfg.FloatOpt(
        'static_local_disk_standby_ratio',
        default=20,
        help='Set percentages of disk standby resources.'
    ),
]


def register_opts(conf):
    conf.register_opts(engine_opts)


def list_opts():
    return {'engine': engine_opts}
