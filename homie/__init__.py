__version__ = "0.4.0"

from homie.core import HomieCore
from homie.modes.normal import MODE_NORMAL
from homie.modes.config import MODE_CONFIG
from homie.modules.configuration import ConfigurationModule


class Homie(HomieCore):
    def __init__(self, setup):
        super().__init__()
        if not setup:
            raise Exception("setup is required")
        self._setup = setup

    def setup(self):
        self.add_module(ConfigurationModule)
        self.add_mode('normal', MODE_NORMAL)
        self.add_mode('config', MODE_CONFIG)

        run = self._setup(self)
        if run:
            self.add_task(run, homie_arg=False)

        super().setup()
