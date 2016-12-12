'''
Created on May 4, 2016

@author: Yael
'''

from oslo_config import cfg
from oslo_log import log as logging
from valet.tests.functional.valet_validator.common.init import CONF
from valet.tests.functional.valet_validator.tests.functional_base import FunctionalTestCase


opt_test_aff = \
    [
        cfg.StrOpt('STACK_NAME', default="basic_affinity_stack"),
        cfg.StrOpt('TEMPLATE_NAME', default="affinity_basic_2_instances"),
    ]

CONF.register_opts(opt_test_aff, group="test_affinity")
LOG = logging.getLogger(__name__)


class TestAffinity(FunctionalTestCase):

    def setUp(self):
        ''' Adding configuration and logging mechanism '''
        super(TestAffinity, self).setUp()
        self.init_template(CONF.test_affinity)

    def test_affinity(self):
        self.run_test(self.stack_name, self.template_path)

    def get_name(self):
        return __name__
