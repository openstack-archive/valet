#!/usr/bin/env bash

# Configure Valet Core Components
#================================

# Fill in valet.conf
sed -i 's/rabbit_userid/stackrabbit/g' /etc/valet/valet.conf
sed -i 's/rabbit_password/stackqueue/g' /etc/valet/valet.conf
sed -i "s/rabbit_host/${HOST_IP}/g" /etc/valet/valet.conf
sed -i 's/identity_project/service/g' /etc/valet/valet.conf
sed -i 's/identity_user/valet/g' /etc/valet/valet.conf
sed -i 's/identity_password/valet/g' /etc/valet/valet.conf
sed -i "s/auth_uri/http:\/\/${HOST_IP}:35357\/v2.0/g" /etc/valet/valet.conf
sed -i "s/music_host/${HOST_IP}/g" /etc/valet/valet.conf
sed -i 's/music_port/8080/g' /etc/valet/valet.conf
sed -i 's/db_keyspace/valet_keyspace/g' /etc/valet/valet.conf
sed -i 's/engine_priority/1/g' /etc/valet/valet.conf
echo "num_of_region_chars=6" >> /etc/valet/valet.conf

# Modify valet_apache.conf and envvars
sed -i 's/valet_user/valet/g' /etc/apache2/sites-available/valet_apache.conf
sed -i 's/www-data/valet/g' /etc/apache2/envvars

# WORKAROUND FOR CQLSH
if [[ `grep -i dist-packages /usr/bin/cqlsh.py` ]]; then
    echo "cqlsh workaround already installed"
else
    sed -i "s/from uuid import UUID/from uuid import UUID\n\nsys.path.append('\/usr\/lib\/python2.7\/dist-packages')/g" /usr/bin/cqlsh.py
fi

