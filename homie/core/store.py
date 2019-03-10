from ucollections import deque
import uasyncio.core as asyncio


DEFAULT_STATE = {
    "core": {
        "id": "homie-default-id",
        "name": None,
        "mode": None,
        "state": None
    },
    "nodes": {},
    "network": {
        "mode": "wifi",
        "connected": False,
        "wifi": {
            "ssid": None,
            "password": None
        }
    },
    "mqtt": {
        "connected": False,
        "host": None,
        "port": 1883,
        "username": None,
        "password": None,
        "qos": 1,
        "base": "homie"
    },
    "convention": {
        "ready": False,
        "stats": {
            "interval": 60,
            "uptime": 0,
            "signal": 0,
            "freeheap": 0
        },
        "broadcast": {}
    },
    "fw": {
        "name": None,
        "version": None
    },
    "implementation": {}
}


def join_paths(*args):
    paths = args[0] if len(args) == 1 and isinstance(args[0], list) else args
    return ".".join(filter(lambda item: False if item is None else True, paths))


class Subscribable:
    def __init__(self):
        self._subscriptions = []

    def subscribe(self, fn):
        self._subscriptions.append(fn)
        return fn

    def unsubscribe(self, fn):
        self._subscriptions.remove(fn)

    def invoke(self, *args):
        for fn in self._subscriptions:
            fn(*args)


class Store(Subscribable):
    def __init__(self, initialState={}):
        super().__init__()
        self._state = initialState
        self._changeQueue = deque((), 20, 1)

    @property
    def state(self):
        return self._state

    def get(self, paths, default_value=None):
        path = join_paths(paths)
        current_key_val = self._state
        keys = path.split(".")
        for key in keys:
            key_val = current_key_val.get(key)
            if key_val is None:
                return default_value
            current_key_val = key_val
        return current_key_val

    def set(self, paths, value, meta=None, ignoreEmptyValue=False, default=False):
        path = join_paths(paths)
        current_key_val = self._state
        keys = path.split(".")
        for key in keys[:-1]:
            key_val = current_key_val.get(key)
            if key_val is None:
                current_key_val[key] = key_val = {}
            if not isinstance(key_val, dict):
                raise Exception("Can not set key of non dic type")
            current_key_val = key_val
        key = keys[-1]
        key_value = current_key_val.get(key)
        if (ignoreEmptyValue or default) and value is None:
            return
        if default and key_value is not None:
            return
        if key_value != value:
            if value is None:
                del current_key_val[key]
            else:
                current_key_val[key] = value
            self._changeQueue.append((path, value, key_value, meta))

    def process(self):
        try:
            while True:
                (path, value, key_value, meta) = self._changeQueue.popleft()
                self.invoke(path, value, key_value, meta)
        except IndexError:
            pass

    async def process_task(self):
        while True:
            self.process()
            await asyncio.sleep_ms(10)
