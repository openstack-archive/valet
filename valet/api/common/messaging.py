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

"""Messaging helper library."""

from oslo_config import cfg
import oslo_messaging as messaging
from pecan import conf


def _messaging_notifier_from_config(config):
    """Initialize the messaging engine based on supplied config."""
    transport_url = config.get('transport_url')
    transport = messaging.get_notification_transport(cfg.CONF, transport_url)
    notifier = messaging.Notifier(transport, driver='messaging',
                                  publisher_id='valet',
                                  topics=['notifications'], retry=10)
    return notifier


def init_messaging():
    """Initialize the messaging engine and place in the config."""
    config = conf.messaging.config
    notifier = _messaging_notifier_from_config(config)
    conf.messaging.notifier = notifier
    conf.messaging.timeout = cfg.CONF.messaging.timeout
