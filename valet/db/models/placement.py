from sqlalchemy import Table, Column, Integer, Boolean, String, MetaData, ForeignKey
from sqlalchemy.orm import relationship
from valet.db.lib.model_base import Base

class Placement(Base):
    __tablename__ = 'placement'

    id = Column(String(255), primary_key=True, nullable=False)
    location = Column(String(255))
    name = Column(String(255))
    orchestration_id = Column(String(255), primary_key=True, nullable=False)
    reserved = Column(Boolean(True))
    resource_id = Column(String(255), primary_key=True, nullable=False)
    plan_id = Column(String(255), ForeignKey('plan.id'))

    plan = relationship('Plan', back_populates='placements')