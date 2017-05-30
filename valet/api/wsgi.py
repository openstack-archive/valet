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
import os
from pecan.deploy import deploy

from common.i18n import _

from valet import api
from valet.common.conf import get_logger
from valet.common.conf import init_conf


def config_file(file_name=None):
    """Return absolute location of the config file."""
    file_name = file_name or 'config.py'
    _file = os.path.abspath(__file__)

    def dirname(x):
        return os.path.dirname(x)
    parent_dir = dirname(_file)
    return os.path.join(parent_dir, file_name)


def application(environ, start_response):
    """Return a WSGI app object."""
    wsgi_app = deploy(config_file('prod.py'))
    return wsgi_app(environ, start_response)

# TODO(JD): Integrate this with a python entry point
# This way we can run valet-api from the command line in a pinch.
if __name__ == '__main__':
    try:
        from wsgiref.simple_server import make_server  # disable=C0411,C0413

        # TODO(JD): At some point, it would be nice to use pecan_mount
        # import pecan_mount
        # HTTPD = make_server('', 8090, pecan_mount.tree)
#         from valet.api.conf import register_conf, set_domain
        init_conf("wsgi.log")
        api.LOG = get_logger("wsgi")
        HTTPD = make_server(
            '', 8090, deploy(config_file('/var/www/valet/config.py')))
        print(_("Serving HTTP on port 8090..."))

        # Respond to requests until process is killed
        HTTPD.serve_forever()
    except Exception:
        import traceback
        print(traceback.format_exc())
