#
# Copyright (c) 2014-2017 AT&T Intellectual Property
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

"""GroupAssignment Heat Resource Plugin"""

import uuid

from heat.common.i18n import _
from heat.engine import properties
from heat.engine import resource
from heat.engine.resources import scheduler_hints as sh
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class GroupAssignment(resource.Resource, sh.SchedulerHintsMixin):
    """Valet Group Assignment Resource

    A Group Assignment describes one or more resources (e.g., Server)
    assigned to a particular group.

    Caution: It is possible to declare multiple GroupAssignment resources
    referring to the same servers, which can lead to problems when one
    GroupAssignment is updated and a duplicate server reference is removed.

    This resource is purely informational in nature and makes no changes
    to heat, nova, or cinder. Instead, the Valet Heat stack lifecycle plugin
    intercepts Heat's create/update/delete operations and invokes valet-api
    as needed.
    """

    PROPERTIES = (
        GROUP, RESOURCES,
    ) = (
        'group', 'resources',
    )

    properties_schema = {
        GROUP: properties.Schema(
            properties.Schema.STRING,
            _('Group reference.'),
            update_allowed=False
        ),
        RESOURCES: properties.Schema(
            properties.Schema.LIST,
            _('List of one or more resource IDs.'),
            required=True,
            update_allowed=True
        ),
    }

    def handle_create(self):
        """Create resource"""
        resource_id = str(uuid.uuid4())
        self.resource_id_set(resource_id)

    def handle_update(self, json_snippet, templ_diff, prop_diff):
        """Update resource"""
        self.resource_id_set(self.resource_id)

    def handle_delete(self):
        """Delete resource"""
        self.resource_id_set(None)


# TODO(jdandrea): This resource is being pre-empted (not deprecated)
# and is unavailable in Valet 1.0.
#
# To assign a server to a Valet Group, specify metadata within that
# server's OS::Nova::Server resource properties like so. Declare
# groups in a separate template/stack using OS::Valet::Group.
#
# properties:
#   metadata:
#     valet:
#       groups: [group1, group2, ..., groupN]
#
# def resource_mapping():
#     """Map names to resources."""
#     return {
#         'OS::Valet::GroupAssignment': GroupAssignment,
#     }
