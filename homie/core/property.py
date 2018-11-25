from homie.utils import valid_id


def REQUIRED(param, val):
    if val is None:
        raise Exception("property must have a {}".format(param))


class HomieProperty:
    def __init__(self, id, name=None, settable=None, retained=None, unit=None, data_type=None, format=None):
        REQUIRED("id", id)

        if not valid_id(id):
            raise Exception("property id must be a valid format")

        self._id = id
        self._name = name
        self._settable = settable
        self._retained = retained
        self._unit = unit
        self._data_type = data_type
        self._format = format
        self._homie = None
        self._node = None

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def settable(self):
        return self._settable

    @property
    def retained(self):
        return self._retained

    @property
    def unit(self):
        return self._unit

    @property
    def data_type(self):
        return self._data_type

    @property
    def format(self):
        return self._format

    @property
    def path(self):
        return ".".join([self.node.path, self.id])

    @property
    def node(self):
        return self._node

    @property
    def value(self):
        return self._homie.store.get(self.path)

    @value.setter
    def value(self, value):
        self._homie.store.set(self.path, value, "prop_setter")

    def setup(self, homie, node):
        self._homie = homie
        self._node = node
