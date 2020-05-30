# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2020 Doug Owings.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ------------------
#
# pytableaux - logic base module

import importlib, notations, os, itertools, time
from types import ModuleType

# http://python-future.org/compatible_idioms.html#basestring
from past.builtins import basestring

current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(current_dir, '..'))
with open(os.path.join(base_dir, 'VERSION'), 'r') as f:
    version = f.read().strip()

copyright = '2014-2020, Doug Owings. Released under the GNU Affero General Public License v3 or later'
source_href = 'https://bitbucket.org/owings1/pytableaux'

# name : arity
operators = {
    'Assertion'              : 1,
    'Negation'               : 1,
    'Conjunction'            : 2,
    'Disjunction'            : 2,
    'Material Conditional'   : 2,
    'Material Biconditional' : 2,
    'Conditional'            : 2,
    'Biconditional'          : 2,
    'Possibility'            : 1,
    'Necessity'              : 1
}

# default display ordering
operators_list = [
    'Assertion'              ,
    'Negation'               ,
    'Conjunction'            ,
    'Disjunction'            ,
    'Material Conditional'   ,
    'Material Biconditional' ,
    'Conditional'            ,
    'Biconditional'          ,
    'Possibility'            ,
    'Necessity'
]

quantifiers_list = [
    'Universal',
    'Existential'
]

system_predicates_list  = [
    'Identity',
    'Existence'
]

system_predicates_index = {
    # negative indexes for system predicates, value is subscript : name.
    -1 : { 0 : 'Identity'  },
    -2 : { 0 : 'Existence' }
}

# The number of symbols is fixed to allow multiple notations.
num_var_symbols       = 4
num_const_symbols     = 4
num_atomic_symbols    = 5
num_predicate_symbols = 4

def nowms():
    return int(round(time.time() * 1000))

class BadArgumentError(Exception):
    pass

class NotImplementedError(Exception):
    pass

def atomic(index, subscript):
    """Return an atomic sentence represented by the given index and subscript integers.
    Examples::

        a  = atomic(index=0, subscript=0)
        a0 = atomic(0, 0)
        assert a == a0
        
        b  = atomic(1, 0)
        a4 = atomic(0, 4)
        
        c3 = atomic(2, 3)
        assert sentence2 == parse('c3', notation='polish') # c has index 2 in polish notation

    """
    return Vocabulary.AtomicSentence(index, subscript)

def negate(sentence):
    """Negate a sentence and return the negated sentence. This is shorthand for 
    ``operate('Negation', [sentence])``. Example::

        a = atomic(0, 0)
        # not a
        sentence = negate(a)

    """
    return Vocabulary.OperatedSentence('Negation', [sentence])

def negative(sentence):
    """Either negate this sentence, or, if it is a negated sentence, return its
    negatum. Example::

        a = atomic(0, 0)
        s1 = negate(a)
        s2 = negative(s1)
        assert s2 == a
    """
    if sentence.is_operated() and sentence.operator == 'Negation':
        return sentence.operand
    return negate(sentence)

def assertion(sentence):
    """Apply the assertion operator to the sentence. This is shorthand for
    ``operate('Assertion', [sentence])``. Example::

        a = atomic(0, 0)
        sentence = assertion(a)

    """
    return Vocabulary.OperatedSentence('Assertion', [sentence])

def operate(operator, operands):
    """Apply an operator to a list of sentences (operands).
    Examples::

        a = atomic(0, 0)
        b = atomic(1, 0)

        # a or b
        sentence2 = operate('Disjunction', [a, b])

        # a or b, and not b
        sentence4 = operate('Conjunction', [sentence2, negate(b)])

        # if a or b, and not b, then a
        sentence5 = operate('Conditional', [sentence4, a])

    Available operators are:

    +------------------------+-------+
    | Operator Name          | Arity |
    +========================+=======+
    | Assertion              | 1     |
    +------------------------+-------+
    | Negation               | 1     |
    +------------------------+-------+
    | Conjunction            | 2     |
    +------------------------+-------+
    | Disjunction            | 2     |
    +------------------------+-------+
    | Material Conditional   | 2     |
    +------------------------+-------+
    | Material Biconditional | 2     |
    +------------------------+-------+
    | Conditional            | 2     |
    +------------------------+-------+
    | Biconditional          | 2     |
    +------------------------+-------+
    | Possibility            | 1     |
    +------------------------+-------+
    | Necessity              | 1     |
    +------------------------+-------+

    """
    return Vocabulary.OperatedSentence(operator, operands)

def constant(index, subscript):
    """Return a constant representend by the given index and subscript integers.
    Example::

        m = constant(0, 0)

    """
    return Vocabulary.Constant(index, subscript)

def variable(index, subscript):
    """
    Return a variable representend by the given index and subscript integers::

        x = variable(0, 0)

    """
    return Vocabulary.Variable(index, subscript)

def predicated(predicate, parameters, vocabulary=None):
    """
    Return a predicate sentence for the given predicate and parameters. ``predicate`` can 
    either be the name of a predicate or a predicate object. Examples using system predicates
    (Existence, Identity)::

        m = constant(0, 0)
        sentence = predicated('Existence', [m])

        n = constant(1, 0)
        sentence2 = predicated('Identity', [m, n])

    Examples using a vocabulary of user-defined predicates::

        vocab = Vocabulary([('is tall', 0, 0, 1)])
        m = constant(0, 0)
        # m is tall
        sentence = predicated('is tall', [m], vocab)

        vocab.declare_predicate(name='is between', index=1, subscript=0, arity=3)
        n = constant(1, 0)
        o = constant(2, 0)
        # m is between n and o
        sentence2 = predicated('is between', [m, n, o], vocab)

    """
    return Vocabulary.PredicatedSentence(predicate, parameters, vocabulary)

def quantify(quantifier, variable, sentence):
    """
    Return a quanitified sentence for the given quantifier, bound variable and
    inner sentence. Example using the Identity system predicate::

        x = variable(0, 0)
        # x is identical to x
        open_sentence = predicated('Identity', [x, x])
        # for all x, x is identical to x
        sentence = quantify('Universal', x, open_sentence)

    Examples using a vocabulary of user-defined predicates::

        vocab = Vocabulary([
            ('is a bachelor', 0, 0, 1),
            ('is unmarried' , 1, 0, 1)
        ])
        x = variable(0, 0)
        # x is a bachelor
        open_sentence = predicated('is a bachelor', [x], vocab)
        # there exists an x, such that x is a bachelor
        sentence = quantify('Existential', x, open_sentence)

        # x is unmarried
        open_sentence2 = predicated('is unmarried', [x], vocab)
        # if x is a bachelor, then x is unmarried
        open_sentence3 = operate('Conditional', [open_sentence, open_sentence2])
        # for all x, if x is a bachelor then x is unmarried
        sentence2 = quantify('Universal', x, open_sentence3)

    """
    return Vocabulary.QuantifiedSentence(quantifier, variable, sentence)

def parse(string, vocabulary=None, notation='polish'):
    """
    Parse a string and return a sentence. If ``vocabulary`` is passed, the parser will
    use its user-defined predicates. The ``notation`` parameter can be either a notation 
    module or a string of the module name. Example::

        sentence1 = parse('Kab', notation='polish')
        assert sentence1 == operate('Conjunction', [atomic(0, 0), atomic(1, 0)])
        sentence2 = parse('A & B', notation='standard')
        assert sentence2 == sentence1

    Example using user-defined predicates from a vocabulary::
    
        vocab = Vocabulary([('is tall', 0, 0, 1)])
        # m is tall
        sentence = parse('Fm', vocab, 'polish')
        assert sentence == predicated(vocab.get_predicate('is tall'), [constant(0, 0)])

    """
    if vocabulary is None:
        vocabulary = Vocabulary()
    notation = _get_module('notations', notation)
    return notation.Parser(vocabulary).parse(string)

