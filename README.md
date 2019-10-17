# JSON-Schema Codegen

This python library consumes JSON-Schema and generates C++ code.  It generates structures to hold the values defined in the schema, restricting the values according to the schema.  Each structure has JSON serialization and de-serialization methods.

## Supported Schema Features

Schemas (and sub-schemas) that are boolean or schemas without `type` are not currently supported.

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

#### References

`$ref` references are supported for array items, object properties, allOf, anyOf, and oneOf.  However, the caller must provide a class which translates the reference into a class name and namespace. 

## Installation

```sh
pip install json-schema-codegen
```

## Usage
See `example_usage.py` for a more elaborate example.

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

## License

GPLv2


