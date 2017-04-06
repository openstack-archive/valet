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
from oslo_log import log as logging

CONF = cfg.CONF
DOMAIN = 'valet'


def get_logger(name):
    return logging.getLogger(name)

LOG = get_logger("engine")

server_group = cfg.OptGroup(name='server', title='Valet API Server conf')
server_opts = [
    cfg.StrOpt('host', default='0.0.0.0'),
    cfg.StrOpt('port', default='8090'),
]


messaging_group = cfg.OptGroup(name='messaging', title='Valet Messaging conf')
messaging_opts = [
    cfg.StrOpt('username'),
    cfg.StrOpt('password'),
    cfg.StrOpt('host'),
    cfg.IntOpt('port', default=5672),
    cfg.IntOpt('timeout', default=3),
]


identity_group = cfg.OptGroup(name='identity', title='Valet identity conf')
identity_opts = [
    cfg.StrOpt('username'),
    cfg.StrOpt('password'),
    cfg.StrOpt('project_name'),
    cfg.StrOpt('auth_url', default='http://controller:5000/v2.0'),
    cfg.StrOpt('interface', default='admin'),
]


music_group = cfg.OptGroup(name='music', title='Valet Persistence conf')
music_opts = [
    cfg.ListOpt('hosts', default=['0.0.0.0']),
    cfg.IntOpt('port', default=8080),
    cfg.StrOpt('keyspace', default='valet'),
    cfg.IntOpt('replication_factor', default=3),
    cfg.IntOpt('tries', default=10),
    cfg.IntOpt('interval', default=1),
    cfg.StrOpt('request_table', default='placement_requests'),
    cfg.StrOpt('response_table', default='placement_results'),
    cfg.StrOpt('event_table', default='oslo_messages'),
    cfg.StrOpt('resource_table', default='resource_status'),
    cfg.StrOpt('app_table', default='app'),
    cfg.StrOpt('resource_index_table', default='resource_log_index'),
    cfg.StrOpt('app_index_table', default='app_log_index'),
    cfg.StrOpt('uuid_table', default='uuid_map'),
    cfg.IntOpt('music_server_retries', default=3),
]

def load_conf(args=None, project=DOMAIN, default_files=None):
    CONF(default_config_files=default_files) if default_files else CONF(args or [], project=project)


def init_conf(log_file="valet.log", args=None, grp2opt=None, cli_opts=None, default_config_files=None):
    CONF.log_file = log_file
    logging.register_options(CONF)

    # init conf
    general_groups = {server_group: server_opts, music_group: music_opts,
                      identity_group: identity_opts, messaging_group: messaging_opts}

    general_groups.update(grp2opt or {})

    _register_conf(general_groups, cli_opts)
    load_conf(args=args, default_files=default_config_files)

    # set logger
    _set_logger()


def _set_logger():
    logging.setup(CONF, DOMAIN)

def _register_conf(grp2opt, cli_opts):
    for grp in grp2opt or {}:
        CONF.register_group(grp)
        CONF.register_opts(grp2opt[grp], grp)

   for opt in cli_opts or []:
        CONF.register_cli_opts(opt)
