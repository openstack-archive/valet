#!/usr/bin/env python
# vi: sw=4 ts=4:
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

"""

        Mnemonic:   ha_valet.py
        Abstract:   High availability script for valet processes.
                    starts it's configured processes, and pings for their availability.
                    If local instances are not running, then makes the
                    current instances start. If it finds multiple instances running, then
                    determines which instance should be shut down based on priorities.

        Author:     Amnon Sagiv based on ha_tegu by Kaustubh Joshi

 ------------------------------------------------------------------------------

  Algorithm
 -----------
 The ha_valet script runs on each valet node in a continuous loop checking for
 heartbeats from all the valet nodes found in the "stand_by_list" conf property once
 every 5 secs (default). A heartbeat is obtained by invoking the "test_command"
 conf property.
 If exactly one monitored process instance is running, the script does
 nothing. If no instance is running, then the local instance is activated after
 waiting for 5*priority seconds to let a higher priority valet take over
 first. A valet monitored process's priority is determined by its conf.
 If the current node's is running and another is found, then a
 conflict resolution process is invoked whereby the priorities of both
 processes are compared, and the instance with the higher value is deactivated.

 IMPORTANT: test_command must return a value != 0, this is value should reflects
            the monitored process priority.
 """

import logging.handlers
import os
from oslo_config import cfg
import socket
import subprocess
import threading
import time
# import argparse
# from oslo_log import log as logging

CONF = cfg.CONF

# Directory locations
LOG_DIR = os.getenv('HA_VALET_LOGD', '/var/log/havalet/')
ETC_DIR = os.getenv('HA_VALET_ETCD', '/etc/valet/ha/')
DEFAULT_CONF_FILE = ETC_DIR + 'ha_valet.cfg'

# Set the maximum logfile size as Byte for time-series log files
max_log_size = 1000000
# Set the maximum number of time-series log files
max_num_of_logs = 10


PRIMARY_SETUP = 1
RETRY_COUNT = 3      # How many times to retry ping command
CONNECT_TIMEOUT = 3  # Ping timeout
MAX_QUICK_STARTS = 10        # we stop if there are > 10 restarts in quick succession
QUICK_RESTART_SEC = 150     # we consider it a quick restart if less than this

# HA Configuration
HEARTBEAT_SEC = 5                    # Heartbeat interval in seconds


NAME = 'name'
ORDER = 'order'
HOST = 'host'
USER = 'user'
PRIORITY = 'priority'
START_COMMAND = 'start'
STOP_COMMAND = 'stop'
TEST_COMMAND = 'test'
STAND_BY_LIST = 'stand_by_list'

ostro_group = cfg.OptGroup(name='Ostro', title='Valet Engine HA conf')
api_group = cfg.OptGroup(name='ValetApi', title='Valet Api HA conf')

havalet_opts = [
    cfg.IntOpt(PRIORITY, default=1, help='master slave distinguish'),
    cfg.IntOpt(ORDER, help='launching order'),
    cfg.StrOpt(HOST, help='where the monitored process is running on'),
    cfg.StrOpt(USER, help='linux user'),
    cfg.ListOpt(STAND_BY_LIST, help='monitored hosts list'),
    cfg.StrOpt(START_COMMAND, help='launch command'),
    cfg.StrOpt(STOP_COMMAND, help='stop command'),
    cfg.StrOpt(TEST_COMMAND, help='test command')
]

CONF.register_group(api_group)
CONF.register_opts(havalet_opts, api_group)

CONF.register_group(ostro_group)
CONF.register_opts(havalet_opts, ostro_group)


