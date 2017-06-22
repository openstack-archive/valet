.. -*- rst -*-

==========
Placements
==========

List active placements
======================

.. rest_method:: HEAD /v1/placements

This operation does not accept a request body.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 200

.. rest_status_code:: error ../status.yaml

   - 401

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - id: placements_id
   - location: placements_location
   - name: placements_name
   - orchestration_id: placements_orchestration_id
   - reserved: placements_reserved
   - resource_id: placements_resource_id
   - plan_id: placements_plan_id

Response Example
----------------

.. literalinclude:: ./samples/list_placements_response.json
   :language: json

Show placement details with no reservation
==========================================

.. rest_method:: GET /v1/placements/{placement_id}

This operation does not accept a request body.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 200

.. rest_status_code:: error ../status.yaml

   - 400
   - 401

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - placement_id: placements_id

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - id: placements_id
   - location: placements_location
   - name: placements_name
   - orchestration_id: placements_orchestration_id
   - reserved: placements_reserved
   - resource_id: placements_resource_id
   - plan_id: placements_plan_id

Response Example
----------------

.. literalinclude:: ./samples/show_placements_details.json
   :language: json

Reserve a placement with possible replanning
============================================

.. rest_method:: GET /v1/placements/{placement_id}

If the placement was not planned in one of these locations, the placement for
this resource (and any others in the same plan not yet reserved) will be
replanned on-the-fly. This operation does not accept a request body.

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

   - location: placements_location
   - placement_id: placements_id
   - resource_id: placements_resource_id

Request Example
---------------

.. literalinclude:: ./samples/reserve_placements_request.json
   :language: json

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - id: placements_id
   - location: placements_location
   - name: placements_name
   - orchestration_id: placements_orchestration_id
   - reserved: placements_reserved
   - resource_id: placements_resource_id
   - plan_id: placements_plan_id

Response Example
----------------

.. literalinclude:: ./samples/reserve_placements_response.json
   :language: json