class argument(object):
    """
    Create an argument::

        a = atomic(0, 0)
        b = atomic(1, 0)
        # if a then b
        premise2 = operate('Conditional', [a, b])
        # from a, and if a then b, it follows that b
        arg = argument(conclusion=b, premises=[a, premise2])

    You can also pass a notation (and optionally, a vocabulary) to parse sentence::

        arg = argument(conclusion='B', premises=['(A > B)', 'A'], notation='standard')
    """

    class MissingNotationError(Exception):
        pass

    def __init__(self, conclusion=None, premises=None, title=None, notation=None, vocabulary=None):
        self.premises = []
        if premises != None:
            for premise in premises:
                if isinstance(premise, basestring):
                    if notation == None:
                        raise argument.MissingNotationError("Must pass notation to parse sentence strings.")
                    premise = parse(premise, vocabulary, notation)
                self.premises.append(premise)
        if isinstance(conclusion, basestring):
            if notation == None:
                raise argument.MissingNotationError("Must pass notation to parse sentence strings.")
            conclusion = parse(conclusion, vocabulary, notation)
        self.conclusion = conclusion
        self.title      = title

    def __repr__(self):
        if self.title is None:
            return [self.premises, self.conclusion].__repr__()
        return [self.premises, self.conclusion, {'title': self.title}].__repr__()

def tableau(logic, arg=None, **opts):
    """
    Create a tableau for the given logic and argument. Example::

        from logics import cfol
        proof = tableau(cfol, arg)
        proof.build()
        if proof.valid:
            print "Valid"
        else:
            print "Invalid"

    """
    return TableauxSystem.Tableau(logic, arg, **opts)

def arity(operator):
    """
    Get the arity of an operator. Examples::

        assert arity('Conjunction') == 2
        assert arity('Negation') == 1
        assert arity(operate('Negation', [atomic(0, 0)]).operator) == 1

    """
    return operators[operator]

def is_constant(obj):
    """
    Check whether a parameter is a constant. Example::

        assert is_constant(constant(0, 0))
        assert not is_constant(variable(0, 0))
        assert not is_constant([0, 0]) # must be an instance of Vocabulary.Constant

    """
    return isinstance(obj, Vocabulary.Constant)

def is_variable(obj):
    """
    Check whether a parameter is a variable. Example::

        assert is_constant(variable(0, 0))
        assert not is_constant(constant(0, 0))
        assert not is_constant([0, 0]) # must be an instance of Vocabulary.Variable

    """
    return isinstance(obj, Vocabulary.Variable)

def get_logic(arg):
    """
    Get the logic module from the specified name. Example::

        assert get_logic('fde') == logics.fde
        assert get_logic('logics.fde') == logics.fde
        assert get_logic('FDE') == logics.fde
        assert get_logic(logics.fde) == logics.fde
    """
    return _get_module('logics', arg)

def get_system_predicate(name):
    """
    Get a system predicate by name. Example::

        assert get_system_predicate('Identity').arity == 2
    """
    return Vocabulary.get_system_predicate(name)

def truth_table(logic, operator):
    model = get_logic(logic).Model()
    inputs = list(itertools.product(*[model.truth_values for x in range(arity(operator))]))
    outputs = [model.truth_function(operator, *values) for values in inputs]
    return {'inputs': inputs, 'outputs': outputs}

def truth_tables(logic):
    model = get_logic(logic).Model()
    return {operator: truth_table(logic, operator) for operator in model.truth_functional_operators}

def _get_module(package, arg):    
    if isinstance(arg, ModuleType):
        return arg
    if isinstance(arg, basestring):
        if '.' not in arg:
            arg = package + '.' + arg
        return importlib.import_module(arg.lower())
    raise BadArgumentError("Argument must be module or string")

