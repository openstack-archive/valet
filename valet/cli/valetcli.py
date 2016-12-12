#!/usr/bin/python
import argparse
import sys
import valet.cli.groupcli as groupcli
# import logging


class Cli(object):
    def __init__(self):
        self.args = None
        self.submod = None
        self.parser = None

    def create_parser(self):
        self.parser = argparse.ArgumentParser(prog='valet', description='VALET REST CLI')
        service_sub = self.parser.add_subparsers(dest='service', metavar='<service>')
        self.submod = {'group': groupcli}
        for s in self.submod.values():
            s.add_to_parser(service_sub)

    def parse(self, argv=sys.argv):
        sys.argv = argv
        self.args = self.parser.parse_args()

    def logic(self):
        self.submod[self.args.service].run(self.args)


def main(argv):
    cli = Cli()
    cli.create_parser()
    cli.parse(argv)
    cli.logic()


if __name__ == "__main__":
    main(sys.argv)
