# Using Postman with valet-api

The placement API (valet-api) can be exercised using [Postman](http://www.getpostman.com/), by importing the file ``Valet.json.postman_collection``.

Before using the collection, create a Postman environment with the following settings:

* ``valet``: valet-api endpoint (e.g., ``http://controller:8090``)
* ``keystone``: keystone-api endpoint (e.g., ``http://controller:5000``)
* ``tenant_name``: tenant name (e.g., ``service``)
* ``username``: username (e.g., ``valet``)
* ``password``: password

All valet-api requests require a valid Keystone token. Use the **Keystone Generate Token v2** POST request to generate one. It will be automatically stored in the Postman environment and used for future API requests. Once the token expires ("Authorization Required"), simply generate a new token.

See the [valet-api](https://github.com/att-comdev/valet/blob/master/README.md) API documentation for a complete list of supported requests.