class Vocabulary(object):
    """
    Create a new vocabulary. *predicate_defs* is a list of tuples (name, index, subscript, arity)
    defining user predicates. Example::

        vocab = Vocabulary([
            ('is tall',        0, 0, 1),
            ('is taller than', 0, 1, 2),
            ('between',        1, 0, 3)
        ])

    """

    class Predicate(object):

        def __init__(self, name, index, subscript, arity):
            if index >= num_predicate_symbols:
                raise Vocabulary.IndexTooLargeError("Predicate index too large {0}".format(str(index)))
            if arity == None or arity < 1:
                raise Vocabulary.PredicateArityError('Invalid predicate arity {0}'.format(str(arity)))
            if subscript == None or subscript < 0:
                raise Vocabulary.PredicateSubscriptError('Invalid predicate subscript {0}'.format(str(subscript)))
            self.name      = name
            self.arity     = arity
            self.index     = index
            self.subscript = subscript

        def hash_tuple(self):
            return (1, self.index, self.subscript, self.arity)

        # TODO: make this DRY with Sentence
        def __eq__(self, other):
            return other != None and self.__dict__ == other.__dict__

        def __ne__(self, other):
            return other == None or self.__dict__ != other.__dict__

        def __lt__(self, other):
            return self.hash_tuple() < other.hash_tuple()

        def __le__(self, other):
            return self.hash_tuple() <= other.hash_tuple()

        def __gt__(self, other):
            return self.hash_tuple() > other.hash_tuple()

        def __ge__(self, other):
            return self.hash_tuple() >= other.hash_tuple()

        def __cmp__(self, other):
            # Python 2 only
            return cmp(self.hash_tuple(), other.hash_tuple())

        def __hash__(self):
            return hash(self.hash_tuple())

    class PredicateError(Exception):
        pass

    class IndexTooLargeError(PredicateError):
        pass

    class PredicateArityError(PredicateError):
        pass

    class PredicateSubscriptError(PredicateError):
        pass

    class PredicateAlreadyDeclaredError(PredicateError):
        pass

    class NoSuchPredicateError(PredicateError):
        pass

    class PredicateArityMismatchError(PredicateError):
        pass

    class PredicateIndexMismatchError(PredicateError):
        pass

    class OperatorError(Exception):
        pass

    class NoSuchOperatorError(OperatorError):
        pass

    class OperatorArityMismatchError(OperatorError):
        pass

    @staticmethod
    def get_system_predicate(name):
        return system_predicates[name]

    def __init__(self, predicate_defs=None):
        self.user_predicates       = {}
        self.user_predicates_list  = []
        self.user_predicates_index = {}
        if predicate_defs:
            for info in predicate_defs:
                if len(info) != 4:
                    raise Vocabulary.PredicateError("Predicate declarations must be 4-tuples (name, index, subscript, arity).")
                self.declare_predicate(*info)

    def get_predicate(self, name=None, index=None, subscript=None):
        """
        Get a defined predicate, either by name, or by index and subscript. This includes system
        predicates::

            vocab = Vocabulary()
            predicate = vocab.get_predicate('Identity')

        Or user-defined predicates::

            vocab = Vocabulary([('is tall', 0, 0, 1)])
            assert vocab.get_predicate('is tall') == vocab.get_predicate(index=0, subscript=0)

        """
        if name == None and index != None and isinstance(index, basestring):
            name = index
            index = None
        elif index == None and name != None and isinstance(name, int):
            index = name
            name = None
        if name != None:
            if name in system_predicates:
                return system_predicates[name]
            if name in self.user_predicates:
                return self.user_predicates[name]
            raise Vocabulary.NoSuchPredicateError(name)
        if index != None and subscript != None:
            idx = str([index, subscript])
            if index < 0:
                if subscript not in system_predicates_index[index]:
                    raise Vocabulary.NoSuchPredicateError(idx)
                return system_predicates[system_predicates_index[index][subscript]]
            if idx not in self.user_predicates_index:
                raise Vocabulary.NoSuchPredicateError(idx)
            return self.user_predicates_index[idx]
        raise Vocabulary.PredicateError('Not enough information to get predicate')

    def declare_predicate(self, name, index, subscript, arity):
        """
        Declare a user-defined predicate::

            vocab = Vocabulary()
            predicate = vocab.declare_predicate(name='is tall', index=0, subscript=0, arity=1)
            assert predicate == vocab.get_predicate('is tall')
            assert predicate == vocab.get_predicate(index=0, subscript=0)
            
            # predicates cannot be re-declared
            try:
                vocab.declare_predicate('is tall', index=1, subscript=2, arity=3)
            except Vocabulary.PredicateAlreadyDeclaredError:
                assert True
            else:
                assert False

        """
        if name in system_predicates:
            raise Vocabulary.PredicateAlreadyDeclaredError("Cannot declare system predicate '{0}'".format(name))
        if name in self.user_predicates:
            raise Vocabulary.PredicateAlreadyDeclaredError("Predicate '{0}' already declared".format(name))
        try:
            self.get_predicate(index=index, subscript=subscript)
        except Vocabulary.NoSuchPredicateError:
            pass
        else:
            raise Vocabulary.PredicateAlreadyDeclaredError("Predicate for {0},{1} already declared".format(str(index), str(subscript)))
        predicate = Vocabulary.Predicate(name, index, subscript, arity)
        self.user_predicates[name] = predicate
        self.user_predicates_list.append(name)
        if index >= 0:
            self.user_predicates_index[str([index, subscript])] = predicate    
        return predicate

    def list_predicates(self):
        return system_predicates_list + self.user_predicates_list

    def list_user_predicates(self):
        return list(self.user_predicates_list)

    class Parameter(object):

        def __init__(self, index, subscript):
            self.index = index
            self.subscript = subscript

        def is_constant(self):
            return isinstance(self, Vocabulary.Constant)

        def is_variable(self):
            return isinstance(self, Vocabulary.Variable)

        def __repr__(self):
            return (self.index, self.subscript).__repr__()

    class Constant(Parameter):

        def __init__(self, index, subscript):
            if index >= num_const_symbols:
                raise Vocabulary.IndexTooLargeError("Index too large {0}".format(str(index)))
            super(Vocabulary.Constant, self).__init__(index, subscript)

        def __eq__(self, other):
            return isinstance(other, Vocabulary.Constant) and self.__dict__ == other.__dict__

        def __hash__(self):
            return hash((2, self.index, self.subscript))

    class Variable(Parameter):

        def __init__(self, index, subscript):
            if index >= num_var_symbols:
                raise Vocabulary.IndexTooLargeError("Index too large {0}".format(str(index)))
            super(Vocabulary.Variable, self).__init__(index, subscript)

        def __eq__(self, other):
            return isinstance(other, Vocabulary.Variable) and self.__dict__ == other.__dict__

        def __hash__(self):
            return hash((3, self.index, self.subscript))

    class Sentence(object):

        operator   = None
        quantifier = None
        predicate  = None

        def is_sentence(self):
            return True

        def is_atomic(self):
            return isinstance(self, Vocabulary.AtomicSentence)

        def is_predicated(self):
            return isinstance(self, Vocabulary.PredicatedSentence)

        def is_quantified(self):
            return isinstance(self, Vocabulary.QuantifiedSentence)

        def is_operated(self):
            return isinstance(self, Vocabulary.OperatedSentence)

        def is_literal(self):
            return self.is_atomic() or self.is_predicated() or (
                self.is_operated() and self.operator == 'Negation' and (
                    self.operand.is_atomic() or
                    self.operand.is_predicated()
                )
            )

        def substitute(self, constant, variable):
            raise NotImplementedError(NotImplemented)

        def constants(self):
            raise NotImplementedError(NotImplemented)

        def variables(self):
            raise NotImplementedError(NotImplemented)

        def atomics(self):
            raise NotImplementedError(NotImplemented)

        def predicates(self):
            raise NotImplementedError(NotImplemented)

        def hash_tuple(self):
            raise NotImplementedError(NotImplemented)

        def __eq__(self, other):
            return other != None and self.__dict__ == other.__dict__

        def __ne__(self, other):
            return other == None or self.__dict__ != other.__dict__

        def __lt__(self, other):
            return self.hash_tuple() < other.hash_tuple()

        def __le__(self, other):
            return self.hash_tuple() <= other.hash_tuple()

        def __gt__(self, other):
            return self.hash_tuple() > other.hash_tuple()

        def __ge__(self, other):
            return self.hash_tuple() >= other.hash_tuple()

        def __cmp__(self, other):
            # Python 2 only
            return cmp(self.hash_tuple(), other.hash_tuple())

        def __repr__(self):
            from notations import polish
            return polish.write(self)

    class AtomicSentence(Sentence):

        def __init__(self, index, subscript):
            if index >= num_atomic_symbols:
                raise Vocabulary.IndexTooLargeError("Index too large {0}".format(str(index)))
            self.index     = index
            self.subscript = subscript

        def substitute(self, constant, variable):
            return self

        def constants(self):
            return set()

        def variables(self):
            return set()

        def atomics(self):
            return set([self])

        def predicates(self):
            return set()

        def next(self):
            if self.index < num_atomic_symbols - 1:
                index = self.index + 1
                subscript = self.subscript
            else:
                index = 0
                subscript = self.subscript + 1
            return Vocabulary.AtomicSentence(index, subscript)

        def hash_tuple(self):
            return (4, self.index, self.subscript)

        def __hash__(self):
            return hash(self.hash_tuple())

    class PredicatedSentence(Sentence):

        def __init__(self, predicate, parameters, vocabulary=None):
            if isinstance(predicate, basestring):
                if predicate in system_predicates:
                    predicate = system_predicates[predicate]
                elif vocabulary is None:
                    raise Vocabulary.NoSuchPredicateError("'{0}' is not a system predicate, and no vocabulary was passed.".format(predicate))
                else:
                    predicate = vocabulary.get_predicate(predicate)    
            if len(parameters) != predicate.arity:
                raise Vocabulary.PredicateArityMismatchError(
                    'Expecting {0} parameters for predicate {1}, got {2} instead.'.format(
                        predicate.arity, str([predicate.index, predicate.subscript]), len(parameters)
                    )
                )
            self.predicate  = predicate
            self.parameters = parameters
            self.vocabulary = vocabulary

        def substitute(self, constant, variable):
            params = []
            for param in self.parameters:
                if param == variable:
                    params.append(constant)
                else:
                    params.append(param)
            return predicated(self.predicate, params)

        def constants(self):
            return {param for param in self.parameters if is_constant(param)}

        def variables(self):
            return {param for param in self.parameters if is_variable(param)}

        def atomics(self):
            return set()

        def predicates(self):
            return set([self.predicate])

        def hash_tuple(self):
            return (5, self.predicate) + tuple((param for param in self.parameters))

        def __hash__(self):
            return hash(self.hash_tuple())

    class QuantifiedSentence(Sentence):

        def __init__(self, quantifier, variable, sentence):
            self.quantifier = quantifier
            self.variable   = variable
            self.sentence   = sentence

        def substitute(self, constant, variable):
            if self.sentence.is_quantified():
                return Vocabulary.QuantifiedSentence(self.sentence.quantifier, self.sentence.variable, self.sentence.substitute(constant, variable))
            return self.sentence.substitute(constant, variable)

        def constants(self):
            return self.sentence.constants()

        def variables(self):
            return self.sentence.variables()

        def atomics(self):
            return self.sentence.atomics()

        def predicates(self):
            return self.sentence.predicates()

        def hash_tuple(self):
            return (6, quantifiers_list.index(self.quantifier), self.variable, self.sentence)

        def __hash__(self):
            return hash(self.hash_tuple())

    class OperatedSentence(Sentence):

        def __init__(self, operator, operands):
            if operator not in operators:
                raise Vocabulary.NoSuchOperatorError("Unknown operator '{0}'.".format(operator))
            if len(operands) != arity(operator):
                raise Vocabulary.OperatorArityMismatchError(
                    "Expecting {0} operands for operator '{1}', got {2}.".format(
                        arity(operator), operator, len(operands)
                    )
                )
            self.operator = operator
            self.operands = operands
            if len(operands) == 1:
                self.operand = operands[0]
            elif len(operands) > 1:
                self.lhs = operands[0]
                self.rhs = operands[-1]

        def substitute(self, constant, variable):
            return operate(self.operator, [operand.substitute(constant, variable) for operand in self.operands])

        def constants(self):
            c = set()
            for operand in self.operands:
                c.update(operand.constants())
            return c

        def variables(self):
            v = set()
            for operand in self.operands:
                v.update(operand.variables())
            return v

        def atomics(self):
            a = set()
            for operand in self.operands:
                a.update(operand.atomics())
            return a

        def predicates(self):
            p = set()
            for operand in self.operands:
                p.update(operand.predicates())
            return p

        def hash_tuple(self):
            return (7, operators_list.index(self.operator)) + tuple((operand for operand in self.operands))

        def __hash__(self):
            return hash(self.hash_tuple())

    class Writer(object):

        symbol_sets = {}
        symbol_set = None

        def __init__(self, symbol_set = None):
            self.symbol_set = self.symset(symbol_set)

        def symset(self, symbol_set = None):
            if symbol_set == None:
                if self.symbol_set == None:
                    symbol_set = 'default'
                else:
                    return self.symbol_set
            if isinstance(symbol_set, basestring):
                return self.symbol_sets[symbol_set]
            else:
                return symbol_set

        def write(self, sentence, symbol_set = None, **opts):
            if sentence.is_atomic():
                return self.write_atomic(sentence, symbol_set = symbol_set)
            elif sentence.is_quantified():
                return self.write_quantified(sentence, symbol_set = symbol_set)
            elif sentence.is_predicated():
                return self.write_predicated(sentence, symbol_set = symbol_set)
            elif sentence.is_operated():
                return self.write_operated(sentence, symbol_set = symbol_set)
            else:
                raise NotImplementedError(NotImplemented)

        def write_atomic(self, sentence, symbol_set = None):
            symset = self.symset(symbol_set)
            return symset.charof('atomic', sentence.index) + self.write_subscript(sentence.subscript, symbol_set = symbol_set)

        def write_quantified(self, sentence, symbol_set = None):
            symset = self.symset(symbol_set)
            return ''.join([
                symset.charof('quantifier', sentence.quantifier),
                symset.charof('variable', sentence.variable.index),
                self.write_subscript(sentence.variable.subscript, symbol_set = symbol_set),
                self.write(sentence.sentence, symbol_set = symbol_set)
            ])

        def write_predicated(self, sentence, symbol_set = None):
            symset = self.symset(symbol_set)
            s = self.write_predicate(sentence.predicate, symbol_set = symbol_set)
            for param in sentence.parameters:
                s += self.write_parameter(param, symbol_set = symbol_set)
            return s

        def write_operated(self, sentence, symbol_set = None):
            raise NotImplementedError(NotImplemented)

        def write_operator(self, operator, symbol_set = None):
            symset = self.symset(symbol_set)
            return symset.charof('operator', operator)

        def write_predicate(self, predicate, symbol_set = None):
            symset = self.symset(symbol_set)
            if predicate.name in system_predicates:
                s = symset.charof('system_predicate', predicate.name)
            else:
                s = symset.charof('user_predicate', predicate.index)
            s += self.write_subscript(predicate.subscript, symbol_set = symbol_set)
            return s

        def write_parameter(self, param, symbol_set = None):
            if param.is_constant():
                return self.write_constant(param, symbol_set = symbol_set)
            elif param.is_variable():
                return self.write_variable(param, symbol_set = symbol_set)
            else:
                raise NotImplementedError(NotImplemented)

        def write_constant(self, constant, symbol_set = None):
            symset = self.symset(symbol_set)
            return ''.join([
                symset.charof('constant', constant.index),
                self.write_subscript(constant.subscript, symbol_set = symbol_set)
            ])

        def write_variable(self, variable, symbol_set = None):
            symset = self.symset(symbol_set)
            return ''.join([
                symset.charof('variable', variable.index),
                self.write_subscript(variable.subscript, symbol_set = symbol_set)
            ])

        def write_subscript(self, subscript, symbol_set = None):
            symset = self.symset(symbol_set)
            if symset.name == 'html':
                if subscript != 0:
                    return ''.join([
                        '<span class="subscript">',
                        symset.subfor(subscript, skip_zero = True),
                        '</span>'
                    ])
                return ''
            else:
                return symset.subfor(subscript, skip_zero = True)

