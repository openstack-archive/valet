.. -*- rst -*-

=====
Plans
=====

Create a plan
=============

.. rest_method:: POST /v1/plans

Creates a plan.

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

   - locations: locations
   - plan_name: plan_name
   - resources: resources
   - stack_id: stack_id


Request Example
---------------

.. literalinclude:: ./samples/create_plan_request.json
   :language: json

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - stack_id: stack_id
   - placements: placements
   - id: plan_id
   - name: plan_name

Response Example
----------------

.. literalinclude:: ./samples/create_plan_response.json
   :language: json

List active plans
=================

.. rest_method:: GET /v1/plans

Lists all plans.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 200

.. rest_status_code:: error ../status.yaml

   - 401

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - stack_id: stack_id
   - placements: placements
   - id: plan_id
   - name: plan_name

Response Example
----------------

.. literalinclude:: ./samples/list_plan_response.json
   :language: json

Show plan details
=================

.. rest_method:: GET /v1/plans/{plan_id}

Lists all plans.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 200

.. rest_status_code:: error ../status.yaml

   - 401
   - 404

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - plan_id: plan_id_query

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - stack_id: stack_id
   - placements: placements
   - id: plan_id
   - name: plan_name

Response Example
----------------

.. literalinclude:: ./samples/show_plan_response.json
   :language: json


Update a plan
=============

.. rest_method:: PUT /v1/plans/{plan_id}

Update a plan.

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

   - plan_id: plan_id_query
   - action: action
   - excluded_hosts: excluded_hosts
   - resources: resources_update

Request Example
---------------

.. literalinclude:: ./samples/update_plan_request.json
   :language: json

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - stack_id: stack_id
   - id: plan_id
   - placements: placements

Response Example
----------------

.. literalinclude:: ./samples/update_plan_response.json
   :language: json

Delete a plan
=============

.. rest_method:: DELETE /v1/plans/{plan_id}

Deletes a plan.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 204

.. rest_status_code:: error ../status.yaml

   - 400
   - 401
   - 404

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - plan_id: plan_id_query
