#!/usr/bin/env bash

# Configure Valet Core Components
#================================

# Generate valet.conf
echo -e "[DEFAULT]" > /etc/valet/valet.conf
echo -e "default_log_levels=\"api=DEBUG,valet=DEBUG,ostro_daemon=DEBUG,ostro_listener=INFO,music=INFO,requests=ERROR,pika=ERROR,pecan=ERROR,urllib3=ERROR\"" >> /etc/valet/valet.conf
echo -e "logging_default_format_string='%(asctime)s.%(msecs)03d [%(levelname)-5.5s] [%(name)s] - %(message)s'" >> /etc/valet/valet.conf
echo -e "use_stderr=False" >> /etc/valet/valet.conf
echo -e "log_dir=/var/log/valet\n" >> /etc/valet/valet.conf
echo -e "[messaging]" >> /etc/valet/valet.conf
echo -e "username=stackrabbit" >> /etc/valet/valet.conf
echo -e "password=stackqueue" >> /etc/valet/valet.conf
echo -e "host=${HOST_IP}" >> /etc/valet/valet.conf
echo -e "port=5672\n" >> /etc/valet/valet.conf
echo -e "[identity]" >> /etc/valet/valet.conf
echo -e "project_name=service" >> /etc/valet/valet.conf
echo -e "username=valet" >> /etc/valet/valet.conf
echo -e "password=valet" >> /etc/valet/valet.conf
echo -e "auth_url=http://${HOST_IP}:35357/v2.0\n" >> /etc/valet/valet.conf
echo -e "[music]" >> /etc/valet/valet.conf
echo -e "hosts=${HOST_IP}" >> /etc/valet/valet.conf
echo -e "port=8080" >> /etc/valet/valet.conf
echo -e "keyspace=valet_keyspace" >> /etc/valet/valet.conf
echo -e "music_server_retries=3\n" >> /etc/valet/valet.conf
echo -e "[engine]" >> /etc/valet/valet.conf
echo -e "datacenter_name=Region1" >> /etc/valet/valet.conf
echo -e "priority=1" >> /etc/valet/valet.conf
echo -e "compute_trigger_frequency=1800" >> /etc/valet/valet.conf
echo -e "topology_trigger_frequency=3600" >> /etc/valet/valet.conf
echo -e "update_batch_wait=600" >> /etc/valet/valet.conf
echo -e "default_cpu_allocation_ratio=8" >> /etc/valet/valet.conf
echo -e "default_ram_allocation_ratio=1" >> /etc/valet/valet.conf
echo -e "default_disk_allocation_ratio=1" >> /etc/valet/valet.conf
echo -e "static_cpu_standby_ratio=0" >> /etc/valet/valet.conf
echo -e "static_mem_standby_ratio=0" >> /etc/valet/valet.conf
echo -e "static_local_disk_standby_ratio=0" >> /etc/valet/valet.conf
echo -e "num_of_region_chars=6" >> /etc/valet/valet.conf

# Modify valet_apache.conf and envvars
sed -i 's/valet_user/valet/g' /etc/apache2/sites-available/valet_apache.conf
sed -i 's/www-data/valet/g' /etc/apache2/envvars

# WORKAROUND FOR CQLSH
if [[ `grep -i dist-packages /usr/bin/cqlsh.py` ]]; then
    echo "cqlsh workaround already installed"
else
    sed -i "s/from uuid import UUID/from uuid import UUID\n\nsys.path.append('\/usr\/lib\/python2.7\/dist-packages')/g" /usr/bin/cqlsh.py
fi

