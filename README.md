# JSON-Schema Codegen

This python library consumes JSON-Schema and generates C++ or Python code.  It generates structures to hold the values defined in the schema, restricting the values according to the schema. 

## Python Requirements for Code Generation

These requirements should be satisfied when `pip3` installing `json-schema-codegen`.

* python 3.7
* jinja2
* stringcase

## Installation

```sh
pip3 install json-schema-codegen
```

## C++ Generated Code

### Supported Schema Features in C++ code generation

A C++ class is generated for each schema node according to the schema's `type` property.  Schemas without a `type` property, with the exception of combining operators `*Of`, are not supported.

* type: string
    * minLength
    * maxLength
    * pattern
* type: string with enum
* type: integer
    * maximum
    * minimum
    * exclusiveMaximum
    * exclusiveMinimum
    * multipleOf
* type: number
    * maximum
    * minimum
    * exclusiveMaximum
    * exclusiveMinimum
    * multipleOf 
* type: boolean
* type: null
* type: array
    * items
    * minItems
    * maxItems
* type: object
    * properties
    * required
* allOf
* anyOf
* oneOf

##### References

`$ref` references are supported for array items, object properties, allOf, anyOf, and oneOf.  However, the caller must provide a "resolver" class which translates the reference into a class name and namespace. 

### Dependencies of the C++ generated code

* boost (boost::optional and boost::variant among others)
* rapidjson
* C++11

### Usage
See [example_usage.py](./examples/example_usage.py) for a more elaborate example on generating C++ code.

```py
import jsonschemacodegen.cpp as cpp

simpleResolver = cpp.SimpleResolver()
output_dir = "/tmp"
    
generator = cpp.GeneratorFromSchema(src_output_dir=output_dir,
    header_output_dir=output_dir, 
    resolver=simpleResolver,
    namespace=[],
    src_usings=[])

sampleSchema = {"type": "string"}

generator.Generate(sampleSchema, 'Example', 'example')
```

## Python Generated Code

A Python3 class is generated for each schema node; the class encapsulating the data described by the schema.  The class accepts in its constructor python primative data types that match the format described the the schema.  Each class has a `Serializable` method which returns data in a format that can be serialized.

JSON (de-)serialization does not happen in the actual class.  This allows for flexibility to use other line-formats, for example, YAML.

### Supported schema features for generating Python code

* type: string
    * minLength
    * maxLength
    * pattern
    * enum
* type: integer
    * maximum
    * minimum
    * exclusiveMaximum
    * exclusiveMinimum
    * multipleOf
    * enum
* type: number
    * maximum
    * minimum
    * exclusiveMaximum
    * exclusiveMinimum
    * multipleOf 
    * enum
* type: boolean
* type: null
* type: array
    * items
    * minItems
    * maxItems
* type: object
    * properties
    * required
* allOf
* anyOf
* oneOf
    * Component schemas with the `title` property.

### Example usage for generating Python code

For a more elaborate example, see [example_python.py](./examples/example_python.py)

```py
from jsonschemacodegen import python as pygen
import json

with open('schema.json') as fp:
    generator = pygen.GeneratorFromSchema('output_dir')
    generator.Generate(json.load(fp), 'Example', 'example')
```

This example will create the file `output_dir/example.py` containing the Python3 class `Example` and nested classes as required.

Using the generated code looks like this:
```py
import example
import json

jsonText = '["an example string in an array"]'

obj = example.Example(json.loads(jsonText))

print(json.dumps(obj, default=lambda x: x.Serializable()))
```

## License

GPLv2


