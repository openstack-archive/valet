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

"""Test Config."""
import mock
import sys

from valet.engine.optimizer.ostro_server.configuration import Config
from valet.tests.base import Base

from oslo_config import cfg


class TestConfig(Base):
    """Unit tests for Valet.engine.optimizer.ostro_server.configuration."""

    def setUp(self):
        """Setup Test Config Testing Class."""
        super(TestConfig, self).setUp()
        sys.argv = [sys.argv[0]]

    def test_unhappy_config_io(self):
        """Test unhappy.cfg I/O and validate I/O error in config status."""
        cfg.CONF.clear()
        try:
            config = Config("unhappy.cfg")
            config_status = config.configure()
            self.validate_test("I/O error" in config_status)

        except Exception as ex:
            self.validate_test(isinstance(ex, cfg.ConfigFilesNotFoundError))

    @mock.patch.object(Config, '_set_simulation')
    @mock.patch.object(Config, '_init_system')
    def test_configure_failed_init(self, mock_config, mock_sim):
        mock_config.return_value = "failed"
        cfg.CONF.clear()
        config = Config("setup.cfg")

        result = config.configure()
        self.assertEqual("failed", result)
        mock_sim.assert_not_called()

    @mock.patch.object(Config, '_set_simulation')
    @mock.patch.object(Config, '_init_system')
    def test_configure_live_mode(self, mock_config, mock_sim):
        mock_config.return_value = "success"
        cfg.CONF.clear()
        config = Config("setup.cfg")
        config.mode = "live"
        config.sim_cfg_loc = "test"

        result = config.configure()
        self.assertEqual("success", result)
        mock_sim.assert_not_called()

    @mock.patch.object(Config, '_set_simulation')
    @mock.patch.object(Config, '_init_system')
    def test_configure_success(self, mock_config, mock_sim):
        mock_config.return_value = "success"
        mock_sim.return_value = "failed"
        cfg.CONF.clear()
        config = Config("setup.cfg")
        config.mode = "test"
        config.sim_cfg_loc = "test"

        result = config.configure()
        self.assertEqual("failed", result)
        mock_sim.assert_called_once_with()
