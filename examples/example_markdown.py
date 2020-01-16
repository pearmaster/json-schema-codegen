from jsonschemacodegen import templator
from jsonschemacodegen.resolver import SimpleResolver
from jsonschemacodegen.schemawrappers import SchemaFactory

schema = {
    "type" : "object",
    "properties": {
        "oneOfSomething": {
            'oneOf': [
                {
                    'type': 'integer',
                    'minimum': 0,
                    'multipleOf': 3,
                },
                {
                    "type": "string"
                },
                {
                    "type": "null"
                },
            ]
        },
        "myName": {
            "type": "string",
            "minLength": 1
        },
        "anObject": {
            "type": "object",
            "properties": {
                "one": {
                    "type": "string",
                    "pattern": "[A-Z]*",
                },
                "two": {
                    "type": "number",
                },
            }
        }
    },
    "required": [
        "myName"
    ]
}       



if __name__ == '__main__':
    simpleResolver = SimpleResolver("myproject")
    t = templator.Generator('jsonschemacodegen.templates.markdown', 'output')
    schema = SchemaFactory(schema)
    t.RenderTemplate('description.md.jinja2', 'example.md', schema=schema, resolver=simpleResolver)
