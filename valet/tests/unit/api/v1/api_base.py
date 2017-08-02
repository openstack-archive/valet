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

"""Api Base."""

import mock

import pecan

from valet.tests.base import Base
# from valet.tests import db


class ApiBase(Base):
    """Api Base Test Class, calls valet tests base."""

    # FIXME(jdandrea): No camel-case! Use __init__().
    def setUp(self):
        """Setup api base and mock pecan identity/music/state."""
        super(ApiBase, self).setUp()
        pecan.conf.identity = mock.MagicMock()
        pecan.conf.music = mock.MagicMock()

        """
        # pecan.conf.music.keyspace = \
        #     mock.PropertyMock(return_value="valet")

        # Set up the mock Music API
        # TODO(jdandrea): In all honesty, instead of
        # using a mock object here, it may be better
        # to mock out only the surface that is being
        # crossed during a given test. We're most of
        # the way there. We may end up dumbing down
        # what the mock object does (vs. having it
        # do simplified in-memory storage).
        keyspace = 'valet'
        engine = db.MusicAPIWithOldMethodNames()

        # FIXME(jdandrea): pecan.conf.music used to be
        # a MagicMock, however it does not appear possible
        # to setattr() on a MagicMock (not one that can be
        # retrieved via obj.get('key') at least). That means
        # keys/values that were magically handled before are
        # no longer being handled now. We may end up filling
        # in the rest of the expected music conf settings
        # with individual mock object values if necessary.
        pecan.conf.music = {
            'keyspace': keyspace,
            'engine': engine,
        }

        # Create a keyspace and various tables (no schema needed)
        pecan.conf.music.engine.keyspace_create(keyspace)
        for table in ('plans', 'placements', 'groups',
                      'placement_requests', 'placement_results',
                      'query'):
            pecan.conf.music.engine.table_create(
                keyspace, table, schema=mock.MagicMock())
        """

        self.response = None
        pecan.core.state = mock.MagicMock()

    @classmethod
    def mock_error(cls, url, msg=None, **kwargs):
        """Mock error and set response to msg."""
        cls.response = msg
