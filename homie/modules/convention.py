import uasyncio.core as asyncio

from homie import __version__
from homie.modules.base import HomieModule, import_module
from homie.core.logger import Logger
from homie.core.task import WaitForStateToBe
from homie.utils import payload_down, payload_up
from homie.core.node import STORE_NODES_PATH


CONVENTION_VERSION = "3.0.1"
BROADCAST_TOPIC = "$broadcast"
BROADCAST_STORE_PATH = "convention.broadcast"
STORE_SET_META_CONVENTION = "convention_setter"

LOG = Logger("Convention Module")


def join_topics(*args):
    return "/".join(filter(lambda item: False if item is None else True, args))


def get_prop(nodes, node_id, prop_id):  # TODO: should this be part of core ?
    node = nodes.get(node_id)
    if node:
        prop = node.properties.get(prop_id)
        if prop:
            return prop
    return None


class ConventionModule(HomieModule):
    def init(self):
        LOG.debug("Init")
        self._network = None
        self._mqtt = None
        self._broadcast_topic = None
        self._base_topic = None
        self._tasks = []

    @property
    def ready(self):
        return self._homie.store.get("convention.ready", False)

    def start(self):
        LOG.debug("Start")
        self._homie.store.set("convention.ready", False)
        self._network = import_module(self._homie, "NetworkModule")
        self._mqtt = import_module(self._homie, "MQTTModule")
        mqtt_base = self._homie.store.get("mqtt.base")
        self._broadcast_topic = join_topics(mqtt_base, BROADCAST_TOPIC)
        self._base_topic = join_topics(mqtt_base, self._homie.store.get("core.id"))
        self._mqtt.set_last_will(join_topics(self._base_topic, "$state"), "lost", True)
        self._mqtt.callbacks.subscribe(self.on_message)
        self._homie.store.subscribe(self.on_store_change)
        self._tasks.append(self._homie.add_task(self._manage_convention))

    def stop(self, reason):
        LOG.debug("Stop:", reason)
        for task in self._tasks:
            self._homie.stop_task(task)
        if self.ready:
            self.publish("$state", "sleeping" if reason == "sleep" else "disconnected")
        self._homie.store.set("convention.ready", False)

    def verify(self):
        # TODO:
        pass

    def publish(self, topic, payload, retained=True, required=True):
        if not required and not payload:
            return
        topic = join_topics(self._base_topic, topic)
        payload = payload_down(payload)
        return self._mqtt.publish(topic, payload_down(payload), retained)

    def publish_node(self, node, topic, payload, retained=True, required=True):
        topic = join_topics(node.id, topic)
        return self.publish(topic, payload, retained, required)

    def publish_prop(self, prop, topic, payload, retained=True, required=True):
        topic = join_topics(prop.id, topic)
        return self.publish_node(prop.node, topic, payload, retained, required)

    def subscribe(self, topic):
        topic = join_topics(self._base_topic, topic)
        return self._mqtt.subscribe(topic)

    def on_message(self, topic, payload):
        topic = topic.replace(self._base_topic + "/", "")
        payload = payload_up(payload)
        if topic.endswith("/set"):
            [node_id, prop_id] = topic.split("/")[0:2]
            prop = get_prop(self._homie.nodes, node_id, prop_id)
            if prop and prop.settable:
                self._homie.store.set([prop.path, "value"], payload, STORE_SET_META_CONVENTION)
        elif topic.startswith(self._broadcast_topic):
            LOG.info("Broadcast:", topic, payload)
            key = topic.replace(self._broadcast_topic + "/", "")
            self._homie.store.set([BROADCAST_STORE_PATH, key], payload, STORE_SET_META_CONVENTION)

    def on_store_change(self, path, value, _, meta):
        # TODO: clean up like ^
        if path.startswith(STORE_NODES_PATH):
            print(path)
            paths = path.split(".")
            prop = get_prop(self._homie.nodes, paths[1], paths[3])
            if prop:
                if prop.settable and meta != STORE_SET_META_CONVENTION:
                    self.publish_prop(prop, "set", value)
                self.publish_prop(prop, None, value)

    async def _manage_convention(self, _):
        while True:
            await WaitForStateToBe(self._homie.store, "mqtt.connected", True, only_change=True)
            self._homie.store.set("convention.ready", False)
            self.publish("$state", "init")
            self.advertise_device()
            self.advertise_nodes()
            self.subscribe_to_topics()
            await asyncio.sleep_ms(100)  # wait for subscription messages
            self.publish("$state", "ready")
            self._homie.store.set("convention.ready", True)

    def advertise_device(self):
        pub = self.publish
        get = self._homie.store.get

        pub("$homie", CONVENTION_VERSION)
        pub("$name", get("core.name"))
        ip, mac = self._network.get_if_config()
        pub("$localip", ip)
        pub("$mac", mac)
        pub("$fw/name", get("fw.name"))
        pub("$fw/version", get("fw.version"))
        pub("$implementation", "{}@{}".format("microhomie", __version__))
        implementation = get("implementation")
        if implementation:
            for key, value in implementation.items():
                pub("$implementation/{}".format(key), value, required=False)
        pub("$nodes", ",".join(self._homie.nodes.keys()))

    def advertise_nodes(self):
        pub_node = self.publish_node
        pub_prop = self.publish_prop

        for node in self._homie.nodes.values():
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
        self._mqtt.subscribe(self._broadcast_topic + "/#")
        self.subscribe("+/+/set")

# async def manage_convention_stats
