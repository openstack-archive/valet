#!/usr/bin/env bash

echo "Uninstalling services required by valet..."
apt -y remove cassandra
apt -y remove zookeeper
apt -y remove zookeeperd
apt -y remove tomcat7
dpkg -r music_3.5.0-0_amd64
pip uninstall --yes notario
pip uninstall --yes pecan-notario

