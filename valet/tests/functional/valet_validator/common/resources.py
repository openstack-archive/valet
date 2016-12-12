# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
'''
Created on May 23, 2016

@author: Yael
'''

from oslo_log import log as logging
import traceback
import yaml

LOG = logging.getLogger(__name__)

TEMPLATE_RES = "resources"


class TemplateResources(object):
    ''' Heat template parser '''
    def __init__(self, template):
        self.instances = []
        self.groups = {}
        self.template_data = None

        try:
            with open(template, "r") as f:
                self.template_data = f.read()
                doc = yaml.load(self.template_data)

                for resource in doc[TEMPLATE_RES]:
                    resource_type = str(doc[TEMPLATE_RES][resource]["type"])
                    if resource_type == "OS::Nova::Server":
                        self.instances.append(Instance(doc, resource))
                    elif resource_type == "ATT::Valet::GroupAssignment":
                        self.groups[resource] = Group(doc, resource)

        except Exception:
            LOG.error("Failed to initialize TemplateResources")
            LOG.error(traceback.format_exc())


class Instance(object):
    def __init__(self, doc, instance_name):
        self.resource_name = instance_name
        self.name = None
        self.image = None
        self.flavor = None
        self.key = None

        self.fill(doc, instance_name)

    def fill(self, doc, instance_name):
        try:
            template_property = doc[TEMPLATE_RES][instance_name]["properties"]

            self.name = template_property["name"]
            self.image = template_property["image"]
            self.flavor = template_property["flavor"]

        except Exception:
            LOG.error("Failed to initialize Instance")
            LOG.error(traceback.format_exc())

    def get_ins(self):
        return("type: %s, name: %s, image: %s, flavor: %s, resource_name: %s "
               % (self.type, self.name, self.image, self.flavor, self.resource_name))


class Group(object):
    def __init__(self, doc, group_name):
        self.group_type = None
        self.group_name = None
        self.level = None
        self.group_resources = []

        self.fill(doc, group_name)

    def fill(self, doc, group_name):
        try:
            template_property = doc[TEMPLATE_RES][group_name]["properties"]

            self.group_type = template_property["group_type"]
            self.group_name = template_property["group_name"] if "group_name" in template_property else None
            self.level = template_property["level"]
            for res in template_property[TEMPLATE_RES]:
                self.group_resources.append(res["get_resource"])

        except Exception:
            LOG.error("Failed to initialize Group")
            LOG.error(traceback.format_exc())
