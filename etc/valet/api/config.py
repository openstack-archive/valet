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
from pecan.hooks import TransactionHook
from valet.api.db import models
from valet.api.common.hooks import NotFoundHook, MessageNotificationHook


CONF = cfg.CONF

# Server Specific Configurations
server = {
    'port': CONF.server.port,
    'host': CONF.server.host
}

# Pecan Application Configurations
app = {
    'root': 'valet.api.v1.controllers.root.RootController',
    'modules': ['valet.api'],
    'default_renderer': 'json',
    'force_canonical': False,
    'debug': False,
    'hooks': [
        TransactionHook(
            models.start,
            models.start_read_only,
            models.commit,
            models.rollback,
            models.clear
        ),
        NotFoundHook(),
        MessageNotificationHook(),
    ],
}

ostro = {
    'tries': CONF.music.tries,
    'interval': CONF.music.interval,
}


messaging = {
    'config': {
        'transport_url': 'rabbit://' + CONF.messaging.username + ':' +
        CONF.messaging.password + '@' + CONF.messaging.host + ':' +
        str(CONF.messaging.port) + '/'
    }
}

identity = {
    'config': {
        'username': CONF.identity.username,
        'password': CONF.identity.password,
        'project_name': CONF.identity.project_name,
        'auth_url': CONF.identity.auth_url,
        'interface': CONF.identity.interface,
    }
}

music = {
    'host': CONF.music.host,
    'port': CONF.music.port,
    'keyspace': CONF.music.keyspace,
    'replication_factor': CONF.music.replication_factor,
}
