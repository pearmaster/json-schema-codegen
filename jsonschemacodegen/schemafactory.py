
from schemawrappers import *

class SchemaFactory(object):

    def CreateSchema(schema, root=None):

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
            if 'x-anyOf-codegen-behavior' in schema and schema['x-anyOf-codegen-behavior'] == "matchFirst":
                return AnyOfFirstMatchSchema(schema, root)
            return AnyOfSchema(schema, root)
        elif 'oneOf' in schema:
            return OneOfSchema(schema, root)
        elif '$ref' in schema:
            return Reference(schema, root)
        else:
            raise NotImplementedError(str(schema))
