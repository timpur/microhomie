import utime as time
import uasyncio.core as asyncio

from homie.core import HomieCore
from homie.core.logger import Logger
from homie.core.node import HomieNode
from homie.core.property import HomieProperty
from homie.core.task import WaitForStateToBe
from homie.modes.normal import MODE_NORMAL


LOG = Logger("Main")

SIMPLE_NODE = HomieNode("simple-node", "Test Node", type="test")
SIMPLE_PROP = HomieProperty("simple-prop", "Test Prop", settable=True)
SIMPLE_NODE.add_property(SIMPLE_PROP)


def setup():
    homie = HomieCore()

    homie.add_mode("normal", MODE_NORMAL)
    homie.set_mode("normal")

    homie.add_task(run)

    homie.add_node(SIMPLE_NODE)

    homie.store.set("core.id", "simple-device")
    homie.store.set("core.name", "Simple Device")
    homie.store.set("network.mode", None)  # linux
    homie.store.set("mqtt.host", "mqtt.example.com")
    # homie.store.set("mqtt.username", "usr")
    # homie.store.set("mqtt.password", "pass")

    homie.setup()

    homie.run()


async def run(homie):
    await WaitForStateToBe(homie.store, "convention.ready", True)
    SIMPLE_PROP.value = time.time()
    await asyncio.sleep(10)
    homie.stop()


setup()
