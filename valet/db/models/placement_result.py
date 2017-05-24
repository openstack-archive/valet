from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import relationship
from valet.db.lib.model_base import Base

class PlacementResults(Base):
    __tablename__ = 'placement_results'
    stack_id = Column(String(255), primary_key=True, nullable=False)
    request = Column(String(255))
