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

from oslo_config import cfg
from oslo_log import log as logging
from valet.tests.functional.valet_validator.common.init import CONF
from valet.tests.functional.valet_validator.tests.functional_base import FunctionalTestCase


opt_test_aff = [
    cfg.StrOpt('STACK_NAME', default="affinity_3_stack"),
    cfg.StrOpt('TEMPLATE_NAME', default="affinity_ 3_Instances"),
    ]

CONF.register_opts(opt_test_aff, group="test_affinity_3")
LOG = logging.getLogger(__name__)


class TestAffinity_3(FunctionalTestCase):

    def setUp(self):
        ''' Adding configuration and logging mechanism '''
        super(TestAffinity_3, self).setUp()
        self.init_template(CONF.test_affinity_3)

    def test_affinity(self):
        self.run_test(self.stack_name, self.template_path)

    def get_name(self):
        return __name__
