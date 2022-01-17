"""
Tests some of the example generation utilities.
"""

import unittest
from .context import jsonschemacodegen
import jsonschemacodegen.example_util

class TestBitCounters(unittest.TestCase):

    def test_bitsNeededForNumber(self):
        self.assertEqual(jsonschemacodegen.example_util.bitsNeededForNumber(1), 1)

if __name__ == '__main__':
    unittest.main()
