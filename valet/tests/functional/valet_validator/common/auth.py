# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
'''
Created on May 4, 2016

@author: Yael
'''

from keystoneclient.auth.identity import v2 as identity
from keystoneclient import session
from oslo_log import log as logging
from valet.tests.functional.valet_validator.common.init import CONF

LOG = logging.getLogger(__name__)

MIN_TOKEN_LIFE_SECONDS = 120


class Auth(object):
    ''' Singleton class for authentication token '''
    auth = None
    session = None

    @staticmethod
    def _init():
        if Auth.is_auth_invalid():
                Auth.auth = identity.Password(auth_url=CONF.auth.OS_AUTH_URL_WITH_VERSION,
                                              username=CONF.auth.OS_USERNAME,
                                              password=CONF.auth.OS_PASSWORD,
                                              tenant_name=CONF.auth.OS_TENANT_NAME)
                Auth.session = session.Session(auth=Auth.auth)

    @staticmethod
    def get_password_plugin():
        Auth._init()
        return Auth.auth

    @staticmethod
    def get_auth_token():
        return Auth.get_password_plugin().get_token(Auth.get_auth_session())

    @staticmethod
    def get_auth_session():
        Auth._init()
        return Auth.session

    @staticmethod
    def get_project_id():
        return Auth.get_password_plugin().get_project_id(Auth.get_auth_session())

    @staticmethod
    def is_auth_invalid():
        return Auth.auth is None or Auth.auth.get_auth_ref(Auth.session).will_expire_soon(CONF.auth.TOKEN_EXPIRATION)
