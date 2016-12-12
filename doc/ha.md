High Availability Valet Tools
=============================

This tool monitors one or more configured processes to maintain high
availability.

~~~~ {.bash}
$ python ./ha_valet.py [-p name]
~~~~

ha\_valet.cfg
-------------

The ha\_valet configuration file contains a list of dictionaries. List
keys are logical process names. List values are dictionaries
representing a monitored Valet-related process.

Each dictionary **must** contain the following properties:

    host
    user
    port
    protocol
    start_command
    stop_command
    test_command

Optional properties include:

    order
    priority
    standy_by_list

### Notes

-   The return value of `test_command` **must not** be 0 and should
    reflect the monitored process priority (see next section).

-   `stand_by_list` is an optional comma-delimited list of hosts used in
    conjunction with active/stand-by scenarios. ha\_valet will attempt
    to restart the instance with the lower priority. If that instance
    fails to start, ha\_valet will try restarting the process of the
    next host in the list.

-   `priority` is used to establish the primary/secondary hierarchy. It
    **must** be greater than 0. The lower the number, the higher the
    priority.

### Monitored Process Priority

Monitored process priority is used in conjunction with active/stand-by
scenarios. Unless a process is down, its priority **must** be greater
than 0. The lower the number, the higher the priority.

For example, an instance returning `1` (in response to `test_command`)
will take precedence over an instance returning `2`. A priority of 0
means the process is down.

Examples
--------

### Host A

    :Ostro
        host = Host_A
        stand_by_list = Host_A,Host_B
        user = stack
        port = 8091
        protocol = http
        priority = 1
        start_command="ssh %s@%s 'cd @OSTRO_SERVER_DIR@ ; sudo python ./ostro_daemon.py start'" % (user, host)
        stop_command="ssh %s@%s 'cd @OSTRO_SERVER_DIR@ ; sudo python ./ostro_daemon.py stop'" % (user, host)
        test_command="ssh %s@%s 'exit $(@OSTRO_SERVER_DIR@ ; sudo python ./ostro_daemon.py status ; echo $?)'" % (user, host)

    :Allegro
        host = Host_A
        user = stack
        port = 8090
        protocol = http
        priority = 1
        start_command="sudo python @ALLEGRO_WSGI_DIR@/wsgi.py &"
        stop_command="sudo pkill -f wsgi"
        test_command="netstat -nap  | grep %s | grep LISTEN | wc -l | exit $(awk \'{print $1}\')" % (port)

### Host B (172.20.90.130)

    :Ostro
        host = Host_B
        stand_by_list = Host_A,Host_B
        user = stack
        port = 8091
        protocol = http
        priority = 2
        start_command="ssh %s@%s 'cd @OSTRO_SERVER_DIR@ ; sudo python ./ostro_daemon.py start'" % (user, host)
        stop_command="ssh %s@%s 'cd @OSTRO_SERVER_DIR@ ; sudo python ./ostro_daemon.py stop'" % (user, host)
        test_command="ssh %s@%s 'exit $(@OSTRO_SERVER_DIR@ ; sudo python ./ostro_daemon.py status ; echo $?)'" % (user, host)

    :Allegro
        host = Host_B
        user = stack
        port = 8090
        protocol = http
        priority = 1
        start_command="sudo python @ALLEGRO_WSGI_DIR@/wsgi.py &"
        stop_command="sudo pkill -f wsgi"
        test_command="netstat -nap  | grep %s | grep LISTEN | wc -l | exit $(awk \'{print $1}\')" % (port)

Contact
-------

Joe D'Andrea <jdandrea@research.att.com>