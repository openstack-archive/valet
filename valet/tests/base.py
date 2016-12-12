'''
Created on May 5, 2016

@author: Yael
'''

from oslo_config import fixture as fixture_config
from oslo_log import log as logging
from oslotest.base import BaseTestCase
from valet.tests.functional.valet_validator.common import init


LOG = logging.getLogger(__name__)


class Base(BaseTestCase):
    """Test case base class for all unit tests."""

    def __init__(self, *args, **kwds):
        '''  '''
        super(Base, self).__init__(*args, **kwds)

        self.CONF = self.useFixture(fixture_config.Config()).conf
        init.prepare(self.CONF)

    def setUp(self):
        super(Base, self).setUp()

    def run_test(self, stack_name, template_path):
        ''' main function '''
        pass

    def validate(self, result):
        self.assertEqual(True, result.ok, result.message)

    def validate_test(self, result):
        self.assertTrue(result)

    def get_name(self):
        pass
