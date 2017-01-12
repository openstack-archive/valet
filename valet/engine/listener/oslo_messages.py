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

'''OsloMessage Database Model'''

# This is based on Music models used in Valet.

import uuid


class OsloMessage(object):
    __tablename__ = 'oslo_messages'

    _database = None

    timestamp = None
    args = None
    exchange = None
    method = None

    @classmethod
    def schema(cls):
        '''Return schema.'''
        schema = {
            'timestamp': 'text',
            'args': 'text',
            'exchange': 'text',
            'method': 'text',
            'PRIMARY KEY': '(timestamp)'
        }
        return schema

    @classmethod
    def pk_name(cls):
        return 'timestamp'

    def pk_value(self):
        return self.timestamp

    def insert(self):
        '''Insert row.'''
        keyspace = self._database.get('keyspace')
        kwargs = {
            'keyspace': keyspace,
            'table': self.__tablename__,
            'values': self.values()
        }
        pk_name = self.pk_name()
        if pk_name not in kwargs['values']:
            the_id = str(uuid.uuid4())
            kwargs['values'][pk_name] = the_id
            setattr(self, pk_name, the_id)
        engine = self._database.get('engine')
        engine.create_row(**kwargs)

    def values(self):
        return {
            'timestamp': self.timestamp,
            'args': self.args,
            'exchange': self.exchange,
            'method': self.method,
        }

    def __init__(self, timestamp, args, exchange,
                 method, database, _insert=True):
        self._database = database
        self.timestamp = timestamp
        self.args = args
        self.exchange = exchange
        self.method = method
        if _insert:
            self.insert()

    def __json__(self):
        json_ = {}
        json_['timestamp'] = self.timestamp
        json_['args'] = self.args
        json_['exchange'] = self.exchange
        json_['method'] = self.method
        return json_
