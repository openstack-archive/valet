import sys

from oslo_db.sqlalchemy import session as db_session
from oslo_config import cfg
import osprofiler.sqlalchemy
import sqlalchemy

CONF = cfg.CONF

_facade = None

def get_facade():

    global _facade

    if not _facade:
        _facade = db_session.EngineFacade.from_config(CONF)
        if CONF.profiler.enabled:
            if CONF.profiler.trace_sqlalchemy:
                osprofiler.sqlalchemy.add_tracing(sqlalchemy,
                                                  _facade.get_engine(),
                                                  "db")

    return _facade


def get_engine():
    return get_facade().get_engine()

def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]