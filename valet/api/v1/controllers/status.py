# -*- encoding: utf-8 -*-
#
# Copyright (c) 2014-2016 AT&T
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.

'''Status'''

import logging

from pecan import expose, request, response
from valet.api.common.i18n import _
from valet.api.common.ostro_helper import Ostro
from valet.api.v1.controllers import error

LOG = logging.getLogger(__name__)

# pylint: disable=R0201


class StatusController(object):
    ''' Status Controller /v1/status '''

    @classmethod
    def _ping_ostro(cls):
        '''Ping Ostro'''
        ostro = Ostro()
        ostro.ping()
        ostro.send()
        return ostro.response

    @classmethod
    def _ping(cls):
        '''Ping each subsystem.'''
        ostro_response = StatusController._ping_ostro()
        # TODO(JD): Ping Music plus any others.
        # music_response = StatusController._ping_music()

        response = {
            "status": {
                "ostro": ostro_response,
                # "music": music_response,
            }
        }

        return response

    @classmethod
    def allow(cls):
        '''Allowed methods'''
        return 'HEAD,GET'

    @expose(generic=True, template='json')
    def index(self):
        '''Catchall for unallowed methods'''
        message = _('The %s method is not allowed.') % request.method
        kwargs = {'allow': self.allow()}
        error('/errors/not_allowed', message, **kwargs)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        '''Options'''
        response.headers['Allow'] = self.allow()
        response.status = 204

    @index.when(method='HEAD', template='json')
    def index_head(self):
        '''Ping each subsystem and return summary response'''
        self._ping()  # pylint: disable=W0612
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        '''Ping each subsystem and return detailed response'''

        _response = self._ping()
        response.status = 200
        return _response
