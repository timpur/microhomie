from homie.core.logger import Logger


LOG = Logger("None Network Module")


def get_if_config():
    return (None, None)


async def manager_task(homie):
    LOG.debug("No network to manage")
    # await asyncio.sleep_ms(0)
    homie.store.set("network.connected", True)
