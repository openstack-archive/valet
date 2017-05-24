from alembic.config import Config
from alembic import command
import os

def stamp_version():
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'alembic.ini')
    alembic_cfg = Config(path)
    command.stamp(alembic_cfg, "head")

    down_revision = None
