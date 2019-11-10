from jsonschemacodegen import python as pygen
import json


if __name__ == '__main__':
    schema = {
        "type": "array",
        "items": {
            "oneOf": [
                {
                    "type": "string",
                    "title": "StringOption",
                },
                {
                    "type": "integer",
                    "title": "InterGerOption",
                },
                {
                    "type": "object",
                    "title": "an object",
                    "properties": {
                        "astring": {"type": "string"},
                        "aboolean": {"type": "boolean"},
                    },
                    "required": [
                        "aboolean"
                    ]
                },
                {
                    "allOf": [
                        {
                            "type": "object",
                            "properties": {
                                "banana": {"type": "string"},
                            },
                            "required": ["banana"],
                        },
                        {
                            "type": "object",
                            "properties": {
                                "apple": {"type": "string"},
                            },
                            "required": ["apple"]
                        }
                    ]
                },
                {
                    "type": "null"
                }
            ]
        }
    }
    if True:
        generator = pygen.GeneratorFromSchema('output')
        generator.Generate(schema, 'Example', 'example')

    from output import example

    def JsonPrint(o):
        print(json.dumps(o, default=lambda x: x.Serializable()))

    data = [
        "a",
        1,
        {"astring": "bool is true", "aboolean": True},
        {"astring": "bool is false", "aboolean": False},
        {"banana": "yello", "apple": "red"},
        None,
    ]
    #exampleObj = example.Example(data)
    #assert(exampleObj[3].Get().GetAstring().Get() == data[3]['astring'])
    #assert(exampleObj[3].Get().GetAboolean().Get() == False)

    #JsonPrint(exampleObj)

    #f = example.Example()
    #JsonPrint(f)

    #nullObj1 = example.Example.Item.Option5()
    #nullObj2 = example.Example.Item.Option5(None)
    #nullObj3 = example.Example.Item.Option5(nullObj1)
    #g = example.Example.Item(nullObj3)
    #JsonPrint(g)

    #comboObject1 = example.Example.Item.Option4({"apple": "a", "banana": "b"})
    #comboObject2 = example.Example.Item.Option4(comboObject1)
    #comboObject3 = example.Example.Item.Option4({"apple":"ap"}, {"banana", "ba"})
    #comboObject4Comp1 = example.Example.Item.Option4.Component1(apple="ap")
    #comboObject3 = example.Example.Item.Option4(comboObject4Comp1, {"banana", "ba"})
    #h = example.Example.Item(comboObject2)
    #JsonPrint(h)
    JsonPrint(example.Example.Item({"banana": "yello", "apple": "red"}))

    #objectThree1 = example.Example.Item.AnObjectOption(astring="jacob", aboolean=True)
    #objectThree2 = example.Example.Item.AnObjectOption({"astring":"jacob", "aboolean":True})
    #objectThree3 = example.Example.Item.AnObjectOption(objectThree1)
