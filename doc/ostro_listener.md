OpenStack Event Listener for Ostro
==================================

This script listens for specific messages needed by Ostro to maintain
up-to-date cloud state. It can persist digested versions of the messages
to Music, which Ostro then picks up.

*Note: This version of the listener does not use oslo.messaging. It
listens directly to RabbitMQ. Future revisions are expected to use
oslo.messaging in order to keep the means of transport abstract.*

Prerequisites
-------------

Prior to installation:

-   Ubuntu 14.04 LTS
-   Python 2.7.6 with pip
-   Access to an OpenStack Kilo cloud (RabbitMQ in particular)
-   Access to Music and Ostro

Throughout this document, the following installation-specific items are
required. Have values for these prepared and ready before continuing.
Suggestions for values are provided in this document where applicable.

  Name                          Description                                         Example
  ----------------------------- --------------------------------------------------- -------------------------------------------
  `$USER`                       User id                                             `user1234`
  `$VENV`                       Python virtual environment path (if any)            `/etc/ostro-listener/venv`
  `$OSTRO_LISTENER_PATH`        Local git repository's `ostro_listener` directory   `/home/user1234/git/allegro/ostro_listener`
  `$CONFIG_FILE`                Event Listener configuration file                   `/etc/ostro-listener/ostro-listener.conf`
  `$RABBITMQ_HOST`              RabbitMQ hostname or IP address                     `localhost`
  `$RABBITMQ_USERNAME`          RabbitMQ username                                   `guest`
  `$RABBITMQ_PASSWORD_FILE`     Full path to RabbitMQ password file                 `/etc/ostro-listener/passwd`
  `$MUSIC_URL`                  Music API endpoints and port in URL format          `http://127.0.0.1:8080/`
  `$MUSIC_KEYSPACE`             Music keyspace                                      `valet`
  `$MUSIC_REPLICATION_FACTOR`   Music replication factor                            `1`

Root or sufficient sudo privileges are required for some steps.

### A Note About Python Virtual Environments

It is recommended to consider using a python [virtuals
environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/)
(venv). A venv helps avoid instabilities and conflicts within the
default python environment.

Installation
------------

Install ostro-listener on any node with line-of-sight to the RabbitMQ
endpoint from which messages are to be monitored.

ostro-listener is located in `ostro_listener`.

~~~~ {.bash}
$ cd $OSTRO_LISTENER_PATH
$ sudo pip install .
~~~~

Command Line Usage
------------------

    usage: ostro-listener [-h] [-c OSTRO_LISTENER_CONFIG] [-x EXCHANGE]
                          [-t {topic,fanout}] [-a] [-H HOST] [-p PORT]
                          [-u USERNAME] [-P PASSWDFILE] [-o {yaml,json,dict}] [-s]
                          [-m MUSIC] [-k KEYSPACE] [-r REPLICATION_FACTOR]

    Ostro-specific OpenStack Event Listener

    optional arguments:
      -h, --help            show this help message and exit
      -c OSTRO_LISTENER_CONFIG, --conf_file OSTRO_LISTENER_CONFIG
                            Defaults to env[OSTRO_LISTENER_CONFIG]
      -x EXCHANGE, --exchange EXCHANGE
                            rabbit exchange to listen to
      -t {topic,fanout}, --exchange_type {topic,fanout}
                            type of exchange (default="topic")
      -a, --auto_delete     autodelete exchange (default=False)
      -H HOST, --host HOST  compute node on which rabbitmq is running
      -p PORT, --port PORT  port on which rabbitmq is running
      -u USERNAME, --username USERNAME
                            rabbitmq username (default="guest")
      -P PASSWDFILE, --passwdfile PASSWDFILE
                            file containing host rabbitmq passwords
      -o {yaml,json,dict}, --output_format {yaml,json,dict}
                            output format (default="dict")
      -s, --store           store messages in music (default=False)
      -m MUSIC, --music MUSIC
                            music endpoint
      -k KEYSPACE, --keyspace KEYSPACE
                            music keyspace
      -r REPLICATION_FACTOR, --replication_factor REPLICATION_FACTOR
                            music replication factor

Example Invocation
------------------

Split across lines for readability:

    # ostro-listener -x nova -t topic -s
                     -H $RABBITMQ_HOST
                     -u $RABBITMQ_USERNAME
                     -P $RABBITMQ_PASSWORD_FILE
                     -m $MUSIC_URL
                     -k $MUSIC_KEYSPACE
                     -r $MUSIC_REPLICATION_FACTOR

