import collections
import random

class ExampleMode(object):

    def __init__(self, index, mode=1):
        self.index = index
        self.mode = mode

    def GetMode(self):
        return self.mode

    def IsMin(self):
        return self.mode == 0

    def IsMost(self):
        return self.mode == 2

    def IsRand(self):
        return self.mode == 1

    def Choices(self, population):
        random.seed(self.index)
        k = random.randrange(len(population))
        return random.choices(population, k=k)

    def Choice(self, population):
        random.seed(self.index+1)
        return random.choice(population)

    def Number(self, seed, mini, maxi):
        random.seed(self.index + seed)
        return random.randrange(mini, maxi)

    def Seed(self, seed):
        random.seed(self.index + hash(seed))
        return ExampleMode(random.randrange(1000), self.mode)


class SchemaBase(collections.UserDict):

    def __init__(self, initialdata, root=None):
        super().__init__(initialdata)
        self.root = root

    def CppIncludes(self, resolver):
        return {
            '"rapidjson/document.h"',
            "<exception>"
        }

    def Resolve(self, resolver):
        return self

    def IsReadOnly(self):
        return ('readOnly' in self.data) and (self.data['readOnly'] is True)
    
    def IsWriteOnly(self):
        return ('writeOnly' in self.data) and (self.data['writeOnly'] is True)


class Reference(SchemaBase):

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        if resolver:
            incs.update({'"'+resolver.cpp_get_header(self.data['$ref'])+'"'})
        return incs

    def Resolve(self, resolver):
        return resolver.get_schema(self.data['$ref'], self.root)

    def Example(self, resolver, index: ExampleMode):
        return self.Resolve(resolver).Example(resolver, index)


class ObjectSchema(SchemaBase):

    def __init__(self, initialdata, root=None):
        super().__init__(initialdata, root)
        if 'properties' in self.data:
            assert(isinstance(self.data['properties'], dict))
        else:
            self.data['properties'] = dict()

    def GetPropertySchemas(self):
        props = {}
        for n, p in self.data['properties'].items():
            props[n] = SchemaFactory(p, self.root)
        return props

    def PropertyKeys(self):
        return [a for a in self.data['properties'].keys()]

    def PropertyValues(self):
        return [a for a in self.data['properties'].values()]

    def __getitem__(self, key):
        if key == 'properties':
            return self.GetPropertySchemas()
        else:
            return self.data[key]

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<boost/optional.hpp>"})
        for _, ps in self.GetPropertySchemas().items():
            incs.update(ps.CppIncludes(resolver))
        return incs

    # TODO: Need something that specifies that this is 'required' for init
    def RequiredList(self):
        theList = []
        for propName, propSchema in self.data['properties'].items():
            if 'required' in self.data and propName in self.data['required'] and 'default' not in propSchema:
                theList.append((propName, SchemaFactory(propSchema, self.root)))
        return theList

    # TODO: Need something that specifies that this is 'required' for init
    def UnRequiredList(self):
        theList = []
        for propName, propSchema in self.data['properties'].items():
            if 'default' in propSchema:
                theList.append((propName, SchemaFactory(propSchema, self.root)))
            elif 'required' not in self.data:
                theList.append((propName, SchemaFactory(propSchema, self.root)))
            elif propName not in self.data['required']:
                theList.append((propName, SchemaFactory(propSchema, self.root)))
        return theList

    def Example(self, resolver, index: ExampleMode):
        if 'example' in self.data:
            return self.data['example']
        if 'examples' in self.data:
            return index.Choice(self.data['examples'])
        ret = {}
        for name, item in self.RequiredList():
            ret[name] = item.Example(resolver, index.Seed(name))
        if not index.IsMin():
            unrequired = self.UnRequiredList()
            if index.IsRand():
                unrequired = index.Choices(unrequired)
            for (name, item) in unrequired:
                ret[name] = item.Example(resolver, index.Seed(name))
        return ret

class StringSchema(SchemaBase):

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<string>", "<boost/functional/hash.hpp>"})
        if 'pattern' in self.data:
            incs.add("<regex>")
        if 'format' in self.data:
            if self.data['format'] == 'uuid':
                incs.update({"<boost/uuid/uuid.hpp>", "<boost/uuid/random_generator.hpp>", "<boost/uuid/uuid_io.hpp>"})
            elif self.data['format'] == 'date-time':
                incs.update({"<boost/optional.hpp>", "<boost/date_time/posix_time/posix_time.hpp>", "<boost/algorithm/string/replace.hpp>"})
        return incs

    def Example(self, resolver, index: ExampleMode):
        if 'example' in self.data:
            return self.data['example']
        if 'examples' in self.data:
            return index.Choice(self.data['examples'])
        if 'format' in self.data:
            if self.data['format'] == 'uuid':
                return "a18dfb2c-2b17-4a19-85e0-5c6c8d6a89e8"
            elif self.data['format'] == 'date-time':
                return "2002-10-02T15:00:00Z"
        theString = "example string 1 2 3 4 5 6 7 8 9"
        if 'maxLength' in self.data:
            theString = theString[:self.data['maxLength']]
        return theString


