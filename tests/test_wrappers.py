"""
Test the ability to wrap schemas with classes that provide more functionality.
"""


import unittest

from . import context
from jsonschemacodegen.schemawrappers import NumberSchema, SchemaFactory

class TestWrappers(unittest.TestCase):

    def test_integer_wrapper(self):
        schema = {
            "type": "integer"
        }
        wrapped = SchemaFactory.CreateSchema(schema)
        self.assertIsInstance(wrapped, NumberSchema)
        example = wrapped.AnExample(None, 1)
        self.assertIsInstance(example, int)