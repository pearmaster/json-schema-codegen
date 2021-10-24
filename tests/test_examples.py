"""
Tests some of the example generation utilities.
"""

import unittest

import jacobsjsondoc

from . context import jsonschemacodegen
import jsonschemacodegen.example_util
import jsonschemacodegen.json_example
from jsonschemacodegen.schemawrappers import SchemaFactory

class TestBitCounters(unittest.TestCase):
    """"""

    def test_bitsNeededForNumber(self):
        self.assertEqual(jsonschemacodegen.example_util.bitsNeededForNumber(1), 1)


class SchemaCreationMixin:

    def create_schema_examples(self, schema_text):
        generator = jsonschemacodegen.json_example.GeneratorFromSchema()
        doc = jacobsjsondoc.parse(schema_text)
        schema = SchemaFactory.CreateSchema(doc)
        return generator.generate(schema, number_of_examples=100)

class TestExampleIntegerGeneration(unittest.TestCase, SchemaCreationMixin):

    def test_integer_examples(self):
        schema_text = """
        {
            "type": "integer"
        }
        """
        examples = self.create_schema_examples(schema_text)
        for example in examples:
            self.assertIsInstance(example, int)

    def test_integer_range_examples(self):
        schema_text = """
        {
            "type": "integer",
            "minimum": 100,
            "maximum": 110
        }
        """
        examples = self.create_schema_examples(schema_text)
        for example in examples:
            self.assertIsInstance(example, int)
            self.assertGreaterEqual(example, 100)
            self.assertLessEqual(example, 110)

if __name__ == '__main__':
    unittest.main()
