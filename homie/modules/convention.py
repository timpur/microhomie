import sys
import uasyncio.core as asyncio

from homie import __version__
from homie.modules.base import HomieModule, import_module
from homie.core.logger import Logger
from homie.core.task import WaitForStateToBe
from homie.utils import payload_down, payload_up
from homie.core.node import STORE_NODE_PATH


CONVENTION_VERSION = "3.0.1"
BROADCAST_TOPIC = "homie/$broadcast"
BROADCAST_STORE_PATH = "convention.broadcast"
STORE_SET_META_MQTT = "mqtt_setter"

LOG = Logger("Convention Module")


def join_topics(*args):
    return '/'.join(filter(lambda item: False if item is None else True, args))


def get_prop(nodes, node_id, prop_id):
    node = nodes.get(node_id)
    if node:
        prop = node.properties.get(prop_id)
        if prop:
            return prop
    return None


class ConventionModule(HomieModule):
    def __init__(self, homie):
        super().__init__(homie)
        self._network = None
        self._mqtt = None
        self._base_topic = None
        self._tasks = []

    def start(self):
        LOG.debug("Start")
        self.homie.store.set("convention.ready", False)
        self._network = import_module(self.homie, "NetworkModule")
        self._mqtt = import_module(self.homie, "MQTTModule")
        self._base_topic = join_topics(self.homie.store.get("mqtt.base"), self.homie.store.get("core.id"))
        self._mqtt.set_last_will(join_topics(self._base_topic, '$state'), "lost", True)
        self._mqtt.callbacks.subscribe(self.on_message)
        self.homie.store.subscribe(self.on_store_change)
        self._tasks.append(self.homie.add_task(self._manage_convention))

    def stop(self, reason):
        LOG.debug("Stop:", reason)
        for task in self._tasks:
            self.homie.stop_task(task)
        self.publish("$state", "sleeping" if reason == "sleep" else "disconnected")
        self.homie.store.set("convention.ready", False)

    def publish(self, topic, payload, retained=True, required=True):
        topic = join_topics(self._base_topic, topic)
        payload = payload_down(payload)
        if required or (not required and payload):
            self._mqtt.publish(topic, payload_down(payload), retained)

    def publish_node(self, node, topic, payload, retained=True, required=True):
        topic = join_topics(node.id, topic)
        self.publish(topic, payload, retained, required)

    def publish_prop(self, prop, topic, payload, retained=True, required=True):
        topic = join_topics(prop.id, topic)
        self.publish_node(prop.node, topic, payload, retained, required)

    def subscribe(self, topic):
        topic = join_topics(self._base_topic, topic)
        self._mqtt.subscribe(topic)

    def on_message(self, topic, payload):
        payload = payload_up(payload)
        if "/set" in topic:
            paths = topic.split('/')
            prop = get_prop(self.homie.nodes, paths[-3], paths[-2])
            if prop and prop.settable:
                self.homie.store.set(prop.path, payload, STORE_SET_META_MQTT)
        elif BROADCAST_TOPIC in topic:
            LOG.info("Broadcast:", topic, payload)
            key = topic.replace(BROADCAST_TOPIC+"/", "")
            self.homie.store.set("{}.{}".format(BROADCAST_STORE_PATH, key), payload, STORE_SET_META_MQTT)

    def on_store_change(self, path, value, _, meta):
        if path.startswith(STORE_NODE_PATH):
            paths = path.split('.')
            prop = get_prop(self.homie.nodes, paths[-2], paths[-1])
            if prop:
                if prop.settable and meta != STORE_SET_META_MQTT:
                    self.publish_prop(prop, "set", value)
                self.publish_prop(prop, None, value, False)

    async def _manage_convention(self, _):
        while True:
            await WaitForStateToBe(self.homie.store, "mqtt.connected", True, only_change=True)
            self.homie.store.set("convention.ready", False)
            self.publish("$state", "init")
            self.advertise_device()
            self.advertise_nodes()
            self.subscribe_to_topics()
            await asyncio.sleep_ms(100)  # wait for subscription messages
            self.publish("$state", "ready")
            self.homie.store.set("convention.ready", True)

    def advertise_device(self):
        pub = self.publish

        pub("$homie", CONVENTION_VERSION)
        pub("$name", self.homie.store.get("core.name"))
        pub("$localip", self._network.get_ifconfig("ip"))
        pub("$mac", self._network.get_ifconfig("mac"))
        pub("$fw/name", "")  # TODO:
        pub("$fw/version", "")  # TODO:
        pub("$implementation", "{}@{}".format("microhomie", __version__))
        pub("$nodes", ",".join(self.homie.nodes.keys()))

    def advertise_nodes(self):
        pub_node = self.publish_node
        pub_prop = self.publish_prop

        for node in self.homie.nodes.values():
            pub_node(node, "$name", node.name)
            pub_node(node, "$type", node.type)
            pub_node(node, "$properties", ",".join(node.properties.keys()))
            for prop in node.properties.values():
                pub_prop(prop, "$name", prop.name, required=False)
                pub_prop(prop, "$settable", prop.settable, required=False)
                pub_prop(prop, "$retained", prop.retained, required=False)
                pub_prop(prop, "$unit", prop.unit, required=False)
                pub_prop(prop, "$datatype", prop.data_type, required=False)
                pub_prop(prop, "$format", prop.format, required=False)
                pub_prop(prop, None, prop.value)

    def subscribe_to_topics(self):
        self._mqtt.subscribe(BROADCAST_TOPIC + "/#")
        self.subscribe("+/+/set")

# async def manage_convention_stats
