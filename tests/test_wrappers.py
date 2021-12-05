"""
Test the ability to wrap schemas with classes that provide more functionality.
"""


import unittest

from . import context
from jsonschemacodegen.schemawrappers import NumberSchema, SchemaFactory
import jacobsjsondoc

class TestWrappers(unittest.TestCase):

    def test_integer_wrapper(self):
        schema = """{
            "type": "integer"
        }"""
        schema_obj = jacobsjsondoc.parse(schema)
        wrapped = SchemaFactory.CreateSchema(schema_obj)
        self.assertIsInstance(wrapped, NumberSchema)
        example = wrapped.AnExample(None, 1)
        self.assertIsInstance(example, int)

    def test_integer_title(self):
        schema_text = """{
            "type": "integer",
            "title": "Hello World"
        }
        """
        schema_obj = jacobsjsondoc.parse(schema_text)
        wrapped = SchemaFactory.CreateSchema(schema_obj)
        self.assertEqual(wrapped["title"], "Hello World")
        self.assertEqual(wrapped.get_title(convert_case="pascalcase"), "HelloWorld")
        self.assertEqual(wrapped.get_title(convert_case="doesnotexistcase"), "Hello World")