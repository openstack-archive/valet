.. -*- rst -*-

======
Groups
======

Create a group
==============

.. rest_method:: POST /v1/groups

Creates a group.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 201

.. rest_status_code:: error ../status.yaml

   - 400
   - 401
   - 500

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - name: group_name
   - description: group_description
   - type: group_type

Request Example
---------------

.. literalinclude:: ./samples/create_group_request.json
   :language: json

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - description: group_description
   - id: group_id_body
   - members: group_members
   - name: group_name
   - type: group_type

Response Parameters
-------------------

.. literalinclude:: ./samples/create_group_response.json
   :language: json


List groups
===========

.. rest_method:: GET /v1/groups

Lists groups.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 200

.. rest_status_code:: error ../status.yaml

   - 401

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - description: group_description
   - id: group_id_body
   - members: group_members
   - name: group_name
   - type: group_type

Response Example
----------------

.. literalinclude:: ./samples/list_groups_response.json
   :language: json

Show group details
==================

.. rest_method:: GET /v1/groups/{group_id}

Show group details. This operation does not accept a request body.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 200

.. rest_status_code:: error ../status.yaml

   - 401
   - 404

Request Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - group_id: group_id_query

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - description: group_description
   - id: group_id_body
   - members: group_members
   - name: group_name
   - type: group_type

Response Example
----------------

.. literalinclude:: ./samples/show_group_response.json
   :language: json


Update a group
==============

.. rest_method:: PUT /v1/groups/{group_id}

Updates a group. Replaces the original description.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 201

.. rest_status_code:: error ../status.yaml

   - 400
   - 401
   - 404

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - group_id: group_id_query
   - description: group_description

Response Example
----------------

.. literalinclude:: ./samples/update_group_request.json
   :language: json

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - description: group_description
   - id: group_id_body
   - members: group_members
   - name: group_name
   - type: group_type

Response Example
----------------

.. literalinclude:: ./samples/update_group_response.json
   :language: json

Delete group
============

.. rest_method:: DELETE /v1/groups/{group_id}

Delete a group. This operation does not accept a request body and does not
return a response body.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 204

.. rest_status_code:: error ../status.yaml

   - 400
   - 401
   - 404
   - 409

Request Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - group_id: group_id_query

Add members to group
====================

.. rest_method:: PUT /v1/groups/{group_id}/members

Adds a list of group members to any previous list of members.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 201

.. rest_status_code:: error ../status.yaml

   - 400
   - 401
   - 404
   - 409

Request Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - group_id: group_id_query
   - members: group_members

Response Example
----------------

.. literalinclude:: ./samples/add_members_request.json
   :language: json

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - description: group_description
   - id: group_id_body
   - members: group_members
   - name: group_name
   - type: group_type

Response Example
----------------

.. literalinclude:: ./samples/add_members_response.json
   :language: json

Verify membership in a group
============================

.. rest_method:: GET /v1/groups/{group_id}/members/{member_id}

This operation does not accept a request body and does not return a response
body.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 200

.. rest_status_code:: error ../status.yaml

   - 400
   - 401
   - 404

Request Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - group_id: group_id_query
   - member_id: member_id_query

Delete all members from a group
===============================

.. rest_method:: DELETE /v1/groups/{group_id}/members

This operation does not accept a request body and does not return a response
body.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 204

.. rest_status_code:: error ../status.yaml

   - 400
   - 401
   - 404

Request Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - group_id: group_id_query

Delete a member from group
==========================

.. rest_method:: DELETE /v1/groups/{group_id}/members/{member_id}

This operation does not accept a request body and does not return a response
body.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 204

.. rest_status_code:: error ../status.yaml

   - 400
   - 401
   - 404

Request Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - group_id: group_id_query
   - member_id: member_id_query
