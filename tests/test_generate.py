from typing import Generator
import unittest
import os.path

from . import context
from jsonschemacodegen.cpp import GeneratorFromSchema
from jsonschemacodegen.cpp_namer import GeneralCppNamer
import jacobsjsondoc

class TestGenerator(unittest.TestCase):

    def setUp(self):
        self.namer = GeneralCppNamer("/tmp")
        self.generator = GeneratorFromSchema(self.namer)
        self.generator.generate_utils()

    def do_compile(self, uri, path):
        source_path = self.namer.get_source_path(uri, path)
        header_dir = "/tmp/include"
        command = ["g++", f"-I{header_dir}", "-c", source_path]
        print(" ".join(command))

    def test_generate_integer_class(self):
        schema_text = """{
            "type": "integer"
        }
        """
        schema = jacobsjsondoc.parse(schema_text)
        uri = "hello"
        path = "/objects/world"
        self.generator.generate(schema, uri, path)
        cpp_files, hpp_files = self.generator.get_lists_of_generated_files()
        self.assertEqual(len(cpp_files), 1)
        self.assertEqual(len(hpp_files), 2)
        self.do_compile(uri, path)
        