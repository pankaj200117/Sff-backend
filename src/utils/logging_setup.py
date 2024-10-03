import logging
import logging.config
import os
import yaml


def setup_logging(
    default_path='configs/logging.yaml',
    log_file_path=None,
):
    path = default_path
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        if log_file_path is not None:
            config["handlers"]["file"]["filename"] = log_file_path
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        logging.config.dictConfig(config)
    else:
        print("Failed to load configuration file. Using default configs.")
        logging.basicConfig(level=logging.INFO)


class RelativePathFilter(logging.Filter):
    def __init__(self, relative_to):
        super().__init__()
        self.relative_to = relative_to

    def filter(self, record):
        record.pathname = os.path.relpath(record.pathname, self.relative_to)
        return True
