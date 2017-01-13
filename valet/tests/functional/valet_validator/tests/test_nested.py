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

"""Test Nested."""

from oslo_config import cfg
from oslo_log import log as logging
from valet.tests.functional.valet_validator.common.init import CONF
from valet.tests.functional.valet_validator.tests.functional_base import FunctionalTestCase


opt_test_aff = \
    [
        cfg.StrOpt('STACK_NAME', default="nest_stack"),
        cfg.StrOpt('TEMPLATE_NAME', default="diversity_between_2_affinity"),
    ]

CONF.register_opts(opt_test_aff, group="test_nested")
LOG = logging.getLogger(__name__)


class TestNested(FunctionalTestCase):
    """Basic setup and functions for nested tests."""

    def setUp(self):
        """Adding configuration and logging mechanism."""
        super(TestNested, self).setUp()
        self.init_template(CONF.test_nested)

    def test_nested(self):
        """Call run_test on stack and give it the path to the template."""
        self.run_test(self.stack_name, self.template_path)

    def get_name(self):
        """Return name."""
        return __name__
