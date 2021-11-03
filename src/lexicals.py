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
from copy import deepcopy
from errors import NotFoundError
from utils import CacheNotationData, cat, isstr, sortedbyval, typecheck, \
    condcheck, emptyset

lexwriter_classes = {
    # Values populated after class declarations below.
    'polish'   : None,
    'standard' : None,
}
notations = tuple(sorted(lexwriter_classes.keys()))
default_notation = notations[notations.index('polish')]
default_notn_encs = {
    notations[notations.index('polish')]   : 'ascii',
    notations[notations.index('standard')] : 'unicode',
}

def create_lexwriter(notn=None, enc=None, **opts):
    if not notn:
        notn = default_notation
    if notn not in notations:
        raise ValueError('Invalid notation: {}'.format(notn))
    if not enc:
        enc = default_notn_encs[notn]
    if 'renderset' not in opts:
        opts['renderset'] = RenderSet.fetch(notn, enc)
    return lexwriter_classes[notn](**opts)

# def get_system_predicate(ref):
#     """
#     Get a system predicate by name or coordinates. Example::

#         p1 = get_system_predicate('Identity')
#         p2 = get_system_predicate((-1, 0))
#         assert p1 == p2

#     :param any ref: The predicate name, or coordinates.
#     :return: The predicate instance.
#     :rtype: Predicate
#     :raises errors.NotFoundError: if the system predicate does not exist.
#     """
#     return Predicates.system.get(ref)

# def get_system_predicates():
#     """
#     Get all system predicate objects.

#     :rtype: tuple(Predicate)
#     """
#     return Predicates.system.predicates

# def is_system_predicate(ref):
#     """
#     Whether the reference attribute matches a system predicate.

#     :param any ref: The predicate reference attribute.
#     :rtype: bool
#     """
#     return Predicates.system.has(ref)

def operarity(oper):
    """
    Get the arity of an operator.

    Note: to get the arity of a predicate, use ``predicate.arity``.

    :param str oper: The operator.
    :return: The arity of the operator.
    :rtype: int
    :raises errors.NotFoundError: if the operator does not exist.
    """
    return Operated._operarity(oper)

def is_operator(obj):
    """
    Whether the object is an operator string.

    :param any obj: The object to check.
    :return: Whether it is an operator.
    :rtype: bool
    """
    return Operated._is_operator(obj)

def list_operators():
    """
    Get a list of all the operator strings.

    :rtype: list(str)
    """
    return Operated._list_operators()

def is_quantifier(obj):
    """
    Whether the object is an quantifier string.

    :param any obj: The object to check.
    :return: Whether it is an quantifier.
    :rtype: bool
    """
    return Quantified._is_quantifier(obj)

def list_quantifiers():
    """
    Get a list of all the quantifier strings.

    :rtype: list(str)
    """
    return Quantified._list_quantifiers()

class ItemMetaClass(type):

    @property
    def RANK(self):
        return LexicalItem.cls_rank(self)

    @property
    def MAXI(self):
        return LexicalItem.cls_maxi(self)

class LexicalItem(object, metaclass = ItemMetaClass):
    """
    Base Lexical Item class.
    """

    @staticmethod
    def cls_rank(cls):
        """
        Get the lexical rank for the given class.

        :param class cls: The class.
        :return: The lexical rank.
        :rtype: int
        :raises KeyError: for invalid class.
        """
        return __class__.__lexrank[cls]

    @staticmethod
    def rank_cls(rank):
        """
        Get the class for the given lexical rank.

        :param int rank: The lexical rank.
        :return: The class.
        :rtype: class
        :raises KeyError: for invalid rank.
        """
        return __class__.__lexrankrev[rank]

    @staticmethod
    def cls_maxi(cls):
        """
        Get the max index for the given class if applicable.

        :param class cls: The class.
        :return: The max index, or ``None``.
        :rtype: int
        :raises KeyError: for invalid class.
        """
        return __class__.__max_indexes[cls]

    @classmethod
    def first(cls):
        raise NotImplementedError()

    @classmethod
    def gen(cls, n, first = None, skipset = emptyset, **opts):
        if first and not isinstance(first, cls):
            raise TypeError('{} not a {}'.format(first.__class__, cls))
        for i in range(n):
            while True:
                item = item.next(**opts) if i else (first or cls.first())
                if item not in skipset:
                    break
            yield item

    def __init__(self):
        if self.RANK >= 400:
            raise TypeError('Cannot instantiate {}'.format(self.__class__))
        self.__ident = self.__hash = None

    @property
    def RANK(self):
        """
        Lexical rank.

        :type: int
        """
        return self.__class__.RANK

    @property
    def MAXI(self):
        """
        Max index, if applicable, else ``None``.

        :type: int
        """
        return self.__class__.MAXI

    @property
    def type(self):
        """
        The type (class name).

        :type: str
        """
        return self.__class__.__name__

    @property
    def ident(self):
        """
        Equality identifier.

        :type: tuple
        """
        if self.__ident == None:
            self.__ident = (self.RANK, self.sort_tuple)
        return self.__ident

    def next(self, **kw):
        raise NotImplementedError()

    @property
    def sort_tuple(self):
        # Sort tuple should always consist of numbers, or tuples with numbers.
        # This is also used in hashing, so equal objects should have equal hashes.
        raise NotImplementedError()

    def __lt__(self, other):
        return self.RANK < other.RANK or self.sort_tuple < other.sort_tuple

    def __le__(self, other):
        return self.RANK <= other.RANK or self.sort_tuple <= other.sort_tuple

    def __gt__(self, other):
        return self.RANK > other.RANK or self.sort_tuple > other.sort_tuple

    def __ge__(self, other):
        return self.RANK >= other.RANK or self.sort_tuple >= other.sort_tuple

    # Default equals and hash implementation is based on sort_tuple.
    #
    # https://docs.python.org/3/reference/datamodel.html#object.__hash__
    #
    # - If a class does not define __eq__ it should not define __hash__.
    #
    # - A class that overrides __eq__ and not __hash__ will have its
    #    __hash__ implicitly set to None.
    #

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.ident == other.ident
        )

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        if self.__hash == None:
            self.__hash = hash(self.sort_tuple)
        return self.__hash

    def __repr__(self):
        return self.ident.__repr__()

    @staticmethod
    def _initorder():
        # Canonical order for all LexicalItem classes.
        __class__.__lexrank = {
            Predicate: 10, Constant: 20, Variable: 30, Atomic: 40,
            Predicated: 50, Quantified: 60, Operated: 70,
            # Abstract classes have rank > 400.
            CoordsItem: 415, Parameter: 416, Sentence: 417, LexicalItem: 418,
        }
        # Reverse index from rank to class.
        __class__.__lexrankrev = {v: k for k, v in __class__.__lexrank.items()}
        # Max indexes for classes if applicable.
        __class__.__max_indexes = {cls: None for cls in __class__.__lexrank}
        __class__.__max_indexes.update({
            Predicate: 3, Constant: 3, Variable: 3, Atomic: 4,
        })
        # Self-destruct
        delattr(__class__, '_initorder')

class CoordsItem(LexicalItem):

    @classmethod
    def first(cls):
        return cls(0, 0)

    def __init__(self, *coords):
        super().__init__()
        if len(coords) == 1:
            coords, = coords
        typecheck(coords, (list, tuple), 'coords')
        index, subscript = coords
        maxi = self.MAXI
        sub = subscript
        typecheck(index, int, 'index')
        condcheck(index <= maxi, 'max `index` is {}, got {}'.format(maxi, index))
        typecheck(sub, int, 'subscript')
        condcheck(sub >= 0, 'min `subscript` is 0, got {}'.format(sub))
        self.__coords = (index, sub)

    @property
    def coords(self):
        return self.__coords

    @property
    def index(self):
        return self.__coords[0]

    @property
    def subscript(self):
        return self.__coords[1]

    @property
    def sort_tuple(self):
        return self.coords

    def next(self, **kw):
        if self.index < self.MAXI:
            coords = (self.index + 1, self.subscript)
        else:
            coords = (0, self.subscript + 1)
        return self.__class__(*coords)

class Parameter(CoordsItem):

    @property
    def is_constant(self):
        return isinstance(self, Constant)

    @property
    def is_variable(self):
        return isinstance(self, Variable)

class Constant(Parameter):
    pass

class Variable(Parameter):
    pass

class Predicate(CoordsItem):

    # @staticmethod
    # def create(*args):
    #     return __class__(*args)

    def __init__(self, *spec):
        """
        The parameters can be passed either expanded, or as a single
        ``list``/``tuple``. A valid spec consists of 3 integers in
        the order of `index`, `subscript`, `arity`, for example::

            Predicate(0, 0, 1)
            Predicate((0, 0, 1))

        An additional `name` parameter can be passed, which is used
        primarily for system predicates, e.g. `Identity`. This was
        designed to provide a convienent reference, but is likely to be
        removed once a decent alternative is developed::

            Predicate(1, 3, 2, 'MyLabel')
            Predicate((1, 3, 2, 'MyLabel'))
        """
        if len(spec) == 1 and isinstance(spec[0], (tuple, list)):
            spec, = spec
        if len(spec) not in (3, 4):
            raise TypeError(
                'need 3 or 4 elements/arguments, got {}'.format(len(spec))
            )
        index, subscript, arity = spec[0:3]
        super().__init__((index, subscript))
        sys = Predicates.system
        if sys and index < 0:
            raise ValueError('`index` must be >= 0')
        typecheck(arity, int, 'arity')
        condcheck(arity > 0, '`arity` must be > 0')
        self.__sort_tuple = (index, subscript, arity)
        self.__arity = arity
        if len(spec) == 4:
            name = spec[3]
            typecheck(name, (str, int, tuple), 'name')
            if sys and name in sys:
                raise ValueError(name)
        else:
            name = self.ident
        self.__name = name
        self.__refs = tuple({
            self.coords, self.sort_tuple, self.ident, self.name
        })

    @classmethod
    def first(cls):
        return cls.create((0, 0, 1))

    def next(self, **kw):
        arity = self.arity
        if self.is_system:
            for pred in Predicates.system:
                if pred > self and pred.arity == arity:
                    return pred
        if self.index < self.MAXI:
            ident = (self.index + 1, self.subscript, arity)
        else:
            ident = (0, self.subscript + 1, arity)
        return self.__class__.create(ident)

    @property
    def arity(self):
        return self.__arity

    @property
    def name(self):
        return self.__name

    @property
    def is_system(self):
        return self.index < 0

    @property
    def sort_tuple(self):
        # (index, subscript, arity)
        return self.__sort_tuple

    @property
    def refs(self):
        """
        The coords and other attributes, each of which uniquely identify this
        instance among other predicates. These are used to create hash indexes
        for retrieving predicates from predicate stores.

        .. _predicate-refs-list:

        - `coords` - A ``tuple`` with (index, subscript).
        - `sort_tuple` - A ``tuple`` with (index, subscript, arity).
        - `ident` - Includes class rank (``10``) plus `sort_tuple`.
        - `name` - For system predicates, e.g. `Identity`, but is legacy for
           user predicates.

        :type: tuple
        """
        return self.__refs


class PredsMetaClass(type):
    @property
    def system(cls):
        try:
            return cls.__system
        except AttributeError:
            pass

    @system.setter
    def system(cls, val):
        if cls.system:
            raise AttributeError()
        cls.__system = val

    def __delattr__(cls, name):
        if Predicates.system and cls == Predicates.system.__class__:
            raise AttributeError()
        super().__delattr__(name)

    def __setattr__(cls, name, value):
        if Predicates.system and cls == Predicates.system.__class__:
            if hasattr(cls, name):
                raise AttributeError()
        super().__setattr__(name, value)

class Predicates(object, metaclass = PredsMetaClass):
    """
    Predicate store
    """

    @staticmethod
    def _initsys():
        preds = tuple(
            Predicate(spec) for spec in (
                (-1, 0, 2, 'Identity'),
                (-2, 0, 1, 'Existence'),
            )
        )
        class System(Predicates, metaclass = PredsMetaClass):
            @property
            def predicates(self):
                return preds
        system = System(*preds)
        Predicates.system = system
        delattr(__class__, '_initsys')

    def __init__(self, *specs):
        if self == Predicates.system:
            raise TypeError()
        self.__idx = {}
        self.__uset = set()
        if Predicates.system:
            self.__idx.update(Predicates.system.__idx)
            self.__uset.update(Predicates.system.__uset)
        if specs:
            if len(specs) == 1 and isinstance(specs[0], (list, tuple)):
                if specs[0] and isinstance(specs[0][0], (list, tuple)):
                    specs, = specs
            for spec in specs:
                self.add(spec)

    def __iter__(self):
        return iter(self.__uset)

    def __getitem__(self, ref):
        return self.__idx[ref]

    def __contains__(self, ref):
        return ref in self.__idx

    def copy(self):
        """
        Make a copy of the predicates store.

        :return: The new predicate store instance.
        :rtype: Predicates
        """
        vocab = self.__class__()
        vocab.__uset = set(self.__uset)
        vocab.__idx = dict(self.__idx)
        return vocab

    def get(self, ref):
        """
        Get a predicate by coords, name, or other reference.

        See :ref:`Predicate.refs <predicate-refs-list>` for a description of the
        ``ref`` parameter.

        :param any ref: A lookup reference.
        :return: The predicate instance.
        :rtype: Predicate
        :raises errors.NotFoundError: when not found.
        """
        try:
            return self.__idx[ref]
        except KeyError:
            raise NotFoundError(ref)

    def has(self, ref):
        """
        Check whether a predicate exists for the given reference, See :ref:`Predicate.refs
        <predicate-refs-list>` for a description of the ``ref`` parameter.

        :param any ref: A lookup reference.
        :rtype: bool
        """
        return ref in self.__idx

    def add(self, pred):
        """
        Add a predicate.

        :param any pred: The predicate or spec to add.
        :return: The predicate
        :rtype: Predicate
        :raises TypeError:
        :raises ValueError:
        """
        if self == Predicates.system:
            raise AttributeError()
        if not isinstance(pred, Predicate):
            pred = Predicate(pred)
        if pred.coords in self:
            p = self[pred.coords]
            if pred != p:
                raise ValueError('{} != {}'.format(pred, p))
        self.__idx.update({ref: pred for ref in pred.refs + (pred,)})
        self.__uset.add(pred)
        return pred

    def clear(self):
        """
        Clear all predicates.

        :return: self
        :type: Predicates
        """
        if self == Predicates.system:
            raise AttributeError()
        self.__idx.clear()
        self.__uset.clear()
        return self

    def __delattr__(self, name):
        if self == Predicates.system:
            raise AttributeError()
        super().__delattr__(name)

    def __setattr__(self, name, value):
        if self == Predicates.system and hasattr(self, name):
            raise AttributeError()
        super().__setattr__(name, value)

class Sentence(LexicalItem):

    @property
    def operator(self):
        """
        The operator, if any.

        :type: str
        """
        return None

    @property
    def quantifier(self):
        """
        The quantifier, if any.

        :type: str
        """
        return None

    @property
    def predicate(self):
        """
        The predicate, if any.

        :type: Predicate
        """
        return None

    @property
    def is_atomic(self):
        """
        Whether this is an atomic sentence.

        :type: bool
        """
        return isinstance(self, Atomic)

    @property
    def is_predicated(self):
        """
        Whether this is a predicated sentence.

        :type: bool
        """
        return isinstance(self, Predicated)

    @property
    def is_quantified(self):
        """
        Whether this a quantified sentence.

        :type: bool
        """
        return isinstance(self, Quantified)

    @property
    def is_operated(self):
        """
        Whether this is an operated sentence.

        :type: bool
        """
        return isinstance(self, Operated)

    @property
    def is_literal(self):
        """
        Whether the sentence is a literal. Here a literal is either a
        predicated sentence, the negation of a predicated sentence,
        an atomic sentence, or the negation of an atomic sentence.

        :type: bool
        """
        return self.is_atomic or self.is_predicated or (
            self.is_negated and (
                self.operand.is_atomic or
                self.operand.is_predicated
            )
        )

    @property
    def is_negated(self):
        """
        Whether this is a negated sentence.

        :type: bool
        """
        return self.operator == 'Negation'

    def substitute(self, new_param, old_param):
        """
        Recursively substitute ``new_param`` for all occurrences of ``old_param``.
        May return self, or a new sentence.

        :rtype: Sentence
        """
        return self

    def negate(self):
        """
        Negate this sentence, returning the new sentence.

        :rtype: Operated
        """
        return Operated('Negation', self)

    def negative(self):
        """
        Either negate this sentence, or, if this is already a negated sentence
        return its negatum, i.e., "un-negate" the sentence.

        :rtype: Sentence
        """
        return self.negatum if self.is_negated else self.negate()

    def asserted(self):
        """
        Apply the assertion operator to this sentence, and return the new sentence.

        :rtype: Sentence
        """
        return Operated('Assertion', self)

    def disjoin(self, rhs):
        """
        TODO: doc
        """
        return Operated('Disjunction', (self, rhs))

    def conjoin(self, rhs):
        """
        TODO: doc
        """
        return Operated('Conjunction', (self, rhs))

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

    def variable_occurs(self, v):
        """
        Whether a variable occurs anywhere in the sentence (recursive).
        """
        return v in self.variables()

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

class Atomic(CoordsItem, Sentence):

    def __init__(self, *coords):
        CoordsItem.__init__(self, *coords)
        Sentence.__init__(self)

    def atomics(self):
        return {self}

    def variable_occurs(self, v):
        return False

class Predicated(Sentence):

    def __init__(self, pred, params):
        super().__init__()
        if isstr(pred):
            try:
                pred = Predicates.system[pred]
            except KeyError:
                raise NotFoundError(pred)
        typecheck(pred, Predicate, 'pred')
        typecheck(params, (list, tuple), 'params')
        condcheck(
            len(params) == pred.arity,
            "{0} is {1}-ary, got {2} params".format(
                pred.name, pred.arity, len(params)
            ),
            err = TypeError,
        )
        for param in params:
            typecheck(param, Parameter, 'param')
        self.__pred = pred
        self.__params = tuple(params)
        self.__paramset = set(params)
        self.__sort_tuple = None

    @classmethod
    def first(cls):
        pred = Predicate.first()
        c = Constant.first()
        params = tuple(c for i in range(pred.arity))
        return cls(pred, params)

    def next(self, **kw):
        pred = self.predicate.next(**kw)
        params = self.params
        return self.__class__(pred, params)

    @property
    def params(self):
        """
        The sentence params.

        :type: type(Parameter)
        """
        return self.__params

    @property
    def predicate(self):
        """
        :overrides: Sentence
        """
        return self.__pred

    @property
    def parameters(self):
        return self.params

    @property
    def sort_tuple(self):
        """
        :implements: LexicalItem
        """
        # Sort predicated sentences by their predicate, then by their parameters
        if self.__sort_tuple == None:
            # Lazy init
            self.__sort_tuple = self.predicate.sort_tuple + tuple(
                param.sort_tuple for param in self.params
            )
        return self.__sort_tuple

    def substitute(self, new_param, old_param):
        """
        :overrides: Sentence
        """
        params = tuple(
            new_param if param == old_param else param
            for param in self.params
        )
        return self.__class__(self.predicate, params)

    def constants(self):
        """
        :overrides: Sentence
        """
        return {param for param in self.__paramset if param.is_constant}

    def variables(self):
        """
        :overrides: Sentence
        """
        return {param for param in self.__paramset if param.is_variable}

    def variable_occurs(self, v):
        """
        :overrides: Sentence
        """
        return v in self.__paramset and v.is_variable

    def predicates(self):
        """
        :overrides: Sentence
        """
        return {self.predicate}

class Quantified(Sentence):

    def __init__(self, quantifier, variable, sentence):
        super().__init__()
        condcheck(
            is_quantifier(quantifier),
            "Invalid quantifier: '{0}'".format(quantifier),
        )
        typecheck(variable, Variable, 'variable')
        typecheck(sentence, Sentence, 'sentence')
        self.__quantifier = quantifier
        self.__variable = variable
        self.__sentence = sentence
        self.__sort_tuple = None

    @property
    def quantifier(self):
        return self.__quantifier

    @property
    def variable(self):
        return self.__variable

    @property
    def sentence(self):
        return self.__sentence

    @classmethod
    def first(cls):
        q = __class__.__quantlist[0]
        v = Variable.first()
        pred = Predicate.first()
        params = (v, *Constant.gen(pred.arity - 1))
        return cls(q, v, Predicated(pred, params))

    def next(self, **kw):
        q = self.quantifier
        v = self.variable
        s = self.sentence.next(**kw)
        if v not in s.variables():
            raise TypeError('{} no longer bound'.format(v))
        return self.__class__(q, v, s)

    @property
    def sort_tuple(self):
        # Sort quantified sentences first by their quantifier, using fixed
        # lexical order (below), then by their variable, followed by their
        # inner sentence.
        if self.__sort_tuple == None:
            self.__sort_tuple = (
                self.__lexorder[self.quantifier],
                self.variable.sort_tuple,
                self.sentence.sort_tuple,
            )
        return self.__sort_tuple

    def substitute(self, new_param, old_param):
        # Always return a new sentence.
        si = self.sentence
        r = si.substitute(new_param, old_param)
        return self.__class__(self.quantifier, self.variable, r)

    def constants(self):
        return self.sentence.constants()

    def variables(self):
        return self.sentence.variables()

    def variable_occurs(self, v):
        return self.variable == v or self.sentence.variable_occurs(v)

    def atomics(self):
        return self.sentence.atomics()

    def predicates(self):
        return self.sentence.predicates()

    def operators(self):
        return self.sentence.operators()

    def quantifiers(self):
        return [self.quantifier] + self.sentence.quantifiers()

    @staticmethod
    def _is_quantifier(obj):
        return obj in __class__.__lexorder

    @staticmethod
    def _list_quantifiers():
        return list(__class__.__quantlist)

    # Lexical sorting order.
    __lexorder = {'Existential': 0, 'Universal': 1}
    __quantlist = sortedbyval(__lexorder)

class Operated(Sentence):

    def __init__(self, operator, operands):
        super().__init__()
        self.__arity = arity = operarity(operator)
        if isinstance(operands, Sentence):
            operands = (operands,)
        typecheck(operands, (list, tuple), 'operands')
        condcheck(
            len(operands) == arity,
            "{0} is {1}-ary, got {2} operands".format(
                operator, arity, len(operands)
            ),
            err = TypeError,
        )
        for s in operands:
            typecheck(s, Sentence, 'operand')
        self.__operator = operator
        self.__operands = tuple(operands)
        if arity == 1:
            self.__operand, = operands
            if self.is_negated:
                self.__negatum = self.__operand
        elif arity == 2:
            self.__lhs, self.__rhs = operands
        # Lazy init
        self.__sort_tuple = None

    @classmethod
    def first(cls):
        oper = __class__.__operlist[0]
        a = Atomic.first()
        operands = tuple(a for i in range(operarity(oper)))
        return cls(oper, operands)

    def next(self, **kw):
        oper = self.operator
        operands = list(self.operands)
        operands[-1] = operands[-1].next(**kw)
        return self.__class__(oper, operands)

    @property
    def operator(self):
        return self.__operator

    @property
    def operands(self):
        return self.__operands

    @property
    def arity(self):
        return self.__arity

    @property
    def operand(self):
        return self.__operand

    @property
    def negatum(self):
        return self.__negatum

    @property
    def lhs(self):
        return self.__lhs

    @property
    def rhs(self):
        return self.__rhs

    @property
    def sort_tuple(self):
        # Sort operated sentences first by their operator, using fixed
        # lexical order (below), then by their operands.
        if self.__sort_tuple == None:
            # Lazy init
            self.__sort_tuple = (
                (self.__lexorder[self.operator],) +
                tuple(s.sort_tuple for s in self.operands)
            )
        return self.__sort_tuple

    def substitute(self, new_param, old_param):
        # Always return a new sentence
        operands = tuple(
            s.substitute(new_param, old_param) for s in self.operands
        )
        return self.__class__(self.operator, operands)

    def constants(self):
        c = set()
        for s in self.operands:
            c.update(s.constants())
        return c

    def variables(self):
        v = set()
        for s in self.operands:
            v.update(s.variables())
        return v

    def variable_occurs(self, v):
        for s in self.operands:
            if s.variable_occurs(v):
                return True
        return False

    def atomics(self):
        a = set()
        for s in self.operands:
            a.update(s.atomics())
        return a

    def predicates(self):
        p = set()
        for operand in self.operands:
            p.update(operand.predicates())
        return p

    def operators(self):
        ops = list()
        ops.append(self.operator)
        for s in self.operands:
            ops.extend(s.operators())
        return ops

    def quantifiers(self):
        qts = list()
        for s in self.operands:
            qts.extend(s.quantifiers())
        return qts

    @staticmethod
    def _is_operator(arg):
        return arg in __class__.__lexorder

    @staticmethod
    def _list_operators():
        return list(__class__.__operlist)

    @staticmethod
    def _operarity(operator):
        try:
            return __class__.__arities[operator]
        except KeyError:
            raise NotFoundError("Unknown operator '{0}'".format(operator))

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

class Argument(object):
    """
    Create an argument from sentence objects. For parsing strings into arguments,
    see ``Parser.argument``.
    """
    def __init__(self, conclusion, premises = None, title = None):
        typecheck(conclusion, Sentence, 'conclusion')
        premises = tuple(premises or ())
        for s in premises:
            typecheck(s, Sentence, 'premise')
        self.title = title
        self.__premises = premises
        self.__conclusion = conclusion

    @property
    def premises(self):
        return self.__premises

    @property
    def conclusion(self):
        return self.__conclusion

    def __repr__(self):
        return (self.premises, self.conclusion).__repr__()

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
            raise TypeError('Unknown lexical string type: {}'.format(item))
        if isinstance(item, Parameter):
            return self._write_parameter(item)
        if isinstance(item, Predicate):
            return self._write_predicate(item)
        if isinstance(item, Sentence):
            return self._write_sentence(item)
        raise TypeError('Unknown lexical type: {}'.format(item))

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
        if predicate in Predicates.system:
            typ, key = ('system_predicate', predicate.name)
        else:
            typ, key = ('user_predicate', predicate.index)
        return cat(
            self._strfor(typ, key),
            self._write_subscript(predicate.subscript),
        )

    def _write_sentence(self, sentence):
        if sentence.is_atomic:
            return self._write_atomic(sentence)
        if sentence.is_predicated:
            return self._write_predicated(sentence)
        if sentence.is_quantified:
            return self._write_quantified(sentence)
        if sentence.is_operated:
            return self._write_operated(sentence)
        raise TypeError('Unknown sentence type: {0}'.format(sentence))

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
        for param in sentence.params:
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
        if self.opts['drop_parens'] and isinstance(item, Operated):
            return self._write_operated(item, drop_parens = True)
        return super().write(item)

    def _write_predicated(self, sentence):
        # Infix notation for predicates of arity > 1
        pred = sentence.predicate
        if pred.arity < 2:
            return super()._write_predicated(sentence)
        # For Identity, add spaces (a = b instead of a=b)
        ws = self._strfor('whitespace', 0) if pred.name == 'Identity' else ''
        return cat(
            self._write_parameter(sentence.params[0]),
            ws,
            self._write_predicate(pred),
            ws,
            *(self._write_parameter(param) for param in sentence.params[1:]),
        )

    def _write_operated(self, sentence, drop_parens = False):
        oper = sentence.operator
        arity = operarity(oper)
        if arity == 1:
            operand = sentence.operand
            if (oper == 'Negation' and
                operand.is_predicated and
                operand.predicate.name == 'Identity'):
                return self._write_negated_identity(sentence)
            else:
                return self._write_operator(oper) + self._write_sentence(operand)
        elif arity == 2:
            return ''.join([
                self._strfor('paren_open', 0) if not drop_parens else '',
                self._strfor('whitespace', 0).join([
                    self._write_sentence(sentence.lhs),
                    self._write_operator(oper),
                    self._write_sentence(sentence.rhs),
                ]),
                self._strfor('paren_close', 0) if not drop_parens else '',
            ])
        raise NotImplementedError('{0}-ary operators not supported'.format(arity))

    def _write_negated_identity(self, sentence):
        params = sentence.operand.params
        return cat(
            self._write_parameter(params[0]),
            self._strfor('whitespace', 0),
            self._strfor('system_predicate', 'NegatedIdentity'),
            self._strfor('whitespace', 0),
            self._write_parameter(params[1]),
        )

class RenderSet(CacheNotationData):

    default_fetch_name = 'ascii'

    def __init__(self, data):
        typecheck(data, dict, 'data')
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

_builtin = {
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
_builtin['polish']['html'] = deepcopy(_builtin['polish']['ascii'])
_builtin['polish']['html'].update({
    'name': 'polish.html',
    'encoding': 'html',
    'formats': {'subscript': '<sub>{0}</sub>'},
})
_builtin['polish']['unicode'] = _builtin['polish']['ascii']
_builtin.update({
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


RenderSet._initcache(notations, _builtin)
del(_builtin)

# Aliases
AtomicSentence = Atomic
PredicatedSentence = Predicated
OperatedSentence = Operated
QuantifiedSentence = Quantified

Vocabulary = Vocab = Predicates

lexwriter_classes.update({
    'polish'   : PolishLexWriter,
    'standard' : StandardLexWriter,
})

# Initialize order.
LexicalItem._initorder()
# Init system predicates
# Predicate._initsys()
Predicates._initsys()