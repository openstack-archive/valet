'''
Created on May 4, 2016

@author: Yael
'''

from valet.tests.tempest.scenario.general_logger import GeneralLogger
from valet.tests.tempest.scenario.scenario_base import ScenarioTestCase


class TestExclusivity(ScenarioTestCase):

    def test_exclusivity(self):
        logger = GeneralLogger("test_exclusivity")
        self.run_test(logger, "exclusivity", "/templates/exclusivity_basic_2_instances.yml")
