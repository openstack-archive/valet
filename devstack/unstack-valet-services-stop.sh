#!/usr/bin/env bash

echo "Stopping valet-engine process..."
sudo -u valet python /usr/bin/valet-engine -c stop
echo "Stopping Apache2 service..."
sudo service apache2 stop
echo "Stopping Tomcat service..."
sudo service tomcat7 stop
echo "Stopping Zookeeper service..."
sudo service zookeeper stop
echo "Stopping Cassandra service..."
sudo service cassandra stop
echo "Done shutting down Valet services."
