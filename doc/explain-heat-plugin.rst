# OpenStack Heat Resource Plugins

[Valet](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/allegro/atRef/refs/heads/master/renderFile/README.md) works with OpenStack Heat through the use of Resource Plugins. This document explains what they are and how they work. As new plugins become formally introduced, they will be added here.

The following is current as of Valet Release 1.0.

## ATT::Valet::GroupAssignment

*Formerly ATT::Valet::ResourceGroup*

A Group Assignment describes one or more resources assigned to a particular type of group. Assignments can reference other assignments, so long as there are no circular references.

There are three types of groups: affinity, diversity, and exclusivity. Exclusivity groups have a unique name, assigned through Valet.

This resource is purely informational in nature and makes no changes to heat, nova, or cinder. The Valet Heat Lifecycle Plugin passes this information to the optimizer.

### Properties

``group_name`` (String)

* Name of group. Required for exclusivity groups. NOT permitted for affinity and diversity groups at this time.
* Can be updated without replacement.

``group_type`` (String)

* Type of group.
* Allowed values: affinity, diversity, exclusivity
* Can be updated without replacement.
* Required property.

``level`` (String)

* Level of relationship between resources.
* See list below for allowed values.
* Can be updated without replacement.
* Required property.

``resources`` (List)

* List of associated resource IDs.
* Can be updated without replacement.
* Required property.

#### Levels

* ``rack``: Across racks, one resource per host.
* ``host``: All resources on a single host.

### Attributes

None. (There is a ``show`` attribute but it is not intended for production use.)

### Example

Given a Heat template with two server resources, declare an affinity between them at the rack level:

```json
  resources:
    server_affinity:
      type: ATT::Valet::GroupAssignment
      properties:
        group_type: affinity
        level: rack
        resources:
        - {get_resource: server1}
        - {get_resource: server2}
```

### Plugin Schema

Use the OpenStack Heat CLI command `heat resource-type-show ATT::Valet::GroupAssignment` to view the schema.

```json
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
    "level": {
      "description": "Level of relationship between resources.", 
      "required": true, 
      "update_allowed": true, 
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
    }, 
    "resources": {
      "type": "list", 
      "required": true, 
      "update_allowed": true, 
      "description": "List of one or more resource IDs.", 
      "immutable": false
    }, 
    "group_type": {
      "description": "Type of group.", 
      "required": true, 
      "update_allowed": true, 
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
    "group_name": {
      "type": "string", 
      "required": false, 
      "update_allowed": true, 
      "description": "Group name. Required for exclusivity groups.", 
      "immutable": false
    }
  }, 
  "resource_type": "ATT::Valet::GroupAssignment"
}
```

### Future Work

The following sections are proposals and *not* implemented. It is provided to aid in ongoing open discussion.

#### Resource Namespace Changes

The resource namespace may change to ``OS::Valet`` in future releases.

#### Resource Properties

Resource property characteristics are under ongoing review and subject to revision.

#### Volume Resource Support

Future placement support will formally include block storage services (e.g., Cinder).

#### Additional Scheduling Levels

Future levels could include:

* ``cluster``: Across a cluster, one resource per cluster.
* ``any``: Any level.

#### Proposed Notation for 'diverse-affinity'

Suppose we are given a set of server/volume pairs, and we'd like to treat each pair as an affinity group, and then treat all affinity groups diversely. The following notation makes this diverse affinity pattern easier to describe, with no name repetition.

```json
  resources:
    my_group_assignment:
      type: ATT::Valet::GroupAssignment
      properties:
        group_name: my_even_awesomer_group
        group_type: diverse-affinity
        level: host
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
