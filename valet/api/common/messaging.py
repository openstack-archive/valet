# -*- encoding: utf-8 -*-
#
# Copyright (c) 2014-2016 AT&T
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.

'''Messaging helper library'''

from oslo_config import cfg
import oslo_messaging as messaging
from pecan import conf
from valet.api.conf import set_domain, DOMAIN


def _messaging_notifier_from_config(config):
    '''Initialize the messaging engine based on supplied config.'''
    transport_url = config.get('transport_url')
    transport = messaging.get_transport(cfg.CONF, transport_url)
    notifier = messaging.Notifier(transport, driver='messaging',
                                  publisher_id='valet',
                                  topic='notifications', retry=10)
    return notifier


def init_messaging():
    '''Initialize the messaging engine and place in the config.'''
    set_domain(DOMAIN)
    config = conf.messaging.config
    notifier = _messaging_notifier_from_config(config)
    conf.messaging.notifier = notifier
    conf.messaging.timeout = cfg.CONF.messaging.timeout
