#!/usr/bin/env bash

# Install all MUSIC components and MUSIC itself
#==============================================

# Install Cassandra
if [[ ! `sudo grep cassandra /etc/apt/sources.list` ]]; then
    export SRC_CMD="echo ${CASSANDRA_DEBIAN_MIRROR} >> /etc/apt/sources.list"
    sudo -E bash -c "${SRC_CMD}"
    sudo curl https://www.apache.org/dist/cassandra/KEYS | sudo apt-key add -
fi
sudo apt-get -y update
sudo apt-get -y install cassandra

sudo service cassandra stop
sudo rm -rf /var/lib/cassandra/data/*
sudo rm -rf /var/lib/cassandra/commitlog/*
sudo chown -R cassandra:cassandra /var/lib/cassandra

# Install latest Zookeeper
sudo apt-get -y install zookeeper
sudo apt-get -y install zookeeperd

# Install latest Tomcat
sudo apt-get -y install tomcat7

# Install Music
echo "Installing music from ${MUSIC_URL}..."
sudo wget ${MUSIC_URL}/${MUSIC_FILE}
sudo dpkg -i ${MUSIC_FILE}

