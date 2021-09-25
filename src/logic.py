# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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

copyright = '2014-2021, Doug Owings. Released under the GNU Affero General Public License v3 or later'
source_href = 'https://github.com/owings1/pytableaux'

default_notation = 'polish'

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
    'Necessity'              : 1,
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
    'Necessity'              ,
]

quantifiers_list = [
    'Universal'  ,
    'Existential',
]

system_predicates_list  = [
    'Identity' ,
    'Existence',
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

def parse(string, vocabulary=None, notation=None):
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
    if notation == None:
        notation = default_notation
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
                    premise = parse(premise, vocabulary, notation)
                self.premises.append(premise)
        if isinstance(conclusion, basestring):
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
    inputs = model.truth_table_inputs(arity(operator))
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

    class HashTupleOrdered(object):

        def hash_tuple(self):
            raise NotImplementedError()

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
            #return cmp(self.hash_tuple(), other.hash_tuple())
            return (self.hash_tuple() > other.hash_tuple()) - (self.hash_tuple() < other.hash_tuple())

    class Predicate(HashTupleOrdered):

        def __init__(self, name, index, subscript, arity):
            if index >= num_predicate_symbols:
                raise Vocabulary.IndexTooLargeError("Predicate index too large {0}".format(str(index)))
            if arity == None or not isinstance(arity, int):
                raise Vocabulary.PredicateArityError('Predicate arity must be an integer')
            if arity < 1:
                raise Vocabulary.PredicateArityError('Invalid predicate arity {0}'.format(str(arity)))
            if subscript == None or not isinstance(subscript, int):
                raise Vocabulary.PredicateSubscriptError('Predicate subscript must be an integer')
            if subscript < 0:
                raise Vocabulary.PredicateSubscriptError('Invalid predicate subscript {0}'.format(str(subscript)))
            self.name      = name
            self.arity     = arity
            self.index     = index
            self.subscript = subscript

        def hash_tuple(self):
            return (1, self.index, self.subscript, self.arity)

        def is_system_predicate(self):
            return self.index < 0

        def __eq__(self, other):
            return other != None and self.__dict__ == other.__dict__
        
        def __ne__(self, other):
            return other == None or self.__dict__ != other.__dict__

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
        # set of predicate instances
        self.user_predicates_set   = set()
        # list of predicate names
        self.user_predicates_list  = []
        # name to predicate instance
        self.user_predicates       = {}
        # string of [subscript, arity] to predicate instance
        self.user_predicates_index = {}
        if predicate_defs:
            for info in predicate_defs:
                if not isinstance(info, list) and not isinstance(info, tuple):
                    raise Vocabulary.PredicateError('predicate_defs must be a list/tuple of lists/tuples.')
                if len(info) != 4:
                    raise Vocabulary.PredicateError("Predicate declarations must be 4-tuples (name, index, subscript, arity).")
                self.declare_predicate(*info)

    def copy(self):
        vocab = Vocabulary()
        vocab.user_predicates = dict(self.user_predicates)
        vocab.user_predicates_list = list(self.user_predicates_list)
        vocab.user_predicates_set = set(self.user_predicates_set)
        vocab.user_predicates_index = dict(self.user_predicates_index)
        return vocab

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
        self.add_predicate(predicate)
        return predicate

    def add_predicate(self, predicate):
        """
        Add a predicate instance::

            vocab1 = Vocabulary()
            predicate = vocab1.declare_predicate(name='is tall', index=0, subscript=0, arity=1)
            vocab2 = Vocabulary()
            vocab2.add_predicate(predicate)
            assert vocab2.get_predicate('is tall') == predicate
        """
        if not isinstance(predicate, Vocabulary.Predicate):
            raise Vocabulary.PredicateError('Predicate must be an instance of Vocabulary.Predicate')
        if predicate.index < 0:
            raise Vocabulary.PredicateError('Cannot add a system predicate to a vocabulary')
        self.user_predicates[predicate.name] = predicate
        self.user_predicates_index[str([predicate.index, predicate.subscript])] = predicate
        if predicate not in self.user_predicates_set:
            self.user_predicates_set.add(predicate)
            self.user_predicates_list.append(predicate.name)
        return predicate
        
    def list_predicates(self):
        """
        List all predicates in the vocabulary, including system predicates.
        """
        return system_predicates_list + self.user_predicates_list

    def list_user_predicates(self):
        """
        List all predicates in the vocabulary, excluding system predicates.
        """
        return list(self.user_predicates_list)

    class Parameter(HashTupleOrdered):

        def __init__(self, index, subscript):
            self.index = index
            self.subscript = subscript

        def is_constant(self):
            return isinstance(self, Vocabulary.Constant)

        def is_variable(self):
            return isinstance(self, Vocabulary.Variable)

        def __repr__(self):
            return (self.__class__.__name__, self.index, self.subscript).__repr__()

    class Constant(Parameter):

        def __init__(self, index, subscript):
            if index >= num_const_symbols:
                raise Vocabulary.IndexTooLargeError("Index too large {0}".format(str(index)))
            super(Vocabulary.Constant, self).__init__(index, subscript)

        def hash_tuple(self):
            return (2, self.index, self.subscript)

        def __eq__(self, other):
            return other != None and isinstance(other, Vocabulary.Constant) and self.__dict__ == other.__dict__

        def __ne__(self, other):
            return other == None or not isinstance(other, Vocabulary.Constant) or self.__dict__ != other.__dict__

        def __hash__(self):
            return hash(self.hash_tuple())

    class Variable(Parameter):

        def __init__(self, index, subscript):
            if index >= num_var_symbols:
                raise Vocabulary.IndexTooLargeError("Index too large {0}".format(str(index)))
            super(Vocabulary.Variable, self).__init__(index, subscript)

        def hash_tuple(self):
            return (3, self.index, self.subscript)

        def __eq__(self, other):
            return other != None and isinstance(other, Vocabulary.Variable) and self.__dict__ == other.__dict__

        def __ne__(self, other):
            return other == None or not isinstance(other, Vocabulary.Variable) or self.__dict__ != other.__dict__

        def __hash__(self):
            return hash(self.hash_tuple())

    class Sentence(HashTupleOrdered):

        #: The operator, if any.
        operator   = None

        #: The quantifier, if any.
        quantifier = None

        #: The predicate, if any.
        predicate  = None

        #: The type (class name).
        type       = None

        def __init__(self):
            self.type = self.__class__.__name__

        def is_sentence(self):
            """
            Whether this is a sentence.
            """
            return True

        def is_atomic(self):
            """
            Whether this is an atomic sentence.
            """
            return isinstance(self, Vocabulary.AtomicSentence)

        def is_predicated(self):
            """
            Whether this is a predicated sentence.
            """
            return isinstance(self, Vocabulary.PredicatedSentence)

        def is_quantified(self):
            """
            Whether this a quantified sentence.
            """
            return isinstance(self, Vocabulary.QuantifiedSentence)

        def is_operated(self):
            """
            Whether this is an operated sentence.
            """
            return isinstance(self, Vocabulary.OperatedSentence)

        def is_literal(self):
            """
            Whether the sentence is a literal. Here a literal is either a
            predicated sentence, the negation of a predicated sentence,
            an atomic sentence, or the negation of an atomic sentence.
            """
            return self.is_atomic() or self.is_predicated() or (
                self.is_operated() and self.operator == 'Negation' and (
                    self.operand.is_atomic() or
                    self.operand.is_predicated()
                )
            )

        def substitute(self, new_param, old_param):
            """
            Recursively substitute ``new_param`` for all occurrences of ``old_param``.
            May return self, or a new sentence.
            """
            raise NotImplementedError()

        def constants(self):
            """
            Set of constants, recursive.
            """
            raise NotImplementedError()

        def variables(self):
            """
            Set of variables, recursive.
            """
            raise NotImplementedError()

        def atomics(self):
            """
            Set of atomic sentences, recursive.
            """
            raise NotImplementedError()

        def predicates(self):
            """
            Set of predicates, recursive.
            """
            raise NotImplementedError()

        def operators(self):
            """
            List of operators, recursive.
            """
            raise NotImplementedError()

        def quantifiers(self):
            """
            List of quantifiers, recursive.
            """
            raise NotImplementedError()

        def __eq__(self, other):
            return other != None and self.__dict__ == other.__dict__

        def __ne__(self, other):
            return other == None or self.__dict__ != other.__dict__

        def __repr__(self):
            from notations import polish
            return polish.write(self)

    class AtomicSentence(Sentence):

        def __init__(self, index, subscript):
            if index >= num_atomic_symbols:
                raise Vocabulary.IndexTooLargeError("Index too large {0}".format(str(index)))
            super(Vocabulary.AtomicSentence, self).__init__()
            self.index     = index
            self.subscript = subscript

        def substitute(self, new_param, old_param):
            return self

        def constants(self):
            return set()

        def variables(self):
            return set()

        def atomics(self):
            return set([self])

        def predicates(self):
            return set()

        def operators(self):
            return list()

        def quantifiers(self):
            return list()

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
            super(Vocabulary.PredicatedSentence, self).__init__()
            self.predicate  = predicate
            self.parameters = parameters
            self.vocabulary = vocabulary

        def substitute(self, new_param, old_param):
            params = []
            for param in self.parameters:
                if param == old_param:
                    params.append(new_param)
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

        def operators(self):
            return list()

        def quantifiers(self):
            return list()

        def hash_tuple(self):
            return (5, self.predicate) + tuple((param for param in self.parameters))

        def __hash__(self):
            return hash(self.hash_tuple())

    class QuantifiedSentence(Sentence):

        def __init__(self, quantifier, variable, sentence):
            super(Vocabulary.QuantifiedSentence, self).__init__()
            self.quantifier = quantifier
            self.variable   = variable
            self.sentence   = sentence
            self._qindex    = quantifiers_list.index(self.quantifier)

        def substitute(self, new_param, old_param):
            # Always return a new sentence.
            si = self.sentence
            r = si.substitute(new_param, old_param)
            return Vocabulary.QuantifiedSentence(self.quantifier, self.variable, r)

        def constants(self):
            return self.sentence.constants()

        def variables(self):
            return self.sentence.variables()

        def atomics(self):
            return self.sentence.atomics()

        def predicates(self):
            return self.sentence.predicates()

        def operators(self):
            return self.sentence.operators()

        def quantifiers(self):
            return [self.quantifier] + self.sentence.quantifiers()

        def hash_tuple(self):
            return (6, self._qindex, self.variable, self.sentence)

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
            super(Vocabulary.OperatedSentence, self).__init__()
            self.operator = operator
            self.operands = operands
            if len(operands) == 1:
                self.operand = operands[0]
                if operator == 'Negation':
                    self.negatum = self.operand
            elif len(operands) > 1:
                self.lhs = operands[0]
                self.rhs = operands[-1]

        def substitute(self, new_param, old_param):
            # Always return a new sentence
            new_operands = [operand.substitute(new_param, old_param) for operand in self.operands]
            return operate(self.operator, new_operands)

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

        def operators(self):
            ops = list()
            ops.append(self.operator)
            for operand in self.operands:
                ops.extend(operand.operators())
            return ops

        def quantifiers(self):
            qts = list()
            for operand in self.operands:
                qts.extend(operand.quantifiers())
            return qts

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
                raise NotImplementedError()

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
            raise NotImplementedError()

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
                raise NotImplementedError()

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
    'Existence' : Vocabulary.Predicate('Existence', -2, 0, 1),
}

