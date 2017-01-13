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

"""Functional Base."""

import os
from oslo_log import log as logging
import time
from valet.tests.base import Base
from valet.tests.functional.valet_validator.common.init import COLORS, CONF
from valet.tests.functional.valet_validator.common.resources import TemplateResources
from valet.tests.functional.valet_validator.compute.analyzer import Analyzer
from valet.tests.functional.valet_validator.orchestration.loader import Loader


LOG = logging.getLogger(__name__)


class FunctionalTestCase(Base):
    """Test case base class for all unit tests."""

    def __init__(self, *args, **kwds):
        """Init.

        Initializing the FunctionalTestCase - loading the
        logger, loader and analyzer.
        """
        super(FunctionalTestCase, self).__init__(*args, **kwds)

    def setUp(self):
        """Start loader and analyzer."""
        super(FunctionalTestCase, self).setUp()

        self.load = Loader()
        self.compute = Analyzer()

        LOG.info("%s %s is starting... %s" % (COLORS["L_BLUE"],
                                              self.get_name(),
                                              COLORS["WHITE"]))

    def run_test(self, stack_name, template_path):
        """Run Test.

        scenario -
                deletes all stacks
                create new stack
                checks if host (or rack) is the same for all instances
        """
        # delete all stacks
        self.load.delete_all_stacks()

        # creates new stack
        my_resources = TemplateResources(template_path)

        res = self.load.create_stack(stack_name, my_resources)
        if "Ostro error" in res.message:
            res = self.try_again(res, stack_name, my_resources)

        self.validate(res)
        LOG.info("%s stack creation is done successfully %s"
                 % (COLORS["L_PURPLE"], COLORS["WHITE"]))
        time.sleep(self.CONF.valet.DELAY_DURATION)

        # validation
        self.validate(self.compute.check(my_resources))
        LOG.info("%s validation is done successfully %s"
                 % (COLORS["L_PURPLE"], COLORS["WHITE"]))

    def try_again(self, res, stack_name, my_resources):
        """Try creating stack again."""
        tries = CONF.valet.TRIES_TO_CREATE
        while "Ostro error" in res.message and tries > 0:
            LOG.error("Ostro error - try number %d"
                      % (CONF.valet.TRIES_TO_CREATE - tries + 2))
            self.load.delete_all_stacks()
            res = self.load.create_stack(stack_name, my_resources)
            tries -= 1
            time.sleep(self.CONF.valet.PAUSE)

        return res

    def get_template_path(self, template_name):
        """Return template path for the template name given."""
        possible_topdir = os.path.normpath(os.path.join(
            os.path.abspath(__file__), os.pardir, os.pardir))
        return os.path.join(possible_topdir, 'tests/templates',
                            template_name + '.yml')

    def init_template(self, test):
        """Init template, call get path for test template."""
        self.stack_name = test.STACK_NAME
        self.template_path = self.get_template_path(test.TEMPLATE_NAME)
