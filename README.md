# Valet

Valet is a cloud resource placement optimization service. Valet gives OpenStack the ability to optimize cloud resources while simultaneously meeting a cloud application's QoS requirements. Through model driven orchestration, the target state of Valet is to provide “holistic OpenStack data-plane resource placement”. Valet provides an api service, a placement optimizer (Ostro), a high availability data storage and persistence layer (Music), and a set of OpenStack plugins.

## Why Valet exists:

For large-scale, multi-tenant cloud operators, there is a large demand for tenant specific service requests.  This demand drives the growth of the number of cloud availability zones and compartmentalization of the cloud, which then leads to increased provisioning and sub-optimal use of cloud and staff resources.  Also, security requirements lead us to place specialized network appliances of these tenants separately into “exclusive” hosts that do not have internet connectivity. 

Valet responds to the challenges outlined above by enhancing OpenStack Nova scheduling to develop resource management optimization.  By planning the placement of all the cloud resources for an application in a holistic manner, there is opportunity to reduce cross-rack traffic, reduce resource fragmentation, and save on operating costs.

## Learn more about Valet:

* [OpenStack Newton Summit Presentation](https://www.openstack.org/videos/video/valet-holistic-data-center-optimization-for-openstack) (Austin, TX, 27 April 2016)
* [Presentation Slides](http://www.research.att.com/export/sites/att_labs/techdocs/TD_101806.pdf) (PDF)

## Valet consists of the following components:

* [valet-openstack](https://github.com/att-comdev/valet/blob/master/doc/valet_os.md): a set of OpenStack plugins used to interact with Valet
* [valet-api](https://github.com/att-comdev/valet/blob/master/doc/valet_api.md): an API engine used to interact with Valet
* [Ostro](https://github.com/att-comdev/valet/blob/master/doc/ostro.md): a placement optimization engine
* Music: a data storage and persistence service
* [ostro-listener](https://github.com/att-comdev/valet/blob/master/doc/ostro_listener.md): a message bus listener used in conjunction with Ostro and Music
* [havalet](https://github.com/att-comdev/valet/blob/master/doc/ha.md): a service that assists in providing high availability for Valet

## Additional documents:

* [OpenStack Heat Resource Plugins](https://github.com/att-comdev/valet/blob/master/valet_plugins/valet_plugins/heat/README.md): Heat resources
* [Placement API](https://github.com/att-comdev/valet/blob/master/doc/valet_api.md): API requests/responses
* [Using Postman with valet-api](https://github.com/att-comdev/valet/blob/master/valet/tests/api/README.md): Postman support

## License:

Valet is distributed under the terms of the Apache License, Version 2.0. The full terms and conditions of this license are detailed in the LICENSE file.
