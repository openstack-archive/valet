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

import json
import os
import sys
import time
import uuid

from oslo_config import cfg

from valet.common.conf import get_logger
from valet.common.music import REST

CONF = cfg.CONF


class HealthCheck(object):

    rest = None

    def __init__(self, hosts=[]):
        # default health_timeout=10
        self.tries = CONF.engine.health_timeout * 2
        self.uuid = str(uuid.uuid4())

        kwargs = {
            'hosts': hosts,
            'port': CONF.music.port,
            'path': '/MUSIC/rest',
            'timeout': CONF.music.interval,
        }
        self.rest = REST(**kwargs)

    def ping(self):

        engine_id = None
        try:
            if self._send():
                engine_id = self._read_response()
        finally:
            self._delete_result()
        return engine_id

    def _send(self):
        request = [
            {
                "action": "ping",
                "stack_id": self.uuid
            }
        ]

        data = {
            "values": {
                "stack_id": self.uuid,
                "request": request
            },
            "consistencyInfo": {
                "type": "eventual"
            }
        }

        path = '/keyspaces/%(keyspace)s/tables/%(table)s/rows' % {
            'keyspace': CONF.music.keyspace,
            'table': CONF.music.request_table,
        }
        response = self.rest.request(method='post', path=path, data=data)

        return response.status_code == 204 if response else False

    def _read_response(self):

        engine_id = None
        pre = '/keyspaces/%(keyspace)s/tables/%(table)s/rows?stack_id=%(uid)s'
        path = pre % {
            'keyspace': CONF.music.keyspace,
            'table': CONF.music.response_table,
            'uid': self.uuid,
        }

        # default 20 tries * 0.5 sec = 10 sec. timeout
        for i in range(self.tries):
            time.sleep(0.5)
            try:
                response = self.rest.request(method='get', path=path)

                if response.status_code == 200 and len(response.text) > 3:

                    j = json.loads(response.text)
                    if j['row 0']['stack_id'] != self.uuid:
                        continue

                    placement = json.loads(j['row 0']['placement'])
                    engine_id = placement['resources']['id']
                    break
            except Exception as e:
                logger.warn("HealthCheck exception in read response " + str(e))

        return engine_id

    def _delete_result(self):
        # leave a clean table - delete from requests and responses
        data = {
            "consistencyInfo": {"type": "eventual"}
        }

        base = '/keyspaces/%(keyspace)s/tables/%(table)s/rows?stack_id=%(uid)s'
        try:
            path = base % {
                'keyspace': CONF.music.keyspace,
                'table': CONF.music.request_table,
                'uid': self.uuid
            }
            self.rest.request(method='delete', path=path, data=data)
        except Exception as e:
            logger.warn("HealthCheck exception in delete request - " + str(e))

        try:
            path = base % {
                'keyspace': CONF.music.keyspace,
                'table': CONF.music.response_table,
                'uid': self.uuid
            }
            self.rest.request(method='delete', path=path, data=data)
        except Exception as e:
            logger.warn("HealthCheck exception in delete response - " + str(e))


if __name__ == "__main__":

    respondent_id = None
    code = 0
    logger = get_logger("ostro_daemon")

    if os.path.exists(CONF.engine.pid):
        respondent_id = HealthCheck().ping()

        if respondent_id == CONF.engine.priority:
            code = CONF.engine.priority
            logger.info("HealthCheck - Alive, "
                        "respondent instance id: {}".format(respondent_id))
        else:
            logger.warn("HealthCheck - pid file exists, "
                        "engine {} did not respond in a timely manner "
                        "(respondent id {})".format(CONF.engine.priority,
                                                    respondent_id))
    else:
        logger.info("HealthCheck - no pid file, engine is not running!")
    sys.exit(code)