*Note: This script has kept its original flexibility in that it may also
be used to listen to other exchanges/topics.*

Always use the nova exchange (`-x nova`) and topic exchange type
(`-t topic`) when using in conjunction with Ostro and Music.

**IMPORTANT**: Always use topic exchanges for "listening on the wire" to
OpenStack message traffic. Failure to do so could risk other RabbitMQ
users (e.g., OpenStack services) missing important messages, and then
you will be sad.

Password File
-------------

A sample password file can be found in
`$OSTRO_LISTENER_PATH/etc/ostro_listener/passwd.txt`.

Copy this file to another location before editing, for example
`/etc/ostro-listener/passwd`.

The password file must be protected. In particular, it must not be
readable by group/other users. It is often set to root ownership.

Within the file, separate hosts/IPs and passwords with a single space.
For example:

    127.0.0.1 password
    localhost password
    myhost password
    myhost.at.att.com password

Hosts/IPs will match based on the value of `$RABBITMQ_HOST`.

Using a Configuration File
--------------------------

A sample configuration file can be found in
`$OSTRO_LISTENER_PATH/etc/ostro_listener/ostro-listener.conf.txt`:

~~~~ {.ini}
[DEFAULT]
exchange = nova
exchange_type = topic
auto_delete = false
host = localhost
port = 5672
username = guest
passwdfile = /etc/ostro-listener/passwd
output_format = dict
store = true
music = http://127.0.0.1:8080/
keyspace = music
replication_factor = 1
~~~~

Copy this file to another location before editing.

Configuration files may be referenced in one of two ways, through the
`--config-file` option:

~~~~ {.bash}
# ostro-listener --config-file $CONFIG_FILE
~~~~

... or via an environment variable:

~~~~ {.bash}
# export OSTRO_EVENT_LISTENER_CONFIG=$CONFIG_FILE
# ostro-listener
~~~~

Running as an Ubuntu Service
----------------------------

A sample Ubuntu init.d script can be found in
`$OSTRO_LISTENER_PATH/etc/ostro_listener/ostro-listener.initd.txt`.

To use, first copy this script to `/etc/init.d/ostro-listener`:

~~~~ {.bash}
$ sudo cp $OSTRO_LISTENER_PATH/etc/ostro_listener/ostro-listener.initd.txt /etc/init.d/ostro-listener
$ sudo chmod 755 /etc/init.d/ostro-listener
~~~~

If ostro-listener was installed in a Python virtual environment, edit
`/etc/init.d/ostro-listener`, uncomment the `export VENV` line, and
adjust as needed. For example, if the virtual environment is installed
in `/etc/ostro-listener/venv`, assign `VENV` as follows:

~~~~ {.bash}
export VENV=/etc/ostro-listener/venv
~~~~

Create `/var/log` and `/var/run` directories for use by the service:

~~~~ {.bash}
$ sudo mkdir /var/log/ostro-listener
$ sudo mkdir /var/run/ostro-listener
$ sudo chmod 750 /var/log/ostro-listener
$ sudo chmod 755 /var/run/ostro-listener
~~~~

Set the run level defaults, then enable ostro-listener as a service:

~~~~ {.bash}
$ sudo update-rc.d ostro-listener defaults
$ sudo update-rc.d ostro-listener enable
~~~~

To start the ostro-listener service:

~~~~ {.bash}
$ sudo service ostro-listener start
~~~~

While running, a process ID file will be found in
`/var/run/ostro-listener/ostro-listener.pid`, and a log file will be
found in `/var/log/ostro-listener/ostro-listener.log`. The log is
appended to upon subsequent starts. Log rotation is left to the
discretion of the server administrator.

To stop the ostro-listener service:

~~~~ {.bash}
$ sudo service ostro-listener stop
~~~~

The process ID file will be removed from `/var/run/ostro-listener` upon
stopping.

Uninstallation
--------------

Activate a virtual environment (venv) first if necessary.

Disable ostro-listener as a service, then uninstall:

~~~~ {.bash}
$ sudo update-rc.d ostro-listener disable
$ sudo pip uninstall ostro-listener
~~~~

Remove previously made configuration file changes, files, and other
settings as needed.

Contact
-------

Joe D'Andrea <jdandrea@research.att.com>
