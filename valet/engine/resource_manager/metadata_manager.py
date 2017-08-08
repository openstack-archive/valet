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

import threading
import time

from copy import deepcopy
# from valet.engine.optimizer.simulator.compute_sim import ComputeSim
from valet.engine.resource_manager.nova_compute import NovaCompute


class MetadataManager(threading.Thread):
    '''Metadata Manager to maintain flavors and groups.'''

    def __init__(self, _t_id, _t_name, _resource, _data_lock, _config,
                 _logger):
        threading.Thread.__init__(self)

        self.thread_id = _t_id
        self.thread_name = _t_name
        self.data_lock = _data_lock
        self.end_of_process = False

        self.resource = _resource

        self.config = _config
        self.logger = _logger

        self.update_batch_wait = self.config.update_batch_wait

    def run(self):
        '''Keep checking timing for this batch job.'''

        self.logger.info("start " + self.thread_name + " ......")

        period_end = 0
        if self.config.metadata_trigger_freq > 0:
            period_end = time.time() + self.config.metadata_trigger_freq

        while self.end_of_process is False:
            time.sleep(60)

            curr_ts = time.time()
            if curr_ts > period_end:
                if ((curr_ts - self.resource.current_timestamp) >
                   self.update_batch_wait):
                    self._run()

                    period_end = time.time() + \
                        self.config.metadata_trigger_freq

        self.logger.info("exit " + self.thread_name)

    def _run(self):
        '''Run this batch job.'''

        if self.set_groups() is not True:
            self.logger.warn("fail to set groups (availability zones and "
                             "host-aggregates) from nova")

        if self.set_flavors() is not True:
            self.logger.warn("fail to set flavor from nova")

        return True

    def set_groups(self):
        '''Set groups (availability zones and host-aggregates) from nova.'''

        self.logger.info("set metadata (groups)")

        groups = {}

        # compute = ComputeSim(self.config)
        compute = NovaCompute()
        if compute.set_groups(groups) != "success":
            return False

        self.data_lock.acquire()
        self._check_group_update(groups)

        if self._check_host_memberships_update(groups) is True:
            self.resource.update_topology(store=False)
        self.data_lock.release()

        return True

    def _check_group_update(self, _groups):
        '''Check any inconsistency for groups.'''

        for lk in _groups.keys():
            if lk not in self.resource.groups.keys():
                self.resource.groups[lk] = deepcopy(_groups[lk])
                self.resource.groups[lk].last_update = time.time()
                self.logger.info("new group (" + lk + ") added")

        for rlk in self.resource.groups.keys():
            rl = self.resource.groups[rlk]
            if (rl.group_type != "EX" and rl.group_type != "AFF" and
               rl.group_type != "DIV"):
                if rlk not in _groups.keys():
                    self.resource.groups[rlk].status = "disabled"
                    self.resource.groups[rlk].last_update = time.time()
                    self.logger.info("group (" + rlk + ") disabled")

        for lk in _groups.keys():
            lg = _groups[lk]
            rlg = self.resource.groups[lk]
            if (lg.group_type != "EX" and lg.group_type != "AFF" and
               lg.group_type != "DIV"):
                if self._check_group_metadata_update(lg, rlg) is True:
                    rlg.last_update = time.time()
                    self.logger.info("group (" + lk + ") updated")

    def _check_group_metadata_update(self, _lg, _rlg):
        '''Check any change in status and metadata of group.'''

        updated = False

        if _lg.status != _rlg.status:
            _rlg.status = _lg.status
            updated = True

        for mdk in _lg.metadata.keys():
            if mdk not in _rlg.metadata.keys():
                _rlg.metadata[mdk] = _lg.metadata[mdk]
                updated = True

        for rmdk in _rlg.metadata.keys():
            if rmdk not in _lg.metadata.keys():
                del _rlg.metadata[rmdk]
                updated = True

        for hk in _lg.vms_per_host.keys():
            if hk not in _rlg.vms_per_host.keys():
                _rlg.vms_per_host[hk] = deepcopy(_lg.vms_per_host[hk])
                updated = True

        for rhk in _rlg.vms_per_host.keys():
            if rhk not in _lg.vms_per_host.keys():
                del _rlg.vms_per_host[rhk]
                updated = True

        return updated

    def _check_host_memberships_update(self, _groups):
        '''Check host memberships consistency.'''

        membership_updated = False

        for lgk, lg in _groups.iteritems():
            for hk in lg.vms_per_host.keys():
                if hk in self.resource.hosts.keys():
                    rhost = self.resource.hosts[hk]
                    if lgk not in rhost.memberships.keys():
                        rhost.memberships[lgk] = self.resource.groups[lgk]
                        self.resource.update_host_time(hk)
                        membership_updated = True
                        self.logger.info("host (" + rhost.name +
                                         ") updated (new membership)")

        for rhk, rhost in self.resource.hosts.iteritems():
            if rhost.check_availability() is True:
                for mk in rhost.memberships.keys():
                    m = rhost.memberships[mk]
                    if (m.group_type != "EX" and m.group_type != "AFF" and
                       m.group_type != "DIV"):
                        if mk not in _groups.keys():
                            del rhost.memberships[mk]
                            self.resource.update_host_time(rhk)
                            membership_updated = True
                            self.logger.info("host (" + rhost.name +
                                             ") updated (delete membership)")
                        else:
                            lg = _groups[mk]
                            if rhk not in lg.vms_per_host.keys():
                                del rhost.memberships[mk]
                                self.resource.update_host_time(rhk)
                                membership_updated = True
                                self.logger.info("host (" + rhost.name + ") "
                                                 "updated (delete membership)")

        return membership_updated

    def set_flavors(self):
        '''Set flavors from nova.'''

        self.logger.info("set metadata (flavors)")

        flavors = {}

        # compute = ComputeSim(self.config)
        compute = NovaCompute()
        if compute.set_flavors(flavors) != "success":
            return False

        self.data_lock.acquire()
        self._check_flavor_update(flavors)
        self.data_lock.release()

        return True

    def _check_flavor_update(self, _flavors):
        '''Check flavor info consistency.'''

        for fk in _flavors.keys():
            if fk not in self.resource.flavors.keys():
                self.resource.flavors[fk] = deepcopy(_flavors[fk])

                self.resource.flavors[fk].last_update = time.time()
                self.logger.info("new flavor (" + fk + ":" +
                                 _flavors[fk].flavor_id + ") added")

        for rfk in self.resource.flavors.keys():
            rf = self.resource.flavors[rfk]
            if rfk not in _flavors.keys():
                rf.status = "disabled"

                rf.last_update = time.time()
                self.logger.info("flavor (" + rfk + ":" + rf.flavor_id +
                                 ") removed")

        for fk in _flavors.keys():
            f = _flavors[fk]
            rf = self.resource.flavors[fk]
            if self._check_flavor_spec_update(f, rf) is True:
                rf.last_update = time.time()
                self.logger.info("flavor (" + fk + ":" + rf.flavor_id +
                                 ") spec updated")

    def _check_flavor_spec_update(self, _f, _rf):
        '''Check flavor's spec consistency.'''

        spec_updated = False

        if _f.status != _rf.status:
            _rf.status = _f.status
            spec_updated = True

        if (_f.vCPUs != _rf.vCPUs or _f.mem_cap != _rf.mem_cap or
           _f.disk_cap != _rf.disk_cap):
            _rf.vCPUs = _f.vCPUs
            _rf.mem_cap = _f.mem_cap
            _rf.disk_cap = _f.disk_cap
            spec_updated = True

        for sk in _f.extra_specs.keys():
            if sk not in _rf.extra_specs.keys():
                _rf.extra_specs[sk] = _f.extra_specs[sk]
                spec_updated = True

        for rsk in _rf.extra_specs.keys():
            if rsk not in _f.extra_specs.keys():
                del _rf.extra_specs[rsk]
                spec_updated = True

        return spec_updated
