import network
import uasyncio.core as asyncio

from homie.core.logger import Logger


LOG = Logger("WiFi Network Module")


def get_if_config(param):
    # TODO: finish getting 'ip' and 'mac' params
    return (None, None)


async def manager_task(homie):
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
            LOG.info("Waiting for connection...")
            while not wlan.isconnected():
                await asyncio.sleep(1)
            homie.store.set("network.connected", True)
            LOG.success("Connected, network config: %s" % repr(wlan.ifconfig()))
        else:
            await asyncio.sleep(1)
