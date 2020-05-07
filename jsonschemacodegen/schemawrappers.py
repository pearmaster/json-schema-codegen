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
        return population[self.Number(len(population)-1)]

    def Number(self, maximum) -> int:
        if self._full() or maximum == 0:
            return maximum
        bits = bitsNeededForNumber(maximum)
        mask = rightBitMask(bits)
        choice = self.current & mask
        self.current = self.current >> bits
        return choice % (maximum + 1)

    def __repr__(self):
        return str(self.index)

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

    def GetTitle(self):
        if 'title' in self.data:
            return self.data['title']
        return ''

    def IsReadOnly(self):
        return ('readOnly' in self.data) and (self.data['readOnly'] is True)
    
    def IsWriteOnly(self):
        return ('writeOnly' in self.data) and (self.data['writeOnly'] is True)

    def GetExampleCombos(self, resolver) -> int:
        combos = 1
        if 'examples' in self.data:
            combos = len(self.data['examples'])
        return combos

    def AnExample(self, resolver, index):
        raise NotImplementedError
    
    def Example(self, resolver, index: ExampleIndex, required=None):
        if 'const' in self.data:
            return self.data['const']
        if 'example' in self.data:
            return self.data['example']
        if 'examples' in self.data:
            return index.Choice(self.data['examples'])
        if 'default' in self.data:
            return self.data['default']
        try:
            try:
                return self.AnExample(resolver, index, required)
            except TypeError:
                pass
            return self.AnExample(resolver, index)
        except:
            print(f"Failed to get an example for {self.data} against {self.root['info']['title']}")
            raise

class Reference(SchemaBase):

    def __init__(self, initialdata, root=None):
        super().__init__(initialdata, root)
        self.requiredProperties = set()

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        if resolver:
            incs.update({'"'+resolver.cpp_get_header(self.data['$ref'])+'"'})
        return incs

    def Resolve(self, resolver):
        resolution = resolver.get_schema(self.data['$ref'], self.root)
        try:
            for propName in self.requiredProperties:
                resolution.SetPropertyRequired(propName)
        except:
            pass
        return resolution

    def SetPropertyRequired(self, propertyName):
        self.requiredProperties.add(propertyName)

    def GetExampleCombos(self, resolver) -> int:
        return self.Resolve(resolver).GetExampleCombos(resolver)

    def Example(self, resolver, index: ExampleIndex, required=None):
        try:
            return self.Resolve(resolver).Example(resolver, index, required)
        except:
            print(f"Trying to resolve {self.data['$ref']} against yaml root {self.root}")
            raise


class ObjectSchema(SchemaBase):

    def __init__(self, initialdata, root=None):
        super().__init__(initialdata, root)
        if 'properties' in self.data:
            assert(isinstance(self.data['properties'], dict)), f"Schema's properties is type {type(self.data['properties'])} instead of dict like expected"
        else:
            self.data['properties'] = dict()
        self.requiredProperties = set()
        if 'required' in self.data:
            self.requiredProperties.update(self.data['required'])

    def SetPropertyRequired(self, propertyName):
        if 'properties' in self.data and propertyName in self.data['properties']:
            self.requiredProperties.add(propertyName)

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
            if (propName in self.requiredProperties) and not (default_negates_required and 'default' in propSchema):
                theList.append((propName, SchemaFactory(propSchema, self.root)))
        return theList

    # TODO: Need something that specifies that this is 'required' for init
    def UnRequiredList(self, default_negates_required=True):
        theList = []
        for propName, propSchema in self.data['properties'].items():
            schemaObject = SchemaFactory(propSchema, self.root)
            if default_negates_required and 'default' in propSchema:
                theList.append((propName, schemaObject))
            elif propName not in self.requiredProperties:
                theList.append((propName, schemaObject))
        return theList

    def GetExampleCombos(self, resolver) -> int:
        combos = 1
        for _, item in self.RequiredList(default_negates_required=False):
            combos *= item.GetExampleCombos(resolver)
        for _, item in self.UnRequiredList(default_negates_required=False):
            combos *= (1 + item.GetExampleCombos(resolver))
        return combos

    def AnExample(self, resolver, index: ExampleIndex, required=None):
        if required is None:
            required = []
        ret = {}
        for name, item in self.RequiredList(default_negates_required=False):
            ret[name] = item.Example(resolver, index)
        for name, item in self.UnRequiredList(default_negates_required=False):
            if index.BooleanChoice() or name in required:
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
        return self.data['type'] == 'integer' and 1 or 1.1

class BooleanSchema(SchemaBase):

    def GetExampleCombos(self, resolver) -> int:
        combos = 2
        if 'example' in self.data or 'examples' in self.data or 'default' in self.data:
            combos = super().GetExampleCombos(resolver)
        return combos

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
        incs.update({"<vector>", "<string>"})
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
        if 'uniqueItems' in self.data and self.data['uniqueItems']:
            ret = list(set(ret))
        return ret

class CombinatorSchemaBase(SchemaBase):
    
    def __init__(self, name, initialdata, root=None):
        super().__init__(initialdata, root)
        self.name = name
        self.requiredProperties = set()
        self.components = []
        for s in self.data[self.name]:
            if 'type' in s or 'required' not in s:
                schema = SchemaFactory(s, self.root)
                self.components.append(schema)

        for s in self.data[self.name]:
            if 'required' in s and 'type' not in s:
                for rp in s['required']:
                    self.requiredProperties.add(rp)
                    self.SetPropertyRequired(rp)
                

    def SetPropertyRequired(self, propertyName):
        for comp in self.components:
            try:
                comp.SetPropertyRequired(propertyName)
            except:
                pass

    def GetComponents(self):
        return self.components

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
        combos = 1
        if 'example' in self.data or 'examples' in self.data or 'default' in self.data:
            combos = super().GetExampleCombos(resolver)
        else:
            combos = len(self.GetComponents())#bitsNeededForNumber(len(self.GetComponents()) - 1)
            max_component_combo = 1
            for comp in self.GetComponents():
                max_component_combo = max(max_component_combo, comp.GetExampleCombos(resolver))
            combos *= max_component_combo
        return combos

    def AnExample(self, resolver, index: ExampleIndex):
        component = index.Choice(self.GetComponents())
        ex = component.Example(resolver, index)
        return ex


class AllOfSchema(CombinatorSchemaBase):

    def __init__(self, initialdata, root=None):
        super().__init__('allOf', initialdata, root)
        assert(isinstance(self.data['allOf'], list))

    def AnExample(self, resolver, index: ExampleIndex, required=None):
        ret = {}
        if required is not None:
            self.requiredProperties.update(required)
        for comp in self.GetComponents():
            ret.update(comp.Example(resolver, index, self.requiredProperties))
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
    
    def AnExample(self, resolver, index: ExampleIndex, required=None):
        ret = {}
        if required is not None:
            self.requiredProperties.update(required)
        gotOne = False
        for comp in self.GetComponents():
            if index.BooleanChoice():
                gotOne = True
                ret.update(comp.Example(resolver, index, self.requiredProperties))
        if not gotOne:
            comp = index.Choice(self.GetComponents())
            ret.update(comp.Example(resolver, index, self.requiredProperties))
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
