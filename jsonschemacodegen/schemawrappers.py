"""
This module wraps a schema object in classes which augment each schema element with additional methods.
"""


import collections
import copy

from .example_util import bitsNeededForNumber, ExampleIndex
from .schemafactory import SchemaFactory

class SchemaBase(collections.UserDict):
    """
    Abstract base class for all types of schemas.
    """

    def __init__(self, initialdata, root=None):
        super().__init__(initialdata)
        self.root = root

    def CppIncludes(self, resolver):
        #pylint: disable=unused-argument
        return {
            '"rapidjson/document.h"',
            "<exception>"
        }

    def Resolve(self, resolver):
        #pylint: disable=unused-argument
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
        #pylint: disable=unused-argument
        combos = 1
        if 'examples' in self.data:
            combos = len(self.data['examples'])
        return combos

    def AnExample(self, resolver, index, required=None):
        raise NotImplementedError
    
    def Example(self, resolver, index: ExampleIndex, required=None):
        if 'const' in self.data:
            return self.data['const']
        if 'example' in self.data:
            return self.data['example']
        if 'examples' in self.data and len(self.data['examples']) > 0:
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
    """
    A reference schema looks like this:

    ```yaml
    $ref: "path/to/schema"
    ```
    """

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
        except Exception:
            pass
        return resolution

    def SetPropertyRequired(self, propertyName):
        self.requiredProperties.add(propertyName)

    def GetExampleCombos(self, resolver) -> int:
        return self.Resolve(resolver).GetExampleCombos(resolver)

    def AnExample(self, resolver, index, required=None):
        try:
            return self.Resolve(resolver).AnExample(resolver, index, required)
        except:
            print(f"Trying to resolve {self.data['$ref']} against yaml root {self.root}")
            raise

    def Example(self, resolver, index: ExampleIndex, required=None):
        try:
            return self.Resolve(resolver).Example(resolver, index, required)
        except:
            print(f"Trying to resolve {self.data['$ref']} against yaml root {self.root}")
            raise


class ObjectSchema(SchemaBase):
    """
    An object schema looks like this:

    ```yaml
    type: object
    properties:
      a: 
        type: integer
    required:
      - a
    ```
    """

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
        if len(self.UnRequiredList(False)) > 0:
            incs.update({"<boost/none.hpp>"})
        if 'additionalProperties' not in self.data or self.data['additionalProperties'] is False:
            incs.update({"<utility>"})
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
    """
    A string schema could look like this:

    ```yaml
    type: string
    minLength: 0
    maxLength: 10
    ```

    or perhaps like this:

    ```yaml
    type: string
    format: uuid
    ```
    """

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<string>", "<boost/functional/hash.hpp>"})
        if 'pattern' in self.data:
            incs.add("<regex>")
        if 'format' in self.data:
            if self.data['format'] == 'uuid':
                incs.update({"<boost/uuid/uuid.hpp>", "<boost/uuid/random_generator.hpp>", "<boost/uuid/uuid_io.hpp>"})
            elif self.data['format'] == 'date-time':
                incs.update({"<boost/optional.hpp>", "<boost/date_time/posix_time/posix_time.hpp>", "<boost/algorithm/string/replace.hpp>", "<boost/algorithm/string/trim.hpp>"})
        return incs

    def AnExample(self, resolver, index: ExampleIndex, required=None):
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
    """
    A string schema with enumerated values looks like this:
    
    ```yaml
    type: string
    enum:
      - a
      - frog
      - george washington
    ```
    """
    
    def GetExampleCombos(self, resolver) -> int:
        if 'example' in self.data or 'examples' in self.data or 'default' in self.data:
            return super().GetExampleCombos(resolver)
        return len(self.data['enum'])
    
    def AnExample(self, resolver, index: ExampleIndex, required=None):
        return index.Choice(self.data['enum'])


