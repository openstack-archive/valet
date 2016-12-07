
from oslo_config import cfg


def logger_conf(logger_name):
    return [
        cfg.StrOpt('output_format', default="%(asctime)s - %(levelname)s - %(message)s"),  # dict
        cfg.BoolOpt('store', default=True),
        cfg.StrOpt('logging_level', default='debug'),
        cfg.StrOpt('logging_dir', default='/var/log/valet/'),
        cfg.StrOpt('logger_name', default=logger_name + ".log"),
        cfg.IntOpt('max_main_log_size', default=5000000),
        cfg.IntOpt('max_log_size', default=1000000),
        cfg.IntOpt('max_num_of_logs', default=3),
    ]
