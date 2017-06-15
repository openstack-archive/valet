#!/usr/bin/env bash

# Install Valet Core (still in venv)
#==================================
cd /opt/stack/valet
if [ ! `id -u valet` ]; then 
    sudo adduser --system --group valet
fi
sudo python setup.py install

if [ ! -d /etc/valet ]; then
    sudo mkdir /etc/valet
    sudo chmod 0777 /etc/valet
    sudo cp /usr/local/etc/valet/valet/valet.conf /etc/valet/valet.conf
    sudo chown -R valet:valet /etc/valet
fi
if [ ! -d /var/log/valet ]; then
    sudo mkdir /var/log/valet
    sudo chown valet:valet /var/log/valet
    sudo chmod 0777 /var/log/valet
fi
if [ ! -d /var/run/valet ]; then
    sudo mkdir /var/run/valet
    sudo chown valet:valet /var/run/valet
    sudo chmod 0750 /var/run/valet
fi
sudo cp /opt/stack/valet/bin/valet-engine /usr/bin/valet-engine
sudo chown valet:valet /usr/bin/valet-engine

# Following are needed to be able to run cleandb.sh
# and pecan_populate.sh
sudo mkdir /opt/app
sudo mkdir /opt/app/aic-valet-tools
sudo cp /opt/stack/valet/tools/utils/* /opt/app/aic-valet-tools
sudo chmod -R 0777 /opt/app/aic-valet-tools
sudo chown -R valet:valet /opt/app/aic-valet-tools

# Install Apache configuration files/directories
if [ ! -f /etc/apache2/sites-available/valet_apache.conf ]; then
    sudo cp /usr/local/etc/valet/valet/api/valet_apache.conf /etc/apache2/sites-available/valet_apache.conf
    sudo ln -s /etc/apache2/sites-available/valet_apache.conf /etc/apache2/sites-enabled/valet_apache.conf
fi
sudo mkdir /var/www/valet
sudo cp /usr/local/etc/valet/valet/api/config.py /var/www/valet/config.py
sudo cp /usr/local/etc/valet/valet/api/app.wsgi /var/www/valet/app.wsgi
sudo chown -R valet:valet /var/www/valet
sudo chmod 0777 /var/www/valet
if [ ! -d /var/log/apache2/valet ]; then
    sudo mkdir /var/log/apache2/valet
    sudo chmod 0777 /var/log/apache2/valet
fi

# Remove this dir as it is no longer needed, and would be
# confusing to leave it there.
sudo rm -R /usr/local/etc/valet

