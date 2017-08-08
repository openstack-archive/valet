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


# from valet.engine.resource_manager.heat import Heat


class StackManager(object):

    def __init__(self, _resource, _config, _logger):
        self.phandler = None
        self.ahandler = None
        self.resource = _resource

        self.config = _config
        self.logger = _logger

    def set_handlers(self, _placement_handler, _app_handler):
        '''Set handlers.'''
        self.phandler = _placement_handler
        self.ahandler = _app_handler

    def set_stacks(self):
        self.logger.info("set stacks")

        # stacks = {}

        # stack_getter = Heat(self.logger)

        return True
