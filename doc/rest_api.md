# Placement API v1 - CURRENT

Determines placement for cloud resources.

## General API information

Authenticated calls that target a known URI but that use an HTTP method the implementation does not support return a 405 Method Not Allowed status. In addition, the HTTP OPTIONS method is supported for each known URI. In both cases, the Allow response header indicates the supported HTTP methods. See the [API Errors](#api-errors) section for more information about the error response structure.


## API versions

### List all Placement API versions

**GET** `/`

**Normal response codes:** 200

```json
{
  "versions": [
    {
      "status": "CURRENT",
      "id": "v1.0",
      "links": [
        {
          "href": "http://127.0.0.1:8090/v1/",
          "rel": "self"
        }
      ]
    }
  ]
}
```

This operation does not accept a request body.

## Groups

### Create a group

**POST** `/v1/groups`

**Normal response codes:** 201
**Error response codes:** badRequest (400), unauthorized (401), internalServerError (500)

#### Request parameters

| Parameter | Style | Type | Description |
|-----------|-------|------|-------------|
| description | plain | xsd:string | A description for the new group. |
| name | plain | xsd:string | A name for the new group. Must only contain letters, numbers, hypens, full stops, underscores, and tildes (RFC 3986, Section 2.3). This parameter is immutable. |
| type | plain | xsd:string | A type for the new group. Presently, the only valid value is `exclusivity`. This parameter is immutable. |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| description | plain | xsd:string | The group description.                            |
| id          | plain | csapi:UUID | The UUID of the group.                            |
| members     | plain | xsd:list   | A list of group members. Initially empty.         |
| name        | plain | xsd:string | The group name.                                   |
| type        | plain | xsd:string | The group type.                                   |

```json
{
  "name": "group",
  "description": "My Awesome Group",
  "type": "exclusivity"
}
```

```json
{
  "description": "My Awesome Group",
  "type": "exclusivity",
  "id": "7de4790e-08f2-44b7-8332-7a41fab36a41",
  "members": [],
  "name": "group"
}
```

* * * * * * * * * * *

### List active groups

**GET** `/v1/groups`

**Normal response codes:** 200
**Error response codes:** unauthorized (401)

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| description | plain | xsd:string | The group description.                            |
| id          | plain | csapi:UUID | The UUID of the group.                            |
| members     | plain | xsd:list   | A list of group members. Initially empty.         |
| name        | plain | xsd:string | The group name.                                   |
| type        | plain | xsd:string | The group type.                                   |

This operation does not accept a request body.

```json
{
  "groups": [
    {
      "description": "My Awesome Group",
      "type": "exclusivity",
      "id": "7de4790e-08f2-44b7-8332-7a41fab36a41",
      "members": [],
      "name": "group"
    }
  ]
}
```

* * * * * * * * * * *

### Show group details

**GET** `/v1/groups/{group_id}`

**Normal response codes:** 200
**Error response codes:** unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| description | plain | xsd:string | The group description.                            |
| id          | plain | csapi:UUID | The UUID of the group.                            |
| members     | plain | xsd:list   | A list of group members.                          |
| name        | plain | xsd:string | The group name.                                   |
| type        | plain | xsd:string | The group type.                                   |

```json
{
  "group": {
    "description": "My Awesome Group",
    "type": "exclusivity",
    "id": "7de4790e-08f2-44b7-8332-7a41fab36a41",
    "members": [],
    "name": "group"
  }
}
```

This operation does not accept a request body.

* * * * * * * * * * *

### Update a group

**PUT** `/v1/groups/{group_id}`

**Normal response codes:** 201
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| description | plain | xsd:string | A description for the group. Replaces the original description. |
| group_id | plain | csapi:UUID | The UUID of the group. |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| description | plain | xsd:string | The group description.                            |
| id          | plain | csapi:UUID | The UUID of the group.                            |
| members     | plain | xsd:list   | A list of group members.                          |
| name        | plain | xsd:string | The group name.                                   |
| type        | plain | xsd:string | The group type.                                   |

```json
{
  "description": "My Extra Awesome Group"
}
```

```json
{
  "description": "My Extra Awesome Group",
  "type": "exclusivity",
  "id": "7de4790e-08f2-44b7-8332-7a41fab36a41",
  "members": [],
  "name": "group"
}
```

* * * * * * * * * * *

### Delete a group

**DELETE** `/v1/groups/{group_id}`

**Normal response codes:** 204
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404), conflict (409)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |

