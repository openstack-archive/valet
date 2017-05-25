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

from oslo_config import cfg


def logger_conf(logger_name):
    return [
        cfg.StrOpt('output_format',
                   default="%(asctime)s - %(levelname)s - %(message)s"),
        cfg.BoolOpt('store', default=True),
        cfg.StrOpt('logging_level', default='debug'),
        cfg.StrOpt('logging_dir', default='/var/log/valet/'),
        cfg.StrOpt('logger_name', default=logger_name + ".log"),
        cfg.IntOpt('max_main_log_size', default=5000000),
        cfg.IntOpt('max_log_size', default=1000000),
        cfg.IntOpt('max_num_of_logs', default=3),
    ]
