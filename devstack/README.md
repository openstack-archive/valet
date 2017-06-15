# All-in-1 Valet on Devstack Setup

### Pre-setup notes and disclaimers:
* Valet as a plugin to Devstack has been tested with Ubuntu 16.04, according to the instructions on the [Devstack website](https://docs.openstack.org/developer/devstack/). The stable Newton version of Devstack was used for testing.

### Pre-requisites:
* If you require proxies in order to upload/download files off of the internet, make sure those proxies are set.

* Git clones should use https by default. To force this (which you will need when you stack), use the following command:
		git config --global url."https://".insteadOf git://

* Put the following line in the /etc/sudoers file:
		ubuntu ALL=(ALL) NOPASSWD: ALL
		   (replace "ubuntu" with whatever user name you're stacking with)

* Make sure you have SSH'd into your devstack VM directly as the stack user (whether it's "stack", "ubuntu" or whatever), otherwise you will not be able to run the screen command to restart services.

### Stacking Instructions

* Follow the quick setup instructions at the [Devstack website](https://docs.openstack.org/developer/devstack/) to clone and setup Devstack. Make sure to use the correct Devstack as specified in the pre-setup notes above. You may choose to create a "stack" user or just use the "ubuntu" (or default user) on your VM.

* When the stack.sh script is called, Valet will be cloned as part of the stacking process. Copy the following line into your local.conf file, underneath the "local|localrc" section:
	enable_plugin valet https://git.openstack.org/openstack/valet

* In your local.conf file, set your HOST_IP variable to the IP address assigned to the management interface (192.168.56.xxx). If you use 127.0.0.1, the services will come up but you won't be able to access the services from a browser running external to your VM.

* In your local.conf file, enable heat: (add this line to the end of the file)
	ENABLED_SERVICES+=,heat,h-api,h-api-cfn,h-api-cw,h-eng

* Check the settings in the "settings" file. If you want to override them you can export the variables in the shell prior to calling "stack.sh".  The variables are listed below, along with their default values:

	CASSANDRA_DEBIAN_MIRROR - this is the debian mirror entry that will be placed in the /etc/apt/sources.list file in order to download the desired version of Cassandra. Default: "deb http://www.apache.org/dist/cassandra/debian 310x main".

	OPENSTACK_PLUGIN_PATH - the path to the "valet_plugins" directory within the valet repo. Default: /opt/stack/valet/plugins/valet_plugins.

	MUSIC_URL - the mirror URL that the plugin will use to retrieve the MUSIC package. Default: None. (must be filled in) Example value: "http://mirror.att.com/repo/pool/main/m/music/". (don't forget the trailing slash)

	MUSIC_FILE - the name of the MUSIC package. Default: None. (must be filled in) Example value: music_3.5.0-0_amd64.deb

* Start stackin!
	cd <devstack-repo>
	./stack.sh

* Currently, the Valet Devstack plugin does not 100% automate the setup of Valet. Until 100% automation is achieved, you will manually need to re-configure Heat and Nova according to the stack-valet-plugins-configure-manual.sh script.

### Unstacking Script

* Unstacking Devstack using the unstack.sh script will trigger the Valet Devstack plugin to stop all Valet/Music related services and processes.

### Clean Script

* When Devstack's clean.sh script is called, the Valet Devstack plugin will be triggered to uninstall/remove all Valet/Music related components. Note, however, that this "clean" operation will leave the valet-related configuration files in place, as it is very annoying to unstack+clean and find that your customized .conf files have been removed.

### Known Issues and Workarounds
* Just after the plugin has deployed Valet (as part of stack.sh), the valet-engine process sometimes does not come up properly (tracebacks are seen in the startup sequence - /var/log/valet/engine.log). Workaround is to restart the valet-engine process (sudo -u valet python /usr/bin/valet-engine -c stop; sudo -u valet python /usr/bin/valet-engine -c start).

* Just before Valet services are started, the pecan_populate.sh script is called to populate the database and setup the WSGI app in Apache2. A "usage" warning is printed at this time: "invalid choice: 'populate'". This issue does not appear to prevent Valet from working properly within the Devstack environment.
