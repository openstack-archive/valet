'''
Created on May 4, 2016

@author: Yael
'''

from oslo_config import cfg
from oslo_log import log as logging
from valet.tests.functional.valet_validator.common.init import CONF
from valet.tests.functional.valet_validator.tests.functional_base import FunctionalTestCase


opt_test_div = \
    [
        cfg.StrOpt('STACK_NAME', default="basic_diversity_stack"),
        cfg.StrOpt('TEMPLATE_NAME', default="diversity_basic_2_instances"),
    ]

CONF.register_opts(opt_test_div, group="test_diversity")
LOG = logging.getLogger(__name__)


class TestDiversity(FunctionalTestCase):

    def setUp(self):
        ''' Initiating template '''
        super(TestDiversity, self).setUp()
        self.init_template(CONF.test_diversity)

    def test_diversity(self):

        self.run_test(self.stack_name, self.template_path)

    def get_name(self):
        return __name__
