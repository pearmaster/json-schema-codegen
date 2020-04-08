import collections
import random

def bitsNeededForNumber(num):
    bits = 0
    while num > 0:
        num = num >> 1
        bits += 1
    return bits

def rightBitMask(bits):
    mask = 1
    mask = mask << bits
    mask -= 1
    return mask

class ExampleIndex(object):

    def __init__(self, index):
        self.index = index
        self.current = index

    def _full(self):
        return self.index == -1

    def BooleanChoice(self):
        if self._full():
            return True
        choice = self.current & 0x01
        self.current = self.current >> 1
        return bool(choice)

    def Choice(self, population):
        return population[self.Number(len(population))-1]

    def Number(self, maximum):
        if self._full() or maximum == 0:
            return maximum
        bits = bitsNeededForNumber(maximum)
        mask = rightBitMask(bits)
        choice = self.current & mask
        self.current = self.current >> bits
        return choice % maximum


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

    def GetExampleCombos(self, resolver) -> int:
        if 'examples' in self.data:
            return len(self.data['examples'])
        return 1
    
    def Example(self, resolver, index: ExampleIndex):
        if 'example' in self.data:
            return self.data['example']
        if 'examples' in self.data:
            return index.Choice(self.data['examples'])
        if 'default' in self.data:
            return self.data['default']
        return self.AnExample(resolver, index)

class Reference(SchemaBase):

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        if resolver:
            incs.update({'"'+resolver.cpp_get_header(self.data['$ref'])+'"'})
        return incs

    def Resolve(self, resolver):
        return resolver.get_schema(self.data['$ref'], self.root)

    def GetExampleCombos(self, resolver) -> int:
        return self.Resolve(resolver).GetExampleCombos(resolver)

    def Example(self, resolver, index: ExampleIndex):
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
    def RequiredList(self, default_negates_required=True):
        theList = []
        for propName, propSchema in self.data['properties'].items():
            if ('required' in self.data and propName in self.data['required']) and not (default_negates_required and 'default' in propSchema):
                theList.append((propName, SchemaFactory(propSchema, self.root)))
        return theList

    # TODO: Need something that specifies that this is 'required' for init
    def UnRequiredList(self, default_negates_required=True):
        theList = []
        for propName, propSchema in self.data['properties'].items():
            if default_negates_required and 'default' in propSchema:
                theList.append((propName, SchemaFactory(propSchema, self.root)))
            elif 'required' not in self.data:
                theList.append((propName, SchemaFactory(propSchema, self.root)))
            elif propName not in self.data['required']:
                theList.append((propName, SchemaFactory(propSchema, self.root)))
        return theList

    def GetExampleCombos(self, resolver) -> int:
        combos = 1
        for _, item in self.RequiredList(default_negates_required=False):
            combos *= item.GetExampleCombos(resolver)
        for _, item in self.UnRequiredList(default_negates_required=False):
            combos *= 2
            combos *= item.GetExampleCombos(resolver)
        return combos

    def AnExample(self, resolver, index: ExampleIndex):
        ret = {}
        for name, item in self.RequiredList(default_negates_required=False):
            ret[name] = item.Example(resolver, index)
        for name, item in self.UnRequiredList(default_negates_required=False):
            if index.BooleanChoice():
                ret[name] = item.Example(resolver, index)
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

    def AnExample(self, resolver, index: ExampleIndex):
        if 'format' in self.data:
            if self.data['format'] == 'uuid':
                return "a18dfb2c-2b17-4a19-85e0-5c6c8d6a89e8"
            elif self.data['format'] == 'date-time':
                return "2002-10-02T15:00:00Z"
        maxLen = 'maxLength' in self.data and self.data['maxLength'] or 6
        minLen = 'minLength' in self.data and self.data['minLength'] or min(maxLen, 6)
        theString = ("string"*minLen)[:minLen]
        return theString


class StringEnumSchema(StringSchema):
    
    def GetExampleCombos(self, resolver) -> int:
        if 'example' in self.data or 'examples' in self.data or 'default' in self.data:
            return super().GetExampleCombos(resolver)
        return len(self.data['enum'])
    
    def AnExample(self, resolver, index: ExampleIndex):
        return index.Choice(self.data['enum'])


