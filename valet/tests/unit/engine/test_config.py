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
