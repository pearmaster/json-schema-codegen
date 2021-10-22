"""

A JSON schema can be thought of as a tree of sub-schemas.  For example, an object can contain a sub-schema for each property of the object.

We should be able to generate one or more example JSON structures for each JSON schema.  We can request an example from a schema, which may in turn, request examples from any sub-schemas.

With a tree of schemas, the number of different examples for a particular schema can grow quite quickly.  We want a way to keep track of a particular example in a way that allows us to consistantly generate the same example repeatedly.  The identifier for an example, given a non-changing schema, is an ExampleIndex object.

Given an ExampleIndex object instantiated with the same index, a non-changing schema will generate the same example output over and over. 

This only works when ExampleIndex answers a series questions asked of it in the exact same order, for a particular index.  The questions may be:

 * BooleanChoice
 * Choice
 * Number

For example, if ExampleIndex was instantiated with the number 1, then asked for [BooleanChoice, Choice([a,b,c]), Choice([d,e,f]), Number(m), BooleanChoice, BooleanChoice], then it would return the same answers each time.

Creating consistent examples is important for document generation, we don't want the document's examples to change on each generation.  However, if the schema changes, then generating new examples is acceptable.

"""

def bitsNeededForNumber(num):
    bits = 0
    while num > 0:
        num = num >> 1
        bits += 1
    return bits

def rightBitMask(bits):
    mask = 1
    mask = mask << bits
    mask -= 1
    return mask

class ExampleIndex(object):
    """
    Starting with an index, a number with lots of bits, we answer questions by consuming least-valuable bits of the index.
    """

    def __init__(self, index: int):
        """ The `index` param is the seed for the rest of the answers.  It should be a number between 0 and INTMAX (-1).
        """
        self.index = index # Constant
        self.current = index # May change on each inquiry

    def _full(self):
        return self.index == -1

    def BooleanChoice(self):
        if self._full():
            return True
        choice = self.current & 0x01
        self.current = self.current >> 1
        return bool(choice)

    def Choice(self, population: list):
        number_choices = len(population)-1
        index = self.Number(number_choices)
        try:
            choice = population[index % (number_choices+1)]
        except Exception as exc:
            print(f"{exc}: Choice {index} from {population}")
        else:
            return choice

    def Number(self, maximum) -> int:
        if self._full() or maximum == 0:
            return maximum
        bits = bitsNeededForNumber(maximum)
        mask = rightBitMask(bits)
        choice = self.current & mask
        self.current = self.current >> bits
        return choice % (maximum + 1)

    def __repr__(self):
        return str(self.index)