from jsonschemacodegen.json_example import GeneratorFromSchema

if __name__ == '__main__':
    schema = {
        "type": "object",
        "properties": {
            "outerstr": {"type":"string", "example":"example outer string"},
            "outerbool": {"type":"boolean", "examples": [False,True]},
            "something": {
                "oneOf": [
                    {"type": "integer", "examples":[12,2,3]},
                    {
                        "type": "object",
                        "properties": {
                            "innerone": {
                                "oneOf": [
                                    {"type": "integer", "examples":[4,5,6]},
                                    {"type": "boolean"}
                                ]
                            },
                            "innertwo": {"type": "string", "example": "inner two"}
                        }
                    }
                ]
            }
        },
        "required": [
            "outerbool"
        ]
    }
    generator = GeneratorFromSchema()
    examples = generator.Generate(schema)
    print(examples)