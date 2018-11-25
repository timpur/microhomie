from homie.utils import valid_id
from homie.core.property import HomieProperty


def REQUIRED(param, val):
    if val is None:
        raise Exception("node must have a {}".format(param))


STORE_NODE_PATH = "nodes"


class HomieNode:
    def __init__(self, id, name, type):
        REQUIRED('id', id)
        REQUIRED("name", name)
        REQUIRED("type", type)

        if not valid_id(id):
            raise Exception("node id must be a valid format")

        self._id = id
        self._name = name
        self._type = type
        self._properties = {}
        self._homie = None

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def properties(self):
        return self._properties

    @property
    def path(self):
        return ".".join([STORE_NODE_PATH, self.id])

    def setup(self, homie):
        self._homie = homie

    def add_property(self, prop):
        if isinstance(prop, HomieProperty):
            self.properties[prop.id] = prop
