#!/bin/python


import json
import six
import traceback

from valet.engine.resource_manager.resources.datacenter import Datacenter


class Bootstrapper(object):
    '''Bootstrap valet-engine.'''

    def __init__(self, _resource, _db, _logger):
        self.logger = _logger
        self.resource = _resource
        self.db = _db

        self.phandler = None

    def set_handlers(self, _placement_handler):
        self.phandler = _placement_handler

    def load_data(self, _compute, _topology, _metadata):
        '''Load all required datacenter resource information.'''

        try:
            resource_status = self.db.get_resource_status(self.resource.datacenter.name)
            if resource_status is None:
                return False

            if len(resource_status) > 0:
                self.resource.load_from_db(resource_status)

            self.logger.info("load data from other systems (e.g., nova)")

            if not _compute.set_hosts():
                return False

            if not _topology.set_topology():
                return False

            if not _metadata.set_groups():
                return False

            if not _metadata.set_flavors():
                return False

            self.resource.update_topology()

        except Exception:
            self.logger.critical("bootstrap failed: " + traceback.format_exc())

        return True

    def verify_pre_valet_placements(self):
        '''Mark if any pre-valet placements were not correctly placed.'''

        self.logger.info("verifying pre-valet placements")

        for hk, host in self.resource.hosts.iteritems():
            for vm_info in host.vm_list:
                if "metadata" in vm_info.keys():   # unknown pre-valet placement
                    placement = self.phandler.get_placement(vm_info["uuid"])
                    if placement is None:
                        return False
                    elif placement.uuid == "none":
                        status = "not existing vm"
                        self.logger.warn("invalid placement: " + status)
                        placement.status = status
                        if not self.phandler.store_placement(vm_info["uuid"], placement):
                            return False
                    else:
                        if placement.status != "verified":
                            (status, valet_group_list) = self._verify_pre_valet_placement(hk, vm_info)
                            if status is None:
                                return False
                            elif status == "verified":
                                placement.status = status
                                if not self.phandler.store_placement(vm_info["uuid"], placement):
                                    return False

                                if len(valet_group_list) > 0:
                                    host = self.resource.hosts[hk]
                                    # overwrite if vm exists
                                    self.resource.add_vm_to_groups(host, vm_info, valet_group_list)
                            else:
                                self.logger.warn("invalid placement: " + status)
                                placement.status = status
                                if not self.phandler.store_placement(vm_info["uuid"], placement):
                                    return False

        return True

    def _verify_pre_valet_placement(self, _hk, _vm_info):
        '''Mark if this pre-valet placement was not correctly placed.'''

        status = "verified"
        valet_group_list = []

        if len(_vm_info["metadata"]) == 0:
            status = self._verify_exclusivity(_hk)
        else:
            metadata = _vm_info["metadata"]

            for mk, md in metadata.iteritems():
                if mk == "valet":
                    group_list = []

                    if isinstance(md, six.string_types):
                        try:
                            groups_dict = json.loads(md)
                            if "groups" in groups_dict.keys():
                                group_list = groups_dict["groups"]
                        except Exception:
                            self.logger.error("valet metadata parsing: " + traceback.format_exc())
                            status = "wrong valet metadata format"
                            return (status, [])
                    else:
                        if "groups" in md.keys():
                            group_list = md["groups"]

                    for gk in group_list:
                        found = False
                        for leveled_gk, g in self.resource.groups.iteritems():
                            if g.group_type in ("EX", "DIV", "AFF") and leveled_gk.split(':')[1] == gk:
                                group_info = self.db.get_group(gk)
                                if group_info is None:
                                    return (None, [])
                                elif len(group_info) == 0:
                                    break

                                if group_info["members"] is not None and len(group_info["members"]) > 0:
                                    if "tenant_id" in _vm_info.keys():
                                        t = _vm_info["tenant_id"]
                                        if t not in group_info["members"]:
                                            status = "tenant(" + t + ") cannot use group(" + gk + ")"
                                            return (status, [])

                                valet_group_list.append(leveled_gk)
                                found = True
                                break

                        if not found:
                            self.logger.warn("unknown group(" + gk + ") was used")

            if len(valet_group_list) == 0:
                status = self._verify_exclusivity(_hk)
            else:
                for gk in valet_group_list:
                    group = self.resource.groups[gk]
                    if group.group_type == "EX" or group.group_type == "AFF":
                        status = self._verify_named_affinity(_hk, gk)
                        if status != "verified":
                            break
                    elif group.group_type == "DIV":
                        status = self._verify_named_diversity(_hk, gk)
                        if status != "verified":
                            break

        return (status, valet_group_list)

    def _verify_exclusivity(self, _hk):
        '''Verify if vm was incorrectly placed in an exclusivity group.'''

        host = self.resource.hosts[_hk]
        for gk, g in host.memberships.iteritems():
            if g.group_type == "EX" and gk.split(':')[0] == "host":
                return "incorrectly placed in exclusive host"

        if host.host_group is not None and host.host_group != "none" and host.host_group != "any":
            rack = host.host_group
            if not isinstance(rack, Datacenter):
                for gk, g in rack.memberships.iteritems():
                    if g.group_type == "EX" and gk.split(':')[0] == "rack":
                        return "incorrectly placed in exclusive rack"

                if rack.parent_resource is not None and \
                   rack.parent_resource != "none" and \
                   rack.parent_resource != "any":
                    cluster = rack.parent_resource
                    if not isinstance(cluster, Datacenter):
                        for gk, g in cluster.memberships.iteritems():
                            if g.group_type == "EX" and gk.split(':')[0] == "cluster":
                                return "incorrectly placed in exclusive cluster"

        return "verified"

    def _verify_named_affinity(self, _hk, _gk):
        '''Verify if vm was correctly placed in an exclusivity or affinity group.'''

        group = self.resource.groups[_gk]
        g_id = _gk.split(':')
        level = g_id[0]
        group_name = g_id[1]
        group_type = None
        if group.group_type == "EX":
            group_type = "exclusivity"
        else:
            group_type = "affinity"

        if level == "host":
            if _hk not in group.vms_per_host.keys():
                return "placed in non-" + group_type + " host of group (" + group_name + ")"

        elif level == "rack":
            host = self.resource.hosts[_hk]
            if host.host_group is not None and host.host_group != "none" and host.host_group != "any":
                rack = host.host_group
                if isinstance(rack, Datacenter):
                    return "placed in non-existing rack level " + group_type + " of group (" + group_name + ")"
                else:
                    if rack.name not in group.vms_per_host.keys():
                        return "placed in non-" + group_type + " rack of group (" + group_name + ")"
            else:
                return "placed in non-existing rack level " + group_type + " of group (" + group_name + ")"

        elif level == "cluster":
            host = self.resource.hosts[_hk]
            if host.host_group is not None and host.host_group != "none" and host.host_group != "any":
                rack = host.host_group
                if isinstance(rack, Datacenter):
                    return "placed in non-existing cluster level " + group_type + " of group (" + group_name + ")"
                else:
                    if rack.parent_resource is not None and \
                       rack.parent_resource != "none" and \
                       rack.parent_resource != "any":
                        cluster = rack.parent_resource
                        if isinstance(cluster, Datacenter):
                            return "placed in non-existing cluster level " + group_type
                        else:
                            if cluster.name not in group.vms_per_host.keys():
                                return "placed in non-" + group_type + " cluster of group (" + group_name + ")"
                    else:
                        return "placed in non-existing cluster level " + group_type
            else:
                return "placed in non-existing cluster level " + group_type

        else:
            return "unknown level"

        return "verified"

    def _verify_named_diversity(self, _hk, _gk):
        '''Verify if vm was correctly placed in a diversity group.'''

        group = self.resource.groups[_gk]
        g_id = _gk.split(':')
        level = g_id[0]
        group_name = g_id[1]

        if level == "host":
            if _hk in group.vms_per_host.keys():
                return "incorrectly placed in diversity host of group (" + group_name + ")"

        elif level == "rack":
            host = self.resource.hosts[_hk]
            if host.host_group is not None and host.host_group != "none" and host.host_group != "any":
                rack = host.host_group
                if isinstance(rack, Datacenter):
                    return "placed in non-existing rack level diversity of group (" + group_name + ")"
                else:
                    if rack.name in group.vms_per_host.keys():
                        return "placed in diversity rack of group (" + group_name + ")"
            else:
                return "placed in non-existing rack level diversity of group (" + group_name + ")"

        elif level == "cluster":
            host = self.resource.hosts[_hk]
            if host.host_group is not None and host.host_group != "none" and host.host_group != "any":
                rack = host.host_group
                if isinstance(rack, Datacenter):
                    return "placed in non-existing cluster level diversity of group (" + group_name + ")"
                else:
                    if rack.parent_resource is not None and \
                       rack.parent_resource != "none" and \
                       rack.parent_resource != "any":
                        cluster = rack.parent_resource
                        if isinstance(cluster, Datacenter):
                            return "placed in non-existing cluster level diversity of group (" + group_name + ")"
                        else:
                            if cluster.name in group.vms_per_host.keys():
                                return "placed in diversity cluster of group (" + group_name + ")"
                    else:
                        return "placed in non-existing cluster level diversity of group (" + group_name + ")"
            else:
                return "placed in non-existing cluster level diversity of group (" + group_name + ")"

        else:
            return "unknown level"

        return "verified"
