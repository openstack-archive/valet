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

from oslo_config import cfg
from oslo_db.sqlalchemy import session as db_session
import osprofiler.sqlalchemy
import sqlalchemy
import sys

CONF = cfg.CONF

INIT_VERSION = 0

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