This operation does not accept a request body and does not return a response body.

* * * * * * * * * * *

### Add members to a group

**PUT** `/v1/groups/{group_id}/members`

**Normal response codes:** 201
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404), conflict (409)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |
| members     | plain | xsd:list   | A list of group members. This is added to any previous list of members. All members must be valid tenant UUIDs. |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| description | plain | xsd:string | The group description.                            |
| id          | plain | csapi:UUID | The UUID of the group.                            |
| members     | plain | xsd:list   | A list of group members.                          |
| name        | plain | xsd:string | The group name.                                   |
| type        | plain | xsd:string | The group type.                                   |

```json
{
  "members": [
    "b7d0e9b175294b649464caa3411adb3f"
  ]
}
```

```json
{
  "description": "My Awesome Group",
  "type": "exclusivity",
  "id": "bf49803b-48b6-4a13-9191-98dde1dbd5e4",
  "members": [
    "b7d0e9b175294b649464caa3411adb3f",
    "65c3e5ee5ee0428caa5e5275c58ead61"
  ],
  "name": "group"
}
```

* * * * * * * * * * *

### Verify membership in a group

**GET** `/v1/groups/{group_id}/members/{member_id}`

**Normal response codes:** 204
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |
| member_id   | plain | csapi:UUID | The UUID of one potential group member. Members are tenant UUIDs. |

This operation does not accept a request body and does not return a response body.

* * * * * * * * * * *

### Delete member from a group

**DELETE** `/v1/groups/{group_id}/members/{member_id}`

**Normal response codes:** 204
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |
| member_id   | plain | csapi:UUID | The UUID of one potential group member. Members are tenant UUIDs. |

This operation does not accept a request body and does not return a response body.

* * * * * * * * * * *

### Delete all members from a group

**DELETE** `/v1/groups/{group_id}/members`

**Normal response codes:** 204
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |

This operation does not accept a request body and does not return a response body.

## Status

### Get summary status of all subsystems

**HEAD** `/v1/status`

**Normal response codes:** 200
**Error response codes:** internalServerError (500)

This operation does not accept a request body and does not return a response body.

### List detailed status of all subsystems

**GET** `/v1/status`

**Normal response codes:** 200
**Error response codes:** internalServerError (500)

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| status      | plain | xsd:dict   | A dictionary of statuses from each subsystem, keyed by name. |

This operation does not accept a request body.

```json
{
  "status": {
    "ostro": {
      "status": {
        "message": "ping",
        "type": "ok"
      },
      "resources": {
        "ip": "135.197.226.83"
      }
    }
  }
}
```

## Placements

### List active placements

**GET** `/v1/placements`

**Normal response codes:** 200
**Error response codes:** unauthorized (401)

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| id          | plain | csapi:UUID | The UUID of the placement.                        |
| location    | plain | xsd:string | The placement location of the resource.           |
| name        | plain | xsd:string | The name of the resource.                         |
| orchestration_id | plain | csapi:UUID | The UUID provided by an orchestration engine (e.g., heat-engine) prior to instantiation of the resource.             |
| resource_id | plain | csapi:UUID | The physical UUID of the resource. The value is unknown until a placement has been reserved for the first time. |
| plan_id     | plain | csapi:UUID | The UUID of the plan.                             |
| reserved    | plain | xsd:boolean | Set to true if the placement was successfully reserved. |

This operation does not accept a request body.

```json
{
  "placements": [
    {
      "plan_id": "e01ae778-52c8-4e52-9f32-a486584f0e89",
      "name": "my-instance-1",
      "orchestration_id": "f8cfab7e-83d0-4a7d-8551-905ea8a43a39",
      "resource_id": "240b2fe5-2e01-4cfb-982c-67e3f1553386",
      "location": "qos104",
      "reserved": true,
      "id": "55f4aee9-b7df-44d0-85d3-3234c08dbfb4"
    },
    {
      "plan_id": "c8b8e9d9-227f-4652-8a18-523cd37b86c0",
      "name": "ad_hoc_instance",
      "orchestration_id": "23ffc206-cb57-4b99-9393-6e01837855bc",
      "resource_id": null,
      "location": "qos101",
      "reserved": false,
      "id": "dbbc9ae2-3ba2-4409-8765-03cdbfcd0dcb"
    }
  ]
}
```

