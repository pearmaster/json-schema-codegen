import json
import abc
import stringcase
import os.path

from jacobsjinjatoo import templator
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

    def Generate(self, schema, root, class_name, filename_base):
        generator = templator.CodeTemplator(self.output_dir)
        generator.add_template_package('jsonschemacodegen.templates.python')

        args = {
            "Name": class_name,
            "schema": schemawrappers.SchemaFactory(schema, root),
        }
        return generator.render_template(template_name="file.py.jinja2", output_name="{}.py".format(filename_base), resolver=self.resolver, **args)

    def Examples(self, schema, root):
        wrapped_schema = schemawrappers.SchemaFactory(schema, root)
        number_of_examples = wrapped_schema.GetExampleCombos(self.resolver)
        examples = []
        examples.append(wrapped_schema.Example(self.resolver, schemawrappers.ExampleIndex(0)))
        examples.append(wrapped_schema.Example(self.resolver, schemawrappers.ExampleIndex(-1)))
        show_examples = min(number_of_examples, 20)
        example_step = int(number_of_examples/show_examples)
        index = example_step
        for _ in range(0, show_examples):
            examples.append(wrapped_schema.Example(self.resolver, schemawrappers.ExampleIndex(index)))
            index += example_step
        return sorted(list(set([json.dumps(x) for x in examples])))

    def GenerateTest(self, schema, root, class_name, filename_base, path):
        filename = self.resolver.py_test_filename(path)
        generator = templator.CodeTemplator(os.path.join(self.output_dir, os.path.dirname(filename)))
        generator.add_template_package('jsonschemacodegen.templates.python')
        wrapped_schema = schemawrappers.SchemaFactory(schema, root)
        args = {
            "Name": class_name.split('.')[-1],
            "schema": wrapped_schema,
            "examples": self.Examples(schema, root),
            "class": class_name,
            "path": path,
            "objType": path.split("/")[-2]
        }
        return generator.render_template(template_name="test.py.jinja2", output_name=os.path.basename(filename), resolver=self.resolver, **args)

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