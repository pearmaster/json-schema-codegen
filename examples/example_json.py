from jsonschemacodegen.json_example import GeneratorFromSchema
from jsonschemacodegen.schemafactory import SchemaFactory

if __name__ == '__main__':
    schema_structure = {
        "type": "object",
        "title": "outer structure",
        "properties": {
            "outerstr": {"type":"string", "example":"example outer string", "title":"outerstr"},
            "outerbool": {"type":"boolean", "examples": [False,True], "title":"outerbool"},
            "something": {
                "title": "somethingoneof",
                "oneOf": [
                    {"type": "integer", "examples":[12,2,3], "title": "oneof something is integer with three examples"},
                    {
                        "type": "object",
                        "title": "oneof something is object with two properties",
                        "properties": {
                            "innerone": {
                                "title": "innerone property is oneof",
                                "oneOf": [
                                    {"type": "integer", "examples":[4,5], "title":"oneof innerone is integer with 2 examples"},
                                    {"type": "boolean", "title": "oneof innerone is boolean"}
                                ]
                            },
                            "innertwo": {"type": "string", "example": "inner two", "title":"innertwo"}
                        }
                    }
                ]
            }
        },
        "required": [
            "outerbool"
        ]
    }
    schema = SchemaFactory.CreateSchema(schema_structure)
    generator = GeneratorFromSchema(None)
    examples = generator.GenerateSome(schema, number_of_examples=10)
    print(f"{len(examples)} number of examples:")
    for ex in examples:
        print(ex)