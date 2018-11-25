DEFAULT_STATE = {
    "core": {
        "id": 'homie-default-id',
        "name": None,
        "mode": None,
        "state": None
    },
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
    'convention': {
        'ready': False,
        "stats": {
            "interval": 60,
            "uptime": 0,
            "signal": 0,
            "freeheap": 0
        },
        "broadcast": {}
    }
}


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

    @property
    def state(self):
        return self._state

    def get(self, path, default_value=None):
        current_key_val = self._state
        keys = path.split('.')
        for key in keys:
            key_val = current_key_val.get(key)
            if key_val is None:
                return default_value
            current_key_val = key_val
        return current_key_val

    def set(self, path, value, meta=None):
        current_key_val = self._state
        keys = path.split('.')
        for key in keys[:-1]:
            key_val = current_key_val.get(key)
            if key_val is None:
                current_key_val[key] = key_val = {}
            if not isinstance(key_val, dict):
                raise Exception("Can not set key of non dic type")
            current_key_val = key_val
        key = keys[-1]
        key_value = current_key_val.get(key)
        if key_value != value:
            if value is None:
                del current_key_val[key]
            else:
                current_key_val[key] = value
            self.invoke(path, value, key_value, meta)
