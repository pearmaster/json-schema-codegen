import collections

class SchemaBase(collections.UserDict):

    def __init__(self, initialdata):
        super().__init__(initialdata)
    
    def CppIncludes(self, resolver=None):
        return {
            '"rapidjson/document.h"',
            "<exception>"
        }


class Reference(SchemaBase):

    def CppIncludes(self, resolver):
        incs = super().CppIncludes(resolver=resolver)
        if resolver:
            incs.update({'"'+resolver.GetHeader(self.data['$ref'])+'"'})
        return incs


class ObjectSchema(SchemaBase):

    def __init__(self, initialdata):
        super().__init__(initialdata)
        assert('properties' in self.data)
        assert(isinstance(self.data['properties'], dict))

    def GetPropertySchemas(self):
        props = {}
        for n, p in self.data['properties'].items():
            props[n] = SchemaFactory(p)
        return props

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
                theList.append((propName, SchemaFactory(propSchema)))
        return theList

    # TODO: Need something that specifies that this is 'required' for init
    def UnRequiredList(self):
        theList = []
        for propName, propSchema in self.data['properties'].items():
            if 'default' in propSchema:
                theList.append((propName, SchemaFactory(propSchema)))
            elif 'required' not in self.data:
                theList.append((propName, SchemaFactory(propSchema)))
            elif propName not in self.data['required']:
                theList.append((propName, SchemaFactory(propSchema)))
        return theList


class StringSchema(SchemaBase):

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.add("<string>")
        if 'pattern' in self.data:
            incs.add("<regex>")
        return incs


class StringEnumSchema(StringSchema):
    pass


class NumberSchema(SchemaBase):

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.add("<boost/lexical_cast.hpp>")
        return incs

class BooleanSchema(SchemaBase):
    pass


class NullSchema(SchemaBase):
    pass


class ArraySchema(SchemaBase):
    
    def GetItemSchema(self):
        return SchemaFactory(self.data['items'])

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<vector>"})
        incs.update(self.GetItemSchema().CppIncludes(resolver))
        return incs


class CombinatorSchemaBase(SchemaBase):
    
    def __init__(self, name, initialdata):
        super().__init__(initialdata)
        self.name = name

    def GetComponents(self):
        return [SchemaFactory(s) for s in self.data[self.name]]

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        for c in self.GetComponents():
            incs.update(c.CppIncludes(resolver))
        return incs

    def __getitem__(self, key):
        if key.upper() in str(type(self)).upper():
            return self.GetComponents()
        raise KeyError()


class OneOfSchema(CombinatorSchemaBase):
    
    def __init__(self, initialdata):
        super().__init__('oneOf', initialdata)
        assert(isinstance(self.data['oneOf'], list))

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<boost/variant.hpp>"})
        return incs


class AllOfSchema(CombinatorSchemaBase):

    def __init__(self, initialdata):
        super().__init__('allOf', initialdata)
        assert(isinstance(self.data['allOf'], list))


class AnyOfSchema(CombinatorSchemaBase):

    def __init__(self, initialdata):
        super().__init__('anyOf', initialdata)
        assert(isinstance(self.data['anyOf'], list))


def SchemaFactory(schema):
    if 'type' in schema:
        if schema['type'] == 'string':
            if 'enum' in schema:
                return StringEnumSchema(schema)
            return StringSchema(schema)
        elif schema['type'] == 'number' or schema['type'] == 'integer':
            return NumberSchema(schema)
        elif schema['type'] == 'boolean':
            return BooleanSchema(schema)
        elif schema['type'] == 'null':
            return NullSchema(schema)
        elif schema['type'] == 'object':
            return ObjectSchema(schema)
        elif schema['type'] == 'array':
            return ArraySchema(schema)
        else:
             NotImplementedError
    elif 'allOf' in schema:
        return AllOfSchema(schema)
    elif 'anyOf' in schema:
        return AnyOfSchema(schema)
    elif 'oneOf' in schema:
        return OneOfSchema(schema)
    elif '$ref' in schema:
        return Reference(schema)
    else:
        raise NotImplementedError(str(schema))
