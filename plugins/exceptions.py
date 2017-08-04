#
# Copyright (c) 2014-2017 AT&T Intellectual Property
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

"""Valet OpenStack Plugin Exceptions"""

# Do not use exceptions as control flow! Recommended guidelines:
# https://julien.danjou.info/blog/2016/python-exceptions-guide
# https://realpython.com/blog/python/the-most-diabolical-python-antipattern/


class ValetOpenStackPluginException(Exception):
    """Base error for Valet"""
    def __init__(self, msg=None):
        super(ValetOpenStackPluginException, self).__init__(msg)


class GroupResourceNotIsolatedError(ValetOpenStackPluginException):
    """Valet Group resources must be isolated in their own template"""
    def __init__(self, msg=None):
        """Initialization"""
        if msg is None:
            msg = "OS::Valet::Group resources must be isolated " \
                  "in a dedicated stack"
        super(GroupResourceNotIsolatedError, self).__init__(msg)


class ResourceNotFoundError(ValetOpenStackPluginException):
    """Resource was not found"""
    def __init__(self, identifier, msg=None):
        """Initialization"""
        if msg is None:
            msg = "Resource identified by {} not found".format(identifier)
        super(ResourceNotFoundError, self).__init__(msg)
        self.identifier = identifier


class ResourceUUIDMissingError(ValetOpenStackPluginException):
    """Resource is missing a UUID (Orchestration ID)"""
    def __init__(self, resource, msg=None):
        """Initialization"""
        if msg is None:
            msg = "Resource named {} has no UUID".format(resource.name)
        super(ResourceUUIDMissingError, self).__init__(msg)
        self.resource = resource


class UnknownError(ValetOpenStackPluginException):
    """Unknown Exception catchall"""


"""Python API"""


class PythonAPIError(ValetOpenStackPluginException):
    """Python API error"""


class NotFoundError(PythonAPIError):
    """Not Found error"""


class HTTPError(PythonAPIError):
    """HTTP error"""