system_predicates = {
    'Identity'  : Vocabulary.Predicate('Identity',  -1, 0, 2),
    'Existence' : Vocabulary.Predicate('Existence', -2, 0, 1)
}

class TableauxSystem(object):

    @staticmethod
    def build_trunk(tableau, argument):
        raise NotImplementedError(NotImplemented)

    @staticmethod
    def read_model(model, branch):
        model.read_branch(branch)

    class TrunkAlreadyBuiltError(Exception):
        pass

    class TrunkNotBuiltError(Exception):
        pass

    class BranchClosedError(Exception):
        pass

    class ProofTimeoutError(Exception):
        pass

    class Tableau(object):
        """
        Represents a tableau proof of an argument for the given logic.
        """

        def __init__(self, logic, argument, **opts):
            #: A tableau is finished when no more rules can apply.
            self.finished = False
            
            #: An argument is proved (valid) when its finished tableau has no open branches.
            self.valid = None
            
            #: The set of branches on the tableau.
            self.branches = list()
            
            #: A tree-map structure of the tableau, generated after the proof is finished.
            self.tree = dict()
            
            # A history of rule applications.
            self.history = []

            #: A reference to the logic, if given
            self.logic = None

            #: The rule instances of the logic, if given
            self.rules = []

            #: The argument of the tableau, if given
            self.argument = None

            # flag to build models
            self.is_build_models = None
            # build start time
            self.build_start_time = None
            # whether we ended pre-maturely (e.g. max_steps)
            self.is_premature = False

            # opts
            self.opts = opts

            self.open_branchset = set()
            self.branch_dict = dict()
            self.trunk_built = False
            self.current_step = 0

            if logic != None:
                self.set_logic(logic)

            if argument != None:
                self.set_argument(argument)

        def build(self, models=False, timeout=None, max_steps=None):
            """
            Build the tableau. Returns self.
            """
            self.is_build_models = models
            self.build_start_time = nowms()
            self.build_timeout = timeout
            while not self.finished:
                if max_steps != None and len(self.history) >= max_steps:
                    self.is_premature = True
                    break
                self.check_timeout()
                self.step()
            self.finish()
            self.is_build_models = None
            return self

        def step(self):
            if self.finished:
                return False
            if self.argument != None and not self.trunk_built:
                raise TableauxSystem.TrunkNotBuiltError("Trunk is not built.") 
            for rule in self.rules:
                target = rule.applies()
                if target:
                    rule.apply(target)
                    application = { 'rule' : rule, 'target' : target }
                    self.history.append(application)
                    self.current_step += 1
                    return application
            self.finish()
            return False

        def set_logic(self, logic):
            self.logic = get_logic(logic)
            opts = dict()
            if 'is_rank_optim' in self.opts:
                opts['is_rank_optim'] = self.opts['is_rank_optim']
            else:
                opts['is_rank_optim'] = True
            self.rules = [Rule(self, **opts) for Rule in self.logic.TableauxRules.rules]
            return self

        def set_argument(self, argument):
            self.argument = argument
            if self.logic != None:
                self.build_trunk()
            return self

        def after_branch_close(self, branch):
            self.open_branchset.remove(branch)
            for rule in self.rules:
                rule.after_branch_close(branch)

        def after_node_add(self, branch, node):
            for rule in self.rules:
                rule.after_node_add(branch, node)

        def after_node_tick(self, branch, node):
            for rule in self.rules:
                rule.after_node_tick(branch, node)

        def open_branches(self):
            """
            Return the set of open branches on the tableau.
            """
            return self.open_branchset

        def get_rule(self, rule):
            """
            Get a rule instance by name or class reference. Returns first occurrence.
            """
            for r in self.rules:
                if r.__class__ == rule or r.__class__.__name__ == rule:
                    return r

        def check_timeout(self):
            if self.build_timeout != None and self.build_timeout >= 0:
                expiry = self.build_start_time + self.build_timeout
                now = nowms()
                if now > expiry:
                    raise TableauxSystem.ProofTimeoutError('Timeout of {0}ms exceeded.'.format(str(self.build_timeout)))
                    
        def structure(self, branches, node_depth=0, track=None):
            is_root = track == None
            if track == None:
                track = {
                    'pos'            : 0,
                    'depth'          : 0,
                    'distinct_nodes' : 0,
                }
            track['pos'] += 1
            structure = {
                # the nodes on this structure.
                'nodes'                 : [],
                # this child structures.
                'children'              : [],
                # whether this is a terminal (childless) structure.
                'leaf'                  : False,
                # whether this is a terminal structure that is closed.
                'closed'                : False,
                # whether this is a terminal structure that is open.
                'open'                  : False,
                # the pre-ordered tree left value.
                'left'                  : track['pos'],
                # the pre-ordered tree right value.
                'right'                 : None,
                # the total node count of all descendants.
                'descendant_node_count' : 0,
                # the node count plus descendant node count.
                'structure_node_count'  : 0,
                # the depth of this structure (ancestor structure count).
                'depth'                 : track['depth'],
                # whether this structure or a descendant is open.
                'has_open'              : False,
                # whether this structure or a descendant is closed.
                'has_closed'            : False,
                # if closed, the step number at which it closed.
                'closed_step'           : None,
                # the step number at which this structure first appears.
                'step'                  : None,
                # the number of descendant terminal structures, or 1.
                'width'                 : 0,
                # 0.5x the width of the first child structure, plus 0.5x the
                # width of the last child structure (if distinct from the first),
                # plus the sum of the widths of the other (distinct) children.
                'balanced_line_width'   : None,
                # 0.5x the width of the first child structure divided by the
                # width of this structure.
                'balanced_line_margin'  : None,
                # the branch id, only set for leaves
                'branch_id'             : None,
                # the model id, if exists, only set for leaves
                'model_id'              : None,
                # whether this is the one and only branch
                'is_only_branch'        : False,
            }
            while True:
                relevant = [branch for branch in branches if len(branch.nodes) > node_depth]
                for branch in relevant:
                    if branch.closed:
                        structure['has_closed'] = True
                    else:
                        structure['has_open'] = True
                    if structure['has_open'] and structure['has_closed']:
                        break
                distinct_nodes = []
                distinct_nodeset = set()
                for branch in relevant:
                    node = branch.nodes[node_depth]
                    if node not in distinct_nodeset:
                        distinct_nodeset.add(node)
                        distinct_nodes.append(node)
                if len(distinct_nodes) == 1:
                    node = relevant[0].nodes[node_depth]
                    structure['nodes'].append(node)
                    if structure['step'] == None or structure['step'] > node.step:
                        structure['step'] = node.step
                    node_depth += 1
                    continue
                break
            track['distinct_nodes'] += len(structure['nodes'])
            if len(branches) == 1:
                branch = branches[0]
                structure['closed'] = branch.closed
                structure['open'] = not branch.closed
                if structure['closed']:
                    structure['closed_step'] = branch.closed_step
                    structure['has_closed'] = True
                else:
                    structure['has_open'] = True
                structure['width'] = 1
                structure['leaf'] = True
                structure['branch_id'] = branch.id
                if branch.model != None:
                    structure['model_id'] = branch.model.id
                if track['depth'] == 0:
                    structure['is_only_branch'] = True
            else:
                inbetween_widths = 0
                track['depth'] += 1
                first_width = 0
                last_width = 0
                for i, node in enumerate(distinct_nodes):
                    child_branches = [branch for branch in branches if branch.nodes[node_depth] == node]
                    # recurse
                    child = self.structure(child_branches, node_depth, track)
                    structure['descendant_node_count'] = len(child['nodes']) + child['descendant_node_count']
                    structure['width'] += child['width']
                    structure['children'].append(child)
                    if i == 0:
                        structure['branch_step'] = child['step']
                        first_width = float(child['width']) / 2
                    elif i == len(distinct_nodes) - 1:
                        last_width = float(child['width']) / 2
                    else:
                        inbetween_widths += child['width']
                    if structure['branch_step'] > child['step']:
                        structure['branch_step'] = child['step']
                if structure['width'] > 0:
                    structure['balanced_line_width'] = float(first_width + last_width + inbetween_widths) / structure['width']
                    structure['balanced_line_margin'] = first_width / structure['width']
                else:
                    structure['balanced_line_width'] = 0
                    structure['balanced_line_margin'] = 0
                track['depth'] -= 1
            structure['structure_node_count'] = structure['descendant_node_count'] + len(structure['nodes'])
            track['pos'] += 1
            structure['right'] = track['pos']
            if is_root:
                structure['distinct_nodes'] = track['distinct_nodes']
            return structure

        def branch(self, other_branch=None):
            """
            Return a new branch on the tableau containing the nodes of the given branch, if any.
            """
            if other_branch == None:
                branch = TableauxSystem.Branch(self)
            else:
                branch = other_branch.copy()
            branch.index = len(self.branches)
            self.branches.append(branch)
            if not branch.closed:
                self.open_branchset.add(branch)
            self.branch_dict[id(branch)] = branch
            for rule in self.rules:
                rule.after_branch_add(branch, other_branch)
            return branch

        def build_trunk(self):
            if self.trunk_built:
                raise TableauxSystem.TrunkAlreadyBuiltError("Trunk is already built.")
            self.logic.TableauxSystem.build_trunk(self, self.argument)
            self.trunk_built = True
            self.current_step += 1

        def get_branch(self, branch_id):
            return self.branch_dict[branch_id]

        def finish(self):
            """
            Mark the tableau as finished. Computes the ``valid`` property and builds the structure
            into the ``tree`` property. Returns self.
            """
            if self.finished:
                return self
            self.finished = True
            num_open      = len(self.open_branches())
            self.valid    = num_open == 0
            self.stats = {
                'branches'       : len(self.branches),
                'open_branches'  : num_open,
                'closed_branches': len(self.branches) - num_open,
                'rules_applied'  : len(self.history),
            }
            if self.valid:
                self.stats['result'] = 'Valid'
            elif self.is_premature:
                self.stats['result'] = 'Unfinished'
            else:
                self.stats['result'] = 'Invalid'
            if self.is_build_models:
                self.build_models()
            self.tree = self.structure(self.branches)
            self.stats['distinct_nodes'] = self.tree['distinct_nodes']
            if self.build_start_time != None:
                self.stats['build_duration'] = nowms() - self.build_start_time
            else:
                self.stats['build_duration'] = None
            return self

        def build_models(self):
            model_start_time = nowms()
            for branch in list(self.open_branches()):
                self.check_timeout()
                branch.make_model()

        def __repr__(self):
            return {
                'argument'      : self.argument,
                'branches'      : len(self.branches),
                'rules_applied' : len(self.history),
                'finished'      : self.finished,
                'valid'         : self.valid
            }.__repr__()

    class Branch(object):
        """
        Represents a tableau branch.
        """

        def __init__(self, tableau=None):
            self.id = id(self)
            self.closed = False
            self.ticked_nodes = set()
            self.nodes = []
            self.consts = set()
            self.ws = set()
            self.preds = set()
            self.atms = set()
            self.leaf = None
            self.tableau = tableau
            self.closed_step = None
            self.index = None
            self.model = None
            self.node_index = {
                'sentence'   : dict(),
                'designated' : dict(),
                'world'      : dict()
            }

        def has(self, props, ticked=None):
            """
            Check whether there is a node on the branch that matches the given properties,
            optionally filtered by ticked status.
            """
            return self.find(props, ticked) != None

        def has_any(self, props_list, ticked=None):
            for props in props_list:
                if self.has(props, ticked=ticked):
                    return True
            return False

        def has_all(self, props_list, ticked=None):
            for props in props_list:
                if not self.has(props, ticked=ticked):
                    return False
            return True

        def find(self, props, ticked=None):
            """
            Find the first node on the branch that matches the given properties, optionally
            filtered by ticked status. Returns ``None`` if not found.
            """
            haystack = set(self.get_nodes(ticked=ticked))
            # reduce from node index
            for prop in self.node_index:
                if prop in props:
                    key = str(props[prop])
                    if key not in self.node_index[prop]:
                        return None
                    haystack = haystack & self.node_index[prop][key]
            for node in haystack:
                if node.has_props(props):
                    return node
            return None

        def add(self, node):
            """
            Add a node (Node object or dict of props). Returns self.
            """
            if not isinstance(node, TableauxSystem.Node):
                node = TableauxSystem.Node(props=node)
            self.nodes.append(node)
            self.consts.update(node.constants())
            self.ws.update(node.worlds())
            self.preds.update(node.predicates())
            self.atms.update(node.atomics())
            node.parent = self.leaf
            if self.tableau != None:
                node.step = self.tableau.current_step
                self.tableau.after_node_add(self, node)
            self.leaf = node
            for prop in self.node_index:
                if prop in node.props:
                    key = str(node.props[prop])
                    if key not in self.node_index[prop]:
                        self.node_index[prop][key] = set()
                    self.node_index[prop][key].add(node)
            return self

        def update(self, nodes):
            """
            Add multiple nodes. Returns self.
            """
            for node in nodes:
                self.add(node)
            return self

        def tick(self, node):
            """
            Tick a node for the branch. Returns self.
            """
            if node not in self.ticked_nodes:
                self.ticked_nodes.add(node)
                node.ticked = True
                if self.tableau != None and self.tableau.current_step != None:
                    if node.ticked_step == None or self.tableau.current_step > node.ticked_step:
                        node.ticked_step = self.tableau.current_step
                    self.tableau.after_node_tick(self, node)
            return self

        def close(self):
            """
            Close the branch. Returns self.
            """
            self.closed = True
            if self.tableau != None:
                self.closed_step = self.tableau.current_step
                self.tableau.after_branch_close(self)
            return self

        def get_nodes(self, ticked=None):
            """
            Return the nodes, optionally filtered by ticked status.
            """
            if ticked == None:
                return self.nodes
            return [node for node in self.nodes if ticked == self.is_ticked(node)]

        def is_ticked(self, node):
            return node in self.ticked_nodes

        def copy(self):
            branch = TableauxSystem.Branch()
            branch.nodes = list(self.nodes)
            branch.ticked_nodes = set(self.ticked_nodes)
            branch.consts = set(self.consts)
            branch.ws = set(self.ws)
            branch.leaf = self.leaf
            branch.tableau = self.tableau
            branch.node_index = {prop : {key : set(self.node_index[prop][key]) for key in self.node_index[prop]} for prop in self.node_index}
            return branch

        def worlds(self):
            """
            Return the set of worlds that appear on the branch.
            """
            return self.ws

        def new_world(self):
            """
            Return a new world that does not appear on the branch.
            """
            worlds = self.worlds()
            if not len(worlds):
                return 0
            return max(worlds) + 1

        def constants(self):
            """
            Return the set of constants that appear on the branch.
            """
            return self.consts

        def predicates(self):
            """
            Return the set of predicates that appear on the branch.
            """
            return self.preds

        def atomics(self):
            """
            Return the set of atomics that appear on the branch.
            """
            return self.atms

        def new_constant(self):
            """
            Return a new constant that does not appear on the branch.
            """
            constants = list(self.constants())
            if not len(constants):
                return constant(0, 0)
            index = 0
            subscript = 0
            c = constant(index, subscript)
            while c in constants:
                index += 1
                if index == num_const_symbols:
                    index = 0
                    subscript += 1
                c = constant(index, subscript)
            return c

        def make_model(self):
            """
            Make a model from the open branch.
            """
            model = self.tableau.logic.Model()
            if self.closed:
                raise BranchClosedError('Cannot build a model from a closed branch')
            model.read_branch(self)
            self.model = model
            return model

        def __repr__(self):
            return {'nodes': self.nodes, 'closed': self.closed}.__repr__()

    class Node(object):
        """
        Represents a node on a branch.
        """

        def __init__(self, props={}, parent=None):
            #: A dictionary of properties for the node.
            self.props = {
                'world'      : None,
                'designated' : None,
            }
            self.props.update(props)
            self.ticked = False
            self.parent = parent
            self.step = None
            self.ticked_step = None
            self.id = id(self)

        def has(self, prop):
            return prop in self.props and self.props[prop] != None

        def has_props(self, props):
            for prop in props:
                if prop not in self.props or not props[prop] == self.props[prop]:
                    return False
            return True

        def worlds(self):    
            worlds = set()
            if 'world' in self.props and self.props['world'] != None:
                worlds.add(self.props['world'])
            if 'world1' in self.props:
                worlds.add(self.props['world1'])
            if 'world2' in self.props:
                worlds.add(self.props['world2'])
            if 'worlds' in self.props:
                worlds.update(self.props['worlds'])
            return worlds

        def atomics(self):
            if self.has('sentence'):
                return self.props['sentence'].atomics()
            return set()

        def constants(self):
            if self.has('sentence'):
                return self.props['sentence'].constants()
            return set()

        def predicates(self):
            if self.has('sentence'):
                return self.props['sentence'].predicates()
            return set()

        def __repr__(self):
            return self.__dict__.__repr__()

    class Rule(object):
        """
        Base interface class for a tableau rule.
        """

        def __init__(self, tableau, **opts):
            """
            Instantiate the rule for the tableau.
            """
            #: Reference to the tableau for which the rule is instantiated.
            self.tableau = tableau

        def applies(self):
            # Whether the rule applies to the tableau. Implementations should return True/False or a target dict.
            raise NotImplementedError(NotImplemented)

        def apply(self, target):
            # Apply the rule to the tableau. Assumes that applies() has returned true. Implementations should
            # modify the tableau directly, with no return value.
            raise NotImplementedError(NotImplemented)

        def example(self):
            # Add example branches/nodes sufficient for applies() to return true. Implementations should modify
            # the tableau directly, with no return value. Used for building examples/documentation.
            raise NotImplementedError(NotImplemented)

        def sentence(self, node):
            if 'sentence' in node.props:
                return node.props['sentence']

        def after_branch_add(self, branch, other_branch = None):
            pass

        def after_node_add(self, branch, node):
            pass

        def after_node_tick(self, branch, node):
            pass

        def after_branch_close(self, branch):
            pass

        def __repr__(self):
            return self.__class__.__name__

    class BranchRule(Rule):
        """
        A branch rule applies to an open branch on a tableau. This base class
        implements the ``applies()`` method by finding the first open branch on
        the tableau to which the abstract method ``applies_to_branch()`` returns
        a non-``False`` value. If ``True`` is returned, then this method will
        return a dictionary with a ``branch`` key, which will then be passed to
        the ``applies()`` method.
        """

        def applies(self):
            for branch in self.tableau.open_branches():
                target = self.applies_to_branch(branch)
                if target:
                    if target == True:
                        target = {'branch': branch}
                    if 'branch' not in target:
                        target['branch'] = branch
                    if 'type' not in target:
                        target['type'] = 'Branch'
                    return target
            return False

        def applies_to_branch(self, branch):
            # Abstract method that must be implemented in sub-classes. Should return a target object.
            raise NotImplementedError(NotImplemented)

    class ClosureRule(BranchRule):
        """
        A closure rule has a fixed ``apply()`` method that marks the branch as
        closed. Sub-classes should implement the ``applies_to_branch()`` method.
        """

        def applies_to_branch(self, branch):
            raise NotImplementedError(NotImplemented)

        def branch_closes_with(self, branch, node):
            # TODO: WIP
            if not isinstance(node, TableauxSystem.Node):
                node = TableauxSystem.Node(props=node)
            return self.node_will_close_branch(node, branch)

        def node_will_close_branch(self, node, branch):
            # TODO: WIP
            raise NotImplementedError(NotImplemented)

        def apply(self, target):
            target['branch'].close()

    class SelectiveTrackingBranchRule(BranchRule):

        def __init__(self, *args, **opts):
            super(TableauxSystem.SelectiveTrackingBranchRule, self).__init__(*args, **opts)
            self.stbr_track = dict()

        def applies_to_branch(self, branch):
            cands = self.get_candidate_targets_for_branch(branch)
            if len(cands) == 0:
                return False
            return self.select_best_target_for_branch(branch, cands)

        def select_best_target_for_branch(self, branch, cands):
            # select the node to which we have applied the least for this branch.
            self.ensure_track_targets(cands)
            cand_node_ids = {target['node'].id for target in cands}
            least_count = min({self.stbr_track[branch.id][node_id] for node_id in cand_node_ids})
            for target in cands:
                if self.stbr_track[branch.id][target['node'].id] == least_count:
                    return target

        def ensure_track_targets(self, cands):
            for target in cands:
                self.ensure_track_target(target)

        def ensure_track_target(self, target):
            branch = target['branch']
            node = target['node']
            if branch.id not in self.stbr_track:
                self.stbr_track[branch.id] = dict()
            if node.id not in self.stbr_track[branch.id]:
                self.stbr_track[branch.id][node.id] = 0

        def apply(self, target):
            branch = target['branch']
            node = target['node']
            self.apply_to_target(target)
            self.ensure_track_target(target)
            self.stbr_track[branch.id][node.id] += 1

        def get_candidate_targets_for_branch(self, branch):
            # Implementation must return target with both branch and node properties.
            raise NotImplementedError(NotImplemented)

        def apply_to_target(self, target):
            raise NotImplementedError(NotImplemented)

    class NodeRule(BranchRule):
        """
        A node rule has a fixed ``applies()`` method that searches open branches
        and queries the ``applies_to_node()`` method. If it applies, return a
        target dictionary with keys ``node`` and ``branch``.
        """

        ticked = False

        def __init__(self, *args, **opts):
            super(TableauxSystem.BranchRule, self).__init__(*args, **opts)
            self.applicable_nodes = dict()
            if 'is_rank_optim' in opts:
                self.is_rank_optim = opts['is_rank_optim']
            else:
                self.is_rank_optim = True

        def after_branch_add(self, branch, other_branch = None):
            if not branch.closed:
                branch_id = id(branch)
                consumed = False
                if other_branch != None:
                    other_branch_id = id(other_branch)
                    if other_branch_id in self.applicable_nodes:
                        self.applicable_nodes[branch_id] = set(self.applicable_nodes[other_branch_id])
                        consumed = True
                if not consumed:
                    self.applicable_nodes[branch_id] = set()
                    for node in branch.get_nodes(ticked=self.ticked):
                        self.after_node_add(branch, node)

        def after_branch_close(self, branch):
            del(self.applicable_nodes[id(branch)])

        def after_node_add(self, branch, node):
            if self.applies_to_node(node, branch):
                self.applicable_nodes[id(branch)].add(node)

        def after_node_tick(self, branch, node):
            branch_id = id(branch)
            if self.ticked == False:
                self.applicable_nodes[branch_id].discard(node)

        def applies(self):
            cands = list()
            for branch_id in self.applicable_nodes:
                branch = self.tableau.get_branch(branch_id)
                for node in set(self.applicable_nodes[branch_id]):
                    target = self.applies_to_node(node, branch)
                    if target:
                        if target == True:
                            target = {'node' : node}
                        if 'node' not in target:
                            target['node'] = node
                        if 'type' not in target:
                            target['type'] = 'Node'
                        if 'branch' not in target:
                            target['branch'] = branch
                        if not self.is_rank_optim:
                            return target
                        cands.append(target)
                    else:
                        self.applicable_nodes[branch_id].discard(node)
            if len(cands):
                # score candidates
                cand_scores = [self.score_target(target) for target in cands]
                max_score = max(set(cand_scores))
                for i in range(len(cands)):
                    if cand_scores[i] == max_score:
                        return cands[i]
            else:
                return False

        def get_branch_additions(self, target):
            # TODO
            # should return a list of lists of node props
            pass

        def score_target(self, target):
            return sum(self.score_target_list(target))

        def score_target_list(self, target):
            return self.score_target_map(target).values()

        def score_target_map(self, target):
            return {}

        def apply(self, target):
            return self.apply_to_node(target['node'], target['branch'])

        def applies_to_node(self, node, branch):
            raise NotImplementedError(NotImplemented)

        def apply_to_node(self, node, branch):
            raise NotImplementedError(NotImplemented)

        def example(self):
            self.tableau.branch().add(self.example_node())

        def example_node(self):
            raise NotImplementedError(NotImplemented)

    class ConditionalNodeRule(NodeRule):
        """
        A conditional node rule has a fixed ``applies_to_node()`` method that searches open branches for nodes
        that match the attribute conditions of the implementing class. This allows implementations to merely
        define their attributes and implement ``the apply_to_node()`` method. This is the most common type of
        rule for operator rules.

        The following attribute conditions can be defined. If a condition is set to ``None``, then it
        will be vacuously met.
        """

        #: The ticked status of the node, default is ``False``.
        ticked      = False

        #: Whether this rule applies to modal nodes, i.e. nodes that
        #: reference one or more worlds.
        modal       = None

        #: The main operator of the node's sentence, if any.
        operator    = None

        #: Whether the sentence must be negated. if ``True``, then nodes
        #: whose sentence's main connective is Negation will be checked,
        #: and if the negatum has the main connective defined in the
        #: ``operator`` condition (above), then this condition will be met.
        negated     = None

        #: The quantifier of the sentence, e.g. 'Universal' or 'Existential'.
        quantifier  = None

        #: The designation status (``True``/``False``) of the node.
        designation = None

        def applies_to_node(self, node, branch):
            if self.ticked != None and self.ticked != (node in branch.ticked_nodes):
                return False
            if self.modal != None:
                modal = len(node.worlds()) > 0
                if self.modal != modal:
                    return False
            sentence = operator = quantifier = None
            if 'sentence' in node.props:
                sentence = node.props['sentence']
                operator = sentence.operator
                quantifier = sentence.quantifier
            if self.negated != None:
                negated = operator == 'Negation'
                if not sentence or negated != self.negated:
                    return False
                if negated:
                    sentence = sentence.operand
                    operator = sentence.operator
                    quantifier = sentence.quantifier
            if self.operator != None:
                if self.operator != operator:
                    return False
            elif self.quantifier != None:
                if self.quantifier != quantifier:
                    return False
            if self.designation != None:
                if 'designated' not in node.props or node.props['designated'] != self.designation:
                    return False
            return True

        def sentence(self, node):
            s = None
            if 'sentence' in node.props:
                s = node.props['sentence']
                if self.negated:
                    s = s.operand
            return s

        def example_node(self):
            props = {}
            if self.modal:
                props['world'] = 0
            if self.designation != None:
                props['designated'] = self.designation
            sentence = None
            a = atomic(0, 0)
            if self.operator != None:
                params = []
                n = arity(self.operator)
                if n > 0:
                    params.append(a)
                for i in range(n - 1):
                    params.append(params[-1].next())
                sentence = operate(self.operator, params)
            elif self.quantifier != None:
                import examples
                sentence = examples.quantified(self.quantifier)
            if self.negated:
                if sentence == None:
                    sentence = a
                sentence = negate(sentence)
            if sentence != None:
                props['sentence'] = sentence
            return props

    class Writer(object):

        def __init__(self, **opts):
            self.defaults = dict(opts)

        def document_header(self):
            return ''

        def document_footer(self):
            return ''

        def write(self, tableau, notation = None, symbol_set = None, sw = None, **options):
            opts = dict(self.defaults)
            opts.update(options)
            
            if sw == None:
                if notation == None:
                    raise Exception("Must specify either notation or sw.")
                sw = notation.Writer(symbol_set)
            return self.write_tableau(tableau, sw, opts)

        def write_tableau(self, tableau, sw, opts):
            raise NotImplementedError(NotImplemented)

