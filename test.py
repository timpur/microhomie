import unittest

from tests.core.store_spec import TestHomieCoreStore

TESTS = [TestHomieCoreStore]


def suite():
    suite = unittest.TestSuite()
    for test in TESTS:
        suite.addTest(test)
    return suite


if __name__ == '__main__':
    runner = unittest.TestRunner()
    runner.run(suite())
