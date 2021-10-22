"""
This module will create the write schema wrapper based on the schemas type.

It implements a factory pattern.
"""

from typing import Optional

from jsonschemacodegen.schemawrappers import BooleanSchema, NullSchema, StringEnumSchema, \
        NumberSchema, ObjectSchema, ArraySchema, AllOfSchema, AnyOfSchema, AnyOfFirstMatchSchema, \
        OneOfSchema, Reference, StringSchema, SchemaBase

class SchemaFactory:
    """
    Class with one factory method.
    """

    @staticmethod
    def CreateSchema(schema:dict, root:Optional[dict]=None) -> SchemaBase:
        """Returns the schema wrapped in one of the schema wrapper classes that provides
        additional functionality.
        """

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
            if 'x-anyOf-codegen-behavior' in schema \
                    and schema['x-anyOf-codegen-behavior'] == "matchFirst":
                return AnyOfFirstMatchSchema(schema, root)
            return AnyOfSchema(schema, root)
        elif 'oneOf' in schema:
            return OneOfSchema(schema, root)
        elif '$ref' in schema:
            return Reference(schema, root)
        else:
            raise NotImplementedError(str(schema))