def read_conf():
    """returns dictionary of configured processes"""
    return dict([
        ('Ostro', {
            NAME: 'Ostro',
            ORDER: CONF.Ostro.order,
            HOST: CONF.Ostro.host,
            USER: CONF.Ostro.user,
            PRIORITY: CONF.Ostro.priority,
            START_COMMAND: CONF.Ostro.start,
            STOP_COMMAND: CONF.Ostro.stop,
            TEST_COMMAND: CONF.Ostro.test,
            STAND_BY_LIST: CONF.Ostro.stand_by_list
        }),

        ('ValetApi', {
            NAME: 'ValetApi',
            ORDER: CONF.ValetApi.order,
            HOST: CONF.ValetApi.host,
            USER: CONF.ValetApi.user,
            PRIORITY: CONF.ValetApi.priority,
            START_COMMAND: CONF.ValetApi.start,
            STOP_COMMAND: CONF.ValetApi.stop,
            TEST_COMMAND: CONF.ValetApi.test,
            STAND_BY_LIST: CONF.ValetApi.stand_by_list
        })])


def prepare_log(obj, name):
    obj.log = logging.getLogger(name)
    obj.log.setLevel(logging.DEBUG)
    # logging.register_options(CONF)
    # logging.setup(CONF, 'valet')
    handler = logging.handlers.RotatingFileHandler(LOG_DIR + name + '.log', maxBytes=max_log_size,
                                                   backupCount=max_num_of_logs)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(fmt)
    obj.log.addHandler(handler)


