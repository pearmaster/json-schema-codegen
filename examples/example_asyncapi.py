import jsonschemacodegen.cpp as cpp
import sys
import yaml
import stringcase

# This comes from the AsyncAPI Streetlights example
# Only the 'components' section is shown because the
# rest would be ignored.
EXAMPLE_YAML="""
components:
  messages:
    lightMeasured:
      name: lightMeasured
      title: Light measured
      summary: Inform about environmental lighting conditions for a particular streetlight.
      contentType: application/json
      traits:
        - $ref: '#/components/messageTraits/commonHeaders'
      payload:
        $ref: "#/components/schemas/lightMeasuredPayload"
    turnOnOff:
      name: turnOnOff
      title: Turn on/off
      summary: Command a particular streetlight to turn the lights on or off.
      traits:
        - $ref: '#/components/messageTraits/commonHeaders'
      payload:
        $ref: "#/components/schemas/turnOnOffPayload"
    dimLight:
      name: dimLight
      title: Dim light
      summary: Command a particular streetlight to dim the lights.
      traits:
        - $ref: '#/components/messageTraits/commonHeaders'
      payload:
        $ref: "#/components/schemas/dimLightPayload"

  schemas:
    lightMeasuredPayload:
      type: object
      properties:
        lumens:
          type: integer
          minimum: 0
          description: Light intensity measured in lumens.
        sentAt:
          $ref: "#/components/schemas/sentAt"
    turnOnOffPayload:
      type: object
      properties:
        command:
          type: string
          enum:
            - on
            - off
          description: Whether to turn on or off the light.
        sentAt:
          $ref: "#/components/schemas/sentAt"
    dimLightPayload:
      type: object
      properties:
        percentage:
          type: integer
          description: Percentage to which the light should be dimmed to.
          minimum: 0
          maximum: 100
        sentAt:
          $ref: "#/components/schemas/sentAt"
    sentAt:
      type: string
      format: date-time
      description: Date and time when the message was sent.
"""

class AsyncApiResolver(cpp.SimpleResolver):

    def GetHeader(self, reference):
        pkg, n, kls = self.GetReferenceParts(reference)
        return "%s%s%s_%s.hpp" % (pkg or '', pkg and '/' or '', stringcase.lowercase(n[:-1]), stringcase.snakecase(kls))

    def GetNamespace(self, reference, usings=[], append=''):
        pkg, n, _kls = self.GetReferenceParts(reference)
        ns = []
        if pkg is not None:
            ns.append(stringcase.lowercase(pkg))
        ns.append(stringcase.lowercase(n[:-1]))
        return self.ResolveNamespace(usings, ns, append)

    def GetName(self, reference):
        _pkg, _n, kls = self.GetReferenceParts(reference)
        return stringcase.pascalcase(kls)


if __name__ == '__main__':

    spec = yaml.load(EXAMPLE_YAML)

    resolver = AsyncApiResolver()
    output_dir = "/tmp/asyncapi"

    # The generated source will be prefixed with 
    # "using namespace foo::bar" and "using namespace std"
    usings = [["asyncapi"]] 

    generator = cpp.GeneratorFromSchema(src_output_dir=output_dir,
        header_output_dir=output_dir, 
        resolver=resolver,
        namespace=["asyncapi", "message"],
        src_usings=usings)

    for msgName, msg in spec['components']['messages'].items():
        filename_base = "message_%s" % stringcase.snakecase(msgName)
        classname = stringcase.pascalcase(msgName)
        generator.Generate(msg['payload'], classname, filename_base)

    generator = cpp.GeneratorFromSchema(src_output_dir=output_dir,
        header_output_dir=output_dir, 
        resolver=resolver,
        namespace=["asyncapi", "schema"],
        src_usings=usings)

    for schemaName, schema in spec['components']['schemas'].items():
        filename_base = "schema_%s" % stringcase.snakecase(schemaName)
        classname = stringcase.pascalcase(schemaName)
        generator.Generate(schema, classname, filename_base)

