from homie.utils import valid_id
from homie.core.store import join_paths

STORE_PROPS_PATH = "props"
STORE_SET_META_PROP = "prop_setter"


def REQUIRED(prop, param, private=False):
    val = getattr(prop, param if not private else "_" + param)
    if val is None:
        raise Exception("property {} must have a {}".format(prop.id, param))


class HomieProperty:
    def __init__(self, homie, node, id):
        self._homie = homie
        self._node = node
        self._id = id

        REQUIRED(self, "homie", True)
        REQUIRED(self, "node")
        REQUIRED(self, "id")

        if not valid_id(id):
            raise Exception("property id must be a valid format")

    @property
    def id(self):
        return self._id

    @property
    def node(self):
        return self._node

    @property
    def path(self):
        return join_paths(self.node.path, STORE_PROPS_PATH, self.id)

    @property
    def name(self):
        return self._getPropValue('name')

    @property
    def settable(self):
        return self._getPropValue('settable')

    @property
    def retained(self):
        return self._getPropValue('retained')

    @property
    def unit(self):
        return self._getPropValue('unit')

    @property
    def data_type(self):
        return self._getPropValue('data_type')

    @property
    def format(self):
        return self._getPropValue('format')

    @property
    def value(self):
        return self._getPropValue('value')

    @value.setter
    def value(self, value):
        self._setPropValue('value', value)

    def configure(self, default=True, **kwargs):
        for key, value in kwargs.items():
            self._setPropValue(key, value, default=default)
        return self

    def setup(self):
        REQUIRED(self, 'name')
        REQUIRED(self, 'data_type')

    def _getPropValue(self, prop):
        return self._homie.store.get([self.path, prop])

    def _setPropValue(self, prop, value, default=False):
        self._homie.store.set([self.path, prop], value, STORE_SET_META_PROP, default=default)
