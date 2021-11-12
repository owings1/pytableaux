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
from enum import Enum, EnumMeta, unique
from errors import NotFoundError
from itertools import chain
from past.builtins import basestring
from types import DynamicClassAttribute, MappingProxyType
from utils import CacheNotationData, Decorators as decs, ReadOnlyDict, cat, isstr, \
    typecheck, condcheck, EmptySet, kwrepr, orepr
lazyget = decs.lazyget
setonce = decs.setonce
nosetattr = decs.nosetattr
flatiter = chain.from_iterable

def _isreadonly(cls):
    return (
        getattr(cls, '_clsinit', False) and
        getattr(cls, '_readonly', False)
    )
def _raise(errcls = AttributeError):
    def fraise(cls, *args, **kw):
        raise errcls('Unsupported operation for %s' % cls)
    return fraise
def _lexstr(item):
    try:
        return _syslw.write(item)
    except NameError:
        try:
            return str(item.ident)
        except AttributeError as e:
            try:
                return '%s(%s)' % (item.TYPE.name, e)
            except AttributeError as e:
                return '%s(%s)' % (item.__class__.__name__, e)
def _lexrepr(item):
    try:
        return '<%s: %s>' % (item.TYPE.role, str(item))
    except AttributeError:
        return '<%s: ?>' % item.__class__.__name__

class MetaBase(type):
    _readonly = True
    __setattr__ = nosetattr(type.__setattr__, check=_isreadonly)
    __delattr__ = _raise(AttributeError)

class EnumMetaBase(EnumMeta):

    _keytypes = (basestring,)

    def __new__(cls, clsname, bases, attrs, **kw):
        keytypes = attrs.get('_keytypes', None)
        if callable(keytypes):
            keytypes = keytypes()
            attrs.pop('_keytypes')
        membersinit = attrs.get('_members_init', None)
        enumcls = super().__new__(cls, clsname, bases, attrs, **kw)
        if keytypes:
            enumcls._keytypes = keytypes
        names = enumcls._member_names_
        if len(names):
            members = [enumcls._member_map_[name] for name in names]
            if callable(membersinit):
                membersinit(enumcls, members)
                enumcls._members_init = None
            else:
                enumcls._members_init(members)
            index = {}
            for i, member in enumerate(members):
                next = members[i + 1] if i < len(members) - 1 else None
                index.update({
                    k: (member, i, next) for k in
                    enumcls._member_keys(member)
                })
            enumcls._Index = MappingProxyType(index)
            enumcls._Ordered = tuple(members)
            enumcls._Set = frozenset(members)
            enumcls._clsinit = True
        return enumcls

    def _member_keys(cls, member):
        return EmptySet

    def _members_init(cls, members):
        pass

    def get(cls, key, dflt = None):
        return cls[key] if key in cls else dflt

    def index(cls, member):
        return cls._Index[member.name][1]

    def __getitem__(cls, key):
        if isinstance(key, cls):
            return key
        if isinstance(key, cls._keytypes):
            return cls._Index[key][0]
        if isinstance(key, (int, slice)):
            return cls._Ordered[key]
        return super().__getitem__(key)

    def __contains__(cls, key):
        if isinstance(key, cls._keytypes):
            return key in cls._Index
        return super().__contains__(key)

    __delattr__ = _raise(AttributeError)
    __setattr__ = nosetattr(EnumMeta.__setattr__, check=_isreadonly)

class EnumBase(Enum, metaclass = EnumMetaBase):

    __delattr__ = _raise(AttributeError)
    __setattr__ = nosetattr(Enum.__setattr__, check=_isreadonly, cls=True)

EnumBase._readonly = True

class LexEnumMeta(EnumMetaBase):

    @DynamicClassAttribute
    def TYPE(cls):
        return LexType[cls.__name__] 

    def __call__(cls, *args, **kw):
        if len(args) == 1 and isinstance(args[0], cls._keytypes) and args[0] in cls:
            return args[0]
        return super().__call__(*args, **kw)

class LexItemMeta(MetaBase):

    @DynamicClassAttribute
    def TYPE(cls):
        return LexType[cls.__name__]

    def __call__(cls, *args, **kw):
        if len(args) == 1 and isinstance(args[0], cls):
            return args[0]
        return super().__call__(*args, **kw)

