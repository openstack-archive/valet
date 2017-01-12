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

'''GroupAssignment Heat Resource Plugin'''

from heat.common.i18n import _
from heat.engine import constraints
from heat.engine import properties
from heat.engine import resource

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class GroupAssignment(resource.Resource):
    ''' A Group Assignment describes one or more resources assigned to a particular type of group.

    Assignments can reference other assignments, so long as there are no circular references.
    There are three types of groups: affinity, diversity, and exclusivity.
    Exclusivity groups have a unique name, assigned through Valet.

    This resource is purely informational in nature and makes no changes to heat, nova, or cinder.
    The Valet Heat Lifecycle Plugin passes this information to the optimizer.
    '''

    _RELATIONSHIP_TYPES = (
        AFFINITY, DIVERSITY, EXCLUSIVITY,
    ) = (
        "affinity", "diversity", "exclusivity",
    )

    PROPERTIES = (
        GROUP_NAME, GROUP_TYPE, LEVEL, RESOURCES,
    ) = (
        'group_name', 'group_type', 'level', 'resources',
    )

    properties_schema = {
        GROUP_NAME: properties.Schema(
            properties.Schema.STRING,
            _('Group name. Required for exclusivity groups.'),
            # TODO(JD): Add a custom constraint
            # Constraint must ensure a valid and allowed name
            # when an exclusivity group is in use.
            # This is presently enforced by valet-api and can also
            # be pro-actively enforced here, so as to avoid unnecessary
            # orchestration.
            update_allowed=True
        ),
        GROUP_TYPE: properties.Schema(
            properties.Schema.STRING,
            _('Type of group.'),
            constraints=[
                constraints.AllowedValues([AFFINITY, DIVERSITY, EXCLUSIVITY])
            ],
            required=True,
            update_allowed=True
        ),
        LEVEL: properties.Schema(
            properties.Schema.STRING,
            _('Level of relationship between resources.'),
            constraints=[
                constraints.AllowedValues(['host', 'rack']),
            ],
            required=True,
            update_allowed=True
        ),
        RESOURCES: properties.Schema(
            properties.Schema.LIST,
            _('List of one or more resource IDs.'),
            required=True,
            update_allowed=True
        ),
    }

    def handle_create(self):
        '''Create resource'''
        self.resource_id_set(self.physical_resource_name())

    def handle_update(self, json_snippet, templ_diff, prop_diff):  # pylint: disable=W0613
        '''Update resource'''
        self.resource_id_set(self.physical_resource_name())

    def handle_delete(self):
        '''Delete resource'''
        self.resource_id_set(None)


def resource_mapping():
    '''Map names to resources.'''
    return {'ATT::Valet::GroupAssignment': GroupAssignment, }