class TableauxSystem(object):

    @classmethod
    def build_trunk(cls, tableau, argument):
        raise NotImplementedError()

    @classmethod
    def branching_complexity(cls, node):
        return 0

    @classmethod
    def add_rules(cls, tableau, opts):
        for Rule in tableau.logic.TableauxRules.closure_rules:
            tableau.add_closure_rule(Rule)
        for Rules in tableau.logic.TableauxRules.rule_groups:
            tableau.add_rule_group(Rules)

    class TableauStateError(Exception):
        pass

    class ProofTimeoutError(Exception):
        pass

    class TrunkAlreadyBuiltError(TableauStateError):
        pass

    class TrunkNotBuiltError(TableauStateError):
        pass

    class BranchClosedError(TableauStateError):
        pass

    class Tableau(object):
        """
        Represents a tableau proof of an argument for the given logic.
        """

        #: A tableau is finished when no more rules can apply.
        finished = False

        #: An argument is proved (valid) when its finished tableau has no
        #: open branches.
        valid = None

        #: An argument is disproved (invalid) when its finished tableau has
        #: at least one open branch, and it was not ended prematurely.
        invalid = None

        #: Whether the tableau ended prematurely.
        is_premature = False

        #: The branches on the tableau.
        branches = list()

        #: The history of rule applications.
        history = list()

        #: A tree structure of the tableau, generated after the proof is finished.
        tree = dict()

        default_opts = {
            'is_group_optim'  : True,
            'is_build_models' : False,
            'build_timeout'   : None,
            'max_steps'       : None,
        }

        def __init__(self, logic, argument, **opts):

            self.finished = False
            self.valid = None
            self.invalid = None
            self.is_premature = False

            self.branches = []
            self.history = []

            self.tree = dict()

            # A reference to the logic, if given.
            self.logic = None

            # The argument of the tableau, if given.
            self.argument = None

            # Rules
            self.all_rules = []
            self.closure_rules = []
            self.rule_groups = []

            # build timers
            self.build_timer = StopWatch()
            self.trunk_build_timer = StopWatch()
            self.tree_timer = StopWatch()
            self.models_timer = StopWatch()

            # opts
            self.opts = dict(self.default_opts)
            self.opts.update(opts)

            self.open_branchset = set()
            self.branch_dict = dict()
            self.trunk_built = False
            self.current_step = 0

            # Cache for the branching complexities
            self.branching_complexities = dict()

            if logic != None:
                self.set_logic(logic)

            if argument != None:
                self.set_argument(argument)

        def set_logic(self, logic):
            """
            Set the logic for the tableau. Assumes building has not started.
            Returns self.
            """
            self._check_not_started()
            self.logic = get_logic(logic)
            self.clear_rules()
            self.logic.TableauxSystem.add_rules(self, self.opts)
            return self

        def clear_rules(self):
            """
            Clear the rules. Assumes building has not started. Returns self.
            """
            self._check_not_started()
            self.closure_rules = []
            self.rule_groups = []
            self.all_rules = []
            return self

        def add_closure_rule(self, rule):
            """
            Add a closure rule. The ``rule`` parameter can be either a class
            or instance. Returns self.
            """
            self._check_not_started()
            if not isinstance(rule, TableauxSystem.Rule):
                rule = rule(self, **self.opts)
            self.closure_rules.append(rule)
            self.all_rules.append(rule)
            return self

        def add_rule_group(self, rules):
            """
            Add a rule group. The ``rules`` parameter should be list of rule
            instances or classes. Returns self.
            """
            self._check_not_started()
            group = []
            for rule in rules:
                if not isinstance(rule, TableauxSystem.Rule):
                    rule = rule(self, **self.opts)
                group.append(rule)
            self.rule_groups.append(group)
            self.all_rules.extend(group)
            return self
            
        def build(self, **opts):
            """
            Build the tableau. Returns self.
            """
            self.opts.update(opts)
            with self.build_timer:
                while not self.finished:
                    self._check_timeout()
                    self.step()
            self.finish()
            return self

        def step(self):
            """
            Find, execute, and return the next rule application. If no rule can
            be applied, the ``finish()`` method is called, and ``None`` is returned.
            If the tableau is already finished when this method is called, return
            ``False``.

            Internally, this calls the ``get_application()`` method to get the
            rule application, and, if non-empty, calls the ``do_application()``
            method.
            """
            if self.finished:
                return False
            self._check_trunk_built()
            application = None
            with StopWatch() as step_timer:
                res = None
                if self._is_max_steps_exceeded():
                    self.is_premature = True
                else:
                    res = self.get_application()
                if res:
                    rule, target = res
                    application = self.do_application(rule, target, step_timer)
                else:
                    self.finish()
            return application

        def get_application(self):
            """
            Find and return the next available rule application. If no rule
            cal be applied, return ``None``. This iterates over the open
            branches and calls ``get_branch_application()``, returning the
            first non-empty result.
            """
            for branch in self.open_branches():
                res = self.get_branch_application(branch)
                if res:
                    return res
            
        def get_branch_application(self, branch):
            """
            Find and return the next available rule application for the given
            open branch. This first checks the closure rules, then iterates
            over the rule groups. The first non-empty result is returned.
            """
            res = self.get_group_application(branch, self.closure_rules)
            if res:
                return res
            for rules in self.rule_groups:
                res = self.get_group_application(branch, rules)
                if res:
                    return res

        def get_group_application(self, branch, rules):
            """
            Find and return the next available rule application for the given
            open branch and rule group. The ``rules`` parameter is a list of
            rules, and is assumed to be either the closure rules, or one of the
            rule groups of the tableau. This calls the ``get_target()`` method
            on the rules.

            If the ``is_group_optim`` option is **disabled**, then the first
            non-empty target returned by a rule is selected. The target is
            updated with the keys `group_score` = ``None``, `total_group_targets` = `1`,
            and `min_group_score` = ``None``.

            If the ``is_group_optim`` option is **enabled**, then all non-empty
            targets from the rules are collected, and the ``select_optim_group_application()``
            method is called to select the result.

            The return value is either a non-empty list of results, or ``None``.
            Each result is a pair (tuple). The first element is the rule, and
            the second element is the target returned by the rule's `get_target()`
            method.
            """
            results = []
            for rule in rules:
                with rule.search_timer:
                    target = rule.get_target(branch)
                if target:
                    if not self.opts['is_group_optim']:
                        target.update({
                            'group_score'         : None,
                            'total_group_targets' : 1,
                            'min_group_score'     : None,
                            'is_group_optim'      : False,
                        })
                        return (rule, target)
                    results.append((rule, target))
            if results:
                return self.select_optim_group_application(results)

        def select_optim_group_application(self, results):
            """
            Choose the best rule to apply from among the list of results. The
            ``results`` parameter is assumed to be a non-empty list, where each
            element is a pair (tuple) of rule, target.

            Internally, this calls the ``group_score()`` method on each rule,
            passing it the target that the rule returned by its ``get_target()``
            method. The target with the max score is selected. If there is a tie,
            the the first target is selected.

            The target is updated with the following keys:
            
            - group_score
            - total_group_targets
            - min_group_score
            - is_group_optim

            The return value an element of ``results``, which is a (rule, target)
            pair.
            """
            group_scores = [rule.group_score(target) for rule, target in results]
            max_group_score = max(group_scores)
            min_group_score = min(group_scores)
            for i in range(len(results)):
                if group_scores[i] == max_group_score:
                    rule, target = results[i]
                    target.update({
                        'group_score'         : max_group_score,
                        'total_group_targets' : len(results),
                        'min_group_score'     : min_group_score,
                        'is_group_optim'      : True,
                    })
                    return (rule, target)

        def do_application(self, rule, target, step_timer):
            """
            Perform the application of the rule. This calls ``rule.apply()``
            with the target. The ``target`` should be what was returned by the
            rule's ``get_target()`` method.

            Internally, this creates an entry in the tableau's history, and
            increments the ``current_step`` property. The history entry is
            a dictionary with `rule`, `target`, and `duration_ms` keys, and
            is the return value of this method.

            This method is called internally by the ``step()`` method, which
            creates a ``StopWatch`` to track the combined time it takes to
            complete both the ``get_target()`` and ``apply()`` methods. The
            elapsed time is then stored in the history entry. This method will
            accept ``None`` for the ``step_timer`` parameter, however, this means
            the timing statistics will be inaccurate.
            """
            rule.apply(target)
            application = {
                'rule'        : rule,
                'target'      : target,
                'duration_ms' : step_timer.elapsed() if step_timer else 0,
            }
            self.history.append(application)
            self.current_step += 1
            return application

        def set_argument(self, argument):
            """
            Set the argument for the tableau. Return self.

            If the tableau has a logic set, then ``build_trunk()`` is automatically
            called.
            """
            self.argument = argument
            if self.logic != None:
                self.build_trunk()
            return self

        def open_branches(self):
            """
            Return the set of open branches on the tableau. This does **not** make
            a copy of the set, and so should be copied by the caller if modifications
            may occur.
            """
            return self.open_branchset

        def get_rule(self, rule):
            """
            Get a rule instance by name or class reference. Returns first occurrence.
            """
            for r in self.all_rules:
                if r.__class__ == rule or r.name == rule or r.__class__.__name__ == rule:
                    return r

        def branch(self, parent = None):
            """
            Create a new branch on the tableau, as a copy of ``parent``, if given.
            This calls the ``after_branch_add`` callback on all the rules of the
            tableau.
            """
            if parent == None:
                branch = TableauxSystem.Branch(self)
            else:
                branch = parent.copy()
                branch.parent = parent
            self.add_branch(branch)
            return branch

        def add_branch(self, branch):
            """
            Add a new branch to the tableau. Returns self.
            """
            branch.index = len(self.branches)
            self.branches.append(branch)
            if not branch.closed:
                self.open_branchset.add(branch)
            self.branch_dict[branch.id] = branch
            self._after_branch_add(branch)
            return self

        def build_trunk(self):
            """
            Build the trunk of the tableau. Delegates to the ``build_trunk()`` method
            of the logic's ``TableauxSystem``. This is called automatically when the
            tableau is instantiated with a logic and an argument, or when instantiated
            with a logic, and the ``set_argument()`` method is called.
            """
            self._check_trunk_not_built()
            with self.trunk_build_timer:
                self.logic.TableauxSystem.build_trunk(self, self.argument)
                self.trunk_built = True
                self.current_step += 1
                self._after_trunk_build()
            return self

        def get_branch(self, branch_id):
            """
            Get a branch by its id. Raises ``KeyError`` if not found.
            """
            return self.branch_dict[branch_id]

        def finish(self):
            """
            Mark the tableau as finished. Computes the ``valid``, ``invalid``,
            and ``stats`` properties, and builds the structure into the ``tree``
            property. Returns self.

            This is safe to call multiple times. If the tableau is already finished,
            this will be a no-op.
            """
            if self.finished:
                return self

            self.finished = True
            self.valid    = len(self.open_branches()) == 0
            self.invalid  = not self.valid and not self.is_premature

            with self.models_timer:
                if self.opts['is_build_models'] and not self.is_premature:
                    self._build_models()

            with self.tree_timer:
                self.tree = make_tree_structure(self.branches)

            self.stats = self._compute_stats()

            return self

        def branching_complexity(self, node):
            """
            Convenience caching method for the logic's ``TableauxSystem.branching_complexity()``
            method. If the tableau has no logic, then ``0`` is returned.
            """
            if node.id not in self.branching_complexities:
                if self.logic != None:
                    self.branching_complexities[node.id] = self.logic.TableauxSystem.branching_complexity(node)
                else:
                    return 0
            return self.branching_complexities[node.id]

        # Callbacks called from other classes

        def after_branch_close(self, branch):
            # Called from the branch instance in the close method.
            branch.closed_step = self.current_step
            self.open_branchset.remove(branch)
            for rule in self.all_rules:
                rule._after_branch_close(branch)

        def after_node_add(self, node, branch):
            # Called from the branch instance in the add/update methods.
            node.step = self.current_step
            for rule in self.all_rules:
                rule._after_node_add(node, branch)

        def after_node_tick(self, node, branch):
            # Called from the branch instance in the tick method.
            if node.ticked_step == None or self.current_step > node.ticked_step:
                node.ticked_step = self.current_step
            for rule in self.all_rules:
                rule._after_node_tick(node, branch)

        # Callbacks called internally

        def _after_branch_add(self, branch):
            # Called from add_branch()
            for rule in self.all_rules:
                rule._after_branch_add(branch)

        def _after_trunk_build(self):
            # Called from build_trunk()
            for rule in self.all_rules:
                rule._after_trunk_build(self.branches)

        # Interal util methods

        def _compute_stats(self):
            # Compute the stats property after the tableau is finished.
            num_open = len(self.open_branches())
            return {
                'result'            : self._result_word(),
                'branches'          : len(self.branches),
                'open_branches'     : num_open,
                'closed_branches'   : len(self.branches) - num_open,
                'rules_applied'     : len(self.history),
                'distinct_nodes'    : self.tree['distinct_nodes'],
                'rules_duration_ms' : sum((application['duration_ms'] for application in self.history)),
                'build_duration_ms' : self.build_timer.elapsed(),
                'trunk_duration_ms' : self.trunk_build_timer.elapsed(),
                'tree_duration_ms'  : self.tree_timer.elapsed(),
                'models_duration_ms': self.models_timer.elapsed(),
                'rules_time_ms'     : sum([
                    sum([rule.search_timer.elapsed(), rule.apply_timer.elapsed()])
                    for rule in self.all_rules
                ]),
                'rules' : [
                    self._compute_rule_stats(rule)
                    for rule in self.all_rules
                ],
            }

        def _compute_rule_stats(self, rule):
            # Compute the stats for a rule after the tableau is finished.
            return {
                'name'            : rule.name,
                'queries'         : rule.search_timer.times_started(),
                'search_time_ms'  : rule.search_timer.elapsed(),
                'search_time_avg' : rule.search_timer.elapsed_avg(),
                'apply_count'     : rule.apply_count,
                'apply_time_ms'   : rule.apply_timer.elapsed(),
                'apply_time_avg'  : rule.apply_timer.elapsed_avg(),
                'timers'          : {
                    name : {
                        'duration_ms'   : rule.timers[name].elapsed(),
                        'duration_avg'  : rule.timers[name].elapsed_avg(),
                        'times_started' : rule.timers[name].times_started(),
                    }
                    for name in rule.timers
                },
            }

        def _check_timeout(self):
            timeout = self.opts['build_timeout']
            if timeout != None and timeout >= 0:
                if self.build_timer.elapsed() > timeout:
                    self.build_timer.stop()
                    raise TableauxSystem.ProofTimeoutError('Timeout of {0}ms exceeded.'.format(str(timeout)))

        def _is_max_steps_exceeded(self):
            max_steps = self.opts['max_steps']
            return max_steps != None and len(self.history) >= max_steps

        def _check_trunk_built(self):
            if self.argument != None and not self.trunk_built:
                raise TableauxSystem.TrunkNotBuiltError("Trunk is not built.")

        def _check_trunk_not_built(self):
            if self.trunk_built:
                raise TableauxSystem.TrunkAlreadyBuiltError("Trunk is already built.")

        def _check_not_started(self):
            if self.current_step > 0:
                raise TableauxSystem.TableauStateError("Proof has already started building.")

        def _result_word(self):
            if self.valid:
                return 'Valid'
            if self.invalid:
                return 'Invalid'
            return 'Unfinished'

        def _build_models(self):
            # Build models for the open branches
            for branch in list(self.open_branches()):
                self._check_timeout()
                branch.make_model()
            
        def __repr__(self):
            return {
                'argument'      : self.argument,
                'branches'      : len(self.branches),
                'rules_applied' : len(self.history),
                'finished'      : self.finished,
                'valid'         : self.valid,
                'invalid'       : self.invalid,
                'is_premature'  : self.is_premature,
            }.__repr__()

    class Branch(object):
        """
        Represents a tableau branch.
        """

        def __init__(self, tableau=None):
            # Make sure properties are copied if needed in copy()
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
            self.parent = None
            self.node_index = {
                'sentence'   : {},
                'designated' : {},
                'world'      : {},
                'world1'     : {},
                'world2'     : {},
                'w1Rw2'      : {},
            }

        def has(self, props, ticked=None):
            """
            Check whether there is a node on the branch that matches the given properties,
            optionally filtered by ticked status.
            """
            return self.find(props, ticked=ticked) != None

        def has_access(self, *worlds):
            """
            Check whether a tuple of the given worlds is on the branch.

            This is a performant way to check typical "access" nodes on the
            branch with `world1` and `world2` properties. For more advanced
            searches, use the ``has()`` method.
            """
            return str(list(worlds)) in self.node_index['w1Rw2']

        def has_any(self, props_list, ticked=None):
            """
            Check a list of property dictionaries against the ``has()`` method. Return ``True``
            when the first match is found.
            """
            for props in props_list:
                if self.has(props, ticked=ticked):
                    return True
            return False

        def has_all(self, props_list, ticked=None):
            """
            Check a list of property dictionaries against the ``has()`` method. Return ``False``
            when the first non-match is found.
            """
            for props in props_list:
                if not self.has(props, ticked=ticked):
                    return False
            return True

        def find(self, props, ticked=None):
            """
            Find the first node on the branch that matches the given properties, optionally
            filtered by ticked status. Returns ``None`` if not found.
            """
            results = self.search_nodes(props, ticked=ticked, limit=1)
            if len(results):
                return results[0]
            return None

        def find_all(self, props, ticked=None):
            """
            Find all the nodes on the branch that match the given properties, optionally
            filtered by ticked status. Returns a list.
            """
            return self.search_nodes(props, ticked=ticked)

        def search_nodes(self, props, ticked=None, limit=None):
            """
            Find all the nodes on the branch that match the given properties, optionally
            filtered by ticked status, up to the limit, if given. Returns a list.
            """
            results = []
            best_haystack = self._select_index(props, ticked)
            if not best_haystack:
                return results
            for node in best_haystack:
                if limit != None and len(results) >= limit:
                    break
                if ticked != None and self.is_ticked(node) != ticked:
                    continue
                if node.has_props(props):
                    results.append(node)
            return results

        def add(self, node):
            """
            Add a node (Node object or dict of props). Returns self.
            """
            node = self.create_node(node)
            self.nodes.append(node)
            self.consts.update(node.constants())
            self.ws.update(node.worlds())
            self.preds.update(node.predicates())
            self.atms.update(node.atomics())
            node.parent = self.leaf
            self.leaf = node

            # Add to index *before* after_node_add callback
            self._add_to_index(node)

            # Tableau callback
            if self.tableau != None:
                self.tableau.after_node_add(node, self)

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
                # Tableau callback
                if self.tableau != None:
                    self.tableau.after_node_tick(node, self)
            return self

        def close(self):
            """
            Close the branch. Returns self.
            """
            self.closed = True
            self.add({'is_flag': True, 'flag': 'closure'})
            # Tableau callback
            if self.tableau != None:
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
            """
            Whether the node is ticked relative to the branch.
            """
            return node in self.ticked_nodes

        def copy(self):
            """
            Return a copy of the branch.
            """
            branch = self.__class__(self.tableau)
            branch.nodes = list(self.nodes)
            branch.ticked_nodes = set(self.ticked_nodes)
            branch.consts = set(self.consts)
            branch.ws = set(self.ws)
            branch.atms = set(self.atms)
            branch.preds = set(self.preds)
            branch.leaf = self.leaf
            branch.node_index = {
                prop : {
                    key : set(self.node_index[prop][key])
                    for key in self.node_index[prop]
                }
                for prop in self.node_index
            }
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

        def constants(self):
            """
            Return the set of constants that appear on the branch.
            """
            return self.consts

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

        def constants_or_new(self):
            """
            Return ``(constants, is_new)``, where ``constants`` is either the
            branch constants, or, if no constants are on the branch, a singleton
            containing a new constants, and ``is_new`` indicates whether it is
            a new constant.
            """
            if self.constants():
                return (self.constants(), False)
            return ({self.new_constant()}, True)

        def make_model(self):
            """
            Make a model from the open branch.
            """
            model = self.tableau.logic.Model()
            if self.closed:
                raise TableauxSystem.BranchClosedError('Cannot build a model from a closed branch')
            model.read_branch(self)
            if self.tableau.argument != None:
                model.is_countermodel = model.is_countermodel_to(self.tableau.argument)
            self.model = model
            return model

        def origin(self):
            """
            Traverse up through the ``parent`` property.
            """
            origin = self
            while origin.parent != None:
                origin = origin.parent
            return origin

        def branch(self):
            """
            Convenience method for ``tableau.branch()``.
            """
            return self.tableau.branch(self)

        def create_node(self, props):
            """
            Create a new node. Does not add it to the branch. If ``props`` is a
            node instance, return it. Otherwise create a new node from the props
            and return it.
            """
            if isinstance(props, TableauxSystem.Node):
                return props
            return TableauxSystem.Node(props=props)

        def _add_to_index(self, node):
            for prop in self.node_index:
                key = None
                if prop == 'w1Rw2':
                    if 'world1' in node.props and 'world2' in node.props:
                        key = str([node.props['world1'], node.props['world2']])
                elif prop in node.props:
                    key = str(node.props[prop])
                if key:
                    if key not in self.node_index[prop]:
                        self.node_index[prop][key] = set()
                    self.node_index[prop][key].add(node)

        def _select_index(self, props, ticked):
            best_index = None
            for prop in self.node_index:
                key = None
                if prop == 'w1Rw2':
                    if 'world1' in props and 'world2' in props:
                        key = str([props['world1'], props['world2']])
                elif prop in props:
                    key = str(props[prop])
                if key != None:
                    if key not in self.node_index[prop]:
                        return False
                    index = self.node_index[prop][key]
                    if best_index == None or len(index) < len(best_index):
                        best_index = index
                    # we could do no better
                    if len(best_index) == 1:
                        break
            if not best_index:
                if ticked:
                    best_index = self.ticked_nodes
                else:
                    best_index = self.nodes
            return best_index

        def __repr__(self):
            return {
                'id'     : self.id,
                'nodes'  : len(self.nodes),
                'leaf'   : self.leaf.id if self.leaf else None,
                'closed' : self.closed,
            }.__repr__()

    class Node(object):
        """
        A tableau node.
        """

        def __init__(self, props={}):
            #: A dictionary of properties for the node.
            self.props = {
                'world'      : None,
                'designated' : None,
            }
            self.props.update(props)
            self.ticked = False
            self.parent = None
            self.step = None
            self.ticked_step = None
            self.id = id(self)

        def has(self, *names):
            """
            Whether the node has a non-None property of all the given names.
            """
            for name in names:
                if name not in self.props or self.props[name] == None:
                    return False
            return True

        def has_any(self, *names):
            """
            Whether the node has a non-None property of any of the given names.
            """
            for name in names:
                if name in self.props and self.props[name] != None:
                    return True
            return False

        def has_props(self, props):
            """
            Whether the node properties match all those give in ``props`` (dict).
            """
            for prop in props:
                if prop not in self.props or not props[prop] == self.props[prop]:
                    return False
            return True

        def worlds(self):
            """
            Return the set of worlds referenced in the node properties. This combines
            the properties `world`, `world1`, `world2`, and `worlds`.
            """
            worlds = set()
            if self.has('world'):
                worlds.add(self.props['world'])
            if self.has('world1'):
                worlds.add(self.props['world1'])
            if self.has('world2'):
                worlds.add(self.props['world2'])
            if self.has('worlds'):
                worlds.update(self.props['worlds'])
            return worlds

        def atomics(self):
            """
            Return the set of atomics (recusive) of the node's `sentence`
            property, if any. If the node does not have a sentence, return
            an empty set.
            """
            if self.has('sentence'):
                return self.props['sentence'].atomics()
            return set()

        def constants(self):
            """
            Return the set of constants (recusive) of the node's `sentence`
            property, if any. If the node does not have a sentence, return
            the empty set.
            """
            if self.has('sentence'):
                return self.props['sentence'].constants()
            return set()

        def predicates(self):
            """
            Return the set of constants (recusive) of the node's `sentence`
            property, if any. If the node does not have a sentence, return
            the empty set.
            """
            if self.has('sentence'):
                return self.props['sentence'].predicates()
            return set()

        def __repr__(self):
            return {
                'id'     : self.id,
                'props'  : self.props,
                'ticked' : self.ticked,
                'step'   : self.step,
                'parent' : self.parent.id if self.parent else None,
            }.__repr__()

    class Rule(object):
        """
        Base class for a tableau rule.
        """

        branch_level = 1

        default_opts = {
            'is_rank_optim' : True
        }

        # for helper
        ticking = None

        # For compatibility in `_after_branch_add()`
        ticked = None

        def __init__(self, tableau, **opts):
            if not isinstance(tableau, TableauxSystem.Tableau):
                raise BadArgumentError('Must instantiate rule with a tableau instance.')
            #: Reference to the tableau for which the rule is instantiated.
            self.tableau = tableau
            self.search_timer = StopWatch()
            self.apply_timer = StopWatch()
            self.timers = {}
            self.helpers = []
            self.name = self.__class__.__name__
            self.apply_count = 0
            self.opts = dict(self.default_opts)
            self.opts.update(opts)
            self.add_helper('adz', TableauxSystem.AdzHelper(self))
            self.setup()

        # External API

        def apply(self, target):
            # Concrete classes should not override this, but should implement
            # ``apply_to_target()`` instead.
            with self.apply_timer:
                self.apply_to_target(target)
                self.apply_count += 1
                self._after_apply(target)

        def get_target(self, branch):
            # Concrete classes should not override this, but should implement
            # ``get_candidate_targets()`` instead.
            cands = self.get_candidate_targets(branch)
            if cands:
                self._extend_branch_targets(cands, branch)
                return self._select_best_target(cands, branch)

        def _extend_branch_targets(self, targets, branch):
            # Augment the targets with the following keys:
            #
            #  - branch
            #  - is_rank_optim
            #  - candidate_score
            #  - total_candidates
            #  - min_candidate_score
            #  - max_candidate_score

            for target in targets:
                if 'branch' not in target:
                    target['branch'] = branch

            if self.opts['is_rank_optim']:
                scores = [self.score_candidate(target) for target in targets]
            else:
                scores = [0]
            max_score = max(scores)
            min_score = min(scores)
            for i in range(len(targets)):
                target = targets[i]
                if self.opts['is_rank_optim']:
                    target.update({
                        'is_rank_optim'       : True,
                        'candidate_score'     : scores[i],
                        'total_candidates'    : len(targets),
                        'min_candidate_score' : min_score,
                        'max_candidate_score' : max_score,
                    })
                else:
                    target.update({
                        'is_rank_optim'       : False,
                        'candidate_score'     : None,
                        'total_candidates'    : len(targets),
                        'min_candidate_score' : None,
                        'max_candidate_score' : None,
                    })

        def _select_best_target(self, targets, branch):
            # Selects the best target. Assumes targets have been extended.
            for target in targets:
                if not self.opts['is_rank_optim']:
                    return target
                if target['candidate_score'] == target['max_candidate_score']:
                    return target

        # Abstract methods

        def get_candidate_targets(self, branch):
            # Intermediate classes such as ClosureRule, PotentialNodeRule, (and its child
            # FilterNodeRule) implement this and ``select_best_target()``, and
            # define finer-grained methods for concrete classes to implement.
            raise NotImplementedError()

        def apply_to_target(self, target):
            # Apply the rule to the target. Implementations should
            # modify the tableau directly, with no return value.
            raise NotImplementedError()

        # Implementation options for ``example()``

        def example(self):
            # Add example branches/nodes sufficient for applies() to return true.
            # Implementations should modify the tableau directly, with no return
            # value. Used for building examples/documentation.
            branch = self.branch()
            branch.update(self.example_nodes(branch))

        def example_nodes(self, branch):
            return [self.example_node(branch)]

        def example_node(self, branch):
            raise NotImplementedError()

        # Default implementation

        def group_score(self, target):
            # Called in tableau
            return self.score_candidate(target) / max(1, self.branch_level)

        def sentence(self, node):
            # Overriden in FilterNodeRule
            if 'sentence' in node.props:
                return node.props['sentence']

        # Candidate score implementation options `is_rank_optim`

        def score_candidate(self, target):
            return sum(self.score_candidate_list(target))

        def score_candidate_list(self, target):
            return self.score_candidate_map(target).values()

        def score_candidate_map(self, target):
            # Will sum to 0 by default
            return {}

        # Private callbacks -- do not implement

        def _after_trunk_build(self, branches):
            self.after_trunk_build(branches)
            for helper in self.helpers:
                helper.after_trunk_build(branches)

        def _after_branch_add(self, branch):
            self.register_branch(branch, branch.parent)
            for helper in self.helpers:
                helper.register_branch(branch, branch.parent)
            if not branch.parent:
                for node in branch.get_nodes(ticked=self.ticked):
                    self.register_node(self, node, branch)
                    for helper in self.helpers:
                        helper.register_node(node, branch)

        def _after_branch_close(self, branch):
            self.after_branch_close(branch)
            for helper in self.helpers:
                helper.after_branch_close(branch)

        def _after_node_add(self, node, branch):
            self.register_node(node, branch)
            for helper in self.helpers:
                helper.register_node(node, branch)

        def _after_node_tick(self, node, branch):
            self.after_node_tick(node, branch)
            for helper in self.helpers:
                helper.after_node_tick(node, branch)

        def _after_apply(self, target):
            self.after_apply(target)
            for helper in self.helpers:
                helper.after_apply(target)

        # Implementable callbacks -- always call super, or use a helper.

        def register_branch(self, branch, parent):
            pass

        def register_node(self, node, branch):
            pass

        def after_trunk_build(self, branches):
            pass

        def after_node_tick(self, node, branch):
            pass

        def after_branch_close(self, branch):
            pass

        def after_apply(self, target):
            pass

        # Util methods

        def setup(self):
            # convenience instead of overriding ``__init__``. should
            # only be used by concrete classes. called in constructor.
            pass

        def branch(self, parent=None):
            # convenience for self.tableau.branch()
            return self.tableau.branch(parent)

        def branching_complexity(self, node):
            return self.tableau.branching_complexity(node)

        def safeprop(self, name, value=None):
            if hasattr(self, name):
                raise KeyError('Property {0} already exists'.format(str(name)))
            self.__dict__[name] = value

        def add_timer(self, *names):
            for name in names:
                if name in self.timers:
                    raise KeyError('Timer {0} already exists'.format(str(name)))
                self.timers[name] = StopWatch()

        def add_helper(self, name, helper):
            self.safeprop(name, helper)
            self.helpers.append(helper)
            return helper

        def add_helpers(self, helpers):
            for name in helpers:
                self.add_helper(name, helpers[name])
            return self

        def __repr__(self):
            return self.name

    class RuleHelper(object):

        ticked = None

        def __init__(self, rule):
            self.rule = rule
            self.setup()

        def setup(self):
            pass

        def register_branch(self, branch, parent):
            pass

        def register_node(self, node, branch):
            pass

        def after_trunk_build(self, branches):
            pass

        def after_node_tick(self, node, branch):
            pass

        def after_branch_close(self, branch):
            pass

        def after_apply(self, target):
            pass

    class AdzHelper(RuleHelper):

        def apply_to_target(self, target):
            branch = target['branch']
            for i in range(len(target['adds'])):
                if i == 0:
                    continue
                b = branch.branch()
                b.update(target['adds'][i])
                if self.rule.ticking:
                    b.tick(target['node'])
            branch.update(target['adds'][0])
            if self.rule.ticking:
                branch.tick(target['node'])

        def closure_score(self, target):
            close_count = 0
            for nodes in target['adds']:
                nodes = [target['branch'].create_node(node) for node in nodes]
                for rule in self.rule.tableau.closure_rules:
                    if rule.nodes_will_close_branch(nodes, target['branch']):
                        close_count += 1
                        break
            return float(close_count / min(1, len(target['adds'])))

    class NodeTargetCheckHelper(RuleHelper):
        """
        Calls the rule's ``check_for_target(node, branch)`` when a node is added to
        a branch. If a target is returned, it is cached relative to the branch. The
        rule can then call ``cached_target(branch)``  on the helper to retrieve the
        target. This is used primarily in closure rules for performance.

        NB: The rule must implement ``check_for_target(self, node, branch)``.
        """

        def cached_target(self, branch):
            """
            Return the cached target for the branch, if any.
            """
            if branch.id in self.targets:
                return self.targets[branch.id]

        # Helper Implementation

        def setup(self):
            self.targets = {}

        def register_node(self, node, branch):
            target = self.rule.check_for_target(node, branch)
            if target:
                self.targets[branch.id] = target

    class ClosureRule(Rule):
        """
        A closure rule has a fixed ``apply()`` method that marks the branch as
        closed. Sub-classes should implement the ``applies_to_branch()`` method.
        """

        default_opts = {
            'is_rank_optim' : False
        }

        def __init__(self, *args, **opts):
            super().__init__(*args, **opts)
            self.add_helper('tracker', TableauxSystem.NodeTargetCheckHelper(self))

        def get_candidate_targets(self, branch):
            target = self.applies_to_branch(branch)
            if target:
                if target == True:
                    target = {'branch': branch}
                if 'branch' not in target:
                    target['branch'] = branch
                if 'type' not in target:
                    target['type'] = 'Branch'
                return [target]

        def apply_to_target(self, target):
            target['branch'].close()

        def applies_to_branch(self, branch):
            raise NotImplementedError()

        def nodes_will_close_branch(self, nodes, branch):
            for node in nodes:
                if self.node_will_close_branch(node, branch):
                    return True

        def node_will_close_branch(self, node, branch):
            raise NotImplementedError()

        # tracker

        def check_for_target(self, node, branch):
            raise NotImplementedError()

    class PotentialNodeRule(Rule):
        """
        PotentialNodeRule base class. Caches potential nodes as they appear,
        and tracks the number of applications to each node. Provides default
        implementation of some methods, and delegates to finer-grained abstract
        methods.
        """

        # Override
        ticked = False

        def __init__(self, *args, **opts):
            super(TableauxSystem.PotentialNodeRule, self).__init__(*args, **opts)
            self.safeprop('potential_nodes', {})
            self.safeprop('node_applications', {})

        # Implementation

        def get_candidate_targets(self, branch):
            # Implementations should be careful with overriding this method.
            # Be sure you at least call ``_extend_node_target()``.
            cands = list()
            if branch.id in self.potential_nodes:
                for node in set(self.potential_nodes[branch.id]):
                    targets = self.get_targets_for_node(node, branch)
                    if targets:
                        for target in targets:
                            target = self._extend_node_target(target, node, branch)
                            cands.append(target)
                    else:
                        if not self.is_potential_node(node, branch):
                            self.potential_nodes[branch.id].discard(node)
            return cands

        def _extend_node_target(self, target, node, branch):
            if target == True:
                target = {'node' : node}
            if 'node' not in target:
                target['node'] = node
            if 'type' not in target:
                target['type'] = 'Node'
            if 'branch' not in target:
                target['branch'] = branch
            return target

        # Caching

        def register_branch(self, branch, parent):
            # Likely to be extended in concrete class - call super and pay attention
            super(TableauxSystem.PotentialNodeRule, self).register_branch(branch, parent)
            if parent != None and parent.id in self.potential_nodes:
                self.potential_nodes[branch.id] = set(self.potential_nodes[parent.id])
                self.node_applications[branch.id] = dict(self.node_applications[parent.id])
            else:
                self.potential_nodes[branch.id] = set()
                self.node_applications[branch.id] = dict()

        def register_node(self, node, branch):
            # Likely to be extended in concrete class - call super and pay attention
            super(TableauxSystem.PotentialNodeRule, self).register_node(node, branch)
            if self.is_potential_node(node, branch):
                self.potential_nodes[branch.id].add(node)
                self.node_applications[branch.id][node.id] = 0

        def after_apply(self, target):
            super(TableauxSystem.PotentialNodeRule, self).after_apply(target)
            self.node_applications[target['branch'].id][target['node'].id] += 1

        def after_branch_close(self, branch):
            super(TableauxSystem.PotentialNodeRule, self).after_branch_close(branch)
            del(self.potential_nodes[branch.id])
            del(self.node_applications[branch.id])

        def after_node_tick(self, node, branch):
            super(TableauxSystem.PotentialNodeRule, self).after_node_tick(node, branch)
            if self.ticked == False and branch.id in self.potential_nodes:
                self.potential_nodes[branch.id].discard(node)

        # Util

        def min_application_count(self, branch_id):
            if branch_id in self.node_applications:
                if not len(self.node_applications[branch_id]):
                    return 0
                return min({
                    self.node_application_count(node_id, branch_id)
                    for node_id in self.node_applications[branch_id]
                })
            return 0

        def node_application_count(self, node_id, branch_id):
            if branch_id in self.node_applications:
                if node_id in self.node_applications[branch_id]:
                    return self.node_applications[branch_id][node_id]
            return 0

        # Default

        def score_candidate(self, target):
            score = super(TableauxSystem.PotentialNodeRule, self).score_candidate(target)
            if score == 0:
                complexity = self.branching_complexity(target['node'])
                score = -1 * complexity
            return score

        # Abstract

        def is_potential_node(self, node, branch):
            raise NotImplementedError()

        # Delegating abstract

        def get_targets_for_node(self, node, branch):
            # Default implementation, delegates to ``get_target_for_node``
            target = self.get_target_for_node(node, branch)
            if target:
                return [target]

        def get_target_for_node(self, node, branch):
            raise NotImplementedError()

        def apply_to_target(self, target):
            # Default implementation, to provide a more convenient
            # method signature.
            self.apply_to_node_target(target['node'], target['branch'], target)

        def apply_to_node_target(self, node, branch, target):
            # Default implementation, to provide a more convenient
            # method signature.
            self.apply_to_node(node, branch)

        def apply_to_node(self, node, branch):
            # Simpler signature to implement, mostly for legacy purposes.
            # New code should implement ``apply_to_node_target()`` instead,
            # which provides more flexibility.
            raise NotImplementedError()

    class FilterNodeRule(PotentialNodeRule):
        """
        A ``FilterNodeRule`` filters potential nodes by matching
        the attribute conditions of the implementing class.

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

        #: The predicate name
        predicate   = None

        # Implementation

        def is_potential_node(self, node, branch):
            return self.conditions_apply(node, branch)

        def get_target_for_node(self, node, branch):
            # Default is to return True, which gets converted into a
            # target along the way.
            return self.conditions_apply(node, branch)

        def conditions_apply(self, node, branch):
            if self.ticked != None and self.ticked != (node in branch.ticked_nodes):
                return False
            if self.modal != None:
                modal = len(node.worlds()) > 0
                if self.modal != modal:
                    return False
            sentence = operator = quantifier = predicate = None
            if node.has('sentence'):
                sentence = node.props['sentence']
                operator = sentence.operator
                quantifier = sentence.quantifier
                predicate = sentence.predicate
            if self.negated != None:
                negated = operator == 'Negation'
                if not sentence or negated != self.negated:
                    return False
                if negated:
                    sentence = sentence.operand
                    operator = sentence.operator
                    quantifier = sentence.quantifier
                    predicate = sentence.predicate
            if self.operator != None:
                if self.operator != operator:
                    return False
            elif self.quantifier != None:
                if self.quantifier != quantifier:
                    return False
            if self.designation != None:
                if 'designated' not in node.props or node.props['designated'] != self.designation:
                    return False
            if self.predicate != None:
                if predicate == None or self.predicate != predicate.name:
                    return False
            return True

        # Override

        def sentence(self, node):
            s = None
            if 'sentence' in node.props:
                s = node.props['sentence']
                if self.negated:
                    s = s.operand
            return s

        # Default

        def example_node(self, branch):
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
                    raise BadArgumentError("Must specify either notation or sw.")
                sw = notation.Writer(symbol_set)
            return self.write_tableau(tableau, sw, opts)

        def write_tableau(self, tableau, sw, opts):
            raise NotImplementedError()

class Model(object):

    class ModelValueError(Exception):
        pass

    class DenotationError(ModelValueError):
        pass

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
            return self.truth_function(operator, *[self.value_of(operand, **kw) for operand in sentence.operands])
        raise NotImplementedError()

    def value_of_quantified(self, sentence, **kw):
        raise NotImplementedError()

    def is_countermodel_to(self, argument):
        raise NotImplementedError()

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

    class ParserThreadError(ParseError):
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
            raise Parser.ParserThreadError('Parser is already parsing -- not thread safe.')
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

def make_tree_structure(branches, node_depth=0, track=None):
    is_root = track == None
    if track == None:
        track = {
            'pos'            : 0,
            'depth'          : 0,
            'distinct_nodes' : 0,
        }
    track['pos'] += 1
    s = {
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
                s['has_closed'] = True
            else:
                s['has_open'] = True
            if s['has_open'] and s['has_closed']:
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
            s['nodes'].append(node)
            if s['step'] == None or s['step'] > node.step:
                s['step'] = node.step
            node_depth += 1
            continue
        break
    track['distinct_nodes'] += len(s['nodes'])
    if len(branches) == 1:
        branch = branches[0]
        s['closed'] = branch.closed
        s['open'] = not branch.closed
        if s['closed']:
            s['closed_step'] = branch.closed_step
            s['has_closed'] = True
        else:
            s['has_open'] = True
        s['width'] = 1
        s['leaf'] = True
        s['branch_id'] = branch.id
        if branch.model != None:
            s['model_id'] = branch.model.id
        if track['depth'] == 0:
            s['is_only_branch'] = True
    else:
        inbetween_widths = 0
        track['depth'] += 1
        first_width = 0
        last_width = 0
        for i, node in enumerate(distinct_nodes):
            child_branches = [branch for branch in branches if branch.nodes[node_depth] == node]

            # recurse
            child = make_tree_structure(child_branches, node_depth, track)

            s['descendant_node_count'] = len(child['nodes']) + child['descendant_node_count']
            s['width'] += child['width']
            s['children'].append(child)
            if i == 0:
                s['branch_step'] = child['step']
                first_width = float(child['width']) / 2
            elif i == len(distinct_nodes) - 1:
                last_width = float(child['width']) / 2
            else:
                inbetween_widths += child['width']
            s['branch_step'] = min(s['branch_step'], child['step'])
        if s['width'] > 0:
            s['balanced_line_width'] = float(first_width + last_width + inbetween_widths) / s['width']
            s['balanced_line_margin'] = first_width / s['width']
        else:
            s['balanced_line_width'] = 0
            s['balanced_line_margin'] = 0
        track['depth'] -= 1
    s['structure_node_count'] = s['descendant_node_count'] + len(s['nodes'])
    track['pos'] += 1
    s['right'] = track['pos']
    if is_root:
        s['distinct_nodes'] = track['distinct_nodes']
    return s

class StopWatch(object):

    class StateError(Exception):
        pass

    def __init__(self, started=False):
        self._start_time = None
        self._elapsed = 0
        self._is_running = False
        self._times_started = 0
        if started:
            self.start()

    def start(self):
        if self._is_running:
            raise StopWatch.StateError('StopWatch already started.')
        self._start_time = nowms()
        self._is_running = True
        self._times_started += 1
        return self

    def stop(self):
        if not self._is_running:
            raise StopWatch.StateError('StopWatch already stopped.')
        self._is_running = False
        self._elapsed += nowms() - self._start_time
        return self

    def reset(self):
        self._elapsed = 0
        if self._is_running:
            self._start_time = nowms()
        return self

    def elapsed(self):
        if self._is_running:
            return self._elapsed + (nowms() - self._start_time)
        return self._elapsed

    def elapsed_avg(self):
        return self.elapsed() / max(1, self.times_started())

    def is_running(self):
        return self._is_running

    def times_started(self):
        return self._times_started

    def __repr__(self):
        return self.elapsed().__repr__()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        if self.is_running():
            self.stop()