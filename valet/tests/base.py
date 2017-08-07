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

import mock

from oslo_config import fixture as fixture_config
from oslotest import base

from valet import api
from valet.tests.functional.valet_validator.common import init


class Base(base.BaseTestCase):
    """Test case base class for all unit tests."""

    def __init__(self, *args, **kwds):
        """Init Base."""
        super(Base, self).__init__(*args, **kwds)

        self.CONF = self.useFixture(fixture_config.Config()).conf
        init.prepare(self.CONF)
        api.LOG = mock.MagicMock()

    def setUp(self):
        """Setup."""
        super(Base, self).setUp()

    def run_test(self, stack_name, template_path):
        """Main Function."""
        pass

    def validate(self, result):
        """Validate."""
        # TODO(CM): Maybe fix unnecessary obfuscation of assertEqual code.
        self.assertEqual(True, result.ok, result.message)

    def validate_test(self, result):
        """Validate Test."""
        # TODO(CM): Maybe fix unnecessary obfuscation of assertTrue code.
        self.assertTrue(result)

    def get_name(self):
        """Get Name."""
        # TODO(CM): Make this function actually do something.
        pass
