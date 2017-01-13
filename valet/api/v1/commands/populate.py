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

"""Populate command."""

from pecan.commands.base import BaseCommand

from valet.api.common.i18n import _
from valet.api.conf import register_conf, set_domain
from valet.api.db import models
from valet.api.db.models import Event
from valet.api.db.models import Group
from valet.api.db.models import Placement
from valet.api.db.models import PlacementRequest
from valet.api.db.models import PlacementResult
from valet.api.db.models import Plan


def out(string):
    """Output helper."""
    print("==> %s" % string)


class PopulateCommand(BaseCommand):
    """Load a pecan environment and initializate the database."""

    def run(self, args):
        """Function creates and initializes database and environment."""
        super(PopulateCommand, self).run(args)
        out(_("Loading environment"))
        register_conf()
        set_domain()
        self.load_app()
        out(_("Building schema"))
        try:
            out(_("Starting a transaction..."))
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
        except Exception:
            models.rollback()
            out(_("Rolling back..."))
            raise
        else:
            out(_("Committing."))
            models.commit()
