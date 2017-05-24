#
# Copyright 2014-2017 AT&T Intellectual Property
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from valet.db.lib.model_base import Base


class Plan(Base):
    __tablename__ = 'plans'

    id = Column(String(255), primary_key=True, nullable=False)
    name = Column(String(255))
    stack_id = Column(String(255))

    placements = relationship('Placement', back_populates='plans')
