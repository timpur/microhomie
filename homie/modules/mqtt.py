import uasyncio.core as asyncio
from umqtt.simple import MQTTClient

from homie.modules.base import HomieModule
from homie.core.logger import Logger
from homie.core.store import Subscribable
from homie.core.task import WaitForStateToBe
from homie.utils import string_down, string_up


LOG = Logger("MQTT Module")


class MQTTModule(HomieModule):
    def init(self):
        LOG.debug("Init")
        self._mqtt = None
        self._tasks = []
        self._callbacks = Subscribable()

    @property
    def connected(self):
        return self._homie.store.get("mqtt.connected", False)

    @property
    def callbacks(self):
        return self._callbacks

    def start(self):
        LOG.debug("Start")
        self._homie.store.set("mqtt.connected", False)
        self._mqtt = MQTTClient(
            self._homie.store.get("core.id"),
            self._homie.store.get("mqtt.host"),
            self._homie.store.get("mqtt.port"),
            self._homie.store.get("mqtt.username"),
            self._homie.store.get("mqtt.password")
            # keepalive=self.settings.MQTT_KEEPALIVE,
            # ssl=self.settings.MQTT_SSL,
            # ssl_params=self.settings.MQTT_SSL_PARAMS,
        )
        self._mqtt.set_callback(self.on_message)

        self._tasks.append(self._homie.add_task(self._manage_mqtt_connection))
        self._tasks.append(self._homie.add_task(self._manage_mqtt_messages))

    def stop(self, reason):
        LOG.debug("Stop:", reason)
        for task in self._tasks:
            self._homie.stop_task(task)
        if self.connected:
            self._mqtt.disconnect()
        self._homie.store.set("mqtt.connected", False)

    def set_last_will(self, topic, payload, retain=False):
        topic = string_down(topic)
        payload = string_down(payload)
        qos = self._homie.store.get("mqtt.qos")
        self._mqtt.set_last_will(topic, payload, retain, qos)

    def publish(self, topic, payload, retain=False):
        if not self.connected:
            return
        topic = string_down(topic)
        payload = string_down(payload)
        qos = self._homie.store.get("mqtt.qos")
        try:
            LOG.debug("Publishing:", topic, payload)
            self._mqtt.publish(topic, payload, retain, qos)
            return True
        except OSError:
            self._homie.store.set("mqtt.connected", False)
            return False

    def subscribe(self, topic):
        if not self.connected:
            return
        topic = string_down(topic)
        qos = self._homie.store.get("mqtt.qos")
        try:
            LOG.debug("Subscribing:", topic)
            self._mqtt.subscribe(topic, qos)
            return True
        except OSError:
            self._homie.store.set("mqtt.connected", False)
            return False

    def on_message(self, topic, payload):
        topic = string_up(topic)
        payload = string_up(payload)

        LOG.debug("OnMessage:", topic, payload)
        self._callbacks.invoke(topic, payload)

    async def _manage_mqtt_connection(self, _):
        while True:
            await WaitForStateToBe(self._homie.store, "mqtt.connected", False)
            await WaitForStateToBe(self._homie.store, "network.connected", True)
            try:
                LOG.info("Waiting for connection ...")
                self._mqtt.connect()
                self._homie.store.set("mqtt.connected", True)
                LOG.success("Connected")
            except OSError as error:
                LOG.error("Connection failed:", error)
                self._homie.store.set("mqtt.connected", False)
                await asyncio.sleep(1)

    async def _manage_mqtt_messages(self, _):
        while True:
            await WaitForStateToBe(self._homie.store, "mqtt.connected", True)
            try:
                self._mqtt.check_msg()
            except OSError:
                self._homie.store.set("mqtt.connected", False)
            await asyncio.sleep_ms(100)
