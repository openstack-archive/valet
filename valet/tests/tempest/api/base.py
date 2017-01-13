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

"""Base."""

from tempest import config
from tempest import test

from valet.tests.tempest.services import client

CONF = config.CONF


class BaseValetTest(test.BaseTestCase):
    """Vase Valet Tempest Test Class."""

    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        """Skp Checks, if CONF service not available, raise exception."""
        super(BaseValetTest, cls).skip_checks()
        if not CONF.service_available.valet:
            skip_msg = ("%s skipped as valet is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        """Setup Valet Clients."""
        super(BaseValetTest, cls).setup_clients()
        cls.valet_client = client.ValetClient(
            cls.os.auth_provider,
            CONF.placement.catalog_type,
            CONF.identity.region,
            **cls.os.default_params_with_timeout_values)

    @classmethod
    def resource_setup(cls):
        """Resource Setup."""
        super(BaseValetTest, cls).resource_setup()
        cls.catalog_type = CONF.placement.catalog_type

    @classmethod
    def resource_cleanup(cls):
        """Resource Cleanup."""
        super(BaseValetTest, cls).resource_cleanup()
