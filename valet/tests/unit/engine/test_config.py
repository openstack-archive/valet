# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
'''
Created on Aug 17, 2016

@author: YB
'''

import sys
from valet.engine.optimizer.ostro_server.configuration import Config
from valet.tests.base import Base

from oslo_config import cfg


class TestConfig(Base):

    def setUp(self):
        super(TestConfig, self).setUp()
        sys.argv = [sys.argv[0]]

#     def test_simple_config(self):
#         cfg.CONF.clear()
#         config = Config()
#         config_status = config.configure()
#
#         self.validate_test(config_status == "success")

    def test_unhappy_config_io(self):
        cfg.CONF.clear()
        try:
            config = Config("unhappy.cfg")
            config_status = config.configure()
            self.validate_test("I/O error" in config_status)

        except Exception as ex:
            self.validate_test(isinstance(ex, cfg.ConfigFilesNotFoundError))

    def test_config_io(self):
        cfg.CONF.clear()
        config = Config("etc/valet/valet.conf")
        config_status = config.configure()

        self.validate_test(config_status == "success")
