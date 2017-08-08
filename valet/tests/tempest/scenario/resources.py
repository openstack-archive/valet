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

"""Resources."""

from oslo_log import log as logging
import traceback
import yaml

LOG = logging.getLogger(__name__)

TEMPLATE_RES = "resources"


class TemplateResources(object):
    """Heat template parser."""

    def __init__(self, template):
        """Init heat template parser."""
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
                        temp = Group(doc, resource)

                        if not any(self.groups):
                            self.groups[temp.group_name] = temp
                        elif temp.group_name in self.groups:
                            self.groups[temp.group_name].group_resources. \
                                append(resource)
                        else:
                            self.groups[temp.group_name] = temp

        except Exception:
            LOG.error("Failed to initialize TemplateResources")
            LOG.error(traceback.format_exc())


class Instance(object):
    """Nova Instance."""

    def __init__(self, doc, instance_name):
        """Init instance with name, image, flavor, key and call fill."""
        self.resource_name = instance_name
        self.name = None
        self.image = None
        self.flavor = None
        self.key = None

        self.fill(doc, instance_name)

    def fill(self, doc, instance_name):
        """Fill instance based on template."""
        try:
            template_property = doc[TEMPLATE_RES][instance_name]["properties"]

            self.name = template_property["name"]
            self.image = template_property["image"]
            self.flavor = template_property["flavor"]

        except Exception:
            LOG.error("Failed to initialize Instance")
            LOG.error(traceback.format_exc())

    def get_ins(self):
        """Return instance and its data."""
        return("type: %s, name: %s, image: %s, flavor: %s, resource_name: %s "
               % (self.type, self.name, self.image, self.flavor,
                  self.resource_name))


class Group(object):
    def __init__(self, doc, instance_name):
        self.group_name = None
        self.group_resources = []

        self.fill(doc, instance_name)

    def fill(self, doc, instance_name):
        try:
            property_metadata = (doc[TEMPLATE_RES][instance_name]["properties"]
                                 ["metadata"]["valet"])

            self.group_name = property_metadata["groups"][0] \
                if "groups" in property_metadata else None
            self.group_resources.append(instance_name)

        except Exception:
            LOG.error("Failed to initialize Group")
            LOG.error(traceback.format_exc())
