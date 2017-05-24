from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import relationship
from valet.db.lib.model_base import Base

class PlacementRequests(Base):
    __tablename__ = 'placement_requests'
    stack_id = Column(String(255), primary_key=True, nullable=False)
    request = Column(String(255))
