import unittest
from homie.core.store import Store


class TestHomieCoreStore(unittest.TestCase):
    def test_store_get(self):
        store = Store({"level1Value": "value", "level1": {"level2Value": "value"}})
        self.assertEqual(store.get("level1Value"), "value")
        self.assertEqual(store.get("level1.level2Value"), "value")
        self.assertEqual(store.get("default", "default"), "default")
        self.assertIsNone(store.get("none"))
