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

from alembic import command
from alembic.config import Config
import os


def stamp_version():
    path = os.path.join(
        os.path.abspath(
            os.path.dirname(__file__)), 'alembic.ini')
    alembic_cfg = Config(path)
    command.stamp(alembic_cfg, "head")
