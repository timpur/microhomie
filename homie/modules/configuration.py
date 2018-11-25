import ujson as json

from homie.modules.base import HomieModule
from homie.core.logger import Logger


LOG = Logger("Configuration Module")


FILE_NAME = "config.json"

IGNORE_STORE_PATHS = [
    "core.state",
    "network.connected",
    "mqtt.connected",
    "convention",
]


def dict_merge(source, destination, ignore_paths=[], path=None):
    for key, val in source.items():
        current_path = ".".join([path, key]) if path else key
        if current_path in ignore_paths:
            continue
        if isinstance(val, dict):
            if not isinstance(destination.get(key), dict):
                destination[key] = {}
            dict_merge(val, destination[key], ignore_paths, current_path)
        else:
            destination[key] = source[key]
    return destination


class ConfigurationModule(HomieModule):
    def start(self):
        LOG.debug("Start")
        self.load(FILE_NAME, self.homie.store.state, IGNORE_STORE_PATHS)
        LOG.success("Loaded Config")

    def stop(self, reason):
        LOG.debug("Stop:", reason)
        self.save(FILE_NAME, self.homie.store.state, IGNORE_STORE_PATHS)
        LOG.success("Saved Config")

    def load(self, file_name, destination, ignore_paths):
        try:
            config_file = open(file_name)
            config = json.load(config_file)
            config_file.close()
            dict_merge(config, destination, ignore_paths)
        except OSError:
            pass
        except ValueError:
            pass

    def save(self, file_name, source, ignore_paths):
        try:
            config_file = open(file_name, 'w')
            config = dict_merge(source, {}, ignore_paths)
            json.dump(config, config_file)
            config_file.close()
        except OSError:
            pass
        except ValueError:
            pass

    def validate(self, config):
        None
