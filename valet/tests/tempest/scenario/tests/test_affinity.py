'''
Created on May 4, 2016

@author: Yael
'''

from valet.tests.tempest.scenario.general_logger import GeneralLogger
from valet.tests.tempest.scenario.scenario_base import ScenarioTestCase


class TestAffinity(ScenarioTestCase):

    def test_affinity(self):
        logger = GeneralLogger("test_affinity")
        self.run_test(logger, "affinity", "/templates/affinity_basic_2_instances.yml")
