#
# Copyright 2015-2017 AT&T Intellectual Property
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

"""Listener Manager."""

from datetime import datetime
import json
import pika
import threading
import traceback
from valet.common.conf import get_logger
from valet.common.music import Music
from valet.engine.listener.oslo_messages import OsloMessage
import yaml


class ListenerManager(threading.Thread):
    """Listener Manager Thread Class."""

    def __init__(self, _t_id, _t_name, _config):
        """Init."""
        threading.Thread.__init__(self)
        self.thread_id = _t_id
        self.thread_name = _t_name
        self.config = _config
        self.listener_logger = get_logger("ostro_listener")
        self.MUSIC = None

    def run(self):
        """Entry point.

        Connect to localhost rabbitmq servers, use
        username:password@ipaddress:port. The port is typically 5672,
        and the default username and password are guest and guest.
        credentials = pika.PlainCredentials("guest", "PASSWORD").
        """
        try:
            self.listener_logger.info("ListenerManager: start " +
                                      self.thread_name + " ......")

            if self.config.events_listener.store:

                kwargs = {
                    'hosts': self.config.music.hosts,
                    'port': self.config.music.port,
                    'replication_factor': self.config.music.replication_factor,
                    'music_server_retries': self.config.music.music_server_retries,
                    'logger': self.listener_logger,
                }
                engine = Music(**kwargs)
                engine.create_keyspace(self.config.music.keyspace)
                self.MUSIC = {'engine': engine,
                              'keyspace': self.config.music.keyspace}
                self.listener_logger.debug('Storing in music on %s, keyspace %s'
                                           % (self.config.music.host,
                                              self.config.music.keyspace))

            self.listener_logger.debug('Connecting to %s, with %s' %
                                       (self.config.messaging.host,
                                        self.config.messaging.username))
            credentials = pika.PlainCredentials(self.config.messaging.username,
                                                self.config.messaging.password)
            parameters = pika.ConnectionParameters(self.config.messaging.host,
                                                   self.config.messaging.port,
                                                   '/', credentials)

            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            # Select the exchange we want our queue to connect to
            exchange_name = self.config.events_listener.exchange
            exchange_type = self.config.events_listener.exchange_type
            auto_delete = self.config.events_listener.auto_delete

            # Use the binding key to select what type of messages you want
            # to receive. '#' is a wild card -- meaning receive all messages
            binding_key = "#"

            # Check whether an exchange with the given name and type exists.
            # Make sure that the exchange is multicast "fanout" or "topic" type
            # otherwise queue will consume messages intended for other queues
            channel.exchange_declare(exchange=exchange_name,
                                     exchange_type=exchange_type,
                                     auto_delete=auto_delete)

            # Create an empty queue
            result = channel.queue_declare(exclusive=True)
            queue_name = result.method.queue

            # Bind the queue to the selected exchange
            channel.queue_bind(exchange=exchange_name, queue=queue_name,
                               routing_key=binding_key)
            self.listener_logger.info('Channel is bound,listening on%s '
                                      'exchange %s', self.config.messaging.host,
                                      self.config.events_listener.exchange)

            # Start consuming messages
            channel.basic_consume(self.on_message, queue_name)
        except Exception:
            self.listener_logger.error(traceback.format_exc())
            return

        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()

        # Close the channel on keyboard interrupt
        channel.close()
        connection.close()

    def on_message(self, channel, method_frame, _, body):
        """Specify the action to be taken on a message received."""
        # pylint: disable=W0613
        message = yaml.load(body)
        try:
            if 'oslo.message' in message.keys():
                message = yaml.load(message['oslo.message'])
            if self.is_message_wanted(message):
                if self.MUSIC and self.MUSIC.get('engine'):
                    self.store_message(message)
            else:
                return

            self.listener_logger.debug("\nMessage No: %s\n", method_frame.delivery_tag)
            self.listener_logger.debug(json.dumps(message, sort_keys=True, indent=2))
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        except Exception:
            self.listener_logger.error(traceback.format_exc())
            return

    def is_message_wanted(self, message):
        """Based on markers from Ostro.

        Determine if this is a wanted message.
        """
        method = message.get('method', None)
        args = message.get('args', None)

        nova_props = {'nova_object.changes', 'nova_object.data',
                      'nova_object.name'}
        args_props = {'filter_properties', 'instance'}

        is_data = method and args
        is_nova = is_data and 'objinst' in args \
            and nova_props.issubset(args['objinst'])

        action_instance = is_nova and method == 'object_action' \
            and self.is_nova_name(args) \
            and self.is_nova_state(args)

        action_compute = is_nova and self.is_compute_name(args)
        create_instance = is_data and method == 'build_and_run_instance' \
            and args_props.issubset(args) \
            and 'nova_object.data' in args['instance']

        return action_instance or action_compute or create_instance

    def store_message(self, message):
        """Store message in Music."""
        timestamp = datetime.now().isoformat()
        args = json.dumps(message.get('args', None))
        exchange = self.config.events_listener.exchange
        method = message.get('method', None)

        kwargs = {
            'timestamp': timestamp,
            'args': args,
            'exchange': exchange,
            'method': method,
            'database': self.MUSIC,
        }
        OsloMessage(**kwargs)  # pylint: disable=W0612

    def is_nova_name(self, args):
        return args['objinst']['nova_object.name'] == 'Instance'

    def is_nova_state(self, args):
        if args['objinst']['nova_object.data']['vm_state'] == 'building':
            return False
        else:
            return True

    def is_compute_name(self, args):
        """Return True if object name is ComputeNode."""
        return args['objinst']['nova_object.name'] == 'ComputeNode'
