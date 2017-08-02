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

from valet.engine.optimizer.app_manager.group import LEVEL


class AvailResources(object):

    def __init__(self, _level):
        self.level = _level
        self.avail_hosts = {}
        self.candidates = {}

    def set_next_avail_hosts(self, _avail_hosts, _resource_of_level):
        for hk, h in _avail_hosts.iteritems():
            if self.level == "cluster":
                if h.cluster_name == _resource_of_level:
                    self.avail_hosts[hk] = h
            elif self.level == "rack":
                if h.rack_name == _resource_of_level:
                    self.avail_hosts[hk] = h
            elif self.level == "host":
                if h.host_name == _resource_of_level:
                    self.avail_hosts[hk] = h

    def set_next_level(self):
        '''Get the next level to search.'''
        current_level_index = LEVEL.index(self.level)
        next_level_index = current_level_index - 1
        if next_level_index < 0:
            self.level = LEVEL[0]
        else:
            self.level = LEVEL[next_level_index]

    def set_candidates(self):
        if self.level == "cluster":
            for _, h in self.avail_hosts.iteritems():
                self.candidates[h.cluster_name] = h
        elif self.level == "rack":
            for _, h in self.avail_hosts.iteritems():
                self.candidates[h.rack_name] = h
        elif self.level == "host":
            self.candidates = self.avail_hosts

    def set_candidate(self, _resource_name):
        if self.level == "cluster":
            for _, h in self.avail_hosts.iteritems():
                if h.cluster_name == _resource_name:
                    self.candidates[_resource_name] = h
                    break
        elif self.level == "rack":
            for _, h in self.avail_hosts.iteritems():
                if h.rack_name == _resource_name:
                    self.candidates[_resource_name] = h
                    break
        elif self.level == "host":
            if _resource_name in self.avail_hosts.keys():
                self.candidates[_resource_name] = self.avail_hosts[_resource_name]

    def get_candidate(self, _resource):
        candidate = None
        if self.level == "cluster":
            for _, h in self.avail_hosts.iteritems():
                if h.cluster_name == _resource.cluster_name:
                    candidate = h
                    break
        elif self.level == "rack":
            for _, h in self.avail_hosts.iteritems():
                if h.rack_name == _resource.rack_name:
                    candidate = h
        elif self.level == "host":
            if _resource.host_name in self.avail_hosts.keys():
                candidate = self.avail_hosts[_resource.host_name]
        return candidate
