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
import os
from signal import SIGTERM
import sys
import time


class Daemon(object):
    """ A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """

    def __init__(self, priority, pidfile, logger, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.priority = priority
        self.logger = logger

    def daemonize(self):
        """ Do the UNIX double-fork magic, see Stevens' "Advanced

        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
            self.logger.error("Daemon error at step1: " + e.strerror)
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as e:
            self.logger.error("Daemon error at step2: " + e.strerror)
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def getpid(self):
        """returns the content of pidfile or None."""
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
        return pid

    def checkpid(self, pid):
        """ Check For the existence of a unix pid. """
        if pid is None:
            return False

        try:
            os.kill(pid, 0)
        except OSError:
            self.delpid()
            return False
        else:
            return True

    def start(self):
        """Start the daemon"""
        # Check for a pidfile to see if the daemon already runs
        pid = self.getpid()

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """Stop the daemon"""
        # Get the pid from the pidfile
        pid = self.getpid()

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                # print str(err)
                sys.exit(1)

    def restart(self):
        """Restart the daemon"""
        self.stop()
        self.start()

    def status(self):
        """ returns instance's priority """
        # Check for a pidfile to see if the daemon already runs
        pid = self.getpid()

        status = 0

        if self.checkpid(pid):
            message = "status: pidfile %s exist. Daemon is running\n"
            status = self.priority
        else:
            message = "status: pidfile %s does not exist. Daemon is not running\n"

        sys.stderr.write(message % self.pidfile)
        return status

    def run(self):
        """ You should override this method when you subclass Daemon.

        It will be called after the process has been daemonized by start() or restart().
        """
