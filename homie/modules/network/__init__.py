import uasyncio.core as asyncio

from homie.core.logger import Logger
from homie.modules.base import HomieModule


LOG = Logger("Network Module")


def _import(module):
    return __import__(module, globals(), locals(), [], 0)


async def manage_no_network(homie):
    LOG.debug("No network to manage")
    # await asyncio.sleep_ms(0)
    homie.store.set("network.connected", True)


class NetworkModule(HomieModule):
    def __init__(self, homie):
        super().__init__(homie)
        self._module = None
        self._tasks = []

    def start(self):
        LOG.debug("Start")
        self.homie.store.set("network.connected", False)

        mode = self.homie.store.get("network.mode")
        if mode == "wifi":
            self._module = _import('homie.modules.network.wifi')

        if self._module:
            self._tasks.append(self.homie.add_task(self._module.manager_task))
        else:
            self._tasks.append(self.homie.add_task(manage_no_network))

    def stop(self, reason):
        LOG.debug("Stop:", reason)
        for task in self._tasks:
            self.homie.stop_task(task)
        self.homie.store.set("network.connected", False)

    def get_ifconfig(self, param):
        if self._module:
            return self._module.get_ifconfig(param)
        return None
