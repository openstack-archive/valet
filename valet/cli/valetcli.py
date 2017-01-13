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

"""Valet cli."""

import argparse
import sys
import valet.cli.groupcli as groupcli
# import logging


class Cli(object):
    """Cli."""

    def __init__(self):
        """Init cli."""
        self.args = None
        self.submod = None
        self.parser = None

    def create_parser(self):
        """Create parser."""
        self.parser = argparse.ArgumentParser(prog='valet',
                                              description='VALET REST CLI')
        service_sub = self.parser.add_subparsers(dest='service',
                                                 metavar='<service>')
        self.submod = {'group': groupcli}
        for s in self.submod.values():
            s.add_to_parser(service_sub)

    def parse(self, argv=sys.argv):
        """Parse args."""
        sys.argv = argv
        self.args = self.parser.parse_args()

    def logic(self):
        """Logic."""
        self.submod[self.args.service].run(self.args)


def main(argv):
    """Main."""
    cli = Cli()
    cli.create_parser()
    cli.parse(argv)
    cli.logic()


if __name__ == "__main__":
    main(sys.argv)