class NumberSchema(SchemaBase):
    """
    A number schema may look like:

    ```yaml
    type: integer
    multipleOf: 4
    ```

    or like this:

    ```yaml
    type: number
    format: double
    minimum: 1.0
    ```
    """

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<boost/lexical_cast.hpp>", "<boost/functional/hash.hpp>"})
        return incs

    def AnExample(self, resolver, index: ExampleIndex, required=None):
        for k in ['minimum', 'maximum']:
            if k in self.data:
                return self.data[k]
        if 'exclusiveMinimum' in self.data:
            return self.data['exclusiveMinimum'] + (self.data['type'] == 'integer' and 1 or 0.000001)
        if 'exclusiveMaximum' in self.data:
            return self.data['exclusiveMaximum'] - (self.data['type'] == 'integer' and 1 or 0.000001)
        return self.data['type'] == 'integer' and 1 or 1.1


class BooleanSchema(SchemaBase):
    """
    A boolean schema may look like this:

    ```yaml
    type: boolean
    default: false
    ```
    """

    def GetExampleCombos(self, resolver) -> int:
        combos = 2
        if 'example' in self.data or 'examples' in self.data or 'default' in self.data:
            combos = super().GetExampleCombos(resolver)
        return combos

    def AnExample(self, resolver, index: ExampleIndex, required=None):
        return index.Choice([True, False])


class NullSchema(SchemaBase):
    """
    A null schema is simply:

    ```yaml
    type: null
    ```
    """

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        incs.update({"<boost/none.hpp>"})
        return incs

    def AnExample(self, resolver, index: ExampleIndex, required=None):
        return None

class ArraySchema(SchemaBase):
    """
    A schema for an array of unique strings looks something like:

    ```yaml
    type: array
    maxItems: 4
    uniqueItems: true
    items:
      type: string
    ```
    """
    
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

    def AnExample(self, resolver, index: ExampleIndex, required=None):
        ret = []
        left = 'minItems' in self.data and int(self.data['minItems']) or 0
        right = 'maxItems' in self.data and int(self.data['maxItems']) or (left + 3)
        for _ in range(0, left+index.Number(right-left)):
            ret.append(self.GetItemSchema().Example(resolver, index))
        if 'uniqueItems' in self.data and self.data['uniqueItems']:
            ret = list(set(ret))
        return ret


class CombinatorSchemaBase(SchemaBase):
    """ This is a base class for anyOf, allOf, oneOf schema types.
    """
    
    def __init__(self, name, initialdata, root=None):
        super().__init__(initialdata, root)
        self.name = name
        self.requiredProperties = set()
        self.components = []
        self.allow_none = False
        for s in self.data[self.name]:
            if hasattr(s, '__iter__') and ('type' in s or 'required' not in s):
                schema = SchemaFactory(s, self.root)
                self.components.append(schema)

        for s in self.data[self.name]:
            if hasattr(s, '__iter__') and 'required' in s and 'type' not in s:
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
    """
    A schema that requires an item to be either a string or null would look like:

    ```yaml
    oneOf:
      - type: string
      - type: null
    ```
    """
    
    def __init__(self, initialdata, root=None):
        super().__init__('oneOf', initialdata, root)
        assert(isinstance(self.data['oneOf'], list))
        if isinstance(initialdata, OneOfSchema):
            self.allow_none = initialdata.allow_none
        else:
            self.allow_none = True in initialdata['oneOf']

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

    def AnExample(self, resolver, index: ExampleIndex, required=None):
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
        self.allow_none = (True in self.data['anyOf'])

    def CppIncludes(self, resolver=None):
        incs = super().CppIncludes(resolver=resolver)
        if not self.allow_none:
            incs.add("<boost/variant.hpp>")
        return incs

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
        gotOne = self.allow_none
        for comp in self.GetComponents():
            if index.BooleanChoice():
                gotOne = True
                ret.update(comp.Example(resolver, index, self.requiredProperties))
        if not gotOne:
            comp = index.Choice(self.GetComponents())
            ret.update(comp.Example(resolver, index, self.requiredProperties))
        return ret

class AnyOfFirstMatchSchema(OneOfSchema):

    def __init__(self, initialdata, root=None):
        CombinatorSchemaBase.__init__(self, 'anyOf', initialdata, root)
        assert(isinstance(self.data['anyOf'], list))

