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
