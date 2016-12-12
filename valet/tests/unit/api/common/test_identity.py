'''
Created on Sep 29, 2016

@author: stack
'''

import mock
from valet.api.common.identity import Identity
from valet.tests.unit.api.v1.api_base import ApiBase


class TestIdentity(ApiBase):

    def setUp(self):
        super(TestIdentity, self).setUp()

        kwargs = {'username': 'admin', 'tenant_name': 'demo', 'password': 'qwer4321', 'auth_url': 'http://controller:5000/v2.0'}

        self.identity = Identity(**kwargs)

    def test_is_token_admin(self):
        self.validate_test(self.identity.is_token_admin(TokenT))
        self.validate_test(not self.identity.is_token_admin(TokenF))

    def test_tenant_from_token(self):
        self.validate_test(self.identity.tenant_from_token(TokenT) == "cb9c9997fc6e41cc87186de92aa0a099")

    def test_user_from_token(self):
        self.validate_test(self.identity.user_from_token(TokenT) == "cb9c9997fc6e41cc87186de92aa0a099")

    def test_client(self):
        with mock.patch('valet.api.common.identity.client'):
            self.identity.client()

    def test_validate_token(self):
        self.validate_test(self.identity.validate_token("auth_token") is None)

        with mock.patch('valet.api.common.identity.client'):
            self.validate_test(self.identity.validate_token("auth_token") is not None)

    def test_is_tenant_list_validself(self):
        with mock.patch('valet.api.common.identity.client'):
            self.validate_test(self.identity.is_tenant_list_valid(["a", "b"]) is False)


class TokenT(object):
    user = {'roles': [{'name': 'user'}, {'name': 'heat_stack_owner'}, {'name': 'admin'}], 'id': 'cb9c9997fc6e41cc87186de92aa0a099'}
    tenant = {'description': 'Demo Project', 'enabled': True, 'id': 'cb9c9997fc6e41cc87186de92aa0a099'}


class TokenF(object):
    user = {'roles': []}
    tenant = {'description': 'Demo Project', 'enabled': True, 'id': 'cb9c9997fc6e41cc87186de92aa0a099'}
