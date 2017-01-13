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

"""Identity helper library."""

from datetime import datetime

import iso8601

from keystoneauth1.identity import v2
from keystoneauth1 import session
from keystoneclient.v2_0 import client
import logging
from pecan import conf
import pytz

LOG = logging.getLogger(__name__)


def utcnow():
    """Return the time (UTC)."""
    return datetime.now(tz=pytz.utc)


class Identity(object):
    """Convenience library for all identity service-related queries."""

    _args = None
    _client = None
    _interface = None
    _session = None

    @classmethod
    def is_token_admin(cls, token):
        """Return true if decoded token has an admin role."""
        for role in token.user.get('roles', []):
            if role.get('name') == 'admin':
                return True
        return False

    @classmethod
    def tenant_from_token(cls, token):
        """Return tenant id from decoded token."""
        return token.tenant.get('id', None)

    @classmethod
    def user_from_token(cls, token):
        """Return user id from decoded token."""
        return token.user.get('id', None)

    def __init__(self, interface='admin', **kwargs):
        """Initializer."""
        self._interface = interface
        self._args = kwargs
        self._client = None
        self._session = None

    @property
    def _client_expired(self):
        """Return True if cached client's token is expired."""
        # NOTE: Keystone may auto-regen the client now (v2? v3?)
        # If so, this trip may no longer be necessary. Doesn't
        # hurt to keep it around for the time being.
        if not self._client or not self._client.auth_ref:
            return True
        token = self._client.auth_ref.get('token')
        if not token:
            return True
        timestamp = token.get('expires')
        if not timestamp:
            return True
        return iso8601.parse_date(timestamp) <= utcnow()

    @property
    def client(self):
        """Return an identity client."""
        if not self._client or self._client_expired:
            auth = v2.Password(**self._args)
            self._session = session.Session(auth=auth)
            self._client = client.Client(session=self._session,
                                         interface=self._interface)
        return self._client

    @property
    def session(self):
        """Read-only access to the session."""
        return self._session

    def validate_token(self, auth_token):
        """Return validated token or None if invalid."""
        kwargs = {
            'token': auth_token,
        }
        try:
            return self.client.tokens.validate(**kwargs)
        except Exception as ex:
            LOG.error("Identity.validate_token: " + ex.message)

        return None

    def is_tenant_list_valid(self, tenant_list):
        """Return true if tenant list contains valid tenant IDs."""
        tenants = self.client.tenants.list()
        if isinstance(tenant_list, list):
            found = False
            for tenant_id in tenant_list:
                found = is_tenant_in_tenants(tenant_id, tenants)
                if found:
                    break
            return found
        return False


def is_tenant_in_tenants(tenant_id, tenants):
    """Return true if tenant exists."""
    for tenant in tenants:
        if tenant_id == tenant.id:
            return True
    return False


def _identity_engine_from_config(config):
    """Initialize the identity engine based on supplied config."""
    # Using tenant_name instead of project name due to keystone v2
    kwargs = {
        'username': config.get('username'),
        'password': config.get('password'),
        'tenant_name': config.get('project_name'),
        'auth_url': config.get('auth_url'),
    }
    interface = config.get('interface')
    engine = Identity(interface, **kwargs)
    return engine


def init_identity():
    """Initialize the identity engine and place in the config."""
    config = conf.identity.config
    engine = _identity_engine_from_config(config)
    conf.identity.engine = engine
