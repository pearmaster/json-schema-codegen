import json
import abc
import stringcase

from . import templator
from . import schemawrappers


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
        generator.RenderTemplate("array.py.jinja2", output_name="{}.py".format(filename_base),
            **args)