class HaValetThread (threading.Thread):

    def __init__(self, data, exit_event):
        threading.Thread.__init__(self)
        self.data = data
        self.log = None

    def run(self):
        """Main function"""
        prepare_log(self, self.data[NAME])
        self.log.info('HA Valet - ' + self.data[NAME] + ' Watcher Thread - starting')

        fqdn_list = []
        this_node = socket.getfqdn()
        fqdn_list.append(this_node)

        # Read list of standby valet nodes and find us
        standby_list = self.data.get(STAND_BY_LIST, None)

        while not len(standby_list) is 0:            # loop until we find us
            self.log.debug("stand by list: " + str(standby_list))
            try:
                for fqdn in fqdn_list:
                    self.log.debug("fqdn_list: " + str(fqdn_list))
                    if fqdn in standby_list:
                        this_node = fqdn
                        break
                standby_list.remove(this_node)
                self.data[STAND_BY_LIST] = standby_list
                self.log.debug("modified stand by list: " + str(standby_list))
            except ValueError:
                self.log.debug("host " + this_node + " is not in standby list: %s - continue"
                               % str(standby_list))
                break

        # Loop forever sending pings
        self._main_loop(this_node)
        self.log.info("HA Valet Watcher Thread - going down!")

    def use(self, param):
        pass

    def _main_loop(self, this_node):
        """ Main heartbeat and liveness check loop

        :param this_node: host name
        :type this_node: string
        :return: None
        :rtype:
        """
        quick_start = 0  # number of restarts close together
        last_start = 0
        priority_wait = False

        """
            DO NOT RENAME, DELETE, MOVE the following parameters,
            they may be referenced from within the process commands
        """
        host = self.data.get(HOST, 'localhost')
        user = self.data.get(USER, None)
        self.use(user)
        my_priority = int(self.data.get(PRIORITY, 1))
        start_command = eval(self.data.get(START_COMMAND, None))
        stop_command = self.data.get(STOP_COMMAND, None)
        test_command = self.data.get(TEST_COMMAND, None)
        standby_list = self.data.get(STAND_BY_LIST)

        while True:
            if not priority_wait:
                # Normal heartbeat
                time.sleep(HEARTBEAT_SEC)
            else:
                # No valet running. Wait for higher priority valet to activate.
                time.sleep(HEARTBEAT_SEC * my_priority)

            self.log.info('checking status here - ' + host + ', my priority: ' + str(my_priority))
            i_am_active, priority = self._is_active(eval(test_command))
            self.log.info(host + ': host_active = ' + str(i_am_active) + ', ' + str(priority))
            any_active = i_am_active
            self.log.info('any active = ' + str(any_active))

            # Check for active valets
            standby_list_is_empty = not standby_list
            if not standby_list_is_empty:
                self.log.debug('main loop: standby_list is not empty ' + str(standby_list))
                for host_in_list in standby_list:
                    if host_in_list == this_node:
                        self.log.info('host_in_list is this_node - skipping')
                        continue

                    self.log.info('checking status on - ' + host_in_list)
                    host = host_in_list
                    host_active, host_priority = self._is_active(eval(test_command))
                    host = self.data.get(HOST, 'localhost')
                    self.log.info(host_in_list + ' - host_active = ' + str(host_active) + ', ' + str(host_priority))
                    # Check for split brain: 2 valets active
                    if i_am_active and host_active:
                        self.log.info('found two live instances, checking priorities')
                        should_be_active = self._should_be_active(host_priority, my_priority)
                        if should_be_active:
                            self.log.info('deactivate myself, ' + host_in_list + ' already running')
                            self._deactivate_process(eval(stop_command))     # Deactivate myself
                            i_am_active = False
                        else:
                            self.log.info('deactivate ' + self.data[NAME] + ' on ' + host_in_list +
                                          ', already running here')
                            host = host_in_list
                            self._deactivate_process(eval(stop_command))  # Deactivate other valet
                            host = self.data.get(HOST, 'localhost')

                    # Track that at-least one valet is active
                    any_active = any_active or host_active

            # If no active process or I'm primary, then we must try to start one
            if not any_active or (not i_am_active and my_priority == PRIMARY_SETUP):
                self.log.warn('there is no instance up')
                self.log.info('Im primary instance:  ' + str(my_priority is PRIMARY_SETUP))
                if priority_wait or my_priority == PRIMARY_SETUP:
                    now = int(time.time())
                    if now - last_start < QUICK_RESTART_SEC:           # quick restart (crash?)
                        quick_start += 1
                        if quick_start > MAX_QUICK_STARTS:
                            self.log.critical("too many restarts in quick succession.")
                    else:
                        quick_start = 0               # reset if it's been a while since last restart

                    if last_start == 0:
                        diff = "never by this instance"
                    else:
                        diff = "%d seconds ago" % (now - last_start)

                    last_start = now
                    priority_wait = False
                    if (not i_am_active and my_priority == PRIMARY_SETUP) or (standby_list is not None):
                        self.log.info('no running instance found, starting here; last start %s' % diff)
                        self._activate_process(start_command, my_priority)
                    else:
                        host = standby_list[0]  # LIMITATION - supporting only 1 stand by host
                        self.log.info('no running instances found, starting on %s; last start %s' % (host, diff))
                        self._activate_process(start_command, my_priority)
                        host = self.data.get(HOST, 'localhost')
                else:
                    priority_wait = True
            else:
                self.log.info("status: up and running")
        # end loop

    def _should_be_active(self, host_priority, my_priority):
        """ Returns True if host should be active as opposed to current node, based on the hosts priorities.

           Lower value means higher Priority,
           0 (zero) - invalid priority (e.g. process is down)

        :param host_priority: other host's priority
        :type host_priority: int
        :param my_priority: my priority
        :type my_priority: int
        :return: True/False
        :rtype: bool
        """
        self.log.info('my priority is %d, remote priority is %d' % (my_priority, host_priority))
        return host_priority < my_priority

    def _is_active(self, call):
        """ Return 'True, Priority' if valet is running on host

           'False, None' Otherwise.
        """

        # must use no-proxy to avoid proxy servers gumming up the works
        for i in xrange(RETRY_COUNT):
            try:
                self.log.info('ping (retry %d): %s' % (i, call))
                proc = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                priority = proc.wait()
                if priority == 255:  # no route to host
                    priority = 0
                out, err = proc.communicate()
                self.log.debug('out: ' + out + ', err: ' + err)
                self.log.info('ping result (should be > 0): %s' % (str(priority)))
                return (priority > 0), priority
            except subprocess.CalledProcessError:
                self.log.error('ping error: ' + str(subprocess.CalledProcessError))
                continue
        return False, None

    def _deactivate_process(self, deactivate_command):
        """ Deactivate valet on a given host. If host is omitted, local

            valet is stopped. Returns True if successful, False on error.
        """

        try:
            # call = "'" + deactivate_command % (PROTO, host, port) + "'"
            self.log.info('deactivate_command: ' + deactivate_command)
            subprocess.check_call(deactivate_command, shell=True)
            return True
        except subprocess.CalledProcessError as e:
            self.log.error(str(e))
            return False

    def _activate_process(self, activate_command, priority):
        """ Activate valet on a given host. If host is omitted, local

            valet is started. Returns True if successful, False on error.
        """

        try:
            self.log.info('activate_command: ' + activate_command)
            subprocess.check_call(activate_command, shell=True)
            time.sleep(HEARTBEAT_SEC * priority)  # allow some grace period
            return True
        except subprocess.CalledProcessError as e:
            self.log.error(str(e))
            return False


