Ostro version 2.0.2 Installation and Usage Guide

Author: Gueyoung Jung
Contact: gjung@research.att.com


INSTALLATION

You can download the latest Ostro python code from repository (CodeCloud).

USAGE

1. Configure Ostro

Set authentication in "ostro_server/ostro.auth" file. User must have the permission to access OpenStack Nova to let Ostro extract underlying cloud infrastructure information.

You must check “ostro_server/ostro.cfg” to correctly run Ostro. Here, explain the configuration parameters found in “ostro.cfg”.

Configuration consists of 1) system, 2) logging, and 3) management parts.

1.1 System configuration
- first, you define the base directory in “root_loc”, where Ostro is installed.
- “mode” can be either “live” or “sim”. “live” means Ostro runs over the real OpenStack site, while “sim” means Ostro can be tested over a simulated datacenter. To configure the simulated datacenter, you should check “ostro_server/ostro_sim.cfg”.
- “control_loc” is to set URL where OpenStack controller is deployed. From the URL, Ostro will get some data from Nova and Keystone (Cinder will be in the next version).
- currently, Ostro communicates with Keystone and Nova via REST APIs. Those APIs are set in “keystone_*” and “nova_*”.
- “db_*” indicates parameters to be used for handling Music database such as Cassandra keyspace and table names. "replication_factor" means how many Music instances run. "db_hosts" includes the ips where Music instances run.
- “ip” indicates the IP address of VM, where this Ostro instance runs. If Ostro instances are installed in multiple VMs, you should set “ip” in each configuration.

1.2 Logging configuration
You can set up the logging configuration including logger name, logging level, and directory. If you set the logging level as “debug”, Ostro will leave detailed record. Ostro also records two time-series data as text files (i.e., resource_log and app_log). Due to the large size of these logs, we limit the number of log files and the maximum size of each log file in “max_num_of_logs” and “max_log_size”. When “max_num_of_logs” is 20 and once it reaches the 21st log file, Ostro over-writes in the 1st file (i.e., rotate the logging).
"max_main_log_size" means the max size of the main Ostro log defined in "logger_name" in the location "logging_loc".

1.3 Management configuration
- “datacenter_name” indicates the name of site (region), where Ostro takes care of. This will be used as key value when getting site topology data from AIC Formation.
- “num_of_region_chars”, “rack_code_list”, and “node_code_list” are used to define the machine naming convention. In current version, Ostro parses each hosting server machine name to figure out the region code and rack name, where each hosting machine is located. This is based on the current naming convention document. Current naming convention is as follow, 
3 chars of CLLI + region number + 'r' + rack id number + 1 char of node type + node id number. For example, “pdk15r05c001” indicates the first KVM compute server (i.e., 'c001') in the fifth rack (i.e., 'r05') in the fifteenth DeKalb-Peachtree Airport Region (i.e., 'pdk15'). 
In “num_of_region_chars”, set the number of chars that indicates the region code. In the above example, 'pdk' is the region code.
In “rack_code_list”, set 1 char of rack indicator. This should be 'r'.
In “node_code_list”, set all of chars, each of which indicates the node type. Currently, 'a': network, 'c': KVM compute, 'u': ESXi compute, 'f': ?, 'o': operation, 'p': power, 's': storage.
- “compute_trigger_time” and “compute_trigger_frequency” are for setting when Nova is called to set information that is used for decision making such as a list of hosting servers and their resource capacities, host aggregates, and availability zone etc. The value of “compute_trigger_time” is based on 24-hour (e.g., “13:00” means 1pm). The value of “compute_trigger_frequency” is seconds (e.g., “3” means every 3 seconds). Ostro checks first “compute_trigger_frequency”. If this value is “0”, then uses “compute_trigger_time”.
- “topology_trigger_time” and “topology_trigger_frequency” are similar with the above, but these are for setting the site layout/topology. Note that currently, Nova must be called first and then, topology next. So, “compute_trigger_time” must be earlier than “topology_trigger_time”.
- “default_*” is for setting default overcommit ratios.
- “static_*” is for setting standby resource amount as percentage. Standby means Ostro will set aside certain amount resources (CPU, memory, and disk) as unused for load spikes of tenant applications. This will be changed more dynamically in the future version.
- “auth_loc” indicates the directory of the authentication file. Admin must have the permission to access OpenStack Nova to let Ostro extract underlying cloud infrastructure information.


2. Start/Stop Ostro daemon

Ostro will run as a daemon process. Go to “ostro_server” directory, then start Ostro daemon as follow,

	python ostro_daemon.py start

To stop this daemon process:

	python ostro_daemon.py stop


