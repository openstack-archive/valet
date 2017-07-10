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

""" Test Daemon """
import mock
import os
import sys
import time

from valet.engine.optimizer.ostro_server.daemon import Daemon
from valet.tests.base import Base


class TestDaemon(Base):

    def setUp(self):
        """Setup Test Daemon Testing Class."""
        super(TestDaemon, self).setUp()

        self.priority = 0
        self.pidfile = \
            "valet/tests/unit/engine/optimizer/ostro_server/test_pid.txt"
        self.daemon = Daemon(self.priority, self.pidfile)

    # TODO(jakecarlson1): test_daemonize

    def test_getpid(self):

        result = self.daemon.getpid()
        self.assertEqual(99999, result)

    def test_checkpid_none_pid(self):

        result = self.daemon.checkpid(None)
        self.assertFalse(result)

    @mock.patch.object(os, 'kill')
    def test_checkpid_has_pid(self, mock_kill):

        result = self.daemon.checkpid(99998)
        self.assertTrue(result)

    @mock.patch.object(Daemon, 'delpid')
    @mock.patch.object(os, 'kill')
    def test_checkpid_excpetion(self, mock_kill, mock_del):
        mock_kill.side_effect = OSError

        result = self.daemon.checkpid(99998)
        self.assertFalse(result)
        mock_del.assert_called_once_with()

    @mock.patch.object(Daemon, 'run')
    @mock.patch.object(Daemon, 'daemonize')
    @mock.patch.object(sys, 'exit')
    @mock.patch.object(Daemon, 'getpid')
    def test_start_has_pid(self, mock_get_pid, mock_exit, mock_daemonize,
                           mock_run):
        mock_get_pid.return_value = 5

        self.daemon.start()
        mock_get_pid.assert_called_once_with()
        mock_exit.assert_called_once_with(1)
        mock_daemonize.assert_called_once_with()
        mock_run.assert_called_once_with()

    @mock.patch.object(Daemon, 'run')
    @mock.patch.object(Daemon, 'daemonize')
    @mock.patch.object(sys, 'exit')
    @mock.patch.object(Daemon, 'getpid')
    def test_start_none_pid(self, mock_get_pid, mock_exit, mock_daemonize,
                            mock_run):
        mock_get_pid.return_value = None

        self.daemon.start()
        mock_get_pid.assert_called_once_with()
        mock_exit.assert_not_called()
        mock_daemonize.assert_called_once_with()
        mock_run.assert_called_once_with()

    @mock.patch.object(sys, 'exit')
    @mock.patch.object(time, 'sleep')
    @mock.patch.object(os, 'kill')
    @mock.patch.object(Daemon, 'getpid')
    def test_stop_none_pid(self, mock_get_pid, mock_kill, mock_sleep,
                           mock_exit):
        mock_get_pid.return_value = None

        result = self.daemon.stop()
        self.assertIsNone(result)
        mock_get_pid.assert_called_once_with()
        mock_kill.assert_not_called()
        mock_sleep.assert_not_called()

    @mock.patch.object(sys, 'exit')
    @mock.patch.object(time, 'sleep')
    @mock.patch.object(os, 'kill')
    @mock.patch.object(Daemon, 'getpid')
    def test_stop_has_pid(self, mock_get_pid, mock_kill, mock_sleep,
                          mock_exit):
        mock_get_pid.return_value = 5
        mock_kill.side_effect = OSError

        result = self.daemon.stop()
        self.assertIsNone(result)
        mock_get_pid.assert_called_once_with()
        mock_sleep.assert_not_called()
        mock_exit.assert_called_once_with(1)

    @mock.patch.object(Daemon, 'checkpid')
    @mock.patch.object(Daemon, 'getpid')
    def test_status_none_pid(self, mock_get_pid, mock_checkpid):
        mock_get_pid.return_value = None
        mock_checkpid.return_value = False
        self.daemon.priority = 1

        result = self.daemon.status()
        self.assertEqual(0, result)
        mock_get_pid.assert_called_once_with()
        mock_checkpid.assert_called_once_with(None)

    @mock.patch.object(Daemon, 'checkpid')
    @mock.patch.object(Daemon, 'getpid')
    def test_status_has_pid(self, mock_get_pid, mock_checkpid):
        mock_get_pid.return_value = 5
        mock_checkpid.return_value = True
        self.daemon.priority = 1

        result = self.daemon.status()
        self.assertEqual(1, result)
        mock_get_pid.assert_called_once_with()
        mock_checkpid.assert_called_once_with(5)
