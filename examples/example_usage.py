import jsonschemacodegen.cpp as cpp

if __name__ == '__main__':
    simpleResolver = SimpleResolver("myproject")
    output_dir = "output"

    # The generated C++ class will be in the namespace foo::bar (ie foo::bar::ClassName)
    namespace = ["foo", "bar"]

    # The generated source will be prefixed with 
    # "using namespace foo::bar" and "using namespace std"
    usings = [["foo", "bar"], ["std"]] 
    
    generator = cpp.GeneratorFromSchema(src_output_dir=output_dir,
        header_output_dir=output_dir, 
        resolver=simpleResolver)

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

    print("Generated {}".format(generator.generate(schema, "myproject#/example/object")))

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
    print("Generated {}".format(generator.generate(schemaWithRefs, "myproject#/example/objectFoo")))

    dateTimeSchema = {
        "type": "string",
        "format": "date-time"
    }

    print("Generated {}".format(generator.generate(dateTimeSchema, "myproject#/example/dateTimeObject")))

    uuidSchema = {
        "type": "string",
        "format": "uuid"
    }

    print("Generated {}".format(generator.generate(uuidSchema, "myproject#/example/uuidObject")))