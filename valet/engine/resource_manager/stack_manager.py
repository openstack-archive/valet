#!/bin/python


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
