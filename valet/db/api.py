import sys
# TODO - Eliminate this somehow
sys.path.insert(0, '/home/ben/valet-project/valet-core')
from oslo_config import cfg
from oslo_db import api as db_api
from oslo_db import options as db_options
from osprofiler import profiler
from sqlalchemy.ext.declarative import declarative_base
from valet.db.lib.model_base import Base
from valet.db.migration.initialize import stamp_version
import valet.db.models.plan
import valet.db.models.placement
import valet.db.models.placement_requests
import valet.db.models.placement_result
import valet.db.models.event
import valet.db.models.group

CONF = cfg.CONF

enabled = cfg.BoolOpt('enabled', default=False)

CONF.register_opt(enabled, 'profiler')

db_options.set_defaults(CONF, connection='mysql+mysqldb://root:stack@localhost:3306/valet') 

_BACKEND_MAPPING = {'sqlalchemy': 'valet.db.migration.api'}

IMPL = db_api.DBAPI.from_config(CONF, backend_mapping=_BACKEND_MAPPING)

def get_engine():
    return IMPL.get_engine()

def get_session():
    return IMPL.get_session()

def init_db():
    # TODO: Call this db engine, orm engine, to differentiate from valet 'engine'
    engine = get_engine()
    Base.metadata.create_all(engine)
    stamp_version()

# TODO - Move this into an interface outside this file
if __name__ == "__main__":
    if "build-db" in sys.argv[1]:
        init_db()
