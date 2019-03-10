import uasyncio.core as asyncio

from homie.core.logger import Logger
from homie.modules.base import HomieModule


LOG = Logger("Network Module")


def _import(module):
    return __import__(module, globals(), locals(), [], 0)


class NetworkModule(HomieModule):
    def init(self):
        LOG.debug("Init")
        self._module = None
        self._tasks = []

    def start(self):
        LOG.debug("Start")
        self._homie.store.set("network.connected", False)

        mode = self._homie.store.get("network.mode")
        if mode == "wifi":
            self._module = _import('homie.modules.network.wifi')
        elif mode == 'none':
            self._module = _import('homie.modules.network.none')
        else:
            raise Exception("Unknown network mode")

        self._tasks.append(self._homie.add_task(self._module.manager_task))

    def stop(self, reason):
        LOG.debug("Stop:", reason)
        for task in self._tasks:
            self._homie.stop_task(task)
        self._homie.store.set("network.connected", False)

    def get_if_config(self):
        return self._module.get_if_config()
