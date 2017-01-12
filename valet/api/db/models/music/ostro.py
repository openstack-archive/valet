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

'''Ostro Models'''

from . import Base


class PlacementRequest(Base):
    '''Placement Request Model'''
    __tablename__ = 'placement_requests'

    stack_id = None
    request = None

    @classmethod
    def schema(cls):
        '''Return schema.'''
        schema = {
            'stack_id': 'text',
            'request': 'text',
            'PRIMARY KEY': '(stack_id)',
        }
        return schema

    @classmethod
    def pk_name(cls):
        '''Primary key name'''
        return 'stack_id'

    def pk_value(self):
        '''Primary key value'''
        return self.stack_id

    def values(self):
        '''Values'''
        return {
            'stack_id': self.stack_id,
            'request': self.request,
        }

    def __init__(self, request, stack_id=None, _insert=True):
        '''Initializer'''
        super(PlacementRequest, self).__init__()
        self.stack_id = stack_id
        self.request = request
        if _insert:
            self.insert()

    def __repr__(self):
        '''Object representation'''
        return '<PlacementRequest %r>' % self.stack_id

    def __json__(self):
        '''JSON representation'''
        json_ = {}
        json_['stack_id'] = self.stack_id
        json_['request'] = self.request
        return json_


class PlacementResult(Base):
    '''Placement Result Model'''
    __tablename__ = 'placement_results'

    stack_id = None
    placement = None

    @classmethod
    def schema(cls):
        '''Return schema.'''
        schema = {
            'stack_id': 'text',
            'placement': 'text',
            'PRIMARY KEY': '(stack_id)',
        }
        return schema

    @classmethod
    def pk_name(cls):
        '''Primary key name'''
        return 'stack_id'

    def pk_value(self):
        '''Primary key value'''
        return self.stack_id

    def values(self):
        '''Values'''
        return {
            'stack_id': self.stack_id,
            'placement': self.placement,
        }

    def __init__(self, placement, stack_id=None, _insert=True):
        '''Initializer'''
        super(PlacementResult, self).__init__()
        self.stack_id = stack_id
        self.placement = placement
        if _insert:
            self.insert()

    def __repr__(self):
        '''Object representation'''
        return '<PlacementResult %r>' % self.stack_id

    def __json__(self):
        '''JSON representation'''
        json_ = {}
        json_['stack_id'] = self.stack_id
        json_['placement'] = self.placement
        return json_


class Event(Base):
    '''Event Model'''
    __tablename__ = 'events'

    event_id = None
    event = None

    @classmethod
    def schema(cls):
        '''Return schema.'''
        schema = {
            'event_id': 'text',
            'event': 'text',
            'PRIMARY KEY': '(event_id)',
        }
        return schema

    @classmethod
    def pk_name(cls):
        '''Primary key name'''
        return 'event_id'

    def pk_value(self):
        '''Primary key value'''
        return self.event_id

    def values(self):
        '''Values'''
        return {
            'event_id': self.event_id,
            'event': self.event,
        }

    def __init__(self, event, event_id=None, _insert=True):
        '''Initializer'''
        super(Event, self).__init__()
        self.event_id = event_id
        self.event = event
        if _insert:
            self.insert()

    def __repr__(self):
        '''Object representation'''
        return '<Event %r>' % self.event_id

    def __json__(self):
        '''JSON representation'''
        json_ = {}
        json_['event_id'] = self.event_id
        json_['event'] = self.event
        return json_
