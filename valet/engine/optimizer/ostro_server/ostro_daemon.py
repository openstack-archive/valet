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

# Modified: Sep. 22, 2016

import os
import sys
import traceback
from valet.engine.optimizer.ostro.ostro import Ostro
from valet.engine.optimizer.ostro_server.configuration import Config
from valet.engine.optimizer.ostro_server.daemon import Daemon   # implemented for Python v2.7
from valet.engine.optimizer.util.util import init_logger


class OstroDaemon(Daemon):

    def run(self):

        self.logger.info("##### Valet Engine is launched #####")
        try:
            ostro = Ostro(config, self.logger)
        except Exception:
            self.logger.error(traceback.format_exc())

        if ostro.bootstrap() is False:
            self.logger.error("ostro bootstrap failed")
            sys.exit(2)

        ostro.run_ostro()


def verify_dirs(list_of_dirs):
    for d in list_of_dirs:
        try:
            if not os.path.exists(d):
                os.makedirs(d)
        except OSError:
            print("Error while verifying: " + d)
            sys.exit(2)


if __name__ == "__main__":
    ''' configuration '''
    # Configuration
    try:
        config = Config()
        config_status = config.configure()
        if config_status != "success":
            print(config_status)
            sys.exit(2)

        ''' verify directories '''
        dirs_list = [config.logging_loc, config.resource_log_loc, config.app_log_loc, os.path.dirname(config.process)]
        verify_dirs(dirs_list)

        ''' logger '''
        logger = init_logger(config)

        # Start daemon process
        daemon = OstroDaemon(config.priority, config.process, logger)

        logger.info("%s ostro ..." % config.command)
        # switch case
        exit_code = {
            'start': daemon.start,
            'stop': daemon.stop,
            'restart': daemon.restart,
            'status': daemon.status,
        }[config.command]()
        exit_code = exit_code or 0

    except Exception:
        logger.error(traceback.format_exc())
        exit_code = 2

    sys.exit(int(exit_code))