class StringEnumSchema(StringSchema):
    
    def Example(self, resolver, index: ExampleMode):
        if 'example' in self.data:
            return self.data['example']
        if 'examples' in self.data:
            return index.Choice(self.data['examples'])
        return index.Choice(self.data['enum'])


class NumberSchema(SchemaBase):

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<boost/lexical_cast.hpp>", "<boost/functional/hash.hpp>"})
        return incs

    def Example(self, resolver, index: ExampleMode):
        if 'example' in self.data:
            return self.data['example']
        if 'examples' in self.data:
            return index.Choice(self.data['examples'])
        mini = 0
        if 'minimum' in self.data:
            mini = self.data['minimum']
        if 'exclusiveMinimum' in self.data:
            mini = self.data['exclusiveMinimum'] + 1
        maxi = 100000
        if 'maximum' in self.data:
            maxi = self.data['maximum']
        if 'exclusiveMaximum' in self.data:
            maxi = self.data['exclusiveMaximum'] - 1
        theNumber = index.Number(1, mini, maxi)
        if self.data['type'] != 'integer':
            theNumber = theNumber/index.Number(2, 3, 9)
        return theNumber


class BooleanSchema(SchemaBase):

    def Example(self, resolver, index: ExampleMode):
        if 'example' in self.data:
            return self.data['example']
        if 'examples' in self.data:
            return index.Choice(self.data['examples'])
        return index.Choice([True, False])


class NullSchema(SchemaBase):

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<boost/none.hpp>"})
        return incs

    def Example(self, resolver, index: ExampleMode):
        return None

class ArraySchema(SchemaBase):
    
    def GetItemSchema(self):
        return SchemaFactory(self.data['items'], self.root)

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<vector>"})
        incs.update(self.GetItemSchema().CppIncludes(resolver))
        return incs

    def Example(self, resolver, index: ExampleMode):
        if 'example' in self.data:
            return self.data['example']
        if 'examples' in self.data:
            return index.Choice(self.data['examples'])
        ret = []
        mini = 0
        maxi = 3
        if 'minItems' in self.data:
            mini = self.data['minItems']
            maxi = mini + 3
        if 'maxItems' in self.data:
            maxi = self.data['maxItems']
        numItems = mini
        if index.IsMost():
            numItems = maxi
        elif index.IsRand():
            numItems = index.Number(10, mini, maxi)
        for i in range(0, numItems):
            ret.append(self.GetItemSchema().Example(resolver, index.Seed(i)))
        return ret

class CombinatorSchemaBase(SchemaBase):
    
    def __init__(self, name, initialdata, root=None):
        super().__init__(initialdata, root)
        self.name = name

    def GetComponents(self):
        return [SchemaFactory(s, self.root) for s in self.data[self.name]]

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        for c in self.GetComponents():
            incs.update(c.CppIncludes(resolver))
        return incs

    def __getitem__(self, key):
        if key.upper() in str(type(self)).upper():
            return self.GetComponents()
        return self.data[key]


class OneOfSchema(CombinatorSchemaBase):
    
    def __init__(self, initialdata, root=None):
        super().__init__('oneOf', initialdata, root)
        assert(isinstance(self.data['oneOf'], list))

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<boost/variant.hpp>", "<boost/functional/hash.hpp>"})
        return incs

    def GetCommonType(self, resolver):
        commonType = None
        for comp in self.GetComponents():
            subSchema = comp.Resolve(resolver)
            if 'type' in subSchema:
                if commonType is None:
                    commonType = subSchema['type']
                elif commonType != subSchema['type']:
                    return None
        return commonType


class AllOfSchema(CombinatorSchemaBase):

    def __init__(self, initialdata, root=None):
        super().__init__('allOf', initialdata, root)
        assert(isinstance(self.data['allOf'], list))


class AnyOfSchema(CombinatorSchemaBase):

    def __init__(self, initialdata, root=None):
        super().__init__('anyOf', initialdata, root)
        assert(isinstance(self.data['anyOf'], list))


def SchemaFactory(schema, root=None):
    if 'type' in schema:
        if schema['type'] == 'string':
            if 'enum' in schema:
                return StringEnumSchema(schema, root)
            return StringSchema(schema, root)
        elif schema['type'] == 'number' or schema['type'] == 'integer':
            return NumberSchema(schema, root)
        elif schema['type'] == 'boolean':
            return BooleanSchema(schema, root)
        elif schema['type'] == 'null':
            return NullSchema(schema, root)
        elif schema['type'] == 'object':
            return ObjectSchema(schema, root)
        elif schema['type'] == 'array':
            return ArraySchema(schema, root)
        else:
            raise NotImplementedError
    elif 'allOf' in schema:
        return AllOfSchema(schema, root)
    elif 'anyOf' in schema:
        return AnyOfSchema(schema, root)
    elif 'oneOf' in schema:
        return OneOfSchema(schema, root)
    elif '$ref' in schema:
        return Reference(schema, root)
    else:
        raise NotImplementedError(str(schema))
