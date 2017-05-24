from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import relationship
from valet.db.lib.model_base import Base

class Event(Base):
    __tablename__ = 'event'
    event_id = Column(String(255), primary_key=True, nullable=False)
    event = Column(String(255))
