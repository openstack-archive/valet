=========
Valet API
=========

Getting Started
~~~~~~~~~~~~~~~

All API requests require a valid Keystone token. Use the **Keystone Generate
Token v2** POST request to generate one. It will be automatically stored in the
Postman environment and used for future API requests. Once the token expires
("Authorization Required"), simply generate a new token.

The placement API can be exercised using curl or Postman by importing the file
``Valet.json.postman_collection``. This document covers installation of valet-api, the API engine used to interact with Valet.

**IMPORTANT**: [Overall Installation of Valet is covered in a separate document](https://github.com/att-comdev/valet/blob/master/doc/valet_os.md).

Before using the collection, create a Postman environment with the following
settings:

.. list-table::
    :header-rows: 1

    * - Component
      - Description
      - Example
    * - ``valet``
      - valet-api endpoint
      - ``http://controller:8090``
    * - ``keystone``
      - keystone-api endpoint
      - ``http://controller:5000``
    * - ``tenant_name``
      - tenant name
      - ``service``
    * - ``username``
      - username
      - ``valet``
    * - ``password``
      - password
      - password

Prerequisites
~~~~~~~~~~~~~

Prior to installation:

* Ubuntu 14.04 LTS
* Python 2.7.6 with pip
* An OpenStack Kilo cloud
* [Music](https://github.com/att-comdev/valet) 6.0
* [Ostro](https://github.com/att-comdev/valet/blob/master/doc/ostro.md) 2.0

Throughout this document, the following installation-specific items are required. Have values for these prepared and ready before continuing. Suggestions for values are provided in this document where applicable.

Root or sufficient sudo privileges are required for some steps.

A Note About Python Virtual Environments
----------------------------------------

It is recommended to install and configure valet-api within a Python virtual
environment [2]. This helps avoid instabilities and conflicts within the
default python environment.

## Installation

Install valet-api on a host that can reach all OpenStack Keystone endpoints (public, internal, and admin). This can be a controller node or a separate host. Likewise, valet-api, Ostro, and Music may be installed on the same host or separate hosts.

valet-api is located in ``valet_api``.

```bash
$ cd $VALET_API_PATH
$ sudo pip install .
```

If the following error appears when installing valet-api, and SSL access is required (e.g., if Keystone can only be reached via SSL), use a newer Python 2.7 Ubuntu package.

```bash
[InsecurePlatformWarning](https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning): A true SSLContext object is not available. This prevents urllib3 from configuring SSL appropriately and may cause certain SSL connections to fail.
```

## User Account

Create an Ubuntu user/group for the valet service user (usually ``valet``):

```bash
$ sudo adduser --gecos "valet service user" valet
```

If the Ubuntu-assigned uid/gid requires adjustment:

```bash
$ sudo usermod -u $DESIRED_ID -U valet
$ sudo groupmod -g $DESIRED_ID valet
```

## Configuration

Copy ``$VALET_API_PATH/etc/valet_api/config.py`` to a suitable configuration path (``$VALET_CONFIG_PATH``) outside of the git repository prior to editing. (Always edit the copy, never the original.) As the config file will contain sensitive passwords, ``$VALET_CONFIG_PATH`` must have limited visibility and be accessible only to the user running valet-api.

Edit the following sections in the ``config.py`` copy. See the [valet-openstack README](https://github.com/att-comdev/valet/blob/master/doc/valet_os.md) for additional context around the ``server`` and ``identity`` sections.

*Note: In OpenStack parlance, Valet is canonically referred to as a **placement service**.*

### Server

* Set ``port`` to match the port number used by OpenStack Keystone's placement service (usually ``8090``).
* ``host`` can remain ``0.0.0.0``.

```python
server = {
    'port': '8090',
    'host': '0.0.0.0'
}
```

### Identity

* Set ``username`` and ``password`` to the OpenStack placement service user.
* Set ``project_name`` to the OpenStack placement service user's tenant name.
* Set ``auth_url`` to the OpenStack Keystone API publicurl endpoint.

```python
identity = {
    'config': {
        'username': '$VALET_USERNAME',
        'password': '$VALET_PASSWORD',
        'project_name': '$VALET_TENANT_NAME',
        'auth_url': '$KEYSTONE_AUTH_API',
    }
}
```

Once authenticated via Keystone's *publicurl* endpoint, valet-api uses Keystone's *adminurl* endpoint for further API calls. Access to the adminurl endpoint is required for:

* Authentication (AuthN) of OpenStack users for valet-api access.
* Authorization (AuthZ) of OpenStack users for valet-api access. This is presently limited to users assigned an ``admin`` role.
* Obtaining a list of all OpenStack cloud tenants (used by Valet Groups).

*Note: Formal Role-Based Access Control (RBAC) support (via oslo-policy) is expected in a future release.*

If the Keystone adminurl endpoint is not reachable, Valet will not be able to obtain a complete tenant list. To mitigate:

* Add an additional identity config setting named ``'interface'``, set to ``'public'``.
* In the OpenStack cloud, ensure the valet user (``$VALET_USERNAME``) is a member of every tenant. Keep membership current as needed.

### Messaging

* Set ``transport_url`` to match the OpenStack Oslo Messaging Service endpoint.

```python
messaging = {
    'config': {
        'transport_url': 'rabbit://$OSLO_MSG_USERNAME:$OSLO_MSG_PASSWORD@$OSLO_MSG_HOST:5672/',
    }
}
```

### Music

* Set ``host``, ``port``, ``keyspace``, and ``replication_factor`` as needed for access to Music.
* Alternately, set ``hosts`` (plural form) to a python list of hosts if more than one host is used (e.g., ``'[host1, host2, host3]'``).

For example, if Music is hosted on ``127.0.0.1`` port ``8080`` with a keyspace of ``valet`` and replication factor of ``3``:

```python
music = {
    'host': '127.0.0.1',
    'port': '8080',
    'keyspace': 'valet',
    'replication_factor': 3,
}
```

*Notes: If ``host`` and ``hosts`` are both set, ``host`` is used and ``hosts`` is ignored. Music does not use AuthN or AuthZ at this time.*

## Data Storage Initialization

Use the ``pecan populate`` command to initialize data storage:

```bash
$ pecan populate $VALET_CONFIG_PATH/config.py
```

Any previously created tables will be left as-is and not deleted/re-created.

*Note: Music does not support migrations. If necessary, schema changes in future versions will be noted here with specific upgrade instructions.*

## Running for the first time

Use the ``pecan serve`` command to run valet-api and verify installation.

```bash
$ pecan serve $VALET_CONFIG_PATH/config.py
```

Browse to ``http://$VALET_HOST:8090/`` (no AuthN/AuthZ required). Check for a response, for example:

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

valet-api comes with a [Postman](http://www.getpostman.com/) collection of sample API calls, located in ``$VALET_API_PATH/valet_api/tests``. [Learn more](https://github.com/att-comdev/valet/blob/master/valet/tests/api/README.md).

See the ``doc`` directory for placement service.

*IMPORTANT: Do not use ``pecan serve`` to run valet-api in a production environment. A number of production-quality WSGI-compatible environments are available (e.g., apache2 httpd).*

Configuring apache2 httpd

This section describes an example WSGI installation using apache2 httpd.

Prerequisites

* apache2 httpd
* libapache2-mod-wsgi (3.4 at a minimum, 3.5 recommended by the author)
* A ``valet`` service user account/group on the host where valet-api is installed.

Configuration
-------------

Set up directories and ownership::

    sudo mkdir $VALET_CONFIG_PATH
    sudo mkdir /var/log/apache2/valet
    sudo cp -p $VALET_API_PATH/etc/valet_api/app.wsgi $VALET_API_PATH/etc/valet_api/config.py $VALET_CONFIG_PATH
    $ sudo chown -R valet:valet /var/log/apache2/valet $VALET_CONFIG_PATH

Set up valet-api as a site::

    sudo cd /etc/apache2/sites-available
    sudo cp -p $VALET_API_PATH/etc/valet_api/app.apache2 valet.conf
    sudo chown root:root valet.conf

If valet-api was installed in a python virtual environment, append
``python-home=$VENV`` to ``WSGIDaemonProcess`` within ``valet.conf``. Apache
will then use the correct python environment and libraries.

Enable valet-api, ensure the configuration syntax is valid, and restart::

    cd $APACHE2_CONFIG_PATH/sites-enabled
    sudo ln -s ../sites-available/valet.conf .
    sudo apachectl -t
    Syntax OK
    sudo apachectl graceful

Uninstallation
--------------

Remove previously made configuration file changes, OpenStack user accounts,
and other settings as needed. Activate a virtual environment (venv) first if
necessary, then uninstall with::

    sudo pip uninstall valet-api

References
----------
