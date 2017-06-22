.. -*- rst -*-

======
Status
======

Get summary status of all subsystems
====================================

.. rest_method:: HEAD /v1/status

This operation does not accept a request body and does not return a response
body.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 200

.. rest_status_code:: error ../status.yaml

   - 500

List detailed status of all subsystems
======================================

.. rest_method:: GET /v1/status

This operation does not accept a request body.

Response Codes
--------------

.. rest_status_code:: success ../status.yaml

   - 200

.. rest_status_code:: error ../status.yaml

   - 500

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - status: status

Response Parameters
-------------------

.. literalinclude:: ./samples/get_status_response.json
   :language: json
