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

"""Test Exclusivity."""

from valet.tests.tempest.scenario.general_logger import GeneralLogger
from valet.tests.tempest.scenario.scenario_base import ScenarioTestCase


class TestExclusivity(ScenarioTestCase):
    """Test Exclusivity Scenario."""

    def test_exclusivity(self):
        """Test Exclusivity."""
        logger = GeneralLogger("test_exclusivity")
        self.run_test(logger, "exclusivity",
                      "/templates/exclusivity_basic_2_instances.yml")