### Show placement details with no reservation

**GET** `/v1/placements/{placement_id}`

**Normal response codes:** 200
**Error response codes:** unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| placement_id | plain | csapi:UUID | The UUID of the placement or its associated orchestration UUID. |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| id          | plain | csapi:UUID | The UUID of the placement.                        |
| location    | plain | xsd:string | The placement location of the resource.           |
| name        | plain | xsd:string | The name of the resource.                         |
| orchestration_id | plain | csapi:UUID | The UUID provided by an orchestration engine (e.g., heat-engine) prior to instantiation of the resource.             |
| resource_id | plain | csapi:UUID | The physical UUID of the resource. The value is unknown until a placement has been reserved for the first time. |
| plan_id     | plain | csapi:UUID | The UUID of the plan.                             |
| reserved    | plain | xsd:boolean | Set to true if the placement was successfully reserved. |

This operation does not accept a request body.

```json
{
  "placement": {
    "plan_id": "a78d1936-0b63-4ce3-9450-832f71ebf160",
    "name": "my_instance",
    "orchestration_id": "b71bedad-dd57-4942-a7bd-ab074b72d652",
    "resource_id": null,
    "location": "qos105",
    "reserved": false,
    "id": "b7116936-5210-448a-b21f-c35f33e9bcc2"
  }
}
```

### Reserve a placement with possible replanning

**POST** `/v1/placements/{placement_id}`

**Normal response codes:** 201
**Error response codes:** unauthorized (401), itemNotFound (404), internalServerError (500)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| locations | plain | xsd:list | A list of available locations. If the placement was not planned in one of these locations, the placement for this resource (and any others in the same plan not yet reserved) will be replanned on-the-fly. |
| resource_id  | plain | csapi:UUID | The physical UUID of the resource.               |
| placement_id | plain | csapi:UUID | The UUID of the placement or its associated orchestration UUID. |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| id          | plain | csapi:UUID | The UUID of the placement.                        |
| location    | plain | xsd:string | The placement location of the resource.           |
| name        | plain | xsd:string | The name of the resource.                         |
| orchestration_id | plain | csapi:UUID | The UUID provided by an orchestration engine (e.g., heat-engine) prior to instantiation of the resource.             |
| resource_id | plain | csapi:UUID | The physical UUID of the resource.                |
| plan_id     | plain | csapi:UUID | The UUID of the plan.                             |
| reserved    | plain | xsd:boolean | Set to true if the placement was successfully reserved. |

```json
{
  "locations": ["qos101", "qos102", "qos104", "qos106", "qos107"],
  "resource_id": "240b2fe5-2e01-4cfb-982c-67e3f1553386"
}
```

```json
{
  "placement": {
    "plan_id": "a78d1936-0b63-4ce3-9450-832f71ebf160",
    "name": "my_instance",
    "orchestration_id": "b71bedad-dd57-4942-a7bd-ab074b72d652",
    "resource_id": "240b2fe5-2e01-4cfb-982c-67e3f1553386",
    "location": "qos101",
    "reserved": true,
    "id": "b7116936-5210-448a-b21f-c35f33e9bcc2"
  }
}
```

## Plans

### Create a plan

**POST** `/v1/plans`

