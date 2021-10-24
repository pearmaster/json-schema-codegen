import unittest
from .context import jsonschemacodegen
from jsonschemacodegen.cpp_namer import GeneralCppNamer

class TestGeneralCppNamer(unittest.TestCase):

    def setUp(self) -> None:
        self.namer = GeneralCppNamer("/path")
        self.yaml_name = "example.yaml"
        self.path = "#/definitions/foo"
        return super().setUp()

    def test_header_path(self):
        header_path = self.namer.get_header_path(self.yaml_name, self.path, None)
        self.assertEqual(header_path, "/path/include/example/definitions_foo.hpp")

    def test_source_path(self):
        source_path = self.namer.get_source_path(self.yaml_name, self.path)
        self.assertEqual(source_path, "/path/src/definitions_foo.cpp")

    def test_object_name(self):
        object_name = self.namer.get_object_name(self.yaml_name, self.path)
        self.assertEqual(object_name, "example::definitions::Foo")

    def test_include_path(self):
        inc_path = self.namer.get_include_path(self.yaml_name, self.path)
        self.assertEqual(inc_path, '"example/definitions_foo.hpp"')
    
    def test_util_header_path(self):
        header_path = self.namer.get_util_header_path("base")
        self.assertEqual(header_path, "/path/include/util/base.hpp")

    def test_util_source_path(self):
        src_path = self.namer.get_util_source_path("base")
        self.assertEqual(src_path, "/path/src/util_base.cpp")

    def test_util_object_name(self):
        obj_name = self.namer.get_util_object_name("base")
        self.assertEqual(obj_name, "util::Base")