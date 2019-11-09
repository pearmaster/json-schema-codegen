from jsonschemacodegen import python as pygen

if __name__ == '__main__':
    schema = {
        "type": "array",
        "items": {
            "oneOf": [
                {
                    "type": "string",
                },
                {
                    "type": "integer"
                },
            ]
        }
    }
    generator = pygen.GeneratorFromSchema('output')
    generator.Generate(schema, 'Example', 'example')


