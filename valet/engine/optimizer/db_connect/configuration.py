#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions
#
#################################################################################################################


import sys


class Config(object):

    def __init__(self):
        self.mode = None

        self.db_keyspace = None
        self.db_request_table = None
        self.db_response_table = None
        self.db_event_table = None
        self.db_resource_table = None
        self.db_app_table = None
        self.db_resource_index_table = None
        self.db_app_index_table = None
        self.db_uuid_table = None

    def configure(self):
        try:
            f = open("./client.cfg", "r")
            line = f.readline()

            while line:
                if line.startswith("#") or line.startswith(" ") or line == "\n":
                    line = f.readline()
                    continue

                (rk, v) = line.split("=")
                k = rk.strip()

                if k == "db_keyspace":
                    self.db_keyspace = v.strip()
                elif k == "db_request_table":
                    self.db_request_table = v.strip()
                elif k == "db_response_table":
                    self.db_response_table = v.strip()
                elif k == "db_event_table":
                    self.db_event_table = v.strip()
                elif k == "db_resource_table":
                    self.db_resource_table = v.strip()
                elif k == "db_app_table":
                    self.db_app_table = v.strip()
                elif k == "db_resource_index_table":
                    self.db_resource_index_table = v.strip()
                elif k == "db_app_index_table":
                    self.db_app_index_table = v.strip()
                elif k == "db_uuid_table":
                    self.db_uuid_table = v.strip()

                line = f.readline()

            f.close()

            return "success"

        except IOError as e:
            return "I/O error({}): {}".format(e.errno, e.strerror)
        except Exception:
            return "Unexpected error: ", sys.exc_info()[0]
