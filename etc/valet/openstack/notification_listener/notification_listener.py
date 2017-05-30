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

"""Notification Listener."""

import json
from oslo_config import cfg
import oslo_messaging


class NotificationEndpoint(object):
    """Endponit for a notifcation (info, warn, error)."""

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        """Print notifaction was received and dumb json data to print."""
        print('recv notification:')
        print(json.dumps(payload, indent=4))

    def warn(self, ctxt, publisher_id, event_type, payload, metadata):
        """Warn."""
        None

    def error(self, ctxt, publisher_id, event_type, payload, metadata):
        """Error."""
        None

transport = oslo_messaging.get_transport(cfg.CONF)
targets = [oslo_messaging.Target(topic='notifications')]
endpoints = [NotificationEndpoint()]

<<<<<<< 7de1e62db57776cc8db132d419963e650c6c7af2
server = oslo_messaging.get_notification_listener(
    transport, targets, endpoints)
=======
server = oslo_messaging.get_notification_listener(transport,
                                                  targets,
                                                  endpoints)
>>>>>>> [WIP] Refactoring the plugin code and tests
server.start()
server.wait()
