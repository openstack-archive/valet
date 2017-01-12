#
# Copyright 2014-2017 AT&T Intellectual Property
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo_config import cfg

service_available_group = cfg.OptGroup(name="service_available",
                                       title="Available OpenStack Services")

ServiceAvailableGroup = [
    cfg.BoolOpt("valet",
                default=True,
                help="Whether or not valet is expected to be available"),
]

placement_group = cfg.OptGroup(name="placement",
                               title="Valet Service option")
PlacementGroup = [
    cfg.StrOpt('catalog_type',
               default='placement',
               help="Catalog type of the placement service."),
    cfg.StrOpt("endpoint_type",
               default="publicURL",
               choices=["publicURL", "adminURL", "internalURL"],
               help="The endpoint type for valet service."),
]

valet_group = cfg.OptGroup(name="valet", title="Valet basic")

opt_valet = \
    [
        cfg.IntOpt('TRIES_TO_CREATE', default=5),
        cfg.IntOpt('PAUSE', default=5),
    ]