**Normal response codes:** 201
**Error response codes:** badRequest (400), unauthorized (401), internalServerError (500)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| plan_name   | plain | xsd:string | The name of the plan.                             |
| resources   | plain | xsd:dict   | A dictionary of resources to be planned. Each is keyed by an orchestration uuid. This is a UUID provided by an orchestration engine (e.g., heat-engine) prior to instantiation of a resource. The dictionary contains three keys: |
|             |       |            | **name**: resource name                             |
|             |       |            | **type**: resource type (in Heat Orchestration Template format) |
|             |       |            | **properties**: resource properties (in Heat Orchestration Template format)                |
| stack_id    | plain | csapi:UUID | The UUID of the stack.                            |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| stack_id    | plain | csapi:UUID | The UUID of the stack.                            |
| id          | plain | csapi:UUID | The UUID of the plan.                             |
| placements  | plain | xsd:dict   | A dictionary of planned resources. Each is keyed by an orchestration uuid. This is a UUID provided by an orchestration engine (e.g., heat-engine) prior to instantiation of a resource. The dictionary contains two keys:                 |
|             |       |            | **location**: resource placement                    |
|             |       |            | **name**: resource name                             |
| name        | plain | xsd:string | The name of the plan.                             |

```json
{
  "plan_name": "e624474b-fc80-4053-ab5f-45cc1030e692",
  "resources": {
    "b71bedad-dd57-4942-a7bd-ab074b72d652": {
      "properties": {
        "flavor": "m1.small",
        "image": "ubuntu12_04",
        "key_name": "demo",
        "networks": [
          {
            "network": "demo-net"
          }
        ]
      },
      "type": "OS::Nova::Server",
      "name": "my_instance"
    }
  },
  "stack_id": "e624474b-fc80-4053-ab5f-45cc1030e692"
}
```

```json
{
  "plan" {
    "stack_id": "e624474b-fc80-4053-ab5f-45cc1030e692",
    "id": "1853a7e7-0075-465b-9019-8908db680f2e",
    "placements": {
      "b71bedad-dd57-4942-a7bd-ab074b72d652": {
        "location": "qos103",
        "name": "my_instance"
      }
    },
    "name": "e624474b-fc80-4053-ab5f-45cc1030e692"
  }
}
```

### List active plans

**GET** `/v1/plans`

**Normal response codes:** 200
**Error response codes:** unauthorized (401)

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| stack_id    | plain | csapi:UUID | The UUID of the stack.                            |
| id          | plain | csapi:UUID | The UUID of the plan.                             |
| placements  | plain | xsd:dict   | A dictionary of planned resources. Each is keyed by an orchestration uuid. This is a UUID provided by an orchestration engine (e.g., heat) prior to instantiation of a resource. The dictionary contains two keys:                 |
|             |       |            | **location**: resource placement                    |
|             |       |            | **name**: resource name                             |
| name        | plain | xsd:string | The name of the plan.                             |

This operation does not accept a request body.

```json
{
  "plans": [
    {
      "stack_id": "e624474b-fc80-4053-ab5f-45cc1030e692",
      "id": "f1a81397-e4d4-46de-8445-dfadef633beb",
      "placements": {
        "b71bedad-dd57-4942-a7bd-ab074b72d652": {
          "location": "qos101",
          "name": "my_instance"
        }
      },
      "name": "e624474b-fc80-4053-ab5f-45cc1030e692"
    },
    {
      "stack_id": "8e06301e-7375-465f-9fc7-70fb13763927",
      "id": "f56391b0-61bb-4e18-b9ca-23c0ff2e4508",
      "placements": {
        "8e06301e-7375-465f-9fc7-70fb13763927": {
          "location": "qos101",
          "name": "ad_hoc_instance"
        }
      },
      "name": "8e06301e-7375-465f-9fc7-70fb13763927"
    }
  ]
}
```

### Show plan details

**GET** `/v1/plans/{plan_id}`

**Normal response codes:** 200
**Error response codes:** unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| plan_id     | plain | csapi:UUID | The UUID of the plan or its associated stack UUID. |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| stack_id    | plain | csapi:UUID | The UUID of the stack.                            |
| id          | plain | csapi:UUID | The UUID of the plan.                             |
| placements  | plain | xsd:dict   | A dictionary of planned resources. Each is keyed by an orchestration UUID. This is provided by an orchestration engine (e.g., heat) prior to instantiation of a resource. The dictionary contains two keys:                 |
|             |       |            | **location**: resource placement                    |
|             |       |            | **name**: resource name                             |
| name        | plain | xsd:string | The name of the plan.                             |

This operation does not accept a request body.

