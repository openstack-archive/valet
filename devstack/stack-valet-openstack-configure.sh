#!/usr/bin/env bash

# CONFIGURE OPENSTACK with VALET and RESTART NOVA/HEAT
#====================================================

cd ${HOME}/devstack
source openrc admin admin
if [[ ! `openstack service list | grep valet` ]]; then
    openstack service create --name valet placement
fi
if [[ ! `openstack endpoint list | grep valet` ]]; then
    openstack endpoint create --publicurl http://${HOST_IP}:8090/v1 --adminurl http://${HOST_IP}:8090/v1 --internalurl http://${HOST_IP}:8090/v1 --region RegionOne valet
fi
if [[ ! `openstack user list | grep valet` ]]; then
    openstack user create --project service --enable --password valet valet
    openstack role add --project service --user valet admin
fi

# Workaround: need to manually copy plugins directory into /usr/local/lib/python2.7/dist-packages/valet
sudo cp -R /opt/stack/valet/plugins/valet_plugins /usr/local/lib/python2.7/dist-packages

