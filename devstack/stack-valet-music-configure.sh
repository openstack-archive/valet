#!/usr/bin/env bash

# Configure MUSIC components
#===========================

sed -i 's/Test Cluster/Valet Cluster/g' /etc/cassandra/cassandra.yaml
sed -i 's/snitch: SimpleSnitch/snitch: GossipingPropertyFileSnitch/g' /etc/cassandra/cassandra.yaml
echo "quorumListenOnAllIPs=true" >> /etc/zookeeper/conf/zoo.cfg
echo "server.1=${HOST_IP}:2888:3888" >> /etc/zookeeper/conf/zoo.cfg
sed -i "s/replace this text with the cluster-unique zookeeper's instance id (1-255)/1/g" /var/lib/zookeeper/myid

