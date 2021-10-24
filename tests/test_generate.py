from typing import Generator
import unittest

from . import context
from jsonschemacodegen.cpp import GeneratorFromSchema
from jsonschemacodegen.cpp_namer import GeneralCppNamer
import jacobsjsondoc

class TestGenerator(unittest.TestCase):

    def test_generate_integer_class(self):
        schema_text = """{
            "type": "integer"
        }
        """
        schema = jacobsjsondoc.parse(schema_text)
        namer = GeneralCppNamer("/tmp")
        generator = GeneratorFromSchema(namer)
        generator.generate(schema, "hello", "/objects/world")
        cpp_files, hpp_files = generator.get_lists_of_generated_files()
        self.assertEqual(len(cpp_files), 1)
        self.assertEqual(len(hpp_files), 1)
        