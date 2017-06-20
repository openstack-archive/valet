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
from pecan.commands.base import BaseCommand

from valet import api
from valet.api.common.i18n import _
from valet.api.db import models
from valet.api.db.models.music.groups import Group
from valet.api.db.models.music.ostro import Event
from valet.api.db.models.music.ostro import PlacementRequest
from valet.api.db.models.music.ostro import PlacementResult
from valet.api.db.models.music.placements import Placement
from valet.api.db.models.music.plans import Plan
from valet.common.conf import get_logger
from valet.common.conf import init_conf


class PopulateCommand(BaseCommand):
    """Load a pecan environment and initializate the database."""

    def run(self, args):
        """Function creates and initializes database and environment."""
        super(PopulateCommand, self).run(args)
        try:
            init_conf("populate.log")
            LOG = api.LOG = get_logger("populate")
            LOG.info(_("Loading environment"))
            self.load_app()
            LOG.info(_("Building schema"))
            LOG.info(_("Starting a transaction..."))
            models.start()

            # FIXME: There's no create_all equivalent for Music.

            # Valet
            Group.create_table()
            Placement.create_table()
            Plan.create_table()

            # Ostro
            Event.create_table()
            PlacementRequest.create_table()
            PlacementResult.create_table()
        except Exception as ex:
            models.rollback()
            LOG.error("Rolling back... %s" % ex)
            raise
        else:
            LOG.info(_("Committing."))
            models.commit()
