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

music_opts = [
    cfg.IntOpt(
        'tries',
        default=10,
        help='''
'''
    ),
    cfg.IntOpt(
        'replication_factor',
        default=3,
        help='''
'''
    ),
    cfg.IntOpt(
        'interval',
        default=1,
        help='''
'''
    ),
    cfg.StrOpt(
        'request_table',
        default='placement_requests',
        help='''
'''),
    cfg.StrOpt(
        'response_table',
        default='placement_results',
        help='''
'''),
    cfg.StrOpt(
        'resource_table',
        default='resource_status',
        help='''
'''),
    cfg.StrOpt(
        'event_table',
        default='oslo_messages',
        help='''
'''),
    cfg.StrOpt(
        'resource_index_table',
        default='resource_log_index',
        help='''
'''),
    cfg.StrOpt(
        'app_table',
        default='app',
        help='''
'''),
    cfg.StrOpt(
        'app_index_table',
        default='app_log_index',
        help='''
'''),
    cfg.StrOpt(
        'uuid_table',
        default='uuid_map',
        help='''
'''),
    cfg.IntOpt(
        'music_server_retries',
        default=3,
        help='''
'''),

]


def register_opts(conf):
    conf.register_opts(music_opts)


def list_opts():
    return {'music': music_opts}
