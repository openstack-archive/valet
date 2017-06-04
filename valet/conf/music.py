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
        'replication_factor',
        default=3,
        help='How many database replicas Music should distribute against.'
    ),
    cfg.IntOpt(
        'music_server_retries',
        default=3,
        help="""
    Number of attempts in performing a read/write action to/from MUSIC.
    After retries are exceeded, another MUSIC host is attempted.
    """),
    cfg.StrOpt(
        'hosts',
        default='localhost',
        help="""
    IP address or FQDN used to contact the MUSIC service.
    Strings can be given in the format "localhost:8080, ip2:8080,host3:8080".
    """),
    cfg.IntOpt(
        'port',
        default=8080,
        help='Port Opened to allow messages to the MUSIC REST service.'
    ),
    cfg.StrOpt(
        'keyspace',
        default='db_keyspace',
        help='Name of Cassandra keyspace used by Valet.'
    )
]


def register_opts(conf):
    conf.register_opts(music_opts)


def list_opts():
    return {'music': music_opts}
