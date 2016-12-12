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
from oslo_log import log as logging
import time
from valet.tests.functional.valet_validator.common.init import CONF, COLORS

LOG = logging.getLogger(__name__)


class Result(object):
    ok = False
    message = ""

    def __init__(self, ok=True, msg=""):
        self.ok = ok
        self.message = msg


class GeneralLogger(object):
    @staticmethod
    def delay(duration=None):
        time.sleep(duration or CONF.heat.DELAY_DURATION)

    @staticmethod
    def log_info(msg):
        LOG.info("%s %s %s" % (COLORS["L_GREEN"], msg, COLORS["WHITE"]))

    @staticmethod
    def log_error(msg, trc_back=""):
        LOG.error("%s %s %s" % (COLORS["L_RED"], msg, COLORS["WHITE"]))
        LOG.error("%s %s %s" % (COLORS["L_RED"], trc_back, COLORS["WHITE"]))

    @staticmethod
    def log_debug(msg):
        LOG.debug("%s %s %s" % (COLORS["L_BLUE"], msg, COLORS["WHITE"]))

    @staticmethod
    def log_group(msg):
        LOG.info("%s %s %s" % (COLORS["Yellow"], msg, COLORS["WHITE"]))
