Ostro version 2.0.2 Usage Guide

USAGE

1: Configure Ostro

Set authentication in "ostro\_server/ostro.auth" file. User must have
the permission to access OpenStack Nova to let Ostro extract underlying
cloud infrastructure information.

You must check “ostro\_server/ostro.cfg” to correctly run Ostro. Here,
explain the configuration parameters found in “ostro.cfg”.

Configuration consists of 1) system, 2) logging, and 3) management
parts.

1.1 System configuration - first, you define the base directory in
“root\_loc”, where Ostro is installed. - “mode” can be either “live” or
“sim”. “live” means Ostro runs over the real OpenStack site, while “sim”
means Ostro can be tested over a simulated datacenter. To configure the
simulated datacenter, you should check “ostro\_server/ostro\_sim.cfg”. -
“control\_loc” is to set URL where OpenStack controller is deployed.
From the URL, Ostro will get some data from Nova and Keystone (Cinder
will be in the next version). - currently, Ostro communicates with
Keystone and Nova via REST APIs. Those APIs are set in “keystone\_*” and
“nova\_*”. - “db\_\*” indicates parameters to be used for handling Music
database such as Cassandra keyspace and table names.
"replication\_factor" means how many Music instances run. "db\_hosts"
includes the ips where Music instances run. - “ip” indicates the IP
address of VM, where this Ostro instance runs. If Ostro instances are
installed in multiple VMs, you should set “ip” in each configuration.

1.2 Logging configuration You can set up the logging configuration
including logger name, logging level, and directory. If you set the
logging level as “debug”, Ostro will leave detailed record. Ostro also
records two time-series data as text files (i.e., resource\_log and
app\_log). Due to the large size of these logs, we limit the number of
log files and the maximum size of each log file in “max\_num\_of\_logs”
and “max\_log\_size”. When “max\_num\_of\_logs” is 20 and once it
reaches the 21st log file, Ostro over-writes in the 1st file (i.e.,
rotate the logging). "max\_main\_log\_size" means the max size of the
main Ostro log defined in "logger\_name" in the location "logging\_loc".

1.3 Management configuration - “datacenter\_name” indicates the name of
site (region), where Ostro takes care of. This will be used as key value
when getting site topology data. -
“num\_of\_region\_chars”, “rack\_code\_list”, and “node\_code\_list” are
used to define the machine naming convention. In current version, Ostro
parses each hosting server machine name to figure out the region code
and rack name, where each hosting machine is located. This is based on
the current naming convention document. Current naming convention is as
follow, 3 chars of CLLI + region number + 'r' + rack id number + 1 char
of node type + node id number. For example, “pdk15r05c001” indicates the
first KVM compute server (i.e., 'c001') in the fifth rack (i.e., 'r05')
in the fifteenth DeKalb-Peachtree Airport Region (i.e., 'pdk15'). In
“num\_of\_region\_chars”, set the number of chars that indicates the
region code. In the above example, 'pdk' is the region code. In
“rack\_code\_list”, set 1 char of rack indicator. This should be 'r'. In
“node\_code\_list”, set all of chars, each of which indicates the node
type. Currently, 'a': network, 'c': KVM compute, 'u': ESXi compute, 'f':
?, 'o': operation, 'p': power, 's': storage. - “compute\_trigger\_time”
and “compute\_trigger\_frequency” are for setting when Nova is called to
set information that is used for decision making such as a list of
hosting servers and their resource capacities, host aggregates, and
availability zone etc. The value of “compute\_trigger\_time” is based on
24-hour (e.g., “13:00” means 1pm). The value of
“compute\_trigger\_frequency” is seconds (e.g., “3” means every 3
seconds). Ostro checks first “compute\_trigger\_frequency”. If this
value is “0”, then uses “compute\_trigger\_time”. -
“topology\_trigger\_time” and “topology\_trigger\_frequency” are similar
with the above, but these are for setting the site layout/topology. Note
that currently, Nova must be called first and then, topology next. So,
“compute\_trigger\_time” must be earlier than “topology\_trigger\_time”.
- “default\_*” is for setting default overcommit ratios. - “static\_*”
is for setting standby resource amount as percentage. Standby means
Ostro will set aside certain amount resources (CPU, memory, and disk) as
unused for load spikes of tenant applications. This will be changed more
dynamically in the future version. - “auth\_loc” indicates the directory
of the authentication file. Admin must have the permission to access
OpenStack Nova to let Ostro extract underlying cloud infrastructure
information.

2:  Start/Stop Ostro daemon

Ostro will run as a daemon process. Go to “ostro\_server” directory,
then start Ostro daemon as follow,

    python ostro_daemon.py start

To stop this daemon process:

    python ostro_daemon.py stop
