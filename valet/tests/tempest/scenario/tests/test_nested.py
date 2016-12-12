'''
Created on May 4, 2016

@author: Yael
'''

from valet.tests.tempest.scenario.general_logger import GeneralLogger
from valet.tests.tempest.scenario.scenario_base import ScenarioTestCase


class TestNested(ScenarioTestCase):

    def test_nested(self):
        logger = GeneralLogger("test_nested")
        self.run_test(logger, "affinity_diversity", "/templates/diversity_between_2_affinity.yml")
