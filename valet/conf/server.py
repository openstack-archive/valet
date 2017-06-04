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

server_options = [
    cfg.StrOpt(
        'host',
        default='0.0.0.0',
        help='''
'''),
    cfg.PortOpt(
        'port',
        default=8090,
        help='''
''')
]


def register_opts(conf):
    conf.register_opts(server_options)


def list_opts():
    return {'server': server_options}
