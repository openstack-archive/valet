'''
Created on May 18, 2016

@author: root
'''

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

    def setUp(self):
        ''' Adding configuration and logging mechanism '''
        super(TestNested, self).setUp()
        self.init_template(CONF.test_nested)

    def test_nested(self):
        self.run_test(self.stack_name, self.template_path)

    def get_name(self):
        return __name__