class Model(object):

    class ModelValueError(Exception):
        pass

    truth_functional_operators = set()

    def __init__(self):
        self.id = id(self)

    def read_branch(self, branch):
        raise NotImplementedError(NotImplemented)

    def value_of(self, sentence, **kw):
        if self.is_sentence_opaque(sentence):
            return self.value_of_opaque(sentence, **kw)
        elif sentence.is_predicated():
            return self.value_of_predicated(sentence, **kw)
        elif sentence.is_atomic():
            return self.value_of_atomic(sentence, **kw)
        elif sentence.is_operated():
            return self.value_of_operated(sentence, **kw)
        elif sentence.is_quantified():
            return self.value_of_quantified(sentence, **kw)

    def truth_function(self, operator, a, b=None):
        raise NotImplementedError(NotImplemented)

    def is_sentence_opaque(self, sentence, **kw):
        return False

    def value_of_opaque(self, sentence, **kw):
        raise NotImplementedError(NotImplemented)

    def value_of_atomic(self, sentence, **kw):
        raise NotImplementedError(NotImplemented)

    def value_of_predicated(self, sentence, **kw):
        raise NotImplementedError(NotImplemented)

    def value_of_operated(self, sentence, **kw):
        operator = sentence.operator
        if operator in self.truth_functional_operators:
            return self.truth_function(operator, *[self.value_of(operand, **kw) for operand in sentence.operands])
        raise NotImplementedError(NotImplemented)

    def value_of_quantified(self, sentence, **kw):
        raise NotImplementedError(NotImplemented)

    def is_countermodel(self, argument):
        # TODO: WIP
        raise NotImplementedError(NotImplemented)

    def get_data(self):
        return dict()

