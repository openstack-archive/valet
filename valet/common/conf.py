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

def _set_logger():
    logging.setup(CONF, DOMAIN)