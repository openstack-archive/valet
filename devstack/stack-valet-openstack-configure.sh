#!/usr/bin/env bash

# CONFIGURE OPENSTACK with VALET and RESTART NOVA/HEAT
#====================================================

cd /home/ubuntu/devstack
source openrc admin admin
openstack service create --name valet placement
openstack endpoint create --publicurl http://${HOST_IP}:8090/v1 --adminurl http://${HOST_IP}:8090/v1 --internalurl http://${HOST_IP}:8090/v1 --region RegionOne valet
openstack user create --project service --enable --password valet valet
openstack role add --project service --user valet admin

# Workaround: need to manually copy plugins directory into /usr/local/lib/python2.7/dist-packages/valet
sudo cp -R /opt/stack/valet/plugins/valet_plugins /usr/local/lib/python2.7/dist-packages

