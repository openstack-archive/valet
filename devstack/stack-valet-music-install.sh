#!/usr/bin/env bash

# Install all MUSIC components and MUSIC itself
#==============================================

# Install latest Cassandra
sudo bash -c 'echo "deb http://www.apache.org/dist/cassandra/debian 310x main" >> /etc/apt/sources.list'
sudo curl https://www.apache.org/dist/cassandra/KEYS | sudo apt-key add -
sudo apt-get -y update
sudo apt-get -y install cassandra

sudo service cassandra stop
sudo rm -rf /var/lib/cassandra/data/*
sudo rm -rf /var/lib/cassandra/commitlog/*

# Install latest Zookeeper
sudo apt-get -y install zookeeper
sudo apt-get -y install zookeeperd

# Install Tomcat and Music
sudo apt-get -y install tomcat7
sudo wget http://mirrors-aic.it.att.com/aic-ops/ops-infra/pool/main/m/music/music_3.5.0-0_amd64.deb
sudo dpkg -i music_3.5.0-0_amd64.deb

