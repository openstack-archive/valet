'''
Created on Jun 1, 2016

@author: Yael
'''

from oslo_config import cfg
from oslo_log import log as logging
from valet.tests.functional.valet_validator.common.init import CONF
from valet.tests.functional.valet_validator.tests.functional_base import FunctionalTestCase


opt_test_ex = \
    [
        cfg.StrOpt('STACK_NAME', default="basic_exclusivity_stack"),
        cfg.StrOpt('TEMPLATE_NAME', default="exclusivity_basic_2_instances"),
    ]

CONF.register_opts(opt_test_ex, group="test_exclusivity")
LOG = logging.getLogger(__name__)


class TestExclusivity(FunctionalTestCase):

    def setUp(self):
        ''' Initiating template '''
        super(TestExclusivity, self).setUp()
        self.init_template(CONF.test_exclusivity)

    def test_exclusivity(self):
        self.run_test(self.stack_name, self.template_path)

    def get_name(self):
        return __name__
