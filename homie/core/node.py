from homie.utils import valid_id
from homie.core.store import join_paths

STORE_NODES_PATH = "nodes"
STORE_SET_META_NODE = "node_setter"


def REQUIRED(node, param, private=False):
    val = getattr(node, param if not private else "_" + param)
    if val is None:
        raise Exception("node {} must have a {}".format(node.id, param))


class HomieNode:
    def __init__(self, homie, id):
        self._homie = homie
        self._id = id
        self._properties = {}

        REQUIRED(self, "homie", True)
        REQUIRED(self, "id")

        if not valid_id(id):
            raise Exception("id must be a valid format")

    @property
    def id(self):
        return self._id

    @property
    def properties(self):
        return self._properties

    @property
    def path(self):
        return join_paths(STORE_NODES_PATH, self.id)

    @property
    def name(self):
        return self._getNodeValue('name')

    @property
    def type(self):
        return self._getNodeValue('type')

    def configure(self, default=True, **kwargs):
        for key, value in kwargs.items():
            self._setNodeValue(key, value, default)
        return self

    def setup(self):
        REQUIRED(self, "name")  # TODO: should this be in the convention ?
        REQUIRED(self, "type")

    def _getNodeValue(self, prop):
        return self._homie.store.get([self.path, prop])

    def _setNodeValue(self, prop, value, default=False):
        self._homie.store.set([self.path, prop], value, STORE_SET_META_NODE, default=default)
