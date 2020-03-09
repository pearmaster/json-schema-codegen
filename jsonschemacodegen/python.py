import json
import abc
import stringcase

from . import templator
from . import schemawrappers
from . import json_example

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

    def Examples(self, schema, root):
        generator = json_example.GeneratorFromSchema(self.resolver)
        assert(root is not None), "No Root"
        examples = generator.Generate(root, schema)
        exampleList = [json.dumps(ex, indent=2, sort_keys=True) for ex in examples]
        sorted(exampleList, reverse=True)
        return exampleList

    def GenerateTest(self, schema, root, class_name, filename_base, path):
        generator = templator.Generator('jsonschemacodegen.templates.python', self.output_dir)
        wrapped_schema = schemawrappers.SchemaFactory(schema, root)
        args = {
            "Name": class_name.split('.')[-1],
            "schema": wrapped_schema,
            "examples": self.Examples(schema, root),
            "class": class_name
        }
        return generator.RenderTemplate("test.py.jinja2", output_name="test_{}".format(filename_base), resolver=self.resolver, **args)

    def GenerateFromPath(self, schema, path):
        assert(self.resolver)
        class_name = self.resolver.py_class_name(path).split('.')[-1]
        filename_base = self.resolver.py_filename(path)
        return self.Generate(schema, class_name, filename_base)

    def GenerateTestFromPath(self, schema, root, path):
        assert(self.resolver)
        class_name = self.resolver.py_class_name(path)
        filename_base = self.resolver.py_filename(path)
        return self.GenerateTest(schema, root, class_name, filename_base, path)