class HAValet(object):

    def __init__(self):
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        self.log = None

    @DeprecationWarning
    def _parse_valet_conf_v010(self, conf_file_name=DEFAULT_CONF_FILE, process=''):
        """ This function reads the valet config file and returns configuration

            attributes in key/value format

        :param conf_file_name: config file name
        :type conf_file_name: string
        :param process: specific process name
                        when not supplied - the module launches all the processes in the configuration
        :type process: string
        :return: dictionary of configured monitored processes
        :rtype: dict
        """

        cdata = {}
        section = ''

        try:
            with open(conf_file_name, 'r') as valet_conf_file:
                for line in valet_conf_file.readlines():
                    if line.strip(' \t\r\n')[:1] == '#' or line.__len__() == 2:
                        continue
                    elif line.lstrip(' \t\r\n')[:1] == ':':
                        tokens = line.lstrip(' \t\n\r').split(' ')
                        section = tokens[0][1:].strip('\n\r\n')
                        cdata[section] = {}
                        cdata[section][NAME] = section
                    else:
                        if line[:1] == '\n':
                            continue
                        tokens = line.split('=')
                        key = tokens[0].strip(' \t\n\r')
                        value = tokens[1].strip(' \t\n\r')
                        cdata[section][key] = value

            # if need to run a specific process
            # remove all others
            if process is not '':
                for key in cdata.keys():
                    if key != process:
                        del cdata[key]

            return cdata
        except OSError:
            print('unable to open %s file for some reason' % conf_file_name)
        return cdata

    def _valid_process_conf_data(self, process_data):
        """ verify all mandatory parameters are found in the monitored process configuration only standby_list is optional

        :param process_data: specific process configuration parameters
        :type process_data: dict
        :return: are all mandatory parameters are found
        :rtype: bool
        """

        if (process_data.get(HOST) is not None and
            process_data.get(PRIORITY) is not None and
            process_data.get(ORDER) is not None and
            process_data.get(START_COMMAND) is not None and
            process_data.get(STOP_COMMAND) is not None and
                process_data.get(TEST_COMMAND) is not None):
            return True
        else:
            return False

    def start(self):
        """Start valet HA - Main function"""
        prepare_log(self, 'havalet')
        self.log.info('ha_valet v1.1 starting')

        conf_data = read_conf()

        if len(conf_data.keys()) is 0:
            self.log.warn('Processes list is empty - leaving.')
            return

        threads = []
        exit_event = threading.Event()

        # sort by launching order
        proc_sorted = sorted(conf_data.values(), key=lambda d: int(d[ORDER]))

        for proc in proc_sorted:
            if self._valid_process_conf_data(proc):
                self.log.info('Launching: ' + proc[NAME] + ' - parameters: ' + str(proc))
                thread = HaValetThread(proc, exit_event)
                time.sleep(HEARTBEAT_SEC)
                thread.start()
                threads.append(thread)
            else:
                self.log.info(proc[NAME] + " section is missing mandatory parameter.")
                continue

        self.log.info('on air.')

        while not exit_event.isSet():
            time.sleep(HEARTBEAT_SEC)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        self.log.info('ha_valet v1.1 exiting')

if __name__ == '__main__' or __name__ == "main":
    CONF(default_config_files=[DEFAULT_CONF_FILE])
    HAValet().start()
