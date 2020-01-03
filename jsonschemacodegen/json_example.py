import json
import random
import abc
from copy import copy

class SchemaResolverBaseClass(abc.ABC):

    @abc.abstractmethod
    def get_schema(self, reference, root=None):
        """Given a reference, returns a wrapped schema object.
        """
        pass

    @abc.abstractmethod
    def get_json(self, reference, root=None) -> dict:
        pass

    @abc.abstractmethod
    def get_document(self, reference):
        pass


class GeneratorFromSchema(object):

    def __init__(self, resolver=None):
        self.resolver = resolver
        self.includeMode = 'all'
        self.seed = 0

    def GetExampleOr(self, schema, default):
        if 'example' in schema:
            return schema['example']
        elif 'examples' in schema:
            exampleList = sorted(schema['examples'])
            return exampleList[0]
        elif 'enum' in schema:
            enums = sorted(schema['enum'])
            return enums[0]
        else:
            return default

    def GetNumber(self, schema):
        return self.GetExampleOr(schema, schema['type'] == 'integer' and 1 or 3.14)

    def GetObject(self, root, schema, base=None):
        base = base or {}
        for propName, propSchema in schema['properties'].items():
            if (self.includeMode == 'required') and (('required' not in schema) or (propName not in schema['required'])):
                continue
            thing = self.GetThing(root, propSchema)
            base[propName] = thing
        default = None
        if 'default' in schema:
            default = schema['default']
        elif 'defaults' in schema and isinstance(schema['defaults'], list):
            default = schema['defaults'][0]
        if default is not None:
            base.update(default)
        return base

    def GetArray(self, root, schema):
        base = []
        defaultMin = self.includeMode == 'all' and 1 or 0
        minItems = 'minItems' in schema and schema['minItems'] or defaultMin
        for _ in range(0, minItems):
            base.append(self.GetThing(root, schema['items']))
        return base

    def GetThing(self, root, schema, base=None):
        root_doc = root
        base = base or {}
        if '$ref' in schema:
            if len(schema['$ref'].split('#')[0]) > 0:
                root_doc = self.resolver.get_document(schema['$ref'])
            schema = self.resolver.get_schema(reference=schema['$ref'], root=root)
        if 'allOf' in schema:
            obj = base
            for opt in schema['allOf']:
                obj = self.GetThing(root_doc, opt, base=obj)
            return obj
        elif 'anyOf' in schema:
            obj = base
            if self.includeMode == 'required':
                return obj
            for opt in schema['anyOf']:
                obj = self.GetThing(root_doc, opt, base=obj)
            return obj
        elif 'oneOf' in schema:
            random.seed(self.seed)
            thing = self.GetThing(root_doc, random.choice(schema['oneOf']))
            return thing
        elif 'type' not in schema:
            raise NotImplementedError(schema)
        elif schema['type'] in ['integer', 'number']:
            return self.GetNumber(schema)
        elif schema['type'] == 'string':
            return self.GetExampleOr(schema, 'string')
        elif schema['type'] == 'null':
            return None
        elif schema['type'] == 'boolean':
            return self.GetExampleOr(schema, True)
        elif schema['type'] == 'object':
            return self.GetObject(root_doc, schema, base)
        elif schema['type'] == 'array':
            return self.GetArray(root_doc, schema)
        else:
            raise NotImplementedError

    def GenerateSome(self, root, schema, run, includeMode) -> set:
        self.includeMode = (includeMode in ['all', 'required']) and includeMode or 'all'
        examples = set()
        for i in range(0, run):
            self.seed = i
            thing = self.GetThing(root, schema)
            examples.add(json.dumps(thing, sort_keys=True))
        return examples

    def GenerateFull(self, root, schema, run=100) -> set:
        schemaJsonText = json.dumps(schema)
        run = max(2, schemaJsonText.count('oneOf')) * 10
        return self.GenerateSome(root, schema, run, 'all')

    def GenerateLimited(self, root, schema, run=2) -> set:
        schemaJsonText = json.dumps(schema)
        run = max(1, schemaJsonText.count('oneOf')) * 5
        return self.GenerateSome(root, schema, run, 'required')
    
    def Generate(self, root, schema) -> list:
        full = self.GenerateFull(root, schema)
        full.update(self.GenerateLimited(root, schema))
        return [json.loads(s) for s in full]

