#!/usr/bin/env bash

# START SERVICES and VALET
#=========================

# Start MUSIC Services required for Valet
echo "Starting Cassandra service..."
sudo service cassandra restart
echo "Starting Zookeeper service..."
sudo service zookeeper restart
echo "Starting Tomcat service..."
sudo service tomcat7 restart

echo "Started MUSIC services...wait 30 seconds before proceeding..."
sleep 30

# Start Valet API
echo "Starting Valet API..."
sudo apachectl graceful

# Populate the database and setup Apache wsgi app
# NOTE: this must come after apache is restarted because this
#       next step helps set up the WSGI App running in apache.
sleep 10
echo "Populating Valet Database and Configuring WSGI app..."
cd /opt/app/aic-valet-tools
./pecan_populate.sh

# Start Valet Engine
# NOTE: this must come after apache is restarted because keystone
#       also runs within apache!
sleep 30
echo "Starting Valet Engine..."
sudo -u valet python /usr/bin/valet-engine -c start

