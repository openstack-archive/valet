'''
Created on May 4, 2016

@author: Yael
'''

from valet.tests.tempest.scenario.general_logger import GeneralLogger
from valet.tests.tempest.scenario.scenario_base import ScenarioTestCase


class TestDiversity(ScenarioTestCase):

    def test_diversity(self):
        logger = GeneralLogger("test_diversity")
        self.run_test(logger, "diversity", "/templates/diversity_basic_2_instances.yml")
