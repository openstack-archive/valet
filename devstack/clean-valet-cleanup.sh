#!/usr/bin/env bash

echo "Removing Valet service/endpoint/user from OpenStack"
cd ${HOME}/devstack
source openrc admin admin
openstack endpoint delete valet
openstack service delete valet
openstack user delete valet

# May not want to do these things, but not sure...
#sudo rm -f /etc/apache2/sites-enabled/valet_apache.conf
#sudo rm -f /etc/apache2/sites-available/valet_apache.conf
#sudo rm -rf /var/log/apache2/valet
#sudo rm -rf /var/www/valet
#sudo rm -rf /etc/valet
#sudo rm -rf /var/log/valet
#sudo rm -rf /var/log/apache2/valet
#sudo rm -rf /etc/zookeeper
#sudo rm -rf /etc/cassandra
#sudo deluser valet

# Definitely need to remove these things:
echo "Removing Valet executables and data files..."
sudo rm -rf /opt/app/aic-valet-tools
sudo rm /usr/bin/valet-engine
sudo rm -rf /var/run/valet
sudo rm -rf ${HOME}/.cassandra
sudo rm -rf /etc/cassandra
sudo rm -rf /var/lib/cassandra
sudo rm -rf /var/lib/tomcat7/webapps/MUSIC*
