import itertools

class BaseModel(object):

    # Default set
    truth_functional_operators = set([
        'Assertion'              ,
        'Negation'               ,
        'Conjunction'            ,
        'Disjunction'            ,
        'Material Conditional'   ,
        'Conditional'            ,
        'Material Biconditional' ,
        'Biconditional'          ,
    ])
    # Default set
    modal_operators = set([
        'Necessity'  ,
        'Possibility',
    ])

    def __init__(self):
        self.id = id(self)
        # flag to be set externally
        self.is_countermodel = None

    def read_branch(self, branch):
        raise NotImplementedError()

    def value_of(self, sentence, **kw):
        if self.is_sentence_opaque(sentence):
            return self.value_of_opaque(sentence, **kw)
        elif sentence.is_operated():
            return self.value_of_operated(sentence, **kw)
        elif sentence.is_predicated():
            return self.value_of_predicated(sentence, **kw)
        elif sentence.is_atomic():
            return self.value_of_atomic(sentence, **kw)
        elif sentence.is_quantified():
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
        operator = sentence.operator
        if operator in self.truth_functional_operators:
            return self.truth_function(
                operator,
                *[
                    self.value_of(operand, **kw)
                    for operand in sentence.operands
                ]
            )
        raise NotImplementedError()

    def value_of_quantified(self, sentence, **kw):
        raise NotImplementedError()

    def is_countermodel_to(self, argument):
        raise NotImplementedError()

    def get_data(self):
        return dict()