class NumberSchema(SchemaBase):

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<boost/lexical_cast.hpp>", "<boost/functional/hash.hpp>"})
        return incs

    def AnExample(self, resolver, index: ExampleIndex):
        for k in ['minimum', 'maximum']:
            if k in self.data:
                return self.data[k]
        if 'exclusiveMinimum' in self.data:
            return self.data['exclusiveMinimum'] + (self.data['type'] == 'integer' and 1 or 0.000001)
        if 'exclusiveMaximum' in self.data:
            return self.data['exclusiveMaximum'] - (self.data['type'] == 'integer' and 1 or 0.000001)
        return 1

class BooleanSchema(SchemaBase):

    def GetExampleCombos(self, resolver) -> int:
        if 'example' in self.data or 'examples' in self.data or 'default' in self.data:
            return super().GetExampleCombos(resolver)
        return 2

    def AnExample(self, resolver, index: ExampleIndex):
        return index.Choice([True, False])


class NullSchema(SchemaBase):

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<boost/none.hpp>"})
        return incs

    def AnExample(self, resolver, index: ExampleIndex):
        return None

class ArraySchema(SchemaBase):
    
    def GetItemSchema(self):
        return SchemaFactory(self.data['items'], self.root)

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<vector>"})
        incs.update(self.GetItemSchema().CppIncludes(resolver))
        return incs

    def GetExampleCombos(self, resolver) -> int:
        if 'example' in self.data or 'examples' in self.data or 'default' in self.data:
            return super().GetExampleCombos(resolver)
        left = 'minItems' in self.data and int(self.data['minItems']) or 0
        right = 'maxItems' in self.data and int(self.data['maxItems']) or (left + 3)
        combos = bitsNeededForNumber((right - left)+1)
        combos *= self.GetItemSchema().GetExampleCombos(resolver)
        return combos

    def AnExample(self, resolver, index: ExampleIndex):
        ret = []
        left = 'minItems' in self.data and int(self.data['minItems']) or 0
        right = 'maxItems' in self.data and int(self.data['maxItems']) or (left + 3)
        for _ in range(0, left+index.Number(right-left)):
            ret.append(self.GetItemSchema().Example(resolver, index))
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

    def GetExampleCombos(self, resolver) -> int:
        if 'example' in self.data or 'examples' in self.data or 'default' in self.data:
            return super().GetExampleCombos(resolver)
        return bitsNeededForNumber(len(self.GetComponents()) - 1)

    def AnExample(self, resolver, index: ExampleIndex):
        return index.Choice(self.GetComponents()).Example(resolver, index)


class AllOfSchema(CombinatorSchemaBase):

    def __init__(self, initialdata, root=None):
        super().__init__('allOf', initialdata, root)
        assert(isinstance(self.data['allOf'], list))

    def AnExample(self, resolver, index: ExampleIndex):
        ret = {}
        for comp in self.GetComponents():
            ret.update(comp.Example(resolver, index))
        return ret


class AnyOfSchema(CombinatorSchemaBase):

    def __init__(self, initialdata, root=None):
        super().__init__('anyOf', initialdata, root)
        assert(isinstance(self.data['anyOf'], list))

    def GetExampleCombos(self, resolver) -> int:
        if 'example' in self.data or 'examples' in self.data or 'default' in self.data:
            return super().GetExampleCombos(resolver)
        numberComponents = len(self.GetComponents())
        combos = bitsNeededForNumber(numberComponents - 1)
        combos << (numberComponents - 1)
        return combos
    
    def AnExample(self, resolver, index: ExampleIndex):
        ret = {}
        gotOne = False
        for comp in self.GetComponents():
            if index.BooleanChoice():
                gotOne = True
                ret.update(comp.Example(resolver, index))
        if not gotOne:
            comp = index.Choice(self.GetComponents())
            ret.update(comp.Example(resolver, index))
        return ret

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
            raise NotImplementedError(f"The type '{schema['type']}' is not implemented")
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
