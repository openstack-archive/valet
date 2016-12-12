# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
'''
Created on May 5, 2016

@author: Yael
'''

import os
from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

DOMAIN = "valet_validator"

"""
Black        0;30     Dark Gray     1;30
Red          0;31     Light Red     1;31
Green        0;32     Light Green   1;32
Brown/Orange 0;33     Yellow        1;33
Blue         0;34     Light Blue    1;34
Purple       0;35     Light Purple  1;35
Cyan         0;36     Light Cyan    1;36
Light Gray   0;37     White         1;37
"""
COLORS = \
    {
        "WHITE": '\033[0;37m',
        "L_RED": '\033[1;31m',
        "L_PURPLE": '\033[1;35m',
        "L_GREEN": '\033[0;32m',
        "L_BLUE": '\033[1;34m',
        "Yellow": '\033[0;33m'
    }


opts_auth = \
    [
        cfg.StrOpt('OS_AUTH_URL_WITH_VERSION', default='http://controller:5000/v2.0'),
        cfg.StrOpt('OS_USERNAME', default="addddmin"),
        cfg.StrOpt('OS_PASSWORD', default="qwer4321"),
        cfg.StrOpt('OS_TENANT_NAME', default="demo"),
        cfg.IntOpt('TOKEN_EXPIRATION', default=600),
    ]

opt_nova = \
    [
        cfg.StrOpt('VERSION', default="2"),
        cfg.StrOpt('ATTR', default="OS-EXT-SRV-ATTR:host"),
    ]

opt_heat = \
    [
        cfg.StrOpt('HEAT_URL', default="http://controller:8004/v1/"),
        cfg.StrOpt('KEY', default="output_key"),
        cfg.StrOpt('VALUE', default="output_value"),
        cfg.StrOpt('VERSION', default="1"),
        cfg.IntOpt('DELAY_DURATION', default=1),
        cfg.IntOpt('TRIES_TO_CREATE', default=5),
        cfg.IntOpt('TIME_CAP', default=60),
    ]

opt_valet = \
    [
        cfg.StrOpt('HOST', default="http://controller:8090/v1"),
        cfg.IntOpt('DELAY_DURATION', default=1),
        cfg.IntOpt('TRIES_TO_CREATE', default=5),
        cfg.IntOpt('PAUSE', default=5),
        cfg.IntOpt('TIME_CAP', default=60),
    ]

CONF.register_opts(opts_auth, group="auth")
CONF.register_opts(opt_heat, group="heat")
CONF.register_opts(opt_nova, group="nova")
CONF.register_opts(opt_valet, group="valet")

_initialized = False


def prepare(CONF):
    global _initialized
    try:
        if _initialized is False:
            logging.register_options(CONF)
            _initialized = True

        # Adding config file
            possible_topdir = os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir, os.pardir, os.pardir))
            conf_file = os.path.join(possible_topdir, 'etc', DOMAIN + '.cfg')
            CONF([], project=DOMAIN, default_config_files=[conf_file] or None, validate_default_values=True)

            logging.setup(CONF, DOMAIN)

    except Exception as ex:
        LOG.error("Preparation failed! %s" % ex)
