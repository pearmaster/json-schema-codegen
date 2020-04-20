import json
import random
import abc
from copy import copy
from . import schemawrappers

class SchemaResolverBaseClass(abc.ABC):

    @abc.abstractmethod
    def get_schema(self, reference, root=None):
        """Given a reference, returns a wrapped schema object.
        """
        pass

    @abc.abstractmethod
    def get_json(self, reference, root=None) -> dict:
        pass

    @abc.abstractmethod
    def get_document(self, reference):
        pass


class GeneratorFromSchema(object):

    def __init__(self, resolver=None):
        self.resolver = resolver

    @staticmethod
    def DeDuplicate(aList : list, limit=None) -> list:
        text_list = [json.dumps(a, sort_keys=True) for a in aList]
        text_unique = []
        for t in text_list:
            if len(text_unique) == limit:
                break
            if t not in text_unique:
                text_unique.append(t)
        text_sorted = sorted(text_unique, key=len)
        return [json.loads(s) for s in text_sorted]

    def GenerateSome(self, schema, number_of_examples=2, random_seed=0xBEEF) -> list:
        examples = []
        indexes = []
        random.seed(random_seed)
        number_of_combos = schema.GetExampleCombos(self.resolver)
        bits_for_combos = schemawrappers.bitsNeededForNumber(number_of_combos)
        index_max = 1 << bits_for_combos
        if number_of_examples >= index_max:
            indexes = [schemawrappers.ExampleIndex(i) for i in range(0, index_max)]
        elif (number_of_examples*3) >= index_max:
            indexes = [schemawrappers.ExampleIndex(i) for i in range(1, index_max)]
            random.shuffle(indexes)
        else:
            index_numbers = []
            while len(indexes) < number_of_examples*3:
                rand_index = random.randint(1, index_max)
                if rand_index not in index_numbers:
                    indexes.append(schemawrappers.ExampleIndex(rand_index))
                    index_numbers.append(rand_index)
        for index in indexes:
            ex = schema.Example(self.resolver, index)
            examples.append(ex)
        return self.DeDuplicate(examples, limit=number_of_examples)

    def GenerateFull(self, schema) -> list:
        index = schemawrappers.ExampleIndex(-1)
        return [schema.Example(self.resolver, index)]

    def GenerateLimited(self, schema) -> list:
        index = schemawrappers.ExampleIndex(0)
        return [schema.Example(self.resolver, index)]
    
    def Generate(self, schema, number_of_examples=3) -> list:
        examples = []
        if number_of_examples > 0:
            ex = self.GenerateFull(schema)
            examples.extend(ex)
        if number_of_examples > 1:
            ex = self.GenerateLimited(schema)
            examples.extend(ex)
        if number_of_examples > 2:
            examples.extend(self.GenerateSome(schema, number_of_examples))
        ret = self.DeDuplicate(examples, limit=number_of_examples)
        return ret

