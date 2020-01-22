import collections

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


class Reference(SchemaBase):

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        if resolver:
            incs.update({'"'+resolver.cpp_get_header(self.data['$ref'])+'"'})
        return incs

    def Resolve(self, resolver):
        return resolver.get_schema(self.data['$ref'], self.root)


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


class StringSchema(SchemaBase):

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.add("<string>")
        if 'pattern' in self.data:
            incs.add("<regex>")
        if 'format' in self.data:
            if self.data['format'] == 'uuid':
                incs.update({"<boost/uuid/uuid.hpp>", "<boost/uuid/random_generator.hpp>", "<boost/uuid/uuid_io.hpp>"})
            elif self.data['format'] == 'date-time':
                incs.update({"<boost/optional.hpp>", "<boost/date_time/posix_time/posix_time.hpp>"})
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
        return SchemaFactory(self.data['items'], self.root)

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<vector>"})
        incs.update(self.GetItemSchema().CppIncludes(resolver))
        return incs


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
        raise KeyError()


class OneOfSchema(CombinatorSchemaBase):
    
    def __init__(self, initialdata, root=None):
        super().__init__('oneOf', initialdata, root)
        assert(isinstance(self.data['oneOf'], list))

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<boost/variant.hpp>"})
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
