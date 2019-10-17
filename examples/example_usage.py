import jsonschemacodegen.cpp as cpp

if __name__ == '__main__':
    simpleResolver = cpp.SimpleResolver()
    output_dir = "/tmp"

    # The generated C++ class will be in the namespace foo::bar (ie foo::bar::ClassName)
    namespace = ["foo", "bar"]

    # The generated source will be prefixed with 
    # "using namespace foo::bar" and "using namespace std"
    usings = [["foo", "bar"], ["std"]] 
    
    generator = cpp.GeneratorFromSchema(src_output_dir=output_dir,
        header_output_dir=output_dir, 
        resolver=simpleResolver,
        namespace=namespace,
        src_usings=usings)

    schema = {
        "type": "object",
        "properties": {
            "aString": {
                "type": "string",
            },
            "aStringEnum": {
                "type": "string",
                "enum": ["a", "b", "c"],
            },
            "aNumber": {
                "type": "number",
                "exclusiveMaximum": 1.0,
                "exclusiveMinimum": 0.0,
            },
            "anArray": {
                "type": "array",
                "items": {
                    "type": "string",
                    "maxLength": 10,
                },
                "maxItems": 5
            },
            "aNullValue": {
                "type": "null",
            },
            "anExampleOfOneOf": {
                "oneOf": [
                    {"type": "integer"},
                    {"type": "boolean"},
                ]
            },
            "anExampleOfAnyOf": {
                "anyOf": [
                    {
                        "type": "object",
                        "properties": {
                            "foo": {
                                "type": "integer",
                            }
                        },
                        "required": [
                            "foo"
                        ]
                    },
                    {
                        "type": "object",
                        "properties": {
                            "bar": {
                                "type": "string",
                            }
                        },
                    },
                ]
            },
            "anExampleOfAllOf": {
                "allOf": [
                    {
                        "type": "object",
                        "properties": {
                            "bunny": {
                                "type": "integer",
                            }
                        },
                        "required": [
                            "bunny"
                        ]
                    },
                    {
                        "type": "object",
                        "properties": {
                            "rabbit": {
                                "type": "boolean",
                            }
                        },
                    },
                ]
            },
        }
    }

    generator.Generate(schema, 'ExampleObject', 'example_object')

    schemaWithRefs = {
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "localReference": {"$ref": "#/components/schemas/localReference"},
                    "externalReference": {"$ref": "other.yaml#/components/schemas/externalReference"},
                    "arrayWithLocalRef": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/localItem"},
                    }, 
                },
            },
            {
                "type": "object",
                "properties": {
                    "arrayWithExtRef": {
                        "type": "array",
                        "items": {"$ref": "other.yaml#/components/schemas/extItem"},
                    },
                },
            },
            {"$ref": "other.yaml#/components/schemas/externalObject"},
            {"$ref": "#/components/schemas/localObject"},
        ]
    }
    generator.Generate(schemaWithRefs, 'ExampleWithRefs', 'example_object2')

