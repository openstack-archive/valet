from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import relationship
from valet.db.lib.model_base import Base

class Group(Base):
    __tablename__ = 'group'

    id = Column(String(255), primary_key=True, nullable=False)
    description = Column(String(255))
    members = Column(String(255))
    name = Column(String(255))
    type = Column(String(255))
