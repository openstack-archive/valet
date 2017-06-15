#!/usr/bin/env bash

echo "Removing Valet service/endpoint/user from OpenStack"
cd ${HOME}/devstack
source openrc admin admin
openstack endpoint delete valet
openstack service delete valet
openstack user delete valet

echo "Removing Valet executables and data files..."
sudo rm -rf /opt/app/aic-valet-tools
sudo rm /usr/bin/valet-engine
sudo rm -rf /var/run/valet
sudo rm -rf /var/lib/cassandra
sudo rm -rf /var/lib/tomcat7/webapps/MUSIC*
