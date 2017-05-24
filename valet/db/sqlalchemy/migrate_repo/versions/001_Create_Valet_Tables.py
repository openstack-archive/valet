from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = sqlalchemy.MetaData()
    meta.bind = migrate_engine
    
    plan = sqlalchemy.Table(
        'plan', meta,
        sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True,
            nullable=False),
        sqlalchemy.Column('name', sqlalchemy.LongText),
        sqlalchemy.Column('stack_id', sqlalchemy.LongText),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    ) 


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass
