# -*- coding: utf-8 -*-
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
# pytableaux - lexicals module
from errors import NotFoundError
from utils import cat, isint, isstr, sortedbyval
from copy import deepcopy

notations = ('polish', 'standard')
default_notation = 'standard'
default_notn_encs = {'polish': 'ascii', 'standard': 'unicode'}

def create_lexwriter(notn=None, enc=None, **opts):
    if not notn:
        notn = default_notation
    if notn not in notations:
        raise ValueError('Invalid notation: {0}'.format(str(notn)))
    if not enc:
        enc = default_notn_encs[notn]
    if 'renderset' not in opts:
        opts['renderset'] = RenderSet.fetch(notn, enc)
    if notn == 'polish':
        return PolishLexWriter(**opts)
    if notn == 'standard':
        return StandardLexWriter(**opts)
    raise NotFoundError('Unknown notation {0}'.format(str(notn)))

def get_system_predicate(name):
    """
    Get a system predicate by name. Example::

        pred = get_system_predicate('Identity')
        assert pred.arity == 2

    :param str name: The predicate name.
    :return: The predicate instance.
    :rtype: Predicate
    :raises KeyError: if the system predicate does not exist.
    """
    return Vocabulary._get_system_predicate(name)

def get_system_predicates():
    """
    Returns a list of predicate objects.
    """
    return Vocabulary._get_system_predicates()

def list_system_predicates():
    """
    Returns a list of predicate names
    """
    return Vocabulary._list_system_predicates()

def is_system_predicate(name):
    return Vocabulary._is_system_predicate(name)

def operarity(oper):
    """
    Get the arity of an operator.

    Note: to get the arity of a predicate, use ``predicate.arity``.

    :param str operator: The operator.
    :return: The arity of the operator.
    :rtype: int
    :raises KeyError: if the operator does not exist.
    """
    return OperatedSentence._operarity(oper)

def is_operator(arg):
    return OperatedSentence._is_operator(arg)

def list_operators():
    return OperatedSentence._list_operators()

def is_quantifier(arg):
    return QuantifiedSentence._is_quantifier(arg)

def list_quantifiers():
    return QuantifiedSentence._list_quantifiers()

class LexicalItem(object):

    @classmethod
    def max_index(cls):
        if cls == Constant:
            return 3
        if cls == Variable:
            return 3
        if cls == AtomicSentence:
            return 4
        if cls == Predicate:
            return 3
        return None

    def __init__(self):
        if self.__class__ == __class__:
            raise TypeError('Class {0} cannot be constructed'.format(self.__class__.__name__))

    # Base LexicalItem class for comparison, hashing, and sorting.

    def sort_tuple(self):
        # Sort tuple should always consist of numbers, or tuples with numbers.
        # This is also used in hashing, so equal objects should have equal hashes.
        raise NotImplementedError()

    def ident(self):
        # Equality/inequality identifier. By default, this delegates to sort_tuple.
        return self.sort_tuple()

    # Sorting implementation. The Vocabulary class defines canonical ordering for
    # each type of lexical item, so we can sort lists with mixed classes, e.g.
    # constants and variables, different sentence types, etc. This class takes
    # care of ensuring different types are not considered equal (e.g. constant(0, 0),
    # variable(0, 0), atomic(0, 0)) and are still sorted properly.
    #
    # This is the reason for _lexrank, and __lexorder, on the Vocabulary class,
    # as well as similar properties on QuantifiedSentence (for quantifiers), and
    # OperatedSentence (for operators). Basically anything that cannot be
    # converted to a number by which we can meaningfully sort needs to be
    # considered specially, i.e. classes, operators, and quantifiers.
    def __lt__(self, other):
        a, b = self.__getcmp(other)
        return a < b

    def __le__(self, other):
        a, b = self.__getcmp(other)
        return a <= b

    def __gt__(self, other):
        a, b = self.__getcmp(other)
        return a > b

    def __ge__(self, other):
        a, b = self.__getcmp(other)
        return a >= b

    def __getcmp(self, other):
        r1, r2 = LexicalItem._lexrank(self, other)
        if r1 == r2:
            return (self.sort_tuple(), other.sort_tuple())
        return (r1, r2)

    # Default equals and hash implementation is based on sort_tuple.
    #
    # https://docs.python.org/3/reference/datamodel.html#object.__hash__
    #
    # - If a class does not define __eq__ it should not define __hash__.
    #
    # - A class that overrides __eq__ and does not  __hash__ will have its
    #    __hash__ implicitly set to None.
    #

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.ident() == other.ident()
        )

    def __ne__(self, other):
        return (
            not isinstance(other, self.__class__) or
            self.ident() != other.ident()
        )

    def __hash__(self):
        return hash(self.sort_tuple())

    def __repr__(self):
        """
        Default representation with lex-order + sort-tuple.
        """
        return (LexicalItem.__lexorder[self.__class__], self.sort_tuple()).__repr__()

    @staticmethod
    def _lexrank(*items):
        # Returns the value of __lexorder (below) for the class of each item.
        return tuple(LexicalItem.__lexorder[clas] for clas in (it.__class__ for it in items))

    @staticmethod
    def _initorder():
        # Canonical order or all the concrete LexicalItem classes.
        LexicalItem.__lexorder = {
            Predicate: 10, Constant: 20, Variable: 30, AtomicSentence: 40,
            PredicatedSentence: 50, QuantifiedSentence: 60, OperatedSentence: 70,
            # Abstract, just a safety measure
            Parameter: 416, Sentence: 417, LexicalItem: 418,
        }
        # This method self-destucts.
        delattr(LexicalItem, '_initorder')

class Parameter(LexicalItem):

    def __init__(self, index, subscript):
        maxi = self.__class__.max_index()
        if maxi == None:
            raise TypeError('Class {0} cannot be constructed'.format(self.__class__.__name__))
        if index > maxi:
            raise ValueError('Index too large: {0}'.format(str(index)))
        self.index = index
        self.subscript = subscript
        self.coords = (index, subscript)

    def is_constant(self):
        return isinstance(self, Constant)

    def is_variable(self):
        return isinstance(self, Variable)

    def sort_tuple(self):
        # Sort constants and variables by index, subscript
        return (self.index, self.subscript)

class Constant(Parameter):
    pass

class Variable(Parameter):
    pass

class Predicate(LexicalItem):

    def __init__(self, name, index, subscript, arity):
        if index > self.__class__.max_index():
            raise ValueError(
                "Predicate index too large: {0}".format(str(index))
            )
        if not isint(arity):
            raise TypeError(
                'Predicate arity must be an integer'
            )
        if arity < 1:
            raise ValueError(
                'Predicate arity cannot be < 1'
            )
        if not isint(subscript):
            raise TypeError(
                'Predicate subscript must be an integer'
            )
        if subscript < 0:
            raise ValueError(
                'Subscript cannot be < 0'
            )
        if name == None:
            name = 'Predicate@({0},{1})'.format(index, subscript)
        self.name      = name
        self.arity     = arity
        self.index     = index
        self.subscript = subscript
        self.coords    = (index, subscript)

    def is_system_predicate(self):
        return self.index < 0

    def sort_tuple(self):
        # Sort predicates by index, subscript, arity
        return (self.index, self.subscript, self.arity)

class Sentence(LexicalItem):

    #: The operator, if any.
    operator = None

    #: The quantifier, if any.
    quantifier = None

    #: The predicate, if any.
    predicate = None

    #: The type (class name).
    type = None

    def __init__(self):
        if self.__class__ == __class__:
            raise TypeError('Class {0} cannot be constructed'.format(self.__class__.__name__))
        self.type = self.__class__.__name__

    def is_atomic(self):
        """
        Whether this is an atomic sentence.

        :rtype: bool
        """
        return isinstance(self, AtomicSentence)

    def is_predicated(self):
        """
        Whether this is a predicated sentence.

        :rtype: bool
        """
        return isinstance(self, PredicatedSentence)

    def is_quantified(self):
        """
        Whether this a quantified sentence.

        :rtype: bool
        """
        return isinstance(self, QuantifiedSentence)

    def is_operated(self):
        """
        Whether this is an operated sentence.

        :rtype: bool
        """
        return isinstance(self, OperatedSentence)

    def is_literal(self):
        """
        Whether the sentence is a literal. Here a literal is either a
        predicated sentence, the negation of a predicated sentence,
        an atomic sentence, or the negation of an atomic sentence.

        :rtype: bool
        """
        return self.is_atomic() or self.is_predicated() or (
            self.is_operated() and self.operator == 'Negation' and (
                self.operand.is_atomic() or
                self.operand.is_predicated()
            )
        )

    def is_negated(self):
        """
        Whether this is a negated sentence.

        :rtype: bool
        """
        return isinstance(self, OperatedSentence) and self.operator == 'Negation'

    def substitute(self, new_param, old_param):
        """
        Recursively substitute ``new_param`` for all occurrences of ``old_param``.
        May return self, or a new sentence.

        :rtype: Sentence
        """
        raise NotImplementedError()

    def negate(self):
        """
        Negate this sentence, returning the new sentence.

        :rtype: OperatedSentence
        """
        return OperatedSentence('Negation', [self])

    def negative(self):
        """
        Either negate this sentence, or, if this is already a negated sentence
        return its negatum, i.e., "un-negate" the sentence.

        :rtype: Sentence
        """
        return self.negatum if self.is_negated() else self.negate()

    def asserted(self):
        """
        Apply the assertion operator to this sentence, and return the new sentence.

        :rtype: Sentence
        """
        return OperatedSentence('Assertion', [self])

    def disjoin(self, rhs):
        """
        TODO: doc
        """
        return OperatedSentence('Disjunction', [self, rhs])

    def conjoin(self, rhs):
        """
        TODO: doc
        """
        return OperatedSentence('Conjunction', [self, rhs])

    def constants(self):
        """
        Set of constants, recursive.
        """
        return set()

    def variables(self):
        """
        Set of variables, recursive.
        """
        return set()

    def atomics(self):
        """
        Set of atomic sentences, recursive.
        """
        return set()

    def predicates(self):
        """
        Set of predicates, recursive.
        """
        return set()

    def operators(self):
        """
        List of operators, recursive.
        """
        # TODO: Explain why operators and quantifiers are returned as a list,
        #       while everything else is returned as a set. I believe is has
        #       something to do tableau rule optimization, or maybe reading
        #       models. In any case, there might be a more consistent way.
        return list()

    def quantifiers(self):
        """
        List of quantifiers, recursive.
        """
        return list()

class AtomicSentence(Sentence):

    def __init__(self, index, subscript):
        if index > AtomicSentence.max_index():
            raise ValueError(
                "Index too large {0}".format(str(index))
            )
        super().__init__()
        self.index     = index
        self.subscript = subscript
        self.coords    = (index, subscript)

    def substitute(self, new_param, old_param):
        return self

    def atomics(self):
        return set([self])

    def next(self):
        if self.index < AtomicSentence.max_index():
            index = self.index + 1
            subscript = self.subscript
        else:
            index = 0
            subscript = self.subscript + 1
        return AtomicSentence(index, subscript)

    def sort_tuple(self):
        # Sort atomic sentences by index, subscript
        return (self.index, self.subscript)

class PredicatedSentence(Sentence):

    def __init__(self, predicate, parameters, vocabulary=None):
        if isstr(predicate):
            if is_system_predicate(predicate):
                predicate = get_system_predicate(predicate)
            elif vocabulary is None:
                raise NotFoundError(
                    "Predicate '{0}' not found.".format(predicate)
                )
            else:
                predicate = vocabulary.get_predicate(predicate)    
        if len(parameters) != predicate.arity:
            raise TypeError(
                'Expecting {0} parameters for predicate {1}, got {2} instead.'.format(
                    predicate.arity, str([predicate.index, predicate.subscript]), len(parameters)
                )
            )
        super().__init__()
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
        return PredicatedSentence(self.predicate, params)

    def constants(self):
        return {param for param in self.parameters if param.is_constant()}

    def variables(self):
        return {param for param in self.parameters if param.is_variable()}

    def predicates(self):
        return set([self.predicate])

    def sort_tuple(self):
        # Sort predicated sentences by their predicate, then by their parameters
        return self.predicate.sort_tuple() + tuple(param.sort_tuple() for param in self.parameters)

class QuantifiedSentence(Sentence):

    # -- docs copied from previous api

    # Return a quanitified sentence for the given quantifier, bound variable and
    # inner sentence. Example using the Identity system predicate::

    #     x = variable(0, 0)

    #     # x is identical to x
    #     open_sentence = predicated('Identity', [x, x])

    #     # for all x, x is identical to x
    #     sentence = quantify('Universal', x, open_sentence)

    # Examples using a vocabulary of user-defined predicates::

    #     vocab = Vocabulary([
    #         ('is a bachelor', 0, 0, 1),
    #         ('is unmarried' , 1, 0, 1)
    #     ])
    #     x = variable(0, 0)

    #     # x is a bachelor
    #     open_sentence = predicated('is a bachelor', [x], vocab)

    #     # there exists an x, such that x is a bachelor
    #     sentence = quantify('Existential', x, open_sentence)

    #     # x is unmarried
    #     open_sentence2 = predicated('is unmarried', [x], vocab)

    #     # if x is a bachelor, then x is unmarried
    #     open_sentence3 = operate('Conditional', [open_sentence, open_sentence2])

    #     # for all x, if x is a bachelor then x is unmarried
    #     sentence2 = quantify('Universal', x, open_sentence3)

    # :rtype: Vocabulary.Sentence

    def __init__(self, quantifier, variable, sentence):
        super().__init__()
        self.quantifier = quantifier
        self.variable   = variable
        self.sentence   = sentence

    def substitute(self, new_param, old_param):
        # Always return a new sentence.
        si = self.sentence
        r = si.substitute(new_param, old_param)
        return QuantifiedSentence(self.quantifier, self.variable, r)

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

    def sort_tuple(self):
        # Sort quantified sentences first by their quanitfier, using fixed
        # lexical order (below), then by their variable, followed by their
        # inner sentence.
        return (self.__lexorder[self.quantifier], self.variable.sort_tuple(), self.sentence.sort_tuple())

    @staticmethod
    def _is_quantifier(arg):
        return arg in __class__.__lexorder

    @staticmethod
    def _list_quantifiers():
        return list(__class__.__quantlist)

    # Lexical sorting order.
    __lexorder = {'Existential': 0, 'Universal': 1}

    __quantlist = sortedbyval(__lexorder)

class OperatedSentence(Sentence):

    def __init__(self, operator, operands):
        if not is_operator(operator):
            raise NotFoundError(
                "Unknown operator '{0}'.".format(operator)
            )
        arity = operarity(operator)
        if len(operands) != arity:
            raise TypeError(
                "Expecting {0} operands for operator '{1}', got {2}.".format(
                    arity, operator, len(operands)
                )
            )
        super().__init__()
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
        return OperatedSentence(self.operator, new_operands)

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

    def sort_tuple(self):
        # Sort operated sentences first by their operator, using fixed
        # lexical order (below), then by their operands.
        return (self.__lexorder[self.operator],) + tuple(s.sort_tuple() for s in self.operands)

    @staticmethod
    def _is_operator(arg):
        return arg in __class__.__lexorder

    @staticmethod
    def _list_operators():
        return list(__class__.__operlist)

    @staticmethod
    def _operarity(operator):
        return __class__.__arities[operator]

    # Lexical sorting order.
    __lexorder = {
        'Assertion': 10, 'Negation': 20, 'Conjunction': 30, 'Disjunction': 40,
        'Material Conditional': 50, 'Material Biconditional': 60, 'Conditional': 70,
        'Biconditional': 80, 'Possibility': 90, 'Necessity': 100,
    }
    __operlist = sortedbyval(__lexorder)
    __arities = {
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

class Vocabulary(object):
    """
    A vocabulary is a store of user-defined predicates.

    Create a new vocabulary. *predicate_defs* is a list of tuples (name, index,
    subscript, arity) defining user predicates. Example::

        vocab = Vocabulary([
            ('is tall',        0, 0, 1),
            ('is taller than', 0, 1, 2),
            ('between',        1, 0, 3)
        ])

    """
    def __init__(self, predicate_defs=None):
        # set of predicate instances
        self.user_predicates_set   = set()
        # list of predicate names
        self.user_predicates_list  = []
        # name to predicate instance
        self.user_predicates       = {}
        # (index, subscript) to predicate instance
        self.user_predicates_index = {}
        if predicate_defs:
            for info in predicate_defs:
                if not isinstance(info, list) and not isinstance(info, tuple):
                    raise TypeError(
                        'predicate_defs must be a list/tuple of lists/tuples.'
                    )
                if len(info) != 4:
                    raise TypeError(
                        'Predicate declarations must be 4-tuples (name, index, subscript, arity).'
                    )
                self.declare_predicate(*info)

    def copy(self):
        # Shallow copy.
        vocab = Vocabulary()
        vocab.user_predicates = dict(self.user_predicates)
        vocab.user_predicates_list = list(self.user_predicates_list)
        vocab.user_predicates_set = set(self.user_predicates_set)
        vocab.user_predicates_index = dict(self.user_predicates_index)
        return vocab

    def get_predicate(self, name=None, index=None, subscript=None):
        """
        Get a defined predicate, either by name, or by index and subscript. This
        includes system predicates::

            vocab = Vocabulary()
            predicate = vocab.get_predicate('Identity')

        Or user-defined predicates::

            vocab = Vocabulary([('is tall', 0, 0, 1)])
            assert vocab.get_predicate('is tall') == vocab.get_predicate(index=0, subscript=0)

        """
        if isstr(name):
            if is_system_predicate(name):
                return get_system_predicate(name)
            if name in self.user_predicates:
                return self.user_predicates[name]
            raise NotFoundError('Predicate {0} not found'.format(name))
        if isint(name) and isint(index) and subscript == None:
            # allow for get_predicate(0, 0)
            index, subscript = name, index
        if not isint(index) or not isint(subscript):
            raise TypeError('index, subscript must be integers')
        coords = (index, subscript)
        if coords in self.user_predicates_index:
            return self.user_predicates_index[coords]
        if coords in Vocabulary.__syslookup:
            return Vocabulary.__syslookup[coords]
        raise NotFoundError('Predicate {0} not found'.format(str(coords)))

    def declare_predicate(self, name, index, subscript, arity):
        """
        Declare a user-defined predicate::

            vocab = Vocabulary()
            pred = vocab.declare_predicate(
                name='is tall', index=0, subscript=0, arity=1
            )
            assert pred == vocab.get_predicate('is tall')
            assert pred == vocab.get_predicate(index=0, subscript=0)
            
            # predicates cannot be re-declared
            try:
                vocab.declare_predicate('is tall', index=1, subscript=2, arity=3)
            except ValueError:
                assert True
            else:
                assert False

        """
        if is_system_predicate(name):
            raise ValueError(
                "Cannot declare system predicate '{0}'".format(name)
            )
        if name in self.user_predicates:
            raise ValueError(
                "Predicate '{0}' already declared".format(name)
            )
        try:
            self.get_predicate(index=index, subscript=subscript)
        except NotFoundError:
            pass
        else:
            raise ValueError(
                "Predicate for {0},{1} already declared".format(
                    str(index), str(subscript)
                )
            )
        predicate = Predicate(name, index, subscript, arity)
        self.add_predicate(predicate)
        return predicate

    def add_predicate(self, predicate):
        """
        Add a predicate instance::

            vocab1 = Vocabulary()
            predicate = vocab1.declare_predicate(
                name='is tall', index=0, subscript=0, arity=1
            )
            vocab2 = Vocabulary()
            vocab2.add_predicate(predicate)
            assert vocab2.get_predicate('is tall') == predicate
        """
        if not isinstance(predicate, Predicate):
            raise TypeError(
                'Predicate must be an instance of Predicate'
            )
        if predicate.index < 0:
            raise TypeError(
                'Cannot add a system predicate to a vocabulary'
            )
        self.user_predicates[predicate.name] = predicate
        key = (predicate.index, predicate.subscript)
        self.user_predicates_index[key] = predicate
        if predicate not in self.user_predicates_set:
            self.user_predicates_set.add(predicate)
            self.user_predicates_list.append(predicate.name)
        return predicate
        
    def list_predicates(self):
        """
        List all predicates in the vocabulary, including system predicates.
        """
        return list_system_predicates() + self.user_predicates_list

    def list_user_predicates(self):
        """
        List all predicates in the vocabulary, excluding system predicates.
        """
        return list(self.user_predicates_list)

    @staticmethod
    def _get_system_predicate(lookup):
        return Vocabulary.__syslookup[lookup]

    @staticmethod
    def _get_system_predicates():
        return list(Vocabulary.__syspreds)

    @staticmethod
    def _is_system_predicate(pred):
        return pred in Vocabulary.__syslookup

    @staticmethod
    def _list_system_predicates():
        return list(p.name for p in Vocabulary.__syspreds)

    @staticmethod
    def _initsys():
        Vocabulary.__syspreds = preds = (
            Predicate('Identity',  -1, 0, 2),
            Predicate('Existence', -2, 0, 1),
        )
        Vocabulary.__syslookup = idx = {p.name: p for p in preds}
        idx.update({p.coords: p for p in preds})
        idx.update({p: p for p in preds})
        # This method self-destucts.
        delattr(Vocabulary, '_initsys')

# Init system predicates
Vocabulary._initsys()
# Initialize order.
LexicalItem._initorder()

class Argument(object):
    """
    Create an argument from sentence objects. For parsing strings into arguments,
    see ``Parser.argument``.
    """
    def __init__(self, conclusion, premises = None, title = None):
        self.premises = []
        if premises:
            for premise in premises:
                if not isinstance(premise, Sentence):
                    raise TypeError('premises must be Sentence objects')
                self.premises.append(premise)
        if not isinstance(conclusion, Sentence):
            raise TypeError('conclusion must be Sentence object')
        self.conclusion = conclusion
        self.title      = title

    def __repr__(self):
        if self.title is None:
            return [self.premises, self.conclusion].__repr__()
        return [self.premises, self.conclusion, {'title': self.title}].__repr__()

    def __hash__(self):
        return hash((self.conclusion,) + tuple(self.premises))

    def __eq__(self, other):
        """
        Two arguments are considered equal just when their conclusions are equal, and their
        premises are equal (and in the same order) The title is not considered in equality.
        """
        return isinstance(other, self.__class__) and hash(self) == hash(other)

    def __ne__(self, other):
        return not isinstance(other, self.__class__) or hash(self) != hash(other)

class LexWriter(object):

    _defaults = {}

    def __init__(self, **opts):
        self.opts = deepcopy(self._defaults)
        self.opts.update(opts)

    def write(self, item):
        """
        Write a lexical item.
        """
        # NB: implementations should avoid calling this method, e.g.
        #     dropping parens will screw up since it is recursive.
        if isstr(item):
            if is_operator(item):
                return self._write_operator(item)
            if is_quantifier(item):
                return self._write_quantifier(item)
            raise TypeError('Unknown lexical string type: {0}'.format(item))
        if isinstance(item, Parameter):
            return self._write_parameter(item)
        if isinstance(item, Predicate):
            return self._write_predicate(item)
        if isinstance(item, Sentence):
            return self._write_sentence(item)
        raise TypeError('Unknown lexical type: {0}'.format(item))

    def _write_parameter(self, param):
        if isinstance(param, Constant):
            return self._write_constant(param)
        elif isinstance(param, Variable):
            return self._write_variable(param)
        raise NotImplementedError()

    def _write_operator(self, item):
        raise NotImplementedError()

    def _write_quantifier(self, item):
        raise NotImplementedError()

    def _write_constant(self, item):
        raise NotImplementedError()

    def _write_variable(self, item):
        raise NotImplementedError()

    def _write_predicate(self, item):
        raise NotImplementedError()

    def _write_sentence(self, item):
        raise NotImplementedError()

class BaseLexWriter(LexWriter):

    def __init__(self, renderset, **opts):
        super().__init__(**opts)
        self.renderset = renderset
        self.encoding = renderset.encoding

    # Base lex writer.
    def _strfor(self, *args, **kw):
        return self.renderset.strfor(*args, **kw)

    def _write_operator(self, operator):
        return self._strfor('operator', operator)

    def _write_quantifier(self, quantifier):
        return self._strfor('quantifier', quantifier)

    def _write_constant(self, constant):
        return cat(
            self._strfor('constant', constant.index),
            self._write_subscript(constant.subscript),
        )

    def _write_variable(self, variable):
        return cat(
            self._strfor('variable', variable.index),
            self._write_subscript(variable.subscript),
        )

    def _write_predicate(self, predicate):
        if is_system_predicate(predicate.name):
            typ, key = ('system_predicate', predicate.name)
        else:
            typ, key = ('user_predicate', predicate.index)
        return cat(
            self._strfor(typ, key),
            self._write_subscript(predicate.subscript),
        )

    def _write_sentence(self, sentence):
        if sentence.is_atomic():
            return self._write_atomic(sentence)
        if sentence.is_predicated():
            return self._write_predicated(sentence)
        if sentence.is_quantified():
            return self._write_quantified(sentence)
        if sentence.is_operated():
            return self._write_operated(sentence)
        raise TypeError('Unknown sentence type: {0}'.format(str(sentence)))

    def _write_atomic(self, sentence):
        return cat(
            self._strfor('atomic', sentence.index),
            self._write_subscript(sentence.subscript)
        )

    def _write_quantified(self, sentence):
        return ''.join([
            self._write_quantifier(sentence.quantifier),
            self._write_variable(sentence.variable),
            self._write_sentence(sentence.sentence),
        ])

    def _write_predicated(self, sentence):
        s = self._write_predicate(sentence.predicate)
        for param in sentence.parameters:
            s += self._write_parameter(param)
        return s

    def _write_subscript(self, subscript):
        if subscript == 0:
            return ''
        return self._strfor('subscript', subscript)

    def _write_operated(self, sentence):
        raise NotImplementedError()

class PolishLexWriter(BaseLexWriter):

    def _write_operated(self, sentence):
        return cat(
            self._write_operator(sentence.operator),
            *(self._write_sentence(s) for s in sentence.operands),
        )

class StandardLexWriter(BaseLexWriter):

    _defaults = {'drop_parens': True}

    def write(self, item):
        if self.opts['drop_parens'] and isinstance(item, OperatedSentence):
            return self._write_operated(item, drop_parens = True)
        return super().write(item)

    def _write_predicated(self, sentence):
        # Infix notation for predicates of arity > 1
        if sentence.predicate.arity < 2:
            return super()._write_predicated(sentence)
        # For Identity, add spaces (a = b instead of a=b)
        ws = self._strfor('whitespace', 0) if sentence.predicate.name == 'Identity' else ''
        return cat(
            self._write_parameter(sentence.parameters[0]),
            ws,
            self._write_predicate(sentence.predicate),
            ws,
            *(self._write_parameter(param) for param in sentence.parameters[1:]),
        )

    def _write_operated(self, sentence, drop_parens = False):
        oper = sentence.operator
        arity = operarity(oper)
        if arity == 1:
            operand = sentence.operand
            if (oper == 'Negation' and
                operand.is_predicated() and
                operand.predicate.name == 'Identity'):
                return self._write_negated_identity(sentence)
            else:
                return self._write_operator(oper) + self._write_sentence(operand)
        elif arity == 2:
            return ''.join([
                self._strfor('paren_open', 0) if not drop_parens else '',
                self._strfor('whitespace', 0).join([
                    # self.write(sentence.lhs),
                    self._write_sentence(sentence.lhs),
                    self._write_operator(oper),
                    # self.write(sentence.rhs),
                    self._write_sentence(sentence.rhs),
                ]),
                self._strfor('paren_close', 0) if not drop_parens else '',
            ])
        raise NotImplementedError('No support for operators of arity {0}'.format(str(arity)))

    def _write_negated_identity(self, sentence):
        params = sentence.operand.parameters
        return cat(
            self._write_parameter(params[0]),
            self._strfor('whitespace', 0),
            self._strfor('system_predicate', 'NegatedIdentity'),
            self._strfor('whitespace', 0),
            self._write_parameter(params[1]),
        )

class RenderSet(object):

    __instances = {'polish': {}, 'standard': {}}

    @staticmethod
    def load(notn, name, data):
        idx = __class__.__instances[notn]
        if name in idx:
            raise ValueError('RenderSet {0}.{1} already defined'.format(notn, name))
        idx[name] = __class__(data)
        return idx[name]

    @staticmethod
    def fetch(notn, name='ascii'):
        idx = __class__.__instances[notn]
        builtin = __class__.__builtin[notn]
        return idx.get(name) or __class__.load(notn, name, builtin[name])

    @staticmethod
    def available(notn):
        return sorted(set(__class__.__instances[notn]).union(__class__.__builtin[notn]))

    def __init__(self, data):
        if not isinstance(data, dict):
            raise TypeError('data must be a dict')
        self.name = data['name']
        self.encoding = data['encoding']
        self.renders = data.get('renders', {})
        self.formats = data.get('formats', {})
        self.strings = data.get('strings', {})
        self.data = data

    def strfor(self, ctype, value):
        if ctype in self.renders:
            return self.renders[ctype](value)
        if ctype in self.formats:
            return self.formats[ctype].format(value)
        return self.strings[ctype][value]

    @staticmethod
    def _initbuiltin(tdata):
        __class__.__builtin = tdata
        del(__class__._initbuiltin)
    __builtin = None

_ = {
    'polish': {
        'ascii': {
            'name'     : 'polish.ascii',
            'notation' : 'polish',
            'encoding' : 'ascii',
            'formats': {
                'subscript': '{0}',
            },
            'strings' : {
                'atomic'   : ['a', 'b', 'c', 'd', 'e'],
                'operator' : {
                    'Assertion'              : 'T',
                    'Negation'               : 'N',
                    'Conjunction'            : 'K',
                    'Disjunction'            : 'A',
                    'Material Conditional'   : 'C',
                    'Material Biconditional' : 'E',
                    'Conditional'            : 'U',
                    'Biconditional'          : 'B',
                    'Possibility'            : 'M',
                    'Necessity'              : 'L',
                },
                'variable'   : ['x', 'y', 'z', 'v'],
                'constant'   : ['m', 'n', 'o', 's'],
                'quantifier' : {
                    'Universal'   : 'V',
                    'Existential' : 'S',
                },
                'system_predicate'  : {
                    'Identity'  : 'I',
                    'Existence' : 'J',
                    'NegatedIdentity' : NotImplemented,
                },
                'user_predicate' : ['F', 'G', 'H', 'O'],
                'paren_open'     : [NotImplemented],
                'paren_close'    : [NotImplemented],
                'whitespace'     : [' '],
                'meta': {
                    'conseq': '|-',
                    'non-conseq': '|/-',
                },
            },
        }
    }
}
_['polish']['html'] = deepcopy(_['polish']['ascii'])
_['polish']['html'].update({
    'name': 'polish.html',
    'encoding': 'html',
    'formats': {'subscript': '<sub>{0}</sub>'},
})
_['polish']['unicode'] = _['polish']['ascii']
_.update({
    'standard': {
        'ascii': {
            'name'     : 'standard.ascii',
            'notation' : 'standard',
            'encoding' : 'ascii',
            'formats': {
                'subscript': '{0}',
            },
            'strings': {
                'atomic' : ['A', 'B', 'C', 'D', 'E'],
                'operator' : {
                    'Assertion'              :  '*',
                    'Negation'               :  '~',
                    'Conjunction'            :  '&',
                    'Disjunction'            :  'V',
                    'Material Conditional'   :  '>',
                    'Material Biconditional' :  '<',
                    'Conditional'            :  '$',
                    'Biconditional'          :  '%',
                    'Possibility'            :  'P',
                    'Necessity'              :  'N',
                },
                'variable' : ['x', 'y', 'z', 'v'],
                'constant' : ['a', 'b', 'c', 'd'],
                'quantifier' : {
                    'Universal'   : 'L',
                    'Existential' : 'X',
                },
                'system_predicate'  : {
                    'Identity'  : '=',
                    'Existence' : 'E!',
                    'NegatedIdentity' : '!=',
                },
                'user_predicate'  : ['F', 'G', 'H', 'O'],
                'paren_open'      : ['('],
                'paren_close'     : [')'],
                'whitespace'      : [' '],
                'meta': {
                    'conseq': '|-',
                    'non-conseq': '|/-'
                },
            },
        },
        'unicode': {
            'name'    : 'standard.unicode',
            'notation': 'standard',
            'encoding': 'utf8',
            'renders': {
                # ['₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉'],
                'subscript': lambda sub: ''.join(chr(0x2080 + int(d)) for d in str(sub))
            },
            'strings': {
                'atomic'   : ['A', 'B', 'C', 'D', 'E'],
                'operator' : {
                    # 'Assertion'              : '°',
                    'Assertion'              : '○',
                    'Negation'               : '¬',
                    'Conjunction'            : '∧',
                    'Disjunction'            : '∨',
                    'Material Conditional'   : '⊃',
                    'Material Biconditional' : '≡',
                    'Conditional'            : '→',
                    'Biconditional'          : '↔',
                    'Possibility'            : '◇',
                    'Necessity'              : '◻',
                },
                'variable'   : ['x', 'y', 'z', 'v'],
                'constant'   : ['a', 'b', 'c', 'd'],
                'quantifier' : {
                    'Universal'   : '∀' ,
                    'Existential' : '∃' ,
                },
                'system_predicate'  : {
                    'Identity'  : '=',
                    'Existence' : 'E!',
                    'NegatedIdentity' : '≠',
                },
                'user_predicate'  : ['F', 'G', 'H', 'O'],
                'paren_open'      : ['('],
                'paren_close'     : [')'],
                'whitespace'      : [' '],
                'meta': {
                    'conseq': '⊢',
                    'nonconseq': '⊬',
                    # 'weak-assertion' : '»',
                },
            },
        },
        'html': {
            'name'    : 'standard.html',
            'notation': 'standard',
            'encoding': 'html',
            'formats' : {
                'subscript': '<sub>{0}</sub>',
            },
            'strings': {
                'atomic'   : ['A', 'B', 'C', 'D', 'E'],
                'operator' : {
                    # 'Assertion'              : '&deg;'   ,
                    'Assertion'              : '&#9675;' ,
                    'Negation'               : '&not;'   ,
                    'Conjunction'            : '&and;'   ,
                    'Disjunction'            : '&or;'    ,
                    'Material Conditional'   : '&sup;'   ,
                    'Material Biconditional' : '&equiv;' ,
                    'Conditional'            : '&rarr;'  ,
                    'Biconditional'          : '&harr;'  ,
                    'Possibility'            : '&#9671;' ,
                    'Necessity'              : '&#9723;' ,
                },
                'variable'   : ['x', 'y', 'z', 'v'],
                'constant'   : ['a', 'b', 'c', 'd'],
                'quantifier' : {
                    'Universal'   : '&forall;' ,
                    'Existential' : '&exist;'  ,
                },
                'system_predicate'  : {
                    'Identity'  : '=',
                    'Existence' : 'E!',
                    'NegatedIdentity' : '&ne;',
                },
                'user_predicate'  : ['F', 'G', 'H', 'O'],
                'paren_open'      : ['('],
                'paren_close'     : [')'],
                'whitespace'      : [' '],
                'meta': {
                    'conseq': '⊢',
                    'nonconseq': '⊬',
                },
            },
        }
    }
})
RenderSet._initbuiltin(_)
del(_)


# Aliases
Atomic = AtomicSentence
Predicated = PredicatedSentence
Operated = OperatedSentence
Quantified = QuantifiedSentence
