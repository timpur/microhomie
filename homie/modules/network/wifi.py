import network
import uasyncio.core as asyncio

from homie.core.logger import Logger
from homie.modules.base import HomieModule


log = Logger("WiFi Network Module")


def get_ifconfig(param):
    None


async def manager_task(homie):
    log.debug("WiFi manager started")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.disconnect()
    while True:
        if not wlan.isconnected():
            homie.store.set("network.connected", False)
            wlan.connect(
                homie.store.get("network.wifi.ssid"),
                homie.store.get("network.wifi.password")
            )
            log.info("Waiting for connection...")
            while not wlan.isconnected():
                await asyncio.sleep(1)
            homie.store.set("network.connected", True)
            log.success("Connected, network config: %s" % repr(wlan.ifconfig()))
        else:
            await asyncio.sleep(1)
