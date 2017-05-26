=====
Valet
=====

Valet is a cloud resource placement optimization service. Valet gives OpenStack
the ability to optimize cloud resources while simultaneously meeting a cloud
application's QoS requirements. Through model driven orchestration, the target
state of Valet is to provide “holistic OpenStack data-plane resource placement”
. Valet provides an api service, a placement optimizer (valet-engine), a high
availability data storage and persistence layer (MUSIC), and a set of OpenStack
plugins.

Why Valet exists
----------------

For large-scale, multi-tenant cloud operators, there is a large demand for
tenant specific service requests. This demand drives the growth of the number
of cloud availability zones and compartmentalization of the cloud, which then
leads to increased provisioning and sub-optimal use of cloud and staff
resources.  Also, security requirements lead us to place specialized network
appliances of these tenants separately into “exclusive” hosts that do not have
internet connectivity. 

Valet responds to the challenges outlined above by enhancing OpenStack Nova
scheduling to develop resource management optimization. By planning the
placement of all the cloud resources for an application in a holistic manner,
there is opportunity to reduce cross-rack traffic, reduce resource
fragmentation, and save on operating costs.

Learn more about Valet
----------------------

* https://www.openstack.org/videos/video/valet-holistic-data-center-optimization-for-openstack (OpenStack Austin Summit presentation)

Valet consists of the following components
------------------------------------------

* A set of OpenStack plugins used to interact with Valet
* An API engine used to interact with Valet
* A placement optimization engine
* A message bus listener

We have interactions with
-------------------------
* https://git.openstack.org/cgit/openstack/nova (instance)
* https://git.openstack.org/cgit/openstack/heat (orchestration)
