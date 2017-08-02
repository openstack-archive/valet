#!/bin/python


from valet.engine.optimizer.app_manager.group import Group, LEVEL
from valet.engine.optimizer.app_manager.vm import VM


def get_group_of_vm(_vmk, _groups):
    '''Get group where vm is located.'''
    group = None
    for gk, g in _groups.iteritems():
        if check_vm_grouping(g, _vmk) is True:
            group = g
            break
    return group


def check_vm_grouping(_vg, _vmk):
    '''Check recursively if vm is located in the group.'''
    exist = False
    for sgk, sg in _vg.subgroups.iteritems():
        if isinstance(sg, VM):
            if sgk == _vmk:
                exist = True
                break
        elif isinstance(sg, Group):
            if check_vm_grouping(sg, _vmk) is True:
                exist = True
                break
    return exist


def get_child_vms(_vg, _vm_list):
    for sgk, sg in _vg.subgroups.iteritems():
        if isinstance(sg, VM):
            _vm_list.append(sgk)
        else:
            get_child_vms(sg, _vm_list)


def get_node_resource_of_level(_n, _level, _avail_hosts):
    '''Get the name of resource in the level for the planned vm or affinity group.'''

    resource_name = None

    if isinstance(_n, VM):
        resource_name = get_resource_of_level(_n.host, _level, _avail_hosts)
    elif isinstance(_n, Group):
        if _n.level == "host":
            resource_name = get_resource_of_level(_n.host, _level, _avail_hosts)
        elif _n.level == "rack":
            if _level == "rack":
                resource_name = _n.host
            elif _level == "cluster":
                for _, ah in _avail_hosts.iteritems():
                    if ah.rack_name == _n.host:
                        resource_name = ah.cluster_name
                        break
        elif _n.level == "cluster":
            if _level == "cluster":
                resource_name = _n.host

    return resource_name


def get_resource_of_level(_host_name, _level, _avail_hosts):
    '''Get resource name of level for the host.'''
    resource_name = None
    if _level == "host":
        resource_name = _host_name
    elif _level == "rack":
        if _host_name in _avail_hosts.keys():
            resource_name = _avail_hosts[_host_name].rack_name
    elif _level == "cluster":
        if _host_name in _avail_hosts.keys():
            resource_name = _avail_hosts[_host_name].cluster_name
    return resource_name


def get_next_placements(_n, _level):
    '''Get vms and groups to be handled in the next level search.'''

    vms = {}
    groups = {}
    if isinstance(_n, Group):
        if LEVEL.index(_n.level) < LEVEL.index(_level):
            groups[_n.orch_id] = _n
        else:
            for _, sg in _n.subgroups.iteritems():
                if isinstance(sg, VM):
                    vms[sg.orch_id] = sg
                elif isinstance(sg, Group):
                    groups[sg.orch_id] = sg
    else:
        vms[_n.orch_id] = _n

    return (vms, groups)