```json
{
  "plan": {
    "stack_id": "e624474b-fc80-4053-ab5f-45cc1030e692",
    "id": "1853a7e7-0075-465b-9019-8908db680f2e",
    "placements": {
      "b71bedad-dd57-4942-a7bd-ab074b72d652": {
        "location": "qos103",
        "name": "my_instance"
      }
    },
    "name": "e624474b-fc80-4053-ab5f-45cc1030e692"
  }
}
```

### Update a plan

**PUT** `/v1/plans/{plan_id}`

**Normal response codes:** 201
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| plan_id     | plain | csapi:UUID | The UUID of the plan or its associated stack id.  |
| action      | plain | xsd:string | The plan update action. There is only one valid option at this time.                              |
|             |       |            | **migrate**: Replan a single resource               |
| excluded_hosts | plain | xsd:list | A list of hosts that must not be considered when replanning |
| resources   | plain | xsd:list | When action="migrate" this is a list of length one. The lone item is either a physical resource id or an orchestration id. |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| stack_id    | plain | csapi:UUID | The UUID of the stack.                            |
| id          | plain | csapi:UUID | The UUID of the plan.                             |
| placements  | plain | xsd:dict   | A dictionary of planned resources. Each is keyed by an orchestration uuid. This is provided by an orchestration engine (e.g., heat) prior to instantiation of a resource. The dictionary contains two keys:                 |
|             |       |            | **location**: resource placement                    |
|             |       |            | **name**: resource name                             |

```json
{
  "action": "migrate",
  "excluded_hosts": ["qos104", "qos106", "qos107"],
  "resources": ["b71bedad-dd57-4942-a7bd-ab074b72d652"]
}
```

```json
{
  "plan": {
    "stack_id": "e624474b-fc80-4053-ab5f-45cc1030e692",
    "id": "a78d1936-0b63-4ce3-9450-832f71ebf160",
    "placements": {
      "b71bedad-dd57-4942-a7bd-ab074b72d652": {
        "location": "qos105",
        "name": "my_instance"
      }
    },
    "name": "e624474b-fc80-4053-ab5f-45cc1030e692"
  }
}
```

### Delete a plan

**DELETE** `/v1/plans/{plan_id}`

**Normal response codes:** 204
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| plan_id     | plain | csapi:UUID | The UUID of the plan or its associated stack id.  |

This operation does not accept a request body and does not return a response body.

## API Errors

In the event of an error with a status other than unauthorized (401), a detailed repsonse body is returned.

### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| title       | plain | xsd:string | Human-readable name.                              |
| explanation | plain | xsd:string | Detailed explanation with remediation (if any).   |
| code        | plain | xsd:int    | HTTP Status Code.                                 |
| error       | plain | xsd:dict   | Error dictionary. Keys include **message**, **traceback** (currently reserved / unused), and **type**. |
| message     | plain | xsd:string | Internal error message.                           |
| traceback   | plain | xsd:string | Python traceback (if available).                  |
| type        | plain | xsd:string | HTTP Status class name (from python-webob)        |

#### Examples

A group with the name "gro up" is considered a bad request because the name contains a space.

```json
{
  "title": "Bad Request",
  "explanation": "-> name -> gro up did not pass validation against callable: group_name_type (must contain only uppercase and lowercase letters, decimal digits, hyphens, periods, underscores, and tildes [RFC 3986, Section 2.3])",
  "code": 400,
  "error": {
    "message": "The server could not comply with the request since it is either malformed or otherwise incorrect.",
    "traceback": null,
    "type": "HTTPBadRequest"
  }
}
```

The HTTP COPY method was attempted but is not allowed.

```json
{
  "title": "Method Not Allowed",
  "explanation": "The COPY method is not allowed.",
  "code": 405,
  "error": {
    "message": "The server could not comply with the request since it is either malformed or otherwise incorrect.",
    "traceback": null,
    "type": "HTTPMethodNotAllowed"
  }
}
```

A Valet Group was not found.

```json
{
  "title": "Not Found",
  "explanation": "Group not found",
  "code": 404,
  "error": {
    "message": "The resource could not be found.",
    "traceback": null,
    "type": "HTTPNotFound"
  }
}
```
