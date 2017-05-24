from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import relationship
from valet.db.lib.model_base import Base

class Plan(Base):
    __tablename__ = 'plan'

    id = Column(String(255), primary_key=True, nullable=False)
    name = Column(String(255))
    stack_id = Column(String(255))

    placements = relationship('Placement', back_populates='plan')