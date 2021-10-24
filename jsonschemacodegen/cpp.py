import json
import abc
import os

from jacobsjinjatoo import templator
import jacobsjsondoc
from . import schemawrappers
from . cpp_namer import CppNamer

class GeneratorFromSchema(object):

    def __init__(self, namer:CppNamer):
        self._namer = namer
        self._created_cpp_files = set()
        self._created_hpp_files = set()
        self._code_generator = templator.CodeTemplator(output_dir=templator.Templator.USE_FULL_PATHS)
        self._code_generator.add_template_package('jsonschemacodegen.templates.cpp')

    def _make_sure_directory_exists(self, filename:str):
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def generate_utils(self):
        path = self._namer.get_util_header_path("exceptions")
        self._make_sure_directory_exists(path)
        self._code_generator.render_template(template_name="exceptions.hpp.jinja2",
            output_name=path,
            ns=self._namer.get_util_object_name("exceptions").split("::")[:-1],
        )
        self._created_cpp_files.add(path)

    def generate(self, schema:jacobsjsondoc.document.DocElement, uri:str, path:str):
        if '$ref' in schema:
            return

        source_path = self._namer.get_source_path(uri, path)
        self._make_sure_directory_exists(source_path)
        header_path = self._namer.get_header_path(uri, path, schema)
        self._make_sure_directory_exists(header_path)

        self._code_generator.render_template(template_name="source.cpp.jinja2", 
            output_name=source_path, 
            schema=schema)
        self._created_cpp_files.add(source_path)

        self._code_generator.render_template(template_name="header.hpp.jinja2", 
            output_name=header_path,
            schema=schema)
        self._created_hpp_files.add(header_path)

    def get_lists_of_generated_files(self):
        return (self._created_cpp_files, self._created_hpp_files)