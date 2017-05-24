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

import sys
sys.path.insert(0, '/home/ben/valet-project/valet-core')
from oslo_config import cfg
from oslo_db import api as db_api
from oslo_db import options as db_options
from valet.db.lib.model_base import Base
from valet.db.migration.initialize import stamp_version
import valet.db.models.events as events
import valet.db.models.groups as groups
import valet.db.models.placements as placements
import valet.db.models.placement_requests as placement_requests
import valet.db.models.placement_results as placement_results
import valet.db.models.plans as plans

CONF = cfg.CONF

enabled = cfg.BoolOpt('enabled', default=False)

CONF.register_opt(enabled, 'profiler')

db_options.set_defaults(
    CONF,
    connection='mysql+mysqldb://root:stack@localhost:3306/valet')

_BACKEND_MAPPING = {'sqlalchemy': 'valet.db.migration.api'}

IMPL = db_api.DBAPI.from_config(CONF, backend_mapping=_BACKEND_MAPPING)


def get_engine():
    return IMPL.get_engine()


def get_session():
    return IMPL.get_session()


def init_db():
    assert [events,
            groups,
            placements,
            placement_requests,
            placement_results,
            plans]
    db_engine = get_engine()
    Base.metadata.create_all(db_engine)
    stamp_version()


if __name__ == "__main__":
    if "build-db" in sys.argv[1]:
        init_db()
