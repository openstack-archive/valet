===============================================
Tempest Integration of valet
===============================================

Tempest has an external test plugin interface which enables anyone to integrate an 
external test suite as part of a tempest run. This will let any project leverage 
being run with the rest of the tempest suite while not requiring the tests live in 
the tempest tree.
http://docs.openstack.org/developer/tempest/plugin.html

Dealing with configuration options
----------------------------------

Historically Tempest didn't provide external guarantees on its configuration options. 
However, with the introduction of the plugin interface this is no longer the case. An 
external plugin can rely on using any configuration option coming from Tempest, there 
will be at least a full deprecation cycle for any option before it's removed. However,
just the options provided by Tempest may not be sufficient for the plugin. If you need 
to add any plugin specific configuration options you should use the register_opts and 
get_opt_lists methods to pass them to Tempest when the plugin is loaded. When adding 
configuration options the register_opts method gets passed the CONF object from tempest.
This enables the plugin to add options to both existing sections and also create new 
configuration sections for new options.

Using Plugins
-------------
Tempest will automatically discover any installed plugins when it is run. So by just 
installing the python packages which contain your plugin you'll be using them with tempest,
nothing else is really required.

However, you should take care when installing plugins. By their very nature there are no 
guarantees when running tempest with plugins enabled about the quality of the plugin. 
Additionally, while there is no limitation on running with multiple plugins it's worth 
noting that poorly written plugins might not properly isolate their tests which could cause 
unexpected cross interactions between plugins.

Notes for using plugins with virtualenvs
----------------------------------------

When using a tempest inside a virtualenv (like when running under tox) you have to ensure that 
the package that contains your plugin is either installed in the venv too or that you have system 
site-packages enabled. The virtualenv will isolate the tempest install from the rest of your system 
so just installing the plugin package on your system and then running tempest inside a venv will not 
work.

Tempest also exposes a tox job, all-plugin, which will setup a tox virtualenv with system site-packages 
enabled. This will let you leverage tox without requiring to manually install plugins in the tox venv 
before running tests.

Commands to Run the plugin
--------------------------

To list all Valet tempest cases, go to tempest directory, then run:

$ testr list-tests valet

To run only these tests in tempest, go to tempest directory, then run:

$ ./run_tempest.sh -N -- valet

$ tox -eall-plugin valet

And, to run a specific test:

$ tox -eall-plugin valet.tests.tempest.tests.api.test_groups.ValetGroupsTest.test_list_groups

To run test from valet folder itself(Make sure /etc/tempest/tempest.conf exists):

$ python -m subunit.run discover | subunit-trace

