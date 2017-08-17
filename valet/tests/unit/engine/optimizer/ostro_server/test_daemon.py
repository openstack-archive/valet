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

import atexit
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
        self.logger = mock.Mock()
        self.daemon = Daemon(self.priority, self.pidfile, self.logger)

    @mock.patch.object(atexit, 'register')
    @mock.patch('sys.stderr')
    @mock.patch('sys.stdout')
    @mock.patch.object(os, 'dup2')
    @mock.patch('sys.stdin')
    @mock.patch.object(os, 'umask')
    @mock.patch.object(os, 'setsid')
    @mock.patch.object(os, 'chdir')
    @mock.patch.object(sys, 'exit')
    @mock.patch.object(os, 'fork')
    def test_daemonize_parents_exit(self, mock_fork, mock_exit, mock_chdir,
                                    mock_setsid, mock_umask, mock_stdin,
                                    mock_dup2, mock_stdout, mock_stderr,
                                    mock_atexit):
        mock_fork.return_value = 1
        mock_stdin.fileno = mock.Mock()
        mock_stdin.fileno.return_value = 1
        mock_stdout.fileno = mock.Mock()
        mock_stdout.fileno.return_value = 2
        mock_stderr.fileno = mock.Mock()
        mock_stderr.fileno.return_value = 3
        fork_calls = [mock.call(), mock.call()]
        exit_calls = [mock.call(0), mock.call(0)]

        self.daemon.daemonize()
        mock_fork.assert_has_calls(fork_calls)
        mock_exit.assert_has_calls(exit_calls)
        mock_chdir.assert_called_once_with("/")
        mock_setsid.assert_called_once_with()
        mock_umask.assert_called_once_with(0)
        self.assertEqual(3, mock_dup2.call_count)
        mock_atexit.assert_called_once_with(self.daemon.delpid)

    @mock.patch.object(atexit, 'register')
    @mock.patch('sys.stderr')
    @mock.patch('sys.stdout')
    @mock.patch.object(os, 'dup2')
    @mock.patch('sys.stdin')
    @mock.patch.object(os, 'umask')
    @mock.patch.object(os, 'setsid')
    @mock.patch.object(os, 'chdir')
    @mock.patch.object(sys, 'exit')
    @mock.patch.object(os, 'fork')
    def test_daemonize_parents_except(self, mock_fork, mock_exit, mock_chdir,
                                      mock_setsid, mock_umask, mock_stdin,
                                      mock_dup2, mock_stdout, mock_stderr,
                                      mock_atexit):
        mock_fork.return_value = 1
        mock_fork.side_effect = OSError(1, "Fork 1 failed")
        mock_stdin.fileno = mock.Mock()
        mock_stdin.fileno.return_value = 1
        mock_stdout.fileno = mock.Mock()
        mock_stdout.fileno.return_value = 2
        mock_stderr.fileno = mock.Mock()
        mock_stderr.fileno.return_value = 3
        fork_calls = [mock.call(), mock.call()]
        exit_calls = [mock.call(1), mock.call(1)]

        self.daemon.daemonize()
        mock_fork.assert_has_calls(fork_calls)
        mock_exit.assert_has_calls(exit_calls)
        mock_chdir.assert_called_once_with("/")
        mock_setsid.assert_called_once_with()
        mock_umask.assert_called_once_with(0)
        self.assertEqual(3, mock_dup2.call_count)
        mock_atexit.assert_called_once_with(self.daemon.delpid)

    def test_getpid_success(self):
        self.daemon.pidfile = "valet/tests/unit/engine/optimizer/ostro_server/test_pid.txt"

        result = self.daemon.getpid()
        self.assertEqual(99999, result)

    def test_getpid_fail(self):
        self.daemon.pidfile = "valet/tests/unit/engine/optimizer/ostro_server/test_none_pid.txt"
        # mock_file.side_effect = IOError

        result = self.daemon.getpid()
        self.assertEqual(None, result)

    def test_checkpid_none_pid(self):

        result = self.daemon.checkpid(None)
        self.assertFalse(result)

    @mock.patch.object(os, 'kill')
    def test_checkpid_has_pid(self, mock_kill):

        result = self.daemon.checkpid(99998)
        self.assertTrue(result)
        mock_kill.assert_called_once_with(99998, 0)

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

    @mock.patch.object(sys, 'exit')
    @mock.patch.object(os.path, 'exists')
    @mock.patch.object(time, 'sleep')
    @mock.patch.object(os, 'kill')
    @mock.patch.object(Daemon, 'getpid')
    def test_stop_has_pid_no_such_process(self, mock_get_pid, mock_kill,
                                          mock_sleep, mock_path, mock_exit):
        mock_get_pid.return_value = 5
        mock_kill.side_effect = OSError("No such process")
        mock_path.return_value = False

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
