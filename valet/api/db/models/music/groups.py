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

"""Group Model."""

from . import Base
import simplejson


class Group(Base):
    """Group model."""

    __tablename__ = 'groups'

    id = None  # pylint: disable=C0103
    name = None
    description = None
    type = None  # pylint: disable=W0622
    members = None

    @classmethod
    def schema(cls):
        """Return schema."""
        schema = {
            'id': 'text',
            'name': 'text',
            'description': 'text',
            'type': 'text',
            'members': 'text',
            'PRIMARY KEY': '(id)',
        }
        return schema

    @classmethod
    def pk_name(cls):
        """Primary key name."""
        return 'id'

    def pk_value(self):
        """Primary key value."""
        return self.id

    def values(self):
        """Values."""
        # TODO(UNKNOWN): Support lists in Music
        # Lists aren't directly supported in Music, so we have to
        # convert to/from json on the way out/in.
        return {
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'members': simplejson.dumps(self.members),
        }

    def __init__(self, name, description, type, members, _insert=True):
        """Initializer."""
        super(Group, self).__init__()
        self.name = name
        self.description = description or ""
        self.type = type
        if _insert:
            self.members = []  # members ignored at init time
            self.insert()
        else:
            # TODO(UNKNOWN): Support lists in Music
            self.members = simplejson.loads(members)

    def __repr__(self):
        """Object representation."""
        return '<Group %r>' % self.name

    def __json__(self):
        """JSON representation."""
        json_ = {}
        json_['id'] = self.id
        json_['name'] = self.name
        json_['description'] = self.description
        json_['type'] = self.type
        json_['members'] = self.members
        return json_
