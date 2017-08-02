#!/bin/python


class Flavor(object):
    '''Container for flavor resource.'''

    def __init__(self, _name):
        self.name = _name
        self.flavor_id = None

        self.status = "enabled"

        self.vCPUs = 0
        self.mem_cap = 0        # MB
        self.disk_cap = 0       # including ephemeral (GB) and swap (MB)

        self.extra_specs = {}

        self.last_update = 0

    def get_json_info(self):
        return {'status': self.status,
                'flavor_id': self.flavor_id,
                'vCPUs': self.vCPUs,
                'mem': self.mem_cap,
                'disk': self.disk_cap,
                'extra_specs': self.extra_specs,
                'last_update': self.last_update}
