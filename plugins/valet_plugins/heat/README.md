# OpenStack Heat Resource Plugins

[Valet](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/allegro/atRef/refs/heads/master/renderFile/README.md) works with OpenStack Heat through the use of Resource Plugins. This document explains what they are and how they work. As new plugins become formally introduced, they will be added here.

**IMPORTANT**: Resources have been rearchitected. Types and properties have changed/moved!

## Example

An example is provided first, followed by more details about each resource.

Given a Heat template with two server resources, declare a group with rack-level affinity, then assign the servers to the group:

```json
  resources:
    affinity_group:
      type: OS::Valet::Group
      properties:
        name: my_vnf_rack_affinity
        type: affinity
        level: rack

    server_affinity:
      type: OS::Valet::GroupAssignment
      properties:
        group: {get_resource: affinity_group}
        resources:
        - {get_resource: server1}
        - {get_resource: server2}
```

## OS::Valet::Group

*This resource is under development and subject to rearchitecture. It is not yet supported within Heat templates. Users bearing an admin role may create and manage Groups using ``valet-api`` directly. Do NOT use OS::Valet::Group at this time.*

A Group is used to define a particular association amongst resources. Groups may be used only by their assigned members, currently identified by project (tenant) IDs.

There are three types of groups: affinity, diversity, and exclusivity.  There are two levels: host and rack.

All groups must have a unique name, regardless of how they were created and regardless of membership.

The user's project (tenant) id is automatically added to the member list upon creation. However, there is no group owner. Any member can edit or delete the group. If all members are removed, only a user bearing an admin role can edit or remove the group.

This resource is purely informational in nature and makes no changes to heat, nova, or cinder. Instead, the Valet Heat stack lifecycle plugin intercepts Heat's create/update/delete operations and invokes valet-api as needed.

### Properties

``name`` (String)

* Name of group.
* Required property.

``description`` (String)

* Description of group.

``type`` (String)

* Type of group.
* Allowed values: affinity, diversity, exclusivity (see "Types" for details)
* Required property.

``level`` (String)

* Level of relationship between resources.
* Allowed values: rack, host (see "Levels" for details)
* Required property.

``members`` (List)

* List of group members.
* Use project (tenant) IDs.
* A user with admin role can add/remove any project ID.
* Creator's project ID is automatically added.

#### Types

* ``affinity``: Same level
* ``diversity``: Different levels (aka "anti-affinity")
* ``exclusivity``: Same level with exclusive use

#### Levels

* ``rack``: Across racks, one resource per host.
* ``host``: All resources on a single host.

### Attributes

None. (There is a ``show`` attribute but it is not intended for production use.)

### Plugin Schema

```json
$ heat resource-type-show OS::Valet::Group
{
  "support_status": {
    "status": "SUPPORTED",
    "message": null,
    "version": null,
    "previous_status": null
  },
  "attributes": {
    "show": {
      "type": "map",
      "description": "Detailed information about resource."
    }
  },
  "properties": {
    "name": {
      "description": "Name of group.",
      "required": true,
      "update_allowed": false,
      "type": "string",
      "immutable": false,
      "constraints": [
        {
          "custom_constraint": "valet.group_name"
        }
      ]
    },
    "type": {
      "description": "Type of group.",
      "required": true,
      "update_allowed": false,
      "type": "string",
      "immutable": false,
      "constraints": [
        {
          "allowed_values": [
            "affinity",
            "diversity",
            "exclusivity"
          ]
        }
      ]
    },
    "description": {
      "type": "string",
      "required": false,
      "update_allowed": true,
      "description": "Description of group.",
      "immutable": false
    },
    "members": {
      "type": "list",
      "required": false,
      "update_allowed": true,
      "description": "List of one or more member IDs allowed to use this group.",
      "immutable": false
    },
    "level": {
      "description": "Level of relationship between resources.",
      "required": true,
      "update_allowed": false,
      "type": "string",
      "immutable": false,
      "constraints": [
        {
          "allowed_values": [
            "host",
            "rack"
          ]
        }
      ]
    }
  },
  "resource_type": "OS::Valet::Group"
}
```

## OS::Valet::GroupAssignment

*This resource is under development and subject to rearchitecture. The ``type`` and ``level`` properties are no longer available and are now part of Groups. Users bearing an admin role may create and manage Groups using ``valet-api`` directly.*

A Group Assignment describes one or more resources (e.g., Server) assigned to a particular group.

**Caution**: It is possible to declare multiple GroupAssignment resources referring to the same servers, which can lead to problems when one GroupAssignment is updated and a duplicate server reference is removed.

This resource is purely informational in nature and makes no changes to heat, nova, or cinder. Instead, the Valet Heat stack lifecycle plugin intercepts Heat's create/update/delete operations and invokes valet-api as needed.

### Properties

``group`` (String)

* A reference to a previously defined group.
* This can be the group resource ID, the group name, or a HOT ``get_resource`` reference.
* Required property.

``resources`` (List)

* List of resource IDs to assign to the group.
* Can be updated without replacement.
* Required property.

### Attributes

None. (There is a ``show`` attribute but it is not intended for production use.)

### Plugin Schema

```json
$ heat resource-type-show OS::Valet::GroupAssignment
{
  "support_status": {
    "status": "SUPPORTED",
    "message": null,
    "version": null,
    "previous_status": null
  },
  "attributes": {
    "show": {
      "type": "map",
      "description": "Detailed information about resource."
    }
  },
  "properties": {
    "group": {
      "type": "string",
      "required": false,
      "update_allowed": false,
      "description": "Group reference.",
      "immutable": false
    },
    "resources": {
      "type": "list",
      "required": true,
      "update_allowed": true,
      "description": "List of one or more resource IDs.",
      "immutable": false
    }
  },
  "resource_type": "OS::Valet::GroupAssignment"
}
```

## Future Work

The following sections are proposals and *not* implemented. It is provided to aid in ongoing open discussion.

### Resource Properties

Resource property characteristics are under ongoing review and subject to revision.

### Volume Resource Support

Future placement support will formally include block storage services (e.g., Cinder).

### Additional Scheduling Levels

Future group levels could include:

* ``cluster``: Across a cluster, one resource per cluster.
* ``any``: Any level.

### Proposed Notation for 'diverse-affinity'

Suppose we are given a set of server/volume pairs, and we'd like to treat each pair as an affinity group, and then treat all affinity groups diversely. The following notation makes this diverse affinity pattern easier to describe, with no name repetition.

```json
  resources:
    my_group:
      type: OS::Valet::Group
      properties:
        name: my_even_awesomer_group
        type: diverse-affinity
        level: host

    my_group_assignment:
      type: OS::Valet::GroupAssignment
      properties:
        group: {get_resource: my_group}
        resources:
        - - {get_resource: server1}
          - {get_resource: volume1}
        - - {get_resource: server2}
          - {get_resource: volume2}
        - - {get_resource: server3}
          - {get_resource: volume3}
```

In this example, ``server1``/``volume1``, ``server2``/``volume2``, and ``server3``/``volume3`` are each treated as their own affinity group. Then, each of these affinity groups is treated as a diversity group. The dash notation is specific to YAML (a superset of JSON and the markup language used by Heat).

Given a hypothetical example of a Ceph deployment with three monitors, twelve OSDs, and one client, each paired with a volume, we would only need to specify three Heat resources instead of eighteen.

## Contact

Joe D'Andrea <jdandrea@research.att.com>
