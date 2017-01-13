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

"""General Logger."""

from oslo_log import log as logging
from tempest import config

CONF = config.CONF
LOG = logging.getLogger(__name__)

COLORS = \
    {
        "WHITE": '\033[0;37m',
        "L_RED": '\033[1;31m',
        "L_PURPLE": '\033[1;35m',
        "L_GREEN": '\033[0;32m',
        "L_BLUE": '\033[1;34m',
        "Yellow": '\033[0;33m'
    }


class GeneralLogger(object):
    """Class containing general log methods."""

    def __init__(self, name):
        """Init logger with test name."""
        self.test_name = name

    def log_info(self, msg):
        """Info log."""
        LOG.info("%s %s - %s %s %s" % (COLORS["L_PURPLE"], self.test_name,
                                       COLORS["L_GREEN"], msg, COLORS["WHITE"]))

    def log_error(self, msg, trc_back=None):
        """Log error and trace_back for error if there is one."""
        LOG.error("%s %s - %s %s %s" % (COLORS["L_PURPLE"], self.test_name,
                                        COLORS["L_RED"], msg, COLORS["WHITE"]))
        if trc_back:
            LOG.error("%s %s - %s %s %s" % (COLORS["L_PURPLE"], self.test_name,
                                            COLORS["L_RED"], trc_back,
                                            COLORS["WHITE"]))

    def log_debug(self, msg):
        """Log debug."""
        LOG.debug("%s %s - %s %s %s" % (COLORS["L_PURPLE"], self.test_name,
                                        COLORS["L_BLUE"], msg, COLORS["WHITE"]))

    def log_group(self, msg):
        """Log info."""
        LOG.info("%s %s - %s %s %s" % (COLORS["L_PURPLE"], self.test_name,
                                       COLORS["Yellow"], msg, COLORS["WHITE"]))
