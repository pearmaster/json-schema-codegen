from jsonschemacodegen import cpp, cpp_namer
import sys
import jacobsjsondoc
from pprint import pprint

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
            - "on"
            - "off"
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

if __name__ == '__main__':

    spec = jacobsjsondoc.parse(EXAMPLE_YAML)
    generator = cpp.GeneratorFromSchema(cpp_namer.GeneralCppNamer("/tmp"))

    for msgName, msg in spec['components']['messages'].items():
        path = f"#/components/messages/{msgName}"
        generator.generate(msg['payload'], "example", path)

    for schemaName, schema in spec['components']['schemas'].items():
        path = f"#/components/schemas/{schemaName}".format(schemaName)
        generator.generate(schema, "example", path)

