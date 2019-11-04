from jsonschemacodegen import python as pygen

if __name__ == '__main__':
    schema = {
        "type": "array"
    }
    generator = pygen.GeneratorFromSchema('output')
    generator.Generate(schema, 'Example', 'example')