class Parser(object):
    # The base Parser class handles parsing operations common to all notations (Polish and Standard).
    # This consists of all parsing except for operator expressions, as well as the following classes
    # of symbols:
    # 
    # - Whitespace symbols: the *space* character.
    # - Subscript symbols: digit characters.
    # 
    # Each specific notation defines its own characters for each of the following classes of symbols:
    # 
    # - Constant symbols
    # - Variable symbols
    # - Predicate symbols, including system-defined predicates, and user-defined predicate.
    # - Quanitfier symbols
    # - Operator symbols
    # - Atomic sentence (proposition) symbols

    class ParseError(Exception):
        pass

    class UnboundVariableError(ParseError):
        pass

    class BoundVariableError(ParseError):
        pass

    class SymbolSet(object):

        def __init__(self, name, m):
            self.m = m
            self.name = name
            self.types = {}
            self.index = {}
            self.reverse = {}
            
            for ctype in m:
                if isinstance(m[ctype], dict):
                    self.types.update({c: ctype for c in m[ctype].values()})
                    self.index[ctype] = dict(m[ctype])
                    self.reverse[ctype] = {m[ctype][k]: k for k in m[ctype]}
                else:
                    self.types.update({c: ctype for c in m[ctype]})
                    self.index[ctype] = {i: c for i, c in enumerate(m[ctype])}
                    self.reverse[ctype] = {c: i for i, c in enumerate(m[ctype])}

        def typeof(self, c):
            if c in self.types:
                return self.types[c]
            return None

        def charof(self, ctype, index, subscript = None, skip_zero = True):
            s = self.index[ctype][index]
            if subscript != None:
                s += self.subfor(subscript, skip_zero = skip_zero)
            return s

        def indexof(self, ctype, ref):
            return self.reverse[ctype][ref]

        def subfor(self, subscript, skip_zero = True):
            if skip_zero and subscript == 0:
                return ''
            return ''.join([self.charof('digit', int(d)) for d in list(str(subscript))])

        def chars(self, ctype):
            return self.m[ctype]

    def __init__(self, vocabulary, symbol_set = None):
        if symbol_set == None:
            symbol_set = 'default'
        if isinstance(symbol_set, Parser.SymbolSet):
            self.symbol_set = symbol_set
        else:
            self.symbol_set = self.symbol_sets[symbol_set]
        self.vocabulary = vocabulary
        self.is_parsing = False

    def chomp(self):
        # proceeed through whitepsace
        while self.has_current() and self.typeof(self.current()) == 'whitespace':
            self.pos += 1

    def current(self):
        # get the current character, or None if after last
        return self.next(0)

    def assert_current(self):
        # raise a parse error if after last
        if not self.has_current():
            raise Parser.ParseError('Unexpected end of input at position {0}.'.format(self.pos))
        return self.typeof(self.current())

    def assert_current_is(self, *ctypes):
        self.assert_current()
        ctype = self.typeof(self.current())
        if ctype not in ctypes:
            raise Parser.ParseError("Unexpected {0} '{1}' at position {2}.".format(ctype, self.current(), self.pos))
        return ctype

    def has_next(self, n=1):
        # check whether there is n-many characters after the current. if n = 0,
        return (len(self.s) > self.pos + n)

    def has_current(self):
        # check whether there is a current character, or return False if after last.
        return self.has_next(0)

    def next(self, n=1):
        # get the nth character after the current, of None if n is after last.
        if self.has_next(n):
            return self.s[self.pos+n]
        return None

    def advance(self, n=1):
        # advance the current pointer n many characters, and then eat whitespace.
        self.pos += n  
        self.chomp()

    def argument(self, conclusion=None, premises=[], title=None):
        # parse a conclusion and premises, and return an argument.
        return argument(
            conclusion = self.parse(conclusion),
            premises = [self.parse(s) for s in premises],
            title = title
        )

    def parse(self, string):
        # parse an input string, and return a sentence.
        if self.is_parsing:
            raise Exception('Parser is already parsing -- not thread safe.')
        self.is_parsing = True
        self.bound_vars = set()
        try:
            self.s   = list(string)
            self.pos = 0
            self.chomp()
            if not self.has_current():
                raise Parser.ParseError('Input cannot be empty.')
            s = self.read()
            self.chomp()
            if self.has_current():
                raise Parser.ParseError("Unexpected character '{0}' at position {1}.".format(self.current(), self.pos))
            self.is_parsing = False
            self.bound_vars = set()
        except:
            self.is_parsing = False
            self.bound_vars = set()
            raise
        return s

    def read_item(self, ctype = None):
        # read an item and its subscript starting from the current character, which must be
        # in the list of characters given. returns a list containing the index of the current
        # character in the chars list, and the subscript of that item. this is a generic way
        # to read predicates, atomics, variables, constants, etc.
        if ctype == None:
            ctype = self.typeof(self.current())
        else:
            self.assert_current_is(ctype)
        index = self.symbol_set.indexof(ctype, self.current())
        self.advance()
        subscript = self.read_subscript()
        return {'index': index, 'subscript': subscript}

    def read_subscript(self):
        # read the subscript starting from the current character. if the current character
        # is not a digit, or we are after last, then the subscript is 0. otherwise, all
        # consecutive digit characters are read (whitepsace allowed), and then converted
        # to an integer, which is then returned.
        sub = []
        while self.current() and self.typeof(self.current()) == 'digit':
            sub.append(self.current())
            self.advance()
        if not len(sub):
            sub.append('0')
        return int(''.join(sub))

    def read_atomic(self):
        # read an atomic sentence starting from the current character.
        return atomic(**self.read_item())

    def read_variable(self):
        # read a variable starting from the current character.
        return variable(**self.read_item())

    def read_constant(self):
        # read a constant starting from the current character.
        return constant(**self.read_item())

    def read_predicate(self):
        # read a predicate starting from the current character.
        pchar = self.current()
        cpos = self.pos
        try:
            return self.vocabulary.get_predicate(**self.read_item())
        except Vocabulary.NoSuchPredicateError:
            raise Parser.ParseError("Undefined predicate symbol '{0}' at position {1}.".format(pchar, cpos))

    def read_parameters(self, num):
        # read the parameters (constants or variables) of a predicate sentence, starting
        # from the current character. if the number of parameters is not equal to num (arity),
        # then a parse error is raised. if variables appear that are not in self.bound_vars,
        # then an unbound variable error is raised. return a list of parameter objects (either
        # variables or constants).
        parameters = []
        while len(parameters) < num:
            parameters.append(self.read_parameter())
        return parameters

    def read_parameter(self):
        ctype = self.assert_current_is('constant', 'variable')
        if ctype == 'constant':
            return self.read_constant()
        else:
            cpos = self.pos
            v = self.read_variable()
            if v not in list(self.bound_vars):
                var_str = self.symbol_set.charof('variable', v.index, subscript = v.subscript)
                raise Parser.UnboundVariableError("Unbound variable '{0}' at position {1}.".format(var_str, cpos))
            return v

    def read_predicate_sentence(self):
        # read a predicate sentence.
        predicate = self.read_predicate()
        params = self.read_parameters(predicate.arity)
        return predicated(predicate, params)

    def read_quantified_sentence(self):
        self.assert_current_is('quantifier')
        quantifier = self.symbol_set.indexof('quantifier', self.current())
        self.advance()
        v = self.read_variable()
        if v in list(self.bound_vars):
            var_str = self.symbol_set.charof('variable', v.index, subscript = v.subscript)
            raise Parser.BoundVariableError("Cannot rebind variable '{0}' at position {1}.".format(var_str, self.pos))
        self.bound_vars.add(v)
        sentence = self.read()
        if v not in list(sentence.variables()):
            var_str = self.symbol_set.charof('variable', v.index, subscript = v.subscript)
            raise Parser.BoundVariableError("Unused bound variable '{0}' at position {1}.".format(var_str, self.pos))
        self.bound_vars.remove(v)
        return quantify(quantifier, v, sentence)

    def read(self):
        # read a sentence.
        ctype = self.assert_current()
        if ctype == 'user_predicate' or ctype == 'system_predicate':
            s = self.read_predicate_sentence()
        elif ctype == 'quantifier':
            s = self.read_quantified_sentence()
        elif ctype == 'atomic':
            s = self.read_atomic()
        else:
            raise Parser.ParseError("Unexpected {0} '{1}' at position {2}.".format(ctype, self.current(), self.pos))
        return s

    def typeof(self, c):
        return self.symbol_set.typeof(c)