class Lexical(object):
    """
    Common Lexical base class.
    """

    @property
    def TYPE(self):
        """
        The LexType enum object.

        :type: Enum
        """
        return LexType[self.__class__.__name__]

    #: The arguments roughly needed to construct, given that we know the
    #: type, i.e. in intuitive order. A tuple, possibly nested, containing
    #: digits or strings.
    #:
    #: :type: tuple
    spec = NotImplemented

    #: Sorting identifier, to order tokens of the same type. Numbers only
    #: (no strings). This is also used in hashing, so equal objects should
    #: have equal hashes.
    #:
    #: :type: tuple
    sort_tuple = NotImplemented

    #: Equality identifier able to compare across types. A tuple, possibly
    #: nested, containing digits and possibly strings. The first value must
    #: be the lexical rank of the type. Most naturally this would be followed
    #: by the spec.
    #:
    #: :type: tuple
    ident = NotImplemented

    #: :type: int
    hash = NotImplemented

    @classmethod
    def first(cls):
        raise NotImplementedError()

    def next(self, **kw):
        raise NotImplementedError()

    @classmethod
    def gen(cls, n, first = None, **opts):
        if first != None and first.TYPE != cls:
            raise TypeError(first.__class__, cls)
        for i in range(n):
            item = item.next(**opts) if i else (first or cls.first())
            if item:
                yield item

    def _sortcheck(sort_comparator):
        def compare(self, other):
            try:
                return sort_comparator(self, other)
            except AttributeError:
                raise TypeError('sort comparisons not available between %s and %s', (
                self.TYPE, other.__class__
            ))
        return compare

    @_sortcheck
    def __lt__(self, other):
        return self.TYPE < other.TYPE or self.sort_tuple < other.sort_tuple

    @_sortcheck
    def __le__(self, other):
        return self.TYPE <= other.TYPE or self.sort_tuple <= other.sort_tuple

    @_sortcheck
    def __gt__(self, other):
        return self.TYPE > other.TYPE or self.sort_tuple > other.sort_tuple

    @_sortcheck
    def __ge__(self, other):
        return self.TYPE >= other.TYPE or self.sort_tuple >= other.sort_tuple

    def __repr__(self):
        return _lexrepr(self)

class LexEnum(Lexical, EnumBase, metaclass = LexEnumMeta):
    """
    Base Lexical Enum class.

    - spec
    - sort_tuple
    - order
    - label
    - index
    - hash
    """
            
    @classmethod
    def first(cls):
        """
        :implements: Lexical
        """
        return cls[0]

    def next(self, loop = False, **kw):
        """
        :implements: Lexical
        """
        cls = self.__class__
        i = self.index + 1
        if i == len(cls):
            if not loop:
                return
            i = 0
        return cls[i]

    def __init__(self, order, label, *_):
        self.spec = self.name
        self.order, self.label = order, label
        self.sort_tuple = (self.order,)
        self.ident = LexItem.ident.fget(self)
        self.hash = LexItem.hash.fget(self)
        super().__init__()

    def __hash__(self): return self.hash

    def __eq__(self, other):
        if isstr(other):
            return other in (self.name, self.label)
        return EnumBase.__eq__(self, other)

    def __str__(self):
        return self.name

    @staticmethod
    def _member_keys(member):
        return (member.value, member.label, member.name)

    @classmethod
    def _members_init(cls, members):
        for member in members:
            member.index = members.index(member)

class LexItem(Lexical, metaclass = LexItemMeta):
    """
    Base Lexical Item class.
    """

    @property
    @lazyget
    def ident(self):
        """
        :implements: Lexical
        """
        return (self.__class__.__name__, self.spec)

    @property
    @lazyget
    def hash(self):
        """
        :implements: Lexical
        """
        return hash((self.__class__.__name__, self.sort_tuple))

    def __hash__(self): return self.hash

    def __eq__(self, other):
        return self.TYPE == getattr(other, 'TYPE', None) and self.ident == other.ident

    def __new__(cls, *args):
        if cls not in LexType: raise TypeError('Abstract type %s' % cls)
        return super().__new__(cls)

    def __str__(self):
        return _lexstr(self)

@unique
class Quantifier(LexEnum):
    Existential = (0, 'Existential')
    Universal   = (1, 'Universal')

    def __call__(self, *spec):
        return Quantified(self, *spec)

@unique
class Operator(LexEnum):
    Assertion               = (10,  'Assertion',    1)
    Negation                = (20,  'Negation',     1)
    Conjunction             = (30,  'Conjunction',  2)
    Disjunction             = (40,  'Disjunction',  2)
    MaterialConditional     = (50,  'Material Conditional',   2)
    MaterialBiconditional   = (60,  'Material Biconditional', 2)
    Conditional             = (70,  'Conditional',   2)
    Biconditional           = (80,  'Biconditional', 2)
    Possibility             = (90,  'Possibility',   1)
    Necessity               = (100, 'Necessity',     1)

    def __init__(self, *value):
        self.arity = value[2]
        super().__init__(*value)

    def __call__(self, *spec):
        return Operated(self, *spec)

class CoordsItem(LexItem):

    @classmethod
    def first(cls):
        """
        :implements: Lexical
        """
        return cls(0, 0)

    def next(self, **kw):
        """
        :implements: Lexical
        """
        if self.index < self.TYPE.maxi:
            coords = (self.index + 1, self.subscript)
        else:
            coords = (0, self.subscript + 1)
        return self.__class__(*coords)

    @property
    def coords(self):
        return self.__coords

    @property
    def index(self):
        return self.coords[0]

    @property
    def subscript(self):
        return self.coords[1]

    @property
    @lazyget
    def scoords(self):
        return (self.subscript, self.index)

    def __init__(self, *coords):
        if len(coords) == 1:
            coords, = coords
        index, subscript = self.__coords = coords
        maxi = self.TYPE.maxi
        sub = subscript
        typecheck(index, int, 'index')
        condcheck(index <= maxi, 'max `index` is {}, got {}'.format(maxi, index))
        typecheck(sub, int, 'subscript')
        condcheck(sub >= 0, 'min `subscript` is 0, got {}'.format(sub))

