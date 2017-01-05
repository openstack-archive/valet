import json
import os
from oslo_config import cfg
import sys
import time
import uuid
from valet.common.conf import get_logger
from valet.common.music import REST
from valet.engine.conf import init_engine

CONF = cfg.CONF


class HealthCheck(object):

    rest = None

    def __init__(self, hosts=[], port='8080', keyspace='valet'):

        self.tries = CONF.engine.health_timeout * 2  # default health_timeout=10
        self.uuid = str(uuid.uuid4())

        kwargs = {
            'hosts': hosts,
            'port': CONF.music.port,
            'path': '/MUSIC/rest',
            'timeout': CONF.music.interval,
        }
        self.rest = REST(**kwargs)

    def ping(self, my_id):

        engine_alive = False
        try:
            if self._send():
                engine_alive = self._read_response(my_id)
        finally:
            self._delete_result()
        return engine_alive

    def _send(self):

        data = {
            "values": {"stack_id": self.uuid,
                       "request": "[{\"action\": \"ping\", \"stack_id\": \"" + self.uuid + "\"}]"
                       },
            "consistencyInfo": {"type": "eventual"}
        }

        path = '/keyspaces/%(keyspace)s/tables/%(table)s/rows' % {
            'keyspace': CONF.music.keyspace,
            'table': CONF.music.request_table,
        }
        response = self.rest.request(method='post', path=path, data=data)

        return response.status_code == 204 if response else False

    def _read_response(self, my_id):

        found = False
        path = '/keyspaces/%(keyspace)s/tables/%(table)s/rows?stack_id=%(uid)s' % {
            'keyspace': CONF.music.keyspace,
            'table': CONF.music.response_table,
            'uid': self.uuid,
        }

        for i in range(self.tries):  # default 20 tries * 0.5 sec = 10 sec. timeout
            time.sleep(0.5)
            try:
                response = self.rest.request(method='get', path=path)

                if response.status_code == 200 and len(response.text) > 3:

                    j = json.loads(response.text)
                    stack_id = j['row 0']['stack_id']
                    placement = json.loads(j['row 0']['placement'])
                    engine_id = placement['resources']['id']

                    if stack_id == self.uuid and engine_id == my_id:
                        found = True
                        break
            except Exception:
                pass

        return found

    def _delete_result(self):
        # leave the table clean - delete from requests and responses
        try:
            path = '/keyspaces/%(keyspace)s/tables/%(table)s/rows?stack_id=%(uid)s' % {
                'keyspace': CONF.music.keyspace,
                'table': CONF.music.request_table,
                'uid': self.uuid
            }
            data = {
                "consistencyInfo": {"type": "eventual"}
            }
            self.rest.request(method='delete', path=path, data=data)

            path = '/keyspaces/%(keyspace)s/tables/%(table)s/rows?stack_id=%(uid)s' % {
                'keyspace': CONF.music.keyspace,
                'table': CONF.music.response_table,
                'uid': self.uuid
            }
            self.rest.request(method='delete', path=path, data=data)
        except Exception:
            pass


if __name__ == "__main__":

    alive = False
    code = 0
    init_engine(default_config_files=['/etc/valet/valet.conf'])
    logger = get_logger("ostro_daemon")
    if os.path.exists(CONF.engine.pid):
        alive = HealthCheck().ping(CONF.engine.priority)
    if alive:
        code = CONF.engine.priority
        logger.info("HealthCheck - Alive, priority = {}".format(CONF.engine.priority))
    else:
        logger.warn("HealthCheck - Engine is DEAD!")
    sys.exit(code)
