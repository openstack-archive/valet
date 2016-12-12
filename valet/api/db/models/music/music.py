# -*- encoding: utf-8 -*-
#
# Copyright (c) 2016 AT&T
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

'''Music Data Store API'''

import json
import logging
import time

from valet.api.common.i18n import _

import requests

LOG = logging.getLogger(__name__)


class REST(object):
    '''Helper class for REST operations.'''

    hosts = None
    port = None
    path = None
    timeout = None

    _urls = None

    def __init__(self, hosts, port, path='/', timeout='10'):
        '''Initializer. Accepts target host list, port, and path.'''

        self.hosts = hosts  # List of IP or FQDNs
        self.port = port  # Port Number
        self.path = path  # Path starting with /
        self.timeout = float(timeout)  # REST request timeout in seconds

    @property
    def urls(self):
        '''Returns list of URLs using each host, plus the port/path.'''

        if not self._urls:
            urls = []
            for host in self.hosts:
                # Must end without a slash
                urls.append('http://%(host)s:%(port)s%(path)s' % {
                    'host': host,
                    'port': self.port,
                    'path': self.path,
                })
            self._urls = urls
        return self._urls

    @staticmethod
    def __headers(content_type='application/json'):
        '''Returns HTTP request headers.'''
        headers = {
            'accept': content_type,
            'content-type': content_type,
        }
        return headers

    def request(self, method='get', content_type='application/json', path='/', data=None):
        ''' Performs HTTP request '''
        if method not in ('post', 'get', 'put', 'delete'):
            raise KeyError(_("Method must be one of post, get, put, or delete."))
        method_fn = getattr(requests, method)

        response = None
        for url in self.urls:
            # Try each url in turn. First one to succeed wins.
            full_url = url + path
            try:
                data_json = json.dumps(data) if data else None
                LOG.debug("Music Request: %s %s%s", method.upper(), full_url,
                          data_json if data else '')
                response = method_fn(full_url, data=data_json,
                                     headers=self.__headers(content_type),
                                     timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.Timeout as err:
                response = requests.Response()
                response.status_code = 408
                response.url = full_url
                LOG.debug("Music: %s", err.message)
            except requests.exceptions.RequestException as err:
                response = requests.Response()
                response.status_code = 400
                response.url = full_url
                LOG.debug("Music: %s", err.message)

        # If we get here, an exception was raised for every url,
        # but we passed so we could try each endpoint. Raise status
        # for the last attempt (for now) so that we report something.
        if response:
            response.raise_for_status()


class Music(object):
    '''Wrapper for Music API'''
    lock_names = None  # Cache of lock names created during session
    lock_timeout = None  # Maximum time in seconds to acquire a lock

    rest = None  # API Endpoint
    replication_factor = None  # Number of Music nodes to replicate across

    def __init__(self, host=None, hosts=None,  # pylint: disable=R0913
                 port='8080', lock_timeout=10, replication_factor=3):
        '''Initializer. Accepts a lock_timeout for atomic operations.'''

        # If one host is provided, that overrides the list
        if not hosts:
            hosts = ['localhost']
        if host:
            hosts = [host]

        kwargs = {
            'hosts': hosts,
            'port': port,
            'path': '/MUSIC/rest',
        }
        self.rest = REST(**kwargs)

        self.lock_names = []
        self.lock_timeout = lock_timeout

        self.replication_factor = replication_factor

    def create_keyspace(self, keyspace):
        '''Creates a keyspace.'''
        data = {
            'replicationInfo': {
                #  'class': 'NetworkTopologyStrategy',
                #  'dc1': self.replication_factor,
                'class': 'SimpleStrategy',
                'replication_factor': self.replication_factor,
            },
            'durabilityOfWrites': True,
            'consistencyInfo': {
                'type': 'eventual',
            },
        }

        path = '/keyspaces/%s' % keyspace
        response = self.rest.request(method='post', path=path, data=data)
        return response.ok

    def create_table(self, keyspace, table, schema):
        '''Creates a table.'''
        data = {
            'fields': schema,
            'consistencyInfo': {
                'type': 'eventual',
            },
        }

        path = '/keyspaces/%(keyspace)s/tables/%(table)s/' % {
            'keyspace': keyspace,
            'table': table,
        }

        response = self.rest.request(method='post', path=path, data=data)
        return response.ok

    def version(self):
        '''Returns version string.'''
        path = '/version'
        response = self.rest.request(method='get',
                                     content_type='text/plain', path=path)
        return response.text

    def create_row(self, keyspace, table, values):
        '''Create a row.'''
        data = {
            'values': values,
            'consistencyInfo': {
                'type': 'eventual',
            },
        }

        path = '/keyspaces/%(keyspace)s/tables/%(table)s/rows' % {
            'keyspace': keyspace,
            'table': table,
        }
        response = self.rest.request(method='post', path=path, data=data)
        return response.ok

    def create_lock(self, lock_name):
        '''Returns the lock id. Use for acquiring and releasing.'''
        path = '/locks/create/%s' % lock_name
        response = self.rest.request(method='post',
                                     content_type='text/plain', path=path)
        return response.text

    def acquire_lock(self, lock_id):
        '''Acquire a lock.'''
        path = '/locks/acquire/%s' % lock_id
        response = self.rest.request(method='get',
                                     content_type='text/plain', path=path)

        return response.text.lower() == 'true'

    def release_lock(self, lock_id):
        '''Release a lock.'''
        path = '/locks/release/%s' % lock_id
        response = self.rest.request(method='delete',
                                     content_type='text/plain', path=path)
        return response.ok

    @staticmethod
    def __row_url_path(keyspace, table, pk_name, pk_value):
        '''Returns a Music-compliant row URL path.'''
        path = '/keyspaces/%(keyspace)s/tables/%(table)s/rows' % {
            'keyspace': keyspace,
            'table': table,
        }

        if pk_name and pk_value:
            path += '?%s=%s' % (pk_name, pk_value)
        return path

    def update_row_eventually(self, keyspace, table,  # pylint: disable=R0913
                              pk_name, pk_value, values):
        '''Update a row. Not atomic.'''
        data = {
            'values': values,
            'consistencyInfo': {
                'type': 'eventual',
            },
        }

        path = self.__row_url_path(keyspace, table, pk_name, pk_value)
        response = self.rest.request(method='put', path=path, data=data)
        return response.ok

    def update_row_atomically(self, keyspace, table,  # pylint: disable=R0913
                              pk_name, pk_value, values):
        '''Update a row atomically.'''

        # Create lock for the candidate. The Music API dictates that the
        # lock name must be of the form keyspace.table.primary_key
        lock_name = '%(keyspace)s.%(table)s.%(primary_key)s' % {
            'keyspace': keyspace,
            'table': table,
            'primary_key': pk_value,
        }
        self.lock_names.append(lock_name)
        lock_id = self.create_lock(lock_name)

        time_now = time.time()
        while not self.acquire_lock(lock_id):
            if time.time() - time_now > self.lock_timeout:
                raise IndexError(_('Lock acquire timeout: %s') % lock_name)

        # Update entry now that we have the lock.
        data = {
            'values': values,
            'consistencyInfo': {
                'type': 'atomic',
                'lockId': lock_id,
            },
        }

        path = self.__row_url_path(keyspace, table, pk_name, pk_value)
        response = self.rest.request(method='put', path=path, data=data)

        # Release lock now that the operation is done.
        self.release_lock(lock_id)
        # FIXME: Wouldn't we delete the lock at this point?

        return response.ok

    def delete_row_eventually(self, keyspace, table, pk_name, pk_value):
        '''Delete a row. Not atomic.'''
        data = {
            'consistencyInfo': {
                'type': 'eventual',
            },
        }

        path = self.__row_url_path(keyspace, table, pk_name, pk_value)
        response = self.rest.request(method='delete', path=path, data=data)
        return response.ok

    def read_row(self, keyspace, table, pk_name, pk_value, log=None):
        '''Read one row based on a primary key name/value.'''
        path = self.__row_url_path(keyspace, table, pk_name, pk_value)
        response = self.rest.request(path=path)
        if log:
            log.debug("response is %s, path is %s" % (response, path))
        return response.json()

    def read_all_rows(self, keyspace, table):
        '''Read all rows.'''
        return self.read_row(keyspace, table, pk_name=None, pk_value=None)

    def drop_keyspace(self, keyspace):
        '''Drops a keyspace.'''
        data = {
            'consistencyInfo': {
                'type': 'eventual',
            },
        }

        path = '/keyspaces/%s' % keyspace
        response = self.rest.request(method='delete', path=path, data=data)
        return response.ok

    def delete_lock(self, lock_name):
        '''Deletes a lock by name.'''
        path = '/locks/delete/%s' % lock_name
        response = self.rest.request(content_type='text/plain',
                                     method='delete', path=path)
        return response.ok

    def delete_all_locks(self):
        '''Delete all locks created during the lifetime of this object.'''

        # TODO(JD): Shouldn't this really be part of internal cleanup?
        # FIXME: It can be several API calls. Any way to do in one fell swoop?
        for lock_name in self.lock_names:
            self.delete_lock(lock_name)