class Parameter(CoordsItem):

    @property
    def spec(self):
        """
        :implements: Lexical
        """
        return self.coords

    @property
    def sort_tuple(self):
        """
        :implements: Lexical
        """
        return self.scoords

    @property
    def is_constant(self):
        return self.TYPE == Constant

    @property
    def is_variable(self):
        return self.TYPE == Variable

    def __init__(self, *coords):
        CoordsItem.__init__(self, *coords)

class Constant(Parameter):
    pass

class Variable(Parameter):
    pass

class Predicate(CoordsItem):
    """
    Predicate

    The parameters can be passed either expanded, or as a single
    ``tuple``. A valid spec consists of 3 integers in
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
    @property
    @lazyget
    def spec(self):
        """
        :implements: Lexical
        """
        return self.coords + (self.arity,)

    @property
    @lazyget
    def sort_tuple(self):
        """
        :implements: Lexical
        """
        return self.scoords + (self.arity,)

    @classmethod
    def first(cls):
        """
        :implements: Lexical
        """
        return cls((0, 0, 1))

    def next(self, **kw):
        """
        :implements: Lexical
        """
        arity = self.arity
        if self.is_system:
            for pred in self.System:
                if pred > self and pred.arity == arity:
                    return pred
        if self.index < self.TYPE.maxi:
            spec = (self.index + 1, self.subscript, arity)
        else:
            spec = (0, self.subscript + 1, arity)
        return self.__class__(spec)

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
    @lazyget
    def refs(self):
        """
        The coords and other attributes, each of which uniquely identify this
        instance among other predicates. These are used to create hash indexes
        for retrieving predicates from predicate stores.

        .. _predicate-refs-list:

        - `coords` - A ``tuple`` with (index, subscript).
        - `spec` - A ``tuple`` with (index, subscript, arity).
        - `ident` - Includes class rank (``10``) plus `spec`.
        - `name` - For system predicates, e.g. `Identity`, but is legacy for
           user predicates.

        :type: tuple
        """
        return tuple({
            self.coords, self.spec, self.ident, self.name
        })

    System = EmptySet
    def __init__(self, *spec):
        if len(spec) == 1 and isinstance(spec[0], (tuple, list)):
            spec, = spec
        if len(spec) not in (3, 4):
            raise TypeError('need 3 or 4 elements, got %s' % len(spec))
        index, subscript, arity = spec[0:3]
        name = spec[3] if len(spec) == 4 else None
        super().__init__((index, subscript))
        if self.System and index < 0:
            raise ValueError('`index` must be >= 0')
        if not isinstance(arity, int):
            raise TypeError('`arity` %s' % type(arity))
        if arity <= 0:
            raise ValueError('`arity` must be > 0')
        self.__arity = arity
        if name != None:
            if name in self.System:
                raise ValueError('system predicate', name)
            if not isinstance(name, (basestring, tuple)):
                raise TypeError('`name` %s' % type(name))
        else:
            name = self.spec
        self.__name = name

    def __str__(self):
        if self.is_system:
            return self.name
        return super().__str__()

    def __call__(self, *spec):
        return Predicated(self, *spec)

class Sentence(LexItem):

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
        return self.TYPE == Atomic

    @property
    def is_predicated(self):
        """
        Whether this is a predicated sentence.

        :type: bool
        """
        return self.TYPE == Predicated

    @property
    def is_quantified(self):
        """
        Whether this a quantified sentence.

        :type: bool
        """
        return self.TYPE == Quantified

    @property
    def is_operated(self):
        """
        Whether this is an operated sentence.

        :type: bool
        """
        return self.TYPE == Operated

    @property
    @lazyget
    def is_literal(self):
        """
        Whether the sentence is a literal. Here a literal is either a
        predicated sentence, the negation of a predicated sentence,
        an atomic sentence, or the negation of an atomic sentence.

        :type: bool
        """
        return self.TYPE in (Atomic, Predicated) or (
            self.is_negated and self.operand.TYPE in (
                (Atomic, Predicated)
            )
        )

    @property
    def is_negated(self):
        """
        Whether this is a negated sentence.

        :type: bool
        """
        return self.operator == Operator.Negation

    @property
    def predicates(self):
        """
        Set of predicates, recursive.

        :rtype: set(Predicate)
        """
        return EmptySet

    @property
    def constants(self):
        """
        Set of constants, recursive.

        :rtype: set(Constant)
        """
        return EmptySet

    @property
    def variables(self):
        """
        Set of variables, recursive.

        :rtype: set(Variable)
        """
        return EmptySet

    @property
    def atomics(self):
        """
        Set of atomic sentences, recursive.

        :rtype: set(Atomic)
        """
        return EmptySet

    @property
    def quantifiers(self):
        """
        Tuple of quantifiers, recursive.

        :rtype: tuple(Quantifier)
        """
        return tuple()

    @property
    def operators(self):
        """
        Tuple of operators, recursive.

        :rtype: tuple(Operator)
        """
        return tuple()

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
        return Operated(Operator.Negation, self)

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
        return Operated(Operator.Assertion, self)

    def disjoin(self, rhs):
        """
        Apply disjunction.

        :rtype: Operated
        """
        return Operated(Operator.Disjunction, (self, rhs))

    def conjoin(self, rhs):
        """
        Apply conjunction.

        :rtype: Operated
        """
        return Operated(Operator.Conjunction, (self, rhs))

    def variable_occurs(self, v):
        """
        Whether a variable occurs anywhere in the sentence (recursive).

        :rtype: bool
        """
        return v in self.variables

class Atomic(Sentence, CoordsItem):

    @property
    def spec(self):
        """
        :implements: Lexical
        """
        return self.coords

    @property
    def sort_tuple(self):
        """
        :implements: Lexical
        """
        return self.scoords

    @property
    @lazyget
    def atomics(self):
        """
        :overrides: Sentence
        """
        return frozenset({self})

    def variable_occurs(self, v):
        """
        :overrides: Sentence
        """
        return False

    def __init__(self, *coords):
        CoordsItem.__init__(self, *coords)

class Predicated(Sentence):

    @property
    @lazyget
    def spec(self):
        """
        :implements: Lexical
        """
        return self.predicate.spec + tuple(
            param.spec for param in self
        )

    @property
    @lazyget
    def sort_tuple(self):
        """
        :implements: Lexical
        """
        return self.predicate.sort_tuple + tuple(
            param.sort_tuple for param in self
        )

    @classmethod
    def first(cls, predicate = None):
        """
        :overrides: CoordsItem
        """
        pred = predicate or Predicate.first()
        c = Constant.first()
        params = tuple(c for i in range(pred.arity))
        return cls(pred, params)

    def next(self, **kw):
        """
        :implements: Lexical
        """
        pred = self.predicate.next(**kw)
        params = self.params
        return self.__class__(pred, params)

    @property
    def predicate(self):
        """
        :overrides: Sentence
        """
        return self.__pred

    @property
    @lazyget
    def predicates(self):
        """
        :overrides: Sentence
        """
        return frozenset({self.predicate})

    @property
    @lazyget
    def constants(self):
        """
        :overrides: Sentence
        """
        return frozenset({param for param in self if param.is_constant})

    @property
    @lazyget
    def variables(self):
        """
        :overrides: Sentence
        """
        return frozenset({param for param in self if param.is_variable})

    def substitute(self, new_param, old_param):
        """
        :overrides: Sentence
        """
        params = tuple(
            new_param if param == old_param else param
            for param in self
        )
        return self.__class__(self.predicate, params)

    def variable_occurs(self, v):
        """
        :overrides: Sentence
        """
        return v in self.__paramset and v.is_variable

    @property
    def params(self):
        """
        The sentence params.

        :type: type(Parameter)
        """
        return self.__params

    @property
    @lazyget
    def paramset(self):
        return frozenset(self.params)

    def __iter__(self):
        return iter(self.params)

    def __getitem__(self, index):
        return self.params.__getitem__(index)

    def __len__(self):
        return self.predicate.arity

    def __contains__(self, p):
        return p in self.params

    def __init__(self, pred, params):
        if isstr(pred):
            try:
                pred = Predicates.System[pred]
            except KeyError:
                raise NotFoundError(pred)
        if not isinstance(pred, Predicate):
            raise TypeError(pred)
        if isinstance(params, Parameter):
            if pred.arity != 1:
                raise TypeError('arity %s predicate got 1 param' % pred.arity)
            params = (params,)
        else:
            if len(params) != pred.arity:
                raise TypeError('arity %s predicate got %s params' % (pred.arity, len(params)))
            for param in params:
                if not isinstance(param, Parameter):
                    raise TypeError('expecting a %s got a %s' % (Parameter, type(param)))
        self.__pred = pred
        self.__params = tuple(params)
        self.__paramset = frozenset(params)

class Quantified(Sentence):

    @property
    @lazyget
    def spec(self):
        return (
            self.quantifier,
            self.variable.spec,
            self.sentence.spec,
        )

    @property
    @lazyget
    def sort_tuple(self):
        return (
            self.quantifier.order,
            self.variable.sort_tuple,
            self.sentence.sort_tuple,
        )

    @property
    def quantifier(self):
        return self.__quantifier

    @classmethod
    def first(cls, quantifier = None):
        q = Quantifier[quantifier or Quantifier.first()]
        v = Variable.first()
        pred = Predicate.first()
        params = (v, *Constant.gen(pred.arity - 1))
        return cls(q, v, Predicated(pred, params))

    def next(self, **kw):
        q = self.quantifier
        v = self.variable
        s = self.sentence.next(**kw)
        if v not in s.variables:
            raise TypeError('%s no longer bound' % v)
        return self.__class__(q, v, s)

    @property
    def variable(self):
        return self.__variable

    @property
    def sentence(self):
        return self.__sentence

    @property
    def constants(self):
        return self.sentence.constants

    @property
    def variables(self):
        return self.sentence.variables

    @property
    def atomics(self):
        return self.sentence.atomics

    @property
    def predicates(self):
        return self.sentence.predicates

    @property
    def operators(self):
        return self.sentence.operators

    @property
    @lazyget
    def quantifiers(self):
        return (self.quantifier, *(q for q in self.sentence.quantifiers))

    def substitute(self, new_param, old_param):
        # Always return a new sentence.
        si = self.sentence
        r = si.substitute(new_param, old_param)
        return self.__class__(self.quantifier, self.variable, r)

    def variable_occurs(self, v):
        return self.variable == v or self.sentence.variable_occurs(v)

    def __init__(self, quantifier, variable, sentence):
        try:
            quantifier = Quantifier[quantifier]
        except KeyError:
            raise TypeError(quantifier) from None
        if not isinstance(variable, Variable):
            raise TypeError(variable)
        if not isinstance(sentence, Sentence):
            raise TypeError(sentence)
        self.__quantifier = quantifier
        self.__variable = variable
        self.__sentence = sentence

class Operated(Sentence):

    @property
    @lazyget
    def spec(self):
        return (
            (self.operator,) +
            tuple(s.spec for s in self)
        )

    @property
    @lazyget
    def sort_tuple(self):
        return (
            (self.operator.order,) +
            tuple(s.sort_tuple for s in self)
        )

    @classmethod
    def first(cls, operator = None):
        operator = Operator[operator or Operator.first()]
        operands = tuple(Atomic.gen(operator.arity))
        return cls(operator, operands)

    def next(self, **kw):
        operands = list(self.operands)
        operands[-1] = operands[-1].next(**kw)
        return self.__class__(self.operator, operands)

    @property
    def operator(self):
        return self.__operator

    @property
    def operands(self):
        return self.__operands

    @property
    def arity(self):
        return self.operator.arity

    @property
    def operand(self):
        return self[0] if len(self) == 1 else None

    @property
    def negatum(self):
        return self[0] if self.is_negated else None

    @property
    def lhs(self):
        return self[0] if len(self) == 2 else None

    @property
    def rhs(self):
        return self[1] if len(self) == 2 else None

    @property
    @lazyget
    def predicates(self):
        return frozenset(flatiter(s.predicates for s in self))

    @property
    @lazyget
    def constants(self):
        return frozenset(flatiter(s.constants for s in self))

    @property
    @lazyget
    def variables(self):
        return frozenset(flatiter(s.variables for s in self))

    @property
    @lazyget
    def atomics(self):
        return frozenset(flatiter(s.atomics for s in self))

    @property
    @lazyget
    def quantifiers(self):
        return tuple(flatiter(s.quantifiers for s in self))

    @property
    @lazyget
    def operators(self):
        return (self.operator,) + tuple(
            flatiter(s.operators for s in self)
        )

    def substitute(self, new_param, old_param):
        # Always return a new sentence
        operands = tuple(
            s.substitute(new_param, old_param) for s in self
        )
        return self.__class__(self.operator, operands)

    def variable_occurs(self, v):
        for s in self:
            if s.variable_occurs(v):
                return True
        return False

    def __init__(self, oper, operands):
        if isinstance(operands, Sentence):
            operands = (operands,)
        else:
            operands = tuple(operands)
        try:
            oper = Operator[oper]
        except KeyError:
            raise ValueError(oper)
        self.__operator = oper
        self.__operands = operands
        if len(operands) != oper.arity:
            raise TypeError(oper, operands, oper.arity)
        for s in operands:
            if not isinstance(s, Sentence):
                raise TypeError(s)

    def __iter__(self):
        return iter(self.operands)

    def __getitem__(self, index):
        return self.operands[index]

    def __len__(self):
        return self.arity

    def __contains__(self, s):
        return s in self.operands

@unique
class LexType(EnumBase, metaclass = EnumMetaBase):
    """
    - rank
    - cls
    - role
    - maxi
    """
    Predicate   = (10,  Predicate,  Predicate,     3)
    Constant    = (20,  Constant,   Parameter,     3)
    Variable    = (30,  Variable,   Parameter,     3)
    Quantifier  = (33,  Quantifier, Quantifier, None)
    Operator    = (35,  Operator,   Operator,   None)
    Atomic      = (40,  Atomic,     Sentence,      4)
    Predicated  = (50,  Predicated, Sentence,   None)
    Quantified  = (60,  Quantified, Sentence,   None)
    Operated    = (70,  Operated,   Sentence,   None)

    def _keytypes(): return (basestring, LexItemMeta, LexEnumMeta)

    def _members_init(cls, members):
        cls.byrank = MappingProxyType({
            member.rank: member for member in members
        })

    @staticmethod
    def _member_keys(member): return (member.name, member.cls)

    def __init__(self, *value):
        super().__init__()
        self.rank, self.cls, self.generic, self.maxi = value
        self.role = self.generic.__name__
        self.hash = hash(self.__class__.__name__) + self.rank
 
    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        cls = self.cls
        return cls is other or cls is getattr(other, 'cls', None)

    def _sortcheck(fcmp):
        opers = {'__lt__': '<', '__le__': '<=', '__gt__': '>', '__ge__': '>='}
        fname = fcmp.__name__
        def fcmpwrap(self, other):
            try:
                return fcmp(self, other)
            except (AttributeError, TypeError):
                raise TypeError('%s not supported between %s and %s' %
                    (opers.get(fname, fname),
                    self.__class__.__name__, other.__class__.__name__)
                ) from None
        return fcmpwrap

    @_sortcheck
    def __lt__(self, other): return self.rank < other.rank
    @_sortcheck
    def __le__(self, other): return self.rank <= other.rank
    @_sortcheck
    def __gt__(self, other): return self.rank > other.rank
    @_sortcheck
    def __ge__(self, other): return self.rank >= other.rank

    def __repr__(self):
        return kwrepr(
            Type=self.name, rank=self.rank, role=self.role
        )

class PredicatesMeta(MetaBase):

    def __getitem__(cls, key): return cls.System[key]
    def __contains__(cls, key): return key in cls.System
    def __len__(cls): return len(cls.System)
    def __iter__(cls): return iter(cls.System)

class Predicates(object, metaclass = PredicatesMeta):
    """
    Predicate store
    """

    @unique
    class System(EnumBase, metaclass = EnumMetaBase):
        pass
        Existence = (-2, 0, 1, 'Existence')
        Identity  = (-1, 0, 2, 'Identity')
        def __new__(self, *spec):
            pred = Predicate(spec)
            pred._value_ = pred
            setattr(Predicate, pred.name, pred)
            return pred
        @staticmethod
        def _member_keys(pred):
            return (*pred.refs, pred)
        def _keytypes(): return (basestring, tuple, Predicate)

    def add(self, pred):
        """
        Add a predicate.

        :param any pred: The predicate or spec to add.
        :return: The predicate
        :rtype: Predicate
        :raises TypeError:
        :raises ValueError:
        """
        if not isinstance(pred, Predicate):
            pred = Predicate(pred)
        check = self.get(pred.coords, pred)
        if check != pred:
            raise ValueError('%s != %s' % (pred, check))
        self.__idx.update({ref: pred for ref in pred.refs + (pred,)})
        self.__uset.add(pred)
        return pred

    def update(self, preds):
        for pred in preds: self.add(pred)
        return self

    def __init__(self, *specs):
        self.__idx = {}
        self.__uset = set()
        if len(specs) == 1 and isinstance(specs[0], (list, tuple)):
            if specs[0] and isinstance(specs[0][0], (list, tuple)):
                specs, = specs
        self.update(specs)

    def get(self, ref, dflt = None):
        return self[ref] if ref in self else dflt

    def __getitem__(self, ref):
        return self.__idx[ref] if ref in self.__idx else self.System[ref]

    def __iter__(self):
        return iter(self.__uset)

    def __len__(self):
        return len(self.__uset)

    def __contains__(self, ref):
        return ref in self.__idx or ref in self.System

    def __bool__(self):
        return True

    def __copy__(self):
        preds = self.__class__()
        preds.__uset = set(self.__uset)
        preds.__idx = dict(self.__idx)
        return preds

    def __repr__(self):
        return orepr(self, len=len(self))
Predicates._clsinit = True
Predicate.System = Predicates.System

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

# def create_lexwriter(*args, **opts):
#     return LexWriter(*args, **opts)
def create_lexwriter(notn=None, enc=None, **opts):
    if not notn:
        notn = default_notation
    if notn not in notations:
        raise ValueError(notn)
    if not enc:
        enc = default_notn_encs[notn]
    if 'renderset' not in opts:
        opts['renderset'] = RenderSet.fetch(notn, enc)
    return lexwriter_classes[notn](**opts)

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

class LexWriter(object, metaclass = MetaBase):

    opts = {}

    def __init__(self, **opts):
        self.opts = self.opts | opts

    @staticmethod
    def canwrite(item):
        try:
            return item.__class__.__name__ in LexType
        except AttributeError:
            return False

    def write(self, item):
        """
        Write a lexical item.
        """
        # NB: implementations should avoid calling this method, e.g.
        #     dropping parens will screw up since it is recursive.
        if isinstance(item, Operator):
            return self._write_operator(item)
        if isinstance(item, Quantifier):
            return self._write_quantifier(item)
        if isinstance(item, Parameter):
            return self._write_parameter(item)
        if isinstance(item, Predicate):
            return self._write_predicate(item)
        if isinstance(item, Sentence):
            return self._write_sentence(item)
        raise TypeError("Unknown lexical type '%s': %s" % (type(item), item))

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

    # def __init__(self, *args, **kw):
    #     for arg in args:
    #         if isinstance(arg, basestring):
    #             if arg in notations:
    #                 if 'notn' in kw:
    #                     raise TypeError('duplicate arg for kw notn', arg)
    #                 kw['notn'] = arg
    #             else:
    #                 raise TypeError('Unknown arg', arg)
    #         elif isinstance(arg, RenderSet):
    #             if 'renderset' in kw:
    #                 raise TypeError('duplicate arg for kw renderset', arg)
    #             kw['renderset'] = arg
    #         else:
    #             raise TypeError(type(arg), arg)
    #     notn = kw.pop('notn', default_notation)
    #     enc = kw.pop('enc', default_notn_encs[notn])
    #     if 'renderset' in kw:
    #         renderset = kw['renderset']
    #         if not isinstance(renderset, RenderSet):
    #             renderset = RenderSet.fetch(notn, enc)
    #     else:
    #         renderset = RenderSet.fetch(notn, enc)
    #     self.renderset = renderset
    #     self.encoding = renderset.encoding
    #     self.opts = self.opts | kw
    #     # return create_lexwriter(**kw)
            
class BaseLexWriter(LexWriter):

    def __init__(self, renderset, **opts):
        super().__init__(**opts)
        self.renderset = renderset
        self.encoding = renderset.encoding

    # Base lex writer.
    def _strfor(self, *args, **kw):
        return self.renderset.strfor(*args, **kw)

    def _write_operator(self, operator):
        return self._strfor(LexType.Operator, operator)

    def _write_quantifier(self, quantifier):
        return self._strfor(LexType.Quantifier, quantifier)

    def _write_constant(self, constant):
        return cat(
            self._strfor(LexType.Constant, constant.index),
            self._write_subscript(constant.subscript),
        )

    def _write_variable(self, variable):
        return cat(
            self._strfor(LexType.Variable, variable.index),
            self._write_subscript(variable.subscript),
        )

    def _write_predicate(self, predicate):
        if predicate.is_system:
            typ, key = ('system_predicate', predicate)
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
            self._strfor(LexType.Atomic, sentence.index),
            self._write_subscript(sentence.subscript)
        )

    def _write_quantified(self, sentence):
        return ''.join((
            self._write_quantifier(sentence.quantifier),
            self._write_variable(sentence.variable),
            self._write_sentence(sentence.sentence),
        ))

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

    opts = {'drop_parens': True}

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
        ws = self._strfor('whitespace', 0) if pred == Predicate.Identity else ''
        return cat(
            self._write_parameter(sentence.params[0]),
            ws,
            self._write_predicate(pred),
            ws,
            *(self._write_parameter(param) for param in sentence.params[1:]),
        )

    def _write_operated(self, sentence, drop_parens = False):
        oper = sentence.operator
        arity = oper.arity
        if arity == 1:
            operand = sentence.operand
            if (oper == Operator.Negation and
                operand.is_predicated and
                operand.predicate == Predicate.Identity):
                return self._write_negated_identity(sentence)
            else:
                return self._write_operator(oper) + self._write_sentence(operand)
        elif arity == 2:
            return ''.join((
                self._strfor('paren_open', 0) if not drop_parens else '',
                self._strfor('whitespace', 0).join((
                    self._write_sentence(sentence.lhs),
                    self._write_operator(oper),
                    self._write_sentence(sentence.rhs),
                )),
                self._strfor('paren_close', 0) if not drop_parens else '',
            ))
        raise NotImplementedError('{0}-ary operators not supported'.format(arity))

    def _write_negated_identity(self, sentence):
        params = sentence.operand.params
        return cat(
            self._write_parameter(params[0]),
            self._strfor('whitespace', 0),
            self._strfor('system_predicate', (Operator.Negation, Predicate.Identity)),
            self._strfor('whitespace', 0),
            self._write_parameter(params[1]),
        )

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
    def conclusion(self):
        return self.__conclusion

    @property
    def premises(self):
        return self.__premises

    def __len__(self):
        return bool(self.conclusion) + len(self.premises)

    def __iter__(self):
        return iter(s for s in (self.conclusion, *self.premises))

    def _cmp(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError('Cannot compare between %s and %s' % (
                self.__class__.__name__, other.__class__.__name__
            ))
        cmp = bool(self.conclusion) - bool(other.conclusion)
        cmp = len(self) - len(other)
        if cmp: return cmp
        cmp = len(self.premises) - len(other.premises)
        if cmp: return cmp
        for a, b in zip(self, other):
            if a < b: return -1
            if a > b: return 1
        return cmp

    def __lt__(self, other): return self._cmp(other) < 0
    def __le__(self, other): return self._cmp(other) <= 0
    def __gt__(self, other): return self._cmp(other) > 0
    def __ge__(self, other): return self._cmp(other) >= 0

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        """
        Two arguments are considered equal just when their conclusions are equal, and their
        premises are equal (and in the same order). The title is not considered in equality.
        """
        return isinstance(other, self.__class__) and (
            self._cmp(other) == 0 and tuple(self) == tuple(other)
        )

    def __repr__(self):
        if self.title:
            desc = repr(self.title)
        else:
            desc = 'len(%d)' % len(self)
        return '<%s:%s>' % (self.__class__.__name__, desc)

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
                LexType.Atomic   : ('a', 'b', 'c', 'd', 'e'),
                LexType.Operator : {
                    Operator.Assertion              : 'T',
                    Operator.Negation               : 'N',
                    Operator.Conjunction            : 'K',
                    Operator.Disjunction            : 'A',
                    Operator.MaterialConditional    : 'C',
                    Operator.MaterialBiconditional  : 'E',
                    Operator.Conditional            : 'U',
                    Operator.Biconditional          : 'B',
                    Operator.Possibility            : 'M',
                    Operator.Necessity              : 'L',
                },
                LexType.Variable   : ('x', 'y', 'z', 'v'),
                LexType.Constant   : ('m', 'n', 'o', 's'),
                LexType.Quantifier : {
                    Quantifier.Universal   : 'V',
                    Quantifier.Existential : 'S',
                },
                'system_predicate'  : {
                    Predicate.Identity  : 'I',
                    Predicate.Existence : 'J',
                    (Operator.Negation, Predicate.Identity) : NotImplemented,
                },
                'user_predicate' : ('F', 'G', 'H', 'O',),
                'paren_open'     : (NotImplemented,),
                'paren_close'    : (NotImplemented,),
                'whitespace'     : (' ',),
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
                LexType.Atomic : ('A', 'B', 'C', 'D', 'E'),
                LexType.Operator : {
                    Operator.Assertion              :  '*',
                    Operator.Negation               :  '~',
                    Operator.Conjunction            :  '&',
                    Operator.Disjunction            :  'V',
                    Operator.MaterialConditional    :  '>',
                    Operator.MaterialBiconditional  :  '<',
                    Operator.Conditional            :  '$',
                    Operator.Biconditional          :  '%',
                    Operator.Possibility            :  'P',
                    Operator.Necessity              :  'N',
                },
                LexType.Variable : ('x', 'y', 'z', 'v'),
                LexType.Constant : ('a', 'b', 'c', 'd'),
                LexType.Quantifier : {
                    Quantifier.Universal   : 'L',
                    Quantifier.Existential : 'X',
                },
                'system_predicate'  : {
                    Predicate.Identity  : '=',
                    Predicate.Existence : 'E!',
                    (Operator.Negation, Predicate.Identity) : '!=',
                },
                'user_predicate'  : ('F', 'G', 'H', 'O'),
                'paren_open'      : ('(',),
                'paren_close'     : (')',),
                'whitespace'      : (' ',),
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
                LexType.Atomic   : ('A', 'B', 'C', 'D', 'E'),
                LexType.Operator : {
                    # 'Assertion'              : '°',
                    Operator.Assertion              : '○',
                    Operator.Negation               : '¬',
                    Operator.Conjunction            : '∧',
                    Operator.Disjunction            : '∨',
                    Operator.MaterialConditional    : '⊃',
                    Operator.MaterialBiconditional  : '≡',
                    Operator.Conditional            : '→',
                    Operator.Biconditional          : '↔',
                    Operator.Possibility            : '◇',
                    Operator.Necessity              : '◻',
                },
                LexType.Variable   : ('x', 'y', 'z', 'v'),
                LexType.Constant   : ('a', 'b', 'c', 'd'),
                LexType.Quantifier : {
                    Quantifier.Universal   : '∀' ,
                    Quantifier.Existential : '∃' ,
                },
                'system_predicate'  : {
                    Predicate.Identity  : '=',
                    Predicate.Existence : 'E!',
                    (Operator.Negation, Predicate.Identity) : '≠',
                },
                'user_predicate'  : ('F', 'G', 'H', 'O'),
                'paren_open'      : ('(',),
                'paren_close'     : (')',),
                'whitespace'      : (' ',),
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
                LexType.Atomic   : ('A', 'B', 'C', 'D', 'E'),
                LexType.Operator : {
                    # 'Assertion'              : '&deg;'   ,
                    Operator.Assertion             : '&#9675;' ,
                    Operator.Negation              : '&not;'   ,
                    Operator.Conjunction           : '&and;'   ,
                    Operator.Disjunction           : '&or;'    ,
                    Operator.MaterialConditional   : '&sup;'   ,
                    Operator.MaterialBiconditional : '&equiv;' ,
                    Operator.Conditional           : '&rarr;'  ,
                    Operator.Biconditional         : '&harr;'  ,
                    Operator.Possibility           : '&#9671;' ,
                    Operator.Necessity             : '&#9723;' ,
                },
                LexType.Variable   : ('x', 'y', 'z', 'v'),
                LexType.Constant   : ('a', 'b', 'c', 'd'),
                LexType.Quantifier : {
                    Quantifier.Universal   : '&forall;' ,
                    Quantifier.Existential : '&exist;'  ,
                },
                'system_predicate'  : {
                    Predicate.Identity  : '=',
                    Predicate.Existence : 'E!',
                    (Operator.Negation, Predicate.Identity) : '&ne;',
                },
                'user_predicate'  : ('F', 'G', 'H', 'O'),
                'paren_open'      : ('(',),
                'paren_close'     : (')',),
                'whitespace'      : (' ',),
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

lexwriter_classes.update({
    'polish'   : PolishLexWriter,
    'standard' : StandardLexWriter,
})

_syslw = create_lexwriter()

LexItem._clsinit = True