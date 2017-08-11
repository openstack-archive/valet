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

"""Group Model"""

import simplejson

from valet.api.db.models.music import Base


class Group(Base):
    """Group model"""
    __tablename__ = 'groups'

    id = None
    name = None
    description = None
    type = None
    level = None
    members = None

    @classmethod
    def schema(cls):
        """Return schema."""
        schema = {
            'id': 'text',
            'name': 'text',
            'description': 'text',
            'type': 'text',
            'level': 'text',
            'members': 'text',
            'PRIMARY KEY': '(id)',
        }
        return schema

    @classmethod
    def pk_name(cls):
        """Primary key name"""
        return 'id'

    def pk_value(self):
        """Primary key value"""
        return self.id

    def values(self):
        """Values"""
        # TODO(JD): Support lists in Music
        # Lists aren't directly supported in Music, so we have to
        # convert to/from json on the way out/in.
        return {
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'level': self.level,
            'members': simplejson.dumps(self.members),
        }

    def __init__(self, name, description, type, level, members, _insert=True):
        """Initializer"""
        super(Group, self).__init__()
        self.name = name
        self.description = description or ""
        self.type = type
        self.level = level
        if _insert:
            self.members = members
            self.insert()
        else:
            # TODO(UNKNOWN): Support lists in Music
            self.members = simplejson.loads(members)

    def __repr__(self):
        """Object representation"""
        return '<Group {} (type={}, level={})>'.format(
            self.name, self.type, self.level)

    def __json__(self):
        """JSON representation"""
        json_ = {}
        json_['id'] = self.id
        json_['name'] = self.name
        json_['description'] = self.description
        json_['type'] = self.type
        json_['level'] = self.level
        json_['members'] = self.members
        return json_
