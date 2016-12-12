# valet-openstack

Valet gives OpenStack the ability to optimize cloud resources while simultaneously meeting a cloud application's QoS requirements. Valet provides an api service, an optimizer (Ostro), and a set of OpenStack plugins.

This document covers installation of valet-openstack, a set of OpenStack plugins used to interact with Valet.

**IMPORTANT**: Overall Installation of Valet is covered in a separate document. These instructions are a component of the overall instructions.

## Prerequisites

Prior to installation:

* Ubuntu 14.04 LTS
* Python 2.7.6 with pip
* An OpenStack Kilo cloud
* Access to a [valet-api](https://github.com/att-comdev/valet/blob/master/doc/valet_api.md) endpoint

Throughout this document, the following installation-specific items are required. Have values for these prepared and ready before continuing. Suggestions for values are provided in this document where applicable.

| Name | Description | Example |
|------|-------------|-------|
| ``USER`` | User id | ``user1234`` |
| ``$VENV`` | Python virtual environment path (if any) | ``/etc/valet/venv`` |
| ``$VALET_OS_PATH`` | Local git repository's ``valet_os`` directory | ``/home/user1234/git/valet/valet_os`` |
| ``$VALET_HOST`` | valet-api hostname | ``localhost`` |
| ``$VALET_USERNAME`` | OpenStack placement service username | ``valet`` |
| ``$VALET_PASSWORD`` | OpenStack placement service password | |
| ``$VALET_TENANT_NAME`` | OpenStack placement service default tenant | ``service`` |
| ``$VALET_FAILURE_MODE`` | Desired failure mode for Nova ValetFilter | ``reject`` |
| ``$KEYSTONE_AUTH_API`` | Keystone Auth API publicurl endpoint | ``http://controller:5000/`` |
| ``$KEYSTONE_REGION`` | Keystone Region | ``RegionOne`` |

Root or sufficient sudo privileges are required for some steps.

### A Note About Python Virtual Environments

As valet-openstack works in concert with OpenStack services, if heat and nova have been installed in a python [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/) (venv), valet-openstack must be installed and configured in the same environment. (A venv helps avoid instabilities and conflicts within the default python environment.)

## Installation

Install valet-openstack on the OpenStack controller node containing heat-engine and nova-scheduler. If these services are distributed across multiple nodes, install and configure valet-openstack as appropriate on each node.

valet-openstack is located in ``valet_os``.

```bash
$ cd $VALET_OS_PATH
$ sudo pip install .
```

## OpenStack Configuration

valet-openstack requires edits to the heat and nova configuration files, and a stop/start of the heat-engine and nova-scheduler services.

### Prerequisites

The following keystone commands must be performed by an OpenStack cloud administrator.

Add a user (``$VALET_USERNAME``), giving it an ``admin`` role in one tenant (``$VALET_TENANT_NAME``, usually ``service``):

```bash
$ keystone user-create --name $VALET_USERNAME --pass $VALET_PASSWORD
$ keystone user-role-add --user $VALET_USERNAME --tenant $VALET_TENANT_NAME --role admin
```

Create the service entity and API endpoints. While this is not used by Valet 1.0, it is being reserved for future use.

```bash
$ keystone service-create --type placement --name valet --description "OpenStack Placement"
$ keystone endpoint-create --region $KEYSTONE_REGION --service valet --publicurl 'http://$VALET_HOST:8090/v1' --adminurl 'http://$VALET_HOST:8090/v1' --internalurl 'http://$VALET_HOST:8090/v1'
```

*Note: In OpenStack parlance, Valet is canonically referred to as a **placement service**.*

The administrator may choose to use differing hostnames/IPs for public vs. admin vs. internal URLs, depending on local architecture and requirements.

### Heat

The following changes are made in ``/etc/heat/heat.conf``.

Set ``plugin_dirs`` in the ``[DEFAULT]`` section such that Heat can locate and use the Valet Stack Lifecycle Plugin.

```ini
[DEFAULT]
plugin_dirs = /usr/local/etc/valet_os/heat
```

*Note: If a virtual environment is in use, change the path to be relative to the virtual environment's location, e.g. ``$VENV/etc/valet_os/heat``.*

If ``plugin_dirs`` is already present, separate entries by commas. The order of entries does not matter. See the OpenStack [heat.conf](http://docs.openstack.org/kilo/config-reference/content/ch_configuring-openstack-orchestration.html) documentation for more information.

Enable stack lifecycle scheduler hints in the ``[DEFAULT]`` section:

```ini
[DEFAULT]
stack_scheduler_hints = True
```

Add a ``[valet]`` section. This will be used by the Valet Stack Lifecycle Plugin:

```ini
[valet]
url = http://$VALET_HOST:8090/v1
```

Restart heat-engine using separate stop and start directives:

```bash
$ sudo service heat-engine stop
$ sudo service heat-engine start
```

Examine the heat-engine log (usually in ``/var/log/heat/heat-engine.log``). The ``ATT::Valet`` plugin should be found and registered:

```log
INFO heat.engine.environment [-]  Registered: [Plugin](User:False) ATT::Valet::GroupAssignment -> <class 'heat.engine.plugins.GroupAssignment.GroupAssignment'>
```

The heat command line interface (python-heatclient) can also be used to verify plugin registration:

```bash
$ heat resource-type-list | grep ATT
| ATT::Valet::GroupAssignment              |
```

### Nova

The following changes are made in ``/etc/nova/nova.conf``.

The ``nova-scheduler`` service requires manual configuration so that Nova can locate and use Valet's Scheduler Filter.

Edit the ``[DEFAULT]`` section so that ``scheduler_available_filters`` and ``scheduler_default_filters`` reference Valet, for example:

```ini
[DEFAULT]
scheduler_available_filters = nova.scheduler.filters.all_filters
scheduler_available_filters = valet_os.nova.valet_filter.ValetFilter
scheduler_default_filters = RetryFilter, AvailabilityZoneFilter, RamFilter, ComputeFilter, ComputeCapabilitiesFilter, ImagePropertiesFilter, ServerGroupAntiAffinityFilter, ServerGroupAffinityFilter, ValetFilter
```

When referring to additional filter plugins, multiple ``scheduler_available_filters`` lines are required. The first line explicitly makes all of nova's default filters available. The second line makes Valet's filter available. Additional lines may be required for additional plugins.

When setting ``scheduler_default_filters``, ensure that ``ValetFilter`` is placed last so that Valet has the final say in scheduling decisions.

*Note: ``scheduler_available_filters`` denotes filters that are available for use. ``scheduler_default_filters`` denotes filters that are enabled by default.*

Add a ``[valet]`` section. This will be used by the Valet Scheduler Filter:

```ini
[valet]
url = http://$VALET_HOST:8090/v1
failure_mode = $VALET_FAILURE_MODE
admin_tenant_name = $VALET_TENANT_NAME
admin_username = $VALET_USERNAME
admin_password = $VALET_PASSWORD
admin_auth_url = $KEYSTONE_AUTH_API
```

``$VALET_FAILURE_MODE`` refers to the action ``ValetFilter`` takes in the effect of a scheduling failure. It can be set to ``yield`` (defer to the other filter choices) or ``reject`` (block all other filter choices). The default action is ``reject`` so as to protect the integrity of Valet exclusivity groups. If exclusivity groups will never be used, or maintaining exclusivity group integrity is not required/practical, it may be desirable to set this to ``yield``.

Restart nova-scheduler using separate stop and start directives:

```bash
$ sudo service nova-scheduler stop
$ sudo service nova-scheduler start
```

## Uninstallation

Activate a virtual environment (venv) first if necessary, then uninstall with:

```bash
$ sudo pip uninstall valet-openstack
```

Remove previously made configuration file changes, OpenStack user accounts, and other settings as needed.

## Contact

Joe D'Andrea <jdandrea@research.att.com>
