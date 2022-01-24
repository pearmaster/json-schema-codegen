from typing import Generator
import subprocess
import unittest
import os

from . import context
from jsonschemacodegen.cpp import GeneratorFromSchema
from jsonschemacodegen.cpp_namer import GeneralCppNamer
import jacobsjsondoc

class CodeGeneratorMixin:

    def setUp(self): # pylint:disable=invalid-name
        self.root_gen_dir = "/tmp"
        self.compile_output = os.path.join(self.root_gen_dir, "compiler_output.o")
        self.namer = GeneralCppNamer("/tmp")
        self.generator = GeneratorFromSchema(self.namer)
        self.generator.generate_utils()
        self.uri = "hello"

    def do_compile(self, uri, path):
        source_path = self.namer.get_source_path(uri, path)
        header_dir = os.path.join(self.root_gen_dir, "include")
        command = ["g++", f"-I{header_dir}", "-c", source_path, "-o", self.compile_output]
        print(" ".join(command))
        rc = subprocess.call(command)
        self.assertEqual(rc, 0, "Generated code did not compile")

    def generate_class(self, schema_text:str, path:str):
        schema = jacobsjsondoc.parse(schema_text)
        self.generator.generate(schema, self.uri, path)
        cpp_files, hpp_files = self.generator.get_lists_of_generated_files()
        self.assertEqual(len(cpp_files), 1)
        self.assertEqual(len(hpp_files), 2)

    def tearDown(self): # pylint:disable=invalid-name
        os.unlink(self.compile_output)


class TestNumberGenerator(unittest.TestCase, CodeGeneratorMixin):

    def setUp(self):
        CodeGeneratorMixin.setUp(self)

    def test_generate_integer_class(self):
        schema_text = """{
            "type": "integer"
        }
        """
        path = "/objects/integer"
        self.generate_class(schema_text, path)
        self.do_compile(self.uri, path)
        
    def test_generate_number_class(self):
        schema_text = """ { "type":"number", "minimum": 0, "maximum": 10 } """
        path = "/objects/number"
        self.generate_class(schema_text, path)
        self.do_compile(self.uri, path)

    def tearDown(self):
        CodeGeneratorMixin.tearDown(self)


class TestStringGenerator(unittest.TestCase, CodeGeneratorMixin):

    def setUp(self):
        CodeGeneratorMixin.setUp(self)

    def test_generate_string_class(self):
        schema_text = """{ "type":"string" }"""
        path = "/objects/string"
        self.generate_class(schema_text, path)
        self.do_compile(self.uri, path)

    def test_generate_string_enum_class(self):
        schema_text = """ { "type": "string", "enum": ["A", "B", "C" ] }"""
        schema_text = """{ "type":"string" }"""
        path = "/objects/string_enum"
        self.generate_class(schema_text, path)
        self.do_compile(self.uri, path)

    def tearDown(self):
        CodeGeneratorMixin.tearDown(self)


class TestNullGenerator(unittest.TestCase, CodeGeneratorMixin):

    def setUp(self):
        CodeGeneratorMixin.setUp(self)

    def test_generate_null_class(self):
        schema_text = """{ "type": "null" }"""
        path = "/objects/null"
        self.generate_class(schema_text, path)
        self.do_compile(self.uri, path)

    def tearDown(self):
        CodeGeneratorMixin.tearDown(self)


class TestArrayGenerator(unittest.TestCase, CodeGeneratorMixin):

    def setUp(self):
        CodeGeneratorMixin.setUp(self)

    def test_generate_array_of_ints_class(self):
        schema_text = """
        {
            "type": "array",
            "items": {
                "type": "integer"
            }
        }
        """
        path = "/objects/array_of_ints"
        self.generate_class(schema_text, path)
        self.do_compile(self.uri, path)

    def test_generate_array_of_strings_class(self):
        schema_text = """
        {
            "type": "array",
            "items": {
                "type": "string",
                "title": "People Names",
            }
        }
        """
        path = "/objects/array_of_strings"
        self.generate_class(schema_text, path)
        self.do_compile(self.uri, path)

    def test_generate_array_of_strings_enum_class(self):
        schema_text = """
        {
            "type": "array",
            "items": {
                "type": "string",
                "title": "People Names",
                "enum": ["george", "washington"]
            }
        }
        """
        path = "/objects/array_of_string_enum"
        self.generate_class(schema_text, path)
        self.do_compile(self.uri, path)


    def test_generate_array_of_arrays_of_numbers(self):
        schema_text = """
        {
            "type": "array",
            "items": {
                "type": "array",
                "title": "List of Numbers",
                "items": {
                    "type": "number"
                },
                "maxItems": 6
            }
        }
        """
        path = "/objects/array_of_arrays_of_nums"
        self.generate_class(schema_text, path)
        self.do_compile(self.uri, path)
    
    def test_generate_array_of_nulls(self):
        schema_text = """
        {
            "type": "array",
            "items": {
                "type": "null",
                "title": "nothing",
            },
            "minItems": 4,
            "maxItems": 6
        }
        """
        path = "/objects/array_of_nulls"
        self.generate_class(schema_text, path)
        self.do_compile(self.uri, path)

    def tearDown(self):
        CodeGeneratorMixin.tearDown(self)

class TestObjectGenerator(unittest.TestCase, CodeGeneratorMixin):

    def setUp(self):
        CodeGeneratorMixin.setUp(self)

    def test_generate_basic_class(self):
        schema_text = """
        {
            "type": "object",
            "properties": {
                "foo": {
                    "type": "integer"
                }
            }
        }"""
        path = "/objects/basic"
        self.generate_class(schema_text, path)
        self.do_compile(self.uri, path)

    def test_generate_example1_class(self):
        schema_text = """
        {
            "type": "object",
            "properties": {
                "foo": {
                    "type": "integer"
                },
                "barIsRequired": {
                    "type": "string",
                    "maxLength": 10
                }
            },
            required: ["barIsRequired"]
        }"""
        path = "/objects/exampleObject1"
        self.generate_class(schema_text, path)
        self.do_compile(self.uri, path)

    def tearDown(self):
        CodeGeneratorMixin.tearDown(self)