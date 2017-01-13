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

"""Util."""

from os import listdir, stat
from os.path import isfile, join
import logging
from logging.handlers import RotatingFileHandler


def get_logfile(_loc, _max_log_size, _name):
    """Get logfile from location and return with file mode."""
    files = [f for f in listdir(_loc) if isfile(join(_loc, f))]

    logfile_index = 0
    for f in files:
        f_name_list = f.split(".")
        f_type = f_name_list[len(f_name_list) - 1]
        if f_type == "log":
            f_id_list = f.split("_")
            temp_f_id = f_id_list[len(f_id_list) - 1]
            f_id = temp_f_id.split(".")[0]
            f_index = int(f_id)
            if f_index > logfile_index:
                logfile_index = f_index

    last_logfile = _name + "_" + str(logfile_index) + ".log"

    mode = None
    if isfile(_loc + last_logfile) is True:
        statinfo = stat(_loc + last_logfile)
        if statinfo.st_size > _max_log_size:
            last_logfile = _name + "_" + str(logfile_index + 1) + ".log"
            mode = 'w'
        else:
            mode = 'a'
    else:
        mode = 'w'

    return (last_logfile, mode)


def get_last_logfile(_loc, _max_log_size, _max_num_of_logs,
                     _name, _last_index):
    """Return last logfile from location with index and mode."""
    last_logfile = _name + "_" + str(_last_index) + ".log"
    mode = None

    if isfile(_loc + last_logfile) is True:
        statinfo = stat(_loc + last_logfile)
        if statinfo.st_size > _max_log_size:
            if (_last_index + 1) < _max_num_of_logs:
                _last_index = _last_index + 1
            else:
                _last_index = 0

            last_logfile = _name + "_" + str(_last_index) + ".log"

            mode = 'w'
        else:
            mode = 'a'
    else:
        mode = 'w'

    return (last_logfile, _last_index, mode)


def adjust_json_string(_data):
    """Adjust data value formatting to be consistent and return."""
    _data = _data.replace("None", '"none"')
    _data = _data.replace("False", '"false"')
    _data = _data.replace("True", '"true"')
    _data = _data.replace('_"none"', "_none")
    _data = _data.replace('_"false"', "_false")
    _data = _data.replace('_"true"', "_true")

    return _data


def init_logger(config):
    """Return an initialized logger."""
    log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - "
                                      "%(message)s")
    log_handler = RotatingFileHandler(config.logging_loc + config.logger_name,
                                      mode='a',
                                      maxBytes=config.max_main_log_size,
                                      backupCount=2,
                                      encoding=None,
                                      delay=0)
    log_handler.setFormatter(log_formatter)
    logger = logging.getLogger(config.logger_name)
    logger.setLevel(logging.DEBUG if config.logging_level == "debug"
                    else logging.INFO)
    logger.addHandler(log_handler)

    return logger
