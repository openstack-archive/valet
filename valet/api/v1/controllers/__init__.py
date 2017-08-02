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

"""Controllers Package"""

from os import path
import string
import uuid

from notario.exceptions import Invalid
from notario.utils import forced_leaf_validator
from pecan import redirect, request

from valet import api
from valet.api.common.i18n import _
from valet.api.db.models import Placement

# Supported valet-engine query types
QUERY_TYPES = (
    'group_vms',
    'invalid_placements'
)

#
# Notario Helpers
#


def valid_group_name(value):
    """Validator for group name type."""
    valid_chars = set(string.letters + string.digits + "-._~")
    if not value or not set(value) <= valid_chars:
        api.LOG.error("group name is not valid")
        api.LOG.error("group name must contain only uppercase and lowercase "
                      "letters, decimal digits, hyphens, periods, "
                      "underscores, and tildes [RFC 3986, Section 2.3]")


# There is a bug in Notario that prevents basic checks for a list/dict
# (without recursion/depth). Instead, we borrow a hack used in the Ceph
# installer, which it turns out also isn't quite correct. Some of the
# code has been removed. Source: https://github.com/ceph/ceph-installer ...
# /blob/master/ceph_installer/schemas.py#L15-L31 (devices_object())
@forced_leaf_validator
def list_or_dict(value, *args):
    """Validator - Value must be of type list or dict"""
    error_msg = 'not of type list or dict'
    if isinstance(value, dict):
        return
    try:
        assert isinstance(value, list)
    except AssertionError:
        if args:
            # What does 'dict type' and 'value' mean in this context?
            raise Invalid(
                'dict type', pair='value', msg=None, reason=error_msg, *args)
        raise


def valid_plan_update_action(value):
    """Validator for plan update action."""
    assert value in ['update', 'migrate'], _("must be update or migrate")

#
# Placement Helpers
#


def set_placements(plan, resources, placements):
    """Set placements"""
    for uuid_key in placements.iterkeys():
        name = resources[uuid_key]['name']
        properties = placements[uuid_key]['properties']
        location = properties['host']
        metadata = resources[uuid_key].get('metadata', {})
        Placement(name, uuid_key, plan=plan,
                  location=location, metadata=metadata)
    return plan


def reserve_placement(placement, resource_id=None, reserve=True, update=True):
    """ Reserve placement. Can optionally set the physical resource id.

    Set reserve=False to unreserve. Set update=False to not update
    the data store (if the update will be made later).
    """
    if placement:
        msg = _('%(rsrv)s placement of %(orch_id)s in %(loc)s.')
        args = {
            'rsrv': _("Reserving") if reserve else _("Unreserving"),
            'orch_id': placement.orchestration_id,
            'loc': placement.location,
        }
        api.LOG.info(msg, args)
        placement.reserved = reserve
        if resource_id:
            msg = _('Associating resource id %(res_id)s with '
                    'orchestration id %(orch_id)s.')
            args = {
                'res_id': resource_id,
                'orch_id': placement.orchestration_id,
            }
            api.LOG.info(msg, args)
            placement.resource_id = resource_id
        if update:
            placement.update()


def engine_query_args(query_type=None, parameters={}):
    """Make a general query of valet-engine."""
    if query_type not in QUERY_TYPES:
        return {}
    transaction_id = str(uuid.uuid4())
    args = {
        "stack_id": transaction_id,
    }
    if query_type:
        args['type'] = query_type
    args['parameters'] = parameters
    ostro_kwargs = {
        "args": args,
    }
    return ostro_kwargs


def update_placements(placements, plan=None, resources=None,
                      reserve_id=None, unlock_all=False):
    """Update placements. Optionally reserve one placement."""
    new_placements = {}
    for uuid_key in placements.iterkeys():
        placement = Placement.query.filter_by(
            orchestration_id=uuid_key).first()
        if placement:
            # Don't use plan or resources for upates (metadata stays as-is).
            properties = placements[uuid_key]['properties']
            location = properties['host']
            if placement.location != location:
                msg = _('Changing placement of %(orch_id)s from '
                        '%(old_loc)s to %(new_loc)s.')
                args = {
                    'orch_id': placement.orchestration_id,
                    'old_loc': placement.location,
                    'new_loc': location,
                }
                api.LOG.info(msg, args)
                placement.location = location
            if unlock_all:
                reserve_placement(placement, reserve=False, update=False)
            elif reserve_id and placement.orchestration_id == reserve_id:
                reserve_placement(placement, reserve=True, update=False)
            placement.update()
        else:
            new_placements[uuid_key] = placements[uuid_key]

    if new_placements and plan and resources:
        set_placements(plan, resources, new_placements)
    return


#
# Error Helpers
#

def error(url, msg=None, **kwargs):
    """Error handler"""
    if msg:
        request.context['error_message'] = msg
    if kwargs:
        request.context['kwargs'] = kwargs
    url = path.join(url, '?error_message=%s' % msg)
    redirect(url, internal=True)
