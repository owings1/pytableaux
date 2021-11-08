from utils import get_logic
from lexicals import Operator
import itertools

class BaseModel(object):

    # Default set
    truth_functional_operators = {
        Operator.Assertion             ,
        Operator.Negation              ,
        Operator.Conjunction           ,
        Operator.Disjunction           ,
        Operator.MaterialConditional   ,
        Operator.Conditional           ,
        Operator.MaterialBiconditional ,
        Operator.Biconditional         ,
    }
    # Default set
    modal_operators = {
        Operator.Necessity  ,
        Operator.Possibility,
    }

    def __init__(self):
        self.id = id(self)
        # flag to be set externally
        self.is_countermodel = None

    def read_branch(self, branch):
        raise NotImplementedError()

    def value_of(self, sentence, **kw):
        if self.is_sentence_opaque(sentence):
            return self.value_of_opaque(sentence, **kw)
        elif sentence.is_operated:
            return self.value_of_operated(sentence, **kw)
        elif sentence.is_predicated:
            return self.value_of_predicated(sentence, **kw)
        elif sentence.is_atomic:
            return self.value_of_atomic(sentence, **kw)
        elif sentence.is_quantified:
            return self.value_of_quantified(sentence, **kw)

    def truth_function(self, operator, a, b=None):
        raise NotImplementedError()

    def truth_table_inputs(self, narity):
        return tuple(itertools.product(*[self.truth_values_list for x in range(narity)]))

    def is_sentence_opaque(self, sentence, **kw):
        return False

    def value_of_opaque(self, sentence, **kw):
        raise NotImplementedError()

    def value_of_atomic(self, sentence, **kw):
        raise NotImplementedError()

    def value_of_predicated(self, sentence, **kw):
        raise NotImplementedError()

    def value_of_operated(self, sentence, **kw):
        oper = sentence.operator
        if oper in self.truth_functional_operators:
            return self.truth_function(
                oper,
                *[
                    self.value_of(operand, **kw)
                    for operand in sentence
                ]
            )
        raise NotImplementedError()

    def value_of_quantified(self, sentence, **kw):
        raise NotImplementedError()

    def is_countermodel_to(self, argument):
        raise NotImplementedError()

    def get_data(self):
        return dict()


def truth_table(logic, oper, reverse=False):
    oper = Operator[oper]
    model = get_logic(logic).Model()
    inputs = model.truth_table_inputs(oper.arity)
    if reverse:
        inputs = tuple(reversed(inputs))
    outputs = [
        model.truth_function(oper, *values)
        for values in inputs
    ]
    return {'inputs': inputs, 'outputs': outputs}

def truth_tables(logic, **kw):
    model = get_logic(logic).Model()
    return {
        oper: truth_table(logic, oper, **kw)
        for oper in model.truth_functional_operators
    }