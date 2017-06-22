============
Valet Engine
============


Configuration 
-------------

From the URL, Valet Engine will get some data from Nova and Keystone.

Logging configuration
Run the valet-engine::

    valet-engine start

To stop::

    valet-engine stop

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

MUSIC Database
--------------

“db_*” indicates parameters to be used for handling Music database such as Cassandra keyspace and table names.
"replication_factor" means how many Music instances run. "db_hosts" includes the ips where Music instances run.
“ip” indicates the IP address of VM, where this Ostro instance runs.
If Ostro instances are installed in multiple VMs, you should set “ip” in each configuration.
