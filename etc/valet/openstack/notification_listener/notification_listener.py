import json
from oslo_config import cfg
import oslo_messaging


class NotificationEndpoint(object):

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        print('recv notification:')
        print(json.dumps(payload, indent=4))

    def warn(self, ctxt, publisher_id, event_type, payload, metadata):
        None

    def error(self, ctxt, publisher_id, event_type, payload, metadata):
        None

transport = oslo_messaging.get_transport(cfg.CONF)
targets = [oslo_messaging.Target(topic='notifications')]
endpoints = [NotificationEndpoint()]

server = oslo_messaging.get_notification_listener(transport, targets, endpoints)
server.start()
server.wait()
