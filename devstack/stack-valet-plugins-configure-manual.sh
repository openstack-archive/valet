#!/usr/bin/env bash

# Modify Heat conf file to include Valet configuration
sudo vi /etc/heat/heat.conf
  [DEFAULT]
  ...
  plugin_dirs=/usr/local/lib/python2.7/dist-packages/valet_plugins/heat

  [valet]
  read_timeout=5
  url=http://${HOST_IP}:8090/v1
  connect_timeout=1

# Modify Nova conf file to include Valet configuration
sudo vi /etc/nova/nova.conf
  [DEFAULT]
  ...
  scheduler_available_filters=nova.scheduler.filters.all_filters
  scheduler_available_filters=valet_plugins.plugins.nova.valet_filter.ValetFilter
  scheduler_default_filters = RetryFilter,AvailabilityZoneFilter,RamFilter,DiskFilter,ComputeFilter,ComputeCapabilitiesFilter,ImagePropertiesFilter,ServerGroupAntiAffinityFilter,ServerGroupAffinityFilter,SameHostFilter,DifferentHostFilter,ValetFilter
  ...

  [valet]
  url=http://${HOST_IP}:8090/v1
  admin_username=valet
  connect_timeout=5
  admin_tenant_name=service
  admin_auth_url=http://${HOST_IP}/identity_v2_admin/v2.0/
  read_timeout=600
  failure_mode=reject
  admin_password=valet

# Restart nova scheduler (n-sch) and heat processes (h-eng, h-api, h-api-cfn, h-api-cw) using screen
sudo systemctl restart devstack@n-sch.service
sudo systemctl restart devstack@h-eng.service
sudo systemctl restart devstack@h-api.service
sudo systemctl restart devstack@h-api-cfn.service
sudo systemctl restart devstack@h-api-cw.service

