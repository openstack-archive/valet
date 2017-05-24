from oslo_config import cfg
from oslo_db import api as db_api
from oslo_db import options as db_options


CONF = cfg.CONF

print(cfg.find_config_files())

# CONF.register_group(cfg.OptGroup(name='database'))
# cnxn = cfg.StrOpt(
#     'connection',
#     default='mysql+mysqldb://root:stack@localhost:3306/valet'
#     )

# CONF.register_opt(cnxn, group='database')

# CONF.database.connection = 'mysql+mysqldb://root:stack@localhost:3306/valet'

# db_options.set_defaults(CONF, connection='mysql+mysqldb://root:stack@localhost:3306/valet')


_BACKEND_MAPPING = {'sqlalchemy': 'valet.db.sqlalchemy.api'}

IMPL = db_api.DBAPI.from_config(CONF, backend_mapping=_BACKEND_MAPPING)

def get_engine():
    return IMPL.get_engine()

def get_session():
    return IMPL.get_session()

def db_sync(engine, version=None):
    """Migrate the database to `version` or the most recent version."""
    return IMPL.db_sync(engine, version=version)