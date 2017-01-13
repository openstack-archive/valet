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

"""Plan Model."""

from . import Base, Query


class Plan(Base):
    """Plan model."""

    __tablename__ = 'plans'

    id = None  # pylint: disable=C0103
    name = None
    stack_id = None

    @classmethod
    def schema(cls):
        """Return schema."""
        schema = {
            'id': 'text',
            'name': 'text',
            'stack_id': 'text',
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
        return {
            'name': self.name,
            'stack_id': self.stack_id,
        }

    def __init__(self, name, stack_id, _insert=True):
        """Initializer."""
        super(Plan, self).__init__()
        self.name = name
        self.stack_id = stack_id
        if _insert:
            self.insert()

    def placements(self):
        """Return list of placements."""
        # TODO(UNKNOWN): Make this a property?
        all_results = Query("Placement").all()
        results = []
        for placement in all_results:
            if placement.plan_id == self.id:
                results.append(placement)
        return results

    @property
    def orchestration_ids(self):
        """Return list of orchestration IDs."""
        return list(set([p.orchestration_id for p in self.placements()]))

    def __repr__(self):
        """Object representation."""
        return '<Plan %r>' % self.name

    def __json__(self):
        """JSON representation."""
        json_ = {}
        json_['id'] = self.id
        json_['stack_id'] = self.stack_id
        json_['name'] = self.name
        json_['placements'] = {}
        for placement in self.placements():
            json_['placements'][placement.orchestration_id] = dict(
                name=placement.name,
                location=placement.location)
        return json_
