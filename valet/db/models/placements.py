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

import sqlalchemy as sql
from sqlalchemy.orm import relationship
from valet.db.lib.model_base import Base


class Placement(Base):
    __tablename__ = 'placements'

    id = sql.Column(
        sql.String(255),
        primary_key=True,
        nullable=False)
    location = sql.Column(sql.String(255))
    name = sql.Column(sql.String(255))
    orchestration_id = sql.Column(
        sql.String(255),
        primary_key=True,
        nullable=False)
    reserved = sql.Column(sql.Boolean(True))
    resource_id = sql.Column(sql.String(255), primary_key=True, nullable=False)
    plan_id = sql.Column(sql.String(255), sql.ForeignKey('plans.id'))

    plan = relationship('Plan', back_populates='placements')
