import json
import abc
import stringcase

from . import templator
from . import schemawrappers

class ResolverBaseClass(abc.ABC):

    @abc.abstractmethod
    def py_include_statement(self, reference):
        """Should return the include statement needed to acquire the object representing the
        schema pointed to at `reference`.  Example, "from schema_foo import Foo"
        """
        pass

    @abc.abstractmethod
    def py_class_name(self, reference):
        """Should return the class name for the object representing the schema pointed to at `reference`.
        For example, "schema_foo.Foo"
        """
        pass

    @abc.abstractmethod
    def py_filename(self, reference):
        """Should return the name of the filename holding the python class representing the schema pointed to
        at `reference`.  For example, "schema_foo.py"
        """
        pass


class GeneratorFromSchema(object):

    def __init__(self, output_dir, resolver=None):
        self.output_dir = output_dir
        self.resolver = resolver

    def GetDeps(self, schema):
        return []

    def Generate(self, schema, class_name, filename_base):
        generator = templator.Generator('jsonschemacodegen.templates.python', self.output_dir)
        args = {
            "Name": class_name,
            "schema": schemawrappers.SchemaFactory(schema),
        }
        return generator.RenderTemplate("file.py.jinja2", output_name="{}.py".format(filename_base), resolver=self.resolver, **args)

    def GenerateFromPath(self, schema, path):
        assert(self.resolver)
        class_name = self.resolver.py_class_name(path).split('.')[-1]
        filename_base = self.resolver.py_filename(path)
        return self.Generate(schema, class_name, filename_base)

