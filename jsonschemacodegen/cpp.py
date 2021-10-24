import json
import abc
import os

from jacobsjinjatoo import templator
from . import schemawrappers

class GeneratorFromSchema(object):

    def __init__(self, src_output_dir, header_output_dir, resolver):
        self.output_dir = {
            "src": src_output_dir,
            "header": header_output_dir,
        }
        assert(isinstance(resolver, ResolverBaseClass)), "Resolver is %s" % (resolver)
        self.resolver = resolver

    def _make_sure_directory_exists(self, output_key, dir_path):
        d = os.path.join(self.output_dir[output_key], dir_path)
        if not os.path.exists(d):
            os.makedirs(d)

    def get_deps(self, schema):
        return schema.CppIncludes(self.resolver)

    def generate(self, schema, path):
        retval = [None, None]
        srcGenerator = templator.CodeTemplator(self.output_dir['src']).add_template_package('jsonschemacodegen.templates.cpp')
        headerGenerator = templator.CodeTemplator(self.output_dir['header']).add_template_package('jsonschemacodegen.templates.cpp')
        args = {
            "Name": self.resolver.cpp_get_name(path),
            "schema": schemawrappers.SchemaFactory(schema),
        }
        headerFilename = self.resolver.cpp_get_header(path)
        self._make_sure_directory_exists('header', os.path.dirname(headerFilename))
        if '$ref' not in schema:
            srcFileName = "{}.cpp".format(self.resolver.cpp_get_filename_base(path))
            self._make_sure_directory_exists('src', os.path.dirname(srcFileName))
            srcGenerator.render_template(template_name="source.cpp.jinja2", 
                output_name=srcFileName, 
                deps=['"{}"'.format(self.resolver.cpp_get_header(path))], 
                usings=self.resolver.cpp_get_usings(),
                ns=self.resolver.cpp_get_namespace(path),
                resolver=self.resolver,
                **args)
            retval[0] = srcFileName
        headerGenerator.render_template(template_name="header.hpp.jinja2", 
            output_name=headerFilename, 
            ns=self.resolver.cpp_get_namespace(path),
            deps=self.get_deps(args['schema']), 
            resolver=self.resolver,
            filename=headerFilename,
            filepath='',
            **args)
        retval[1] = headerFilename
        return tuple(retval)


class LibraryGenerator(object):

    def __init__(self, src_output_dir: str, header_output_dir: str, resolver):
        self.output_dir = {
            "src": src_output_dir,
            "header": header_output_dir,
        }
        self.resolver = resolver
    
    def _make_sure_directory_exists(self, output_key, dir_path):
        d = os.path.join(self.output_dir[output_key], dir_path)
        if not os.path.exists(d):
            os.makedirs(d)

    def generate(self):
        retval = [None, "exceptions.hpp"]
        headerGenerator = templator.CodeTemplator(self.output_dir['header']).add_template_package('jsonschemacodegen.templates.cpp')
        headerGenerator.render_template(template_name="exceptions.hpp.jinja2", 
            output_name="exceptions.hpp", 
            ns=self.resolver.cpp_get_lib_ns(), 
        )
        return tuple(retval)
