import json
import abc
import stringcase

from . import templator
from . import schemawrappers


class SimpleResolver(object):

    def __init__(self, loader=None):
        self.loader = loader

    def ReferenceParts(self, reference):
        url, path = reference.split('#')
        theType, name = path.split('/')[-2:]
        return {
            "url": url,
            "path": path,
            "type": theType,
            "PascalType": stringcase.pascalcase(theType),
            "name": name,
            "PascalName": stringcase.pascalcase(name),
            "pkg": url is not None and url.split(".")[0] or None,
        }

    def IncludeStatement(self, reference):
        ref = self.ReferenceParts(reference)
        if ref['pkg'] is not None:
            return "import {pkg}.{type}_{name}".format(**ref)
        else:
            return "import {type}_{name}".format(**ref)

    def ClassName(self, reference):
        ref = self.ReferenceParts(reference)
        if ref['pkg'] is not None:
            return "{pkg}.{type}_{name}.{PascalName}".format(**ref)
        else:
            return "{type}_{name}.{PascalName}".format(**ref)

    def FileName(self, reference):
        ref = self.ReferenceParts(reference)
        return "{type}_{name}.py".format(**ref)



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
        generator.RenderTemplate("file.py.jinja2", output_name=filename_base, resolver=self.resolver, **args)


