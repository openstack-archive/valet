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

"""Application."""

from pecan.deploy import deploy
from pecan import make_app

from valet import api
from valet.api.common import identity
from valet.api.common import messaging
from valet.api.db import models
from valet.common.conf import get_logger


def setup_app(config):
    """App Setup."""
    identity.init_identity()
    messaging.init_messaging()
    models.init_model()
    app_conf = dict(config.app)

    return make_app(
        app_conf.pop('root'),
        logging=getattr(config, 'logging', {}), **app_conf)


# entry point for apache2
def load_app(config_file):
    """App Load."""
    api.LOG = get_logger("api")

    return deploy(config_file)
