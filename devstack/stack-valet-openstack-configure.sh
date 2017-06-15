#!/usr/bin/env bash

# CONFIGURE OPENSTACK with VALET and RESTART NOVA/HEAT
#====================================================

cd ${HOME}/devstack
source openrc admin admin
if [[ ! `openstack service list | grep valet` ]]; then
    echo "Creating Valet (placement) service..."
    openstack service create --name valet placement
fi
if [[ ! `openstack endpoint list | grep valet` ]]; then
    echo "Creating Valet service endpoint..."
    openstack endpoint create --publicurl http://${HOST_IP}:8090/v1 --adminurl http://${HOST_IP}:8090/v1 --internalurl http://${HOST_IP}:8090/v1 --region RegionOne valet
fi
if [[ ! `openstack user list | grep valet` ]]; then
    echo "Creating Valet user and adding appropriate roles..."
    openstack user create --project service --enable --password valet valet
    openstack role add --project service --user valet admin
fi

echo "Copying ${OPENSTACK_PLUGIN_PATH} into /usr/local/lib/python2.7/dist-packages..."
sudo cp -R ${OPENSTACK_PLUGIN_PATH} /usr/local/lib/python2.7/dist-packages

