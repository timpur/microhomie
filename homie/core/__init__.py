import builtins
import uasyncio.core as asyncio

from homie.core.task import runner
from homie.core.store import Store, DEFAULT_STATE
from homie.utils import valid_id
from homie.modules.base import HomieModule
from homie.core.node import HomieNode
from homie.core.property import HomieProperty


class HomieCore:
    def __init__(self):
        asyncio._event_loop = None  # FIXME: Better way to clear all tasks ?
        self._event_loop = asyncio.get_event_loop()
        self._store = Store(DEFAULT_STATE)
        self._modules = []
        self._modes = {}
        self._nodes = {}
        self._store.set("core.state", "init")
        self.add_task(self._store.process_task, homie_arg=False)

    @builtins.property
    def store(self):
        return self._store

    @builtins.property
    def modules(self):
        return self._modules

    @builtins.property
    def modes(self):
        return self._modes

    @builtins.property
    def nodes(self):
        return self._nodes

    def add_task(self, coro_builder, *args, delay=0, homie_arg=True):
        coro = coro_builder(self, *args) if homie_arg else coro_builder(*args)
        coro = runner(coro)
        self._event_loop.call_later_ms(delay, coro, self)
        return coro

    def stop_task(self, coro):
        asyncio.cancel(coro)

    def add_module(self, module_creator):
        if not issubclass(module_creator, HomieModule):
            raise Exception("module_creator is not of type HomieModule")
        module = module_creator(self)
        self.modules.append(module)
        module.init()
        return module

    def get_module(self, name):
        for module in self.modules:
            if type(module).__name__ == name:
                return module
        return None

    def add_mode(self, mode_id, mode):
        for module_creator in mode:
            if not issubclass(module_creator, HomieModule):
                raise Exception("every module in mode must be of HomieModule type")
        self.modes[mode_id] = mode

    def set_mode(self, mode_id):
        mode = self.modes.get(mode_id)
        if not mode:
            raise Exception(mode, "mode not found")
        self._store.set("core.mode", mode_id)

    def add_node(self, node_id, node_creator=HomieNode):
        if not issubclass(node_creator, HomieNode):
            raise Exception("node_creator is not of type HomieNode")
        node = node_creator(self, node_id)
        self.nodes[node_id] = node
        return node

    def add_property(self, node, property_id, property_creator=HomieProperty):
        if not issubclass(property_creator, HomieProperty):
            raise Exception("property_creator is not of type HomieProperty")
        property = property_creator(self, node, property_id)
        node.properties[property_id] = property
        return property

    def set_fw(self, name, version):
        # TODO: validate values
        self._store.set("fw.name", name)
        self._store.set("fw.version", version)

    def setup(self):
        self._store.process()
        if not valid_id(self._store.get("core.id")):
            raise Exception("device id must be a valid format")

        self._store.set("core.state", "setup")
        self._setup_nodes()
        self._setup_mode()

    def run(self):
        self._store.set("core.state", "run")
        self._start_modules()
        self._event_loop.run_forever()

    def stop(self, reason="user"):
        self._store.set("core.state", "stop")
        self._stop_modules(reason)
        self._modules.clear()

    def sleep(self):
        self.stop("sleep")

    def _setup_nodes(self):
        for node in self.nodes.values():
            node.setup()
            for prop in node.properties.values():
                prop.setup()

    def _setup_mode(self):
        mode_id = self._store.get("core.mode")
        mode = self.modes.get(mode_id)
        if not mode:
            raise Exception("please set a mode")
        for module in mode:
            self.add_module(module)

    def _start_modules(self):
        for module in self.modules:
            module._status = "starting"
            module.start()
            module._status = "started"

    def _stop_modules(self, reason="user"):
        for module in reversed(self.modules):
            module._status = "stoping"
            module.stop(reason)
            module._status = "stopped"
