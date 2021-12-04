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
from abc import ABCMeta
from copy import deepcopy
from enum import Enum, EnumMeta, unique
from itertools import chain
from past.builtins import basestring
from types import DynamicClassAttribute, MappingProxyType
from typing import Callable, Dict, FrozenSet, Hashable, Iterable, Iterator, \
    Mapping, MutableMapping, NamedTuple, Sequence, Set, Tuple, Union, \
    cast, final
from utils import CacheNotationData, Decorators, UniqueList, \
    EmptySet, \
    cat, orepr

abstract = Decorators.abstract
lazyget = Decorators.lazyget
setonce = Decorators.setonce
nosetattr = Decorators.nosetattr
nochangeattr = Decorators.nochangeattr
cmperr = Decorators.cmperr
cmptype = Decorators.cmptype

flatiter = chain.from_iterable

def isreadonly(cls: type) -> bool:
    return (
        getattr(cls, '_clsinit', False) and
        getattr(cls, '_readonly', False)
    )

def raises(errcls = AttributeError) -> Callable:
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
    _readonly: bool
    _clsinit: bool
    __setattr__ = nosetattr(type.__setattr__, check = isreadonly)
    __delattr__ = raises(AttributeError)

class AbcMetaBase(ABCMeta):
    _readonly = bool
    _clsinit: bool
    __setattr__ = nosetattr(ABCMeta.__setattr__, check = isreadonly)
    __delattr__ = raises(AttributeError)

class EnumMetaBase(EnumMeta):

    _readonly: bool
    _clsinit: bool
    __delattr__ = raises(AttributeError)
    __setattr__ = nosetattr(EnumMeta.__setattr__, check = isreadonly)

    _keytypes: Tuple[type, ...] = (basestring,)
    _Index: Dict
    _Ordered: Sequence[Enum]
    _Set: FrozenSet[Enum]

    def __new__(cls, clsname, bases, attrs: MutableMapping, **kw):
        keytypes = attrs.get('_keytypes', EmptySet)
        if callable(keytypes):
            keytypes = keytypes()
            attrs.pop('_keytypes')
        keytypes = tuple(keytypes)
        for keytype in keytypes:
            if issubclass(keytype, (int, slice)):
                raise TypeError('Illegal keytype %s' % keytype)
        membersinit = attrs.get('_members_init', None)
        EnumCls = super().__new__(cls, clsname, bases, attrs, **kw)
        if keytypes:
            EnumCls._keytypes = keytypes
        names = EnumCls._member_names_
        if len(names):
            members = [EnumCls._member_map_[name] for name in names]
            if callable(membersinit):
                membersinit(EnumCls, members)
                EnumCls._members_init = None
            else:
                EnumCls._members_init(members)
            index = {}
            for i, member in enumerate(members):
                next = members[i + 1] if i < len(members) - 1 else None
                index.update({
                    k: (member, i, next) for k in
                    EnumCls._member_keys(member)
                })
            EnumCls._Index = MappingProxyType(index)
            EnumCls._Ordered = tuple(members)
            EnumCls._Set = frozenset(members)
        return EnumCls

    def _member_keys(cls, member: Enum) -> Iterable[Hashable]:
        return EmptySet

    def _members_init(cls, members: Sequence[Enum]):
        pass

    def get(cls, key, default = None) -> Enum:
        try:
            return cls[key]
        except KeyError:
            return default

    def index(cls, member: Enum) -> int:
        return cls._Index[member.name][1]

    def __getitem__(cls, key) -> Enum:
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

    def __call__(cls, *args, **kw) -> Enum:
        if len(args) == 1 and isinstance(args[0], cls._keytypes):
            key, = args
            try:
                return cls[key]
            except KeyError:
                pass
        return super().__call__(*args, **kw)

class EnumBase(Enum, metaclass = EnumMetaBase):

    __delattr__ = raises(AttributeError)
    __setattr__ = nosetattr(Enum.__setattr__, check = isreadonly, cls = True)

class AbstractLexType(EnumBase, metaclass = EnumMetaBase):
    rank    : int
    cls     : type
    generic : type
    role    : str
    maxi    : Union[int, None]

class LexEnumMeta(EnumMetaBase):

    @DynamicClassAttribute
    def TYPE(cls) -> AbstractLexType:
        return LexType[cls.__name__]

class LexItemMeta(MetaBase):

    _cache = {}
    _iscache = True

    @DynamicClassAttribute
    def TYPE(cls) -> AbstractLexType:
        return LexType[cls.__name__]

    def __new__(cls, clsname, bases, attrs: MutableMapping, **kw):
        identattr = 'IdentType'
        identtype = attrs.get(identattr, None)
        # if 'IdentType' in attrs:
        #     print('IdentType', attrs['IdentType'], clsname)
        ItemCls = super().__new__(cls, clsname, bases, attrs, **kw)
        if identtype is None:
            oldval = getattr(ItemCls, identattr, None)
            spectype = ItemCls.SpecType
            identtype = tuple[str, spectype]
            setattr(ItemCls, identattr, identtype)
            print(clsname)
            print('  ', oldval)
            print('    ', identtype)
            print('    ', getattr(ItemCls, identattr))
        return ItemCls

    def __call__(cls, *spec, **kw):
        if len(spec) == 1 and isinstance(spec[0], cls):
            return spec[0]
        iscache = __class__._iscache
        if iscache:
            cache = __class__._cache
            clsname = cls.__name__
            try:
                return cache[clsname, spec]
            except KeyError:
                pass
        inst: AbstractLexical
        try:
            inst = super().__call__(*spec, **kw)
        except TypeError:
            if cls in LexType or len(spec) != 1:
                raise
            clsname, spec = spec[0]
            lextype: LexType = LexType[clsname]
            if not issubclass(lextype.cls, cls):
                raise TypeError('%s is not a role for %s' % (cls, lextype))
            if iscache:
                try:
                    return cache[clsname, spec]
                except KeyError:
                    pass
            inst = lextype(*spec, **kw)
        if iscache:
            try:
                inst = cache[inst.ident]
            except KeyError:
                cache[inst.ident] = inst
            cache[clsname, spec] = inst
        return inst

class AbstractLexical(object):
    """
    Lexical abstract base class.
    """

    SpecType = tuple
    SortType = tuple[int, ...]
    IdentType = tuple[str, SpecType]

    #: The LexType enum object.
    #:
    #: :type: LexType
    TYPE: AbstractLexType

    #: The arguments roughly needed to construct, given that we know the
    #: type, i.e. in intuitive order. A tuple, possibly nested, containing
    #: digits or strings.
    spec: SpecType

    #: Sorting identifier, to order tokens of the same type. Numbers only
    #: (no strings). This is also used in hashing, so equal objects should
    #: have equal sort_tuples. The first value must be the lexical rank of
    # the type.
    sort_tuple: SortType

    #: Equality identifier able to compare across types. A tuple, possibly
    #: nested, containing digits and possibly strings. The first should be
    #: the class name. Most naturally this would be followed by the spec.
    ident: IdentType

    hash: int

    @classmethod
    @abstract
    def first(cls): ...

    @abstract
    def next(self, **kw): ...

    @classmethod
    @abstract
    def gen(cls, n: int, first = None, **opts): ...

class Lexical(AbstractLexical):

    @property
    def TYPE(self):
        return LexType[self.__class__.__name__]
    TYPE: AbstractLexType

    @classmethod
    @abstract
    def first(cls) -> AbstractLexical: ...

    @abstract
    def next(self, **kw) -> AbstractLexical: ...

    @classmethod
    def gen(cls, n: int, first: AbstractLexical = None, **opts) -> Iterable[AbstractLexical]:
        if first is not None and first.TYPE != cls:
            raise TypeError(first.__class__, cls)
        for i in range(n):
            item = item.next(**opts) if i else (first or cls.first())
            if item:
                yield item

    @cmperr
    def __lt__(self, other: AbstractLexical):
        return self.TYPE < other.TYPE or self.sort_tuple < other.sort_tuple

    @cmperr
    def __le__(self, other: AbstractLexical):
        return self.TYPE <= other.TYPE or self.sort_tuple <= other.sort_tuple

    @cmperr
    def __gt__(self, other: AbstractLexical):
        return self.TYPE > other.TYPE or self.sort_tuple > other.sort_tuple

    @cmperr
    def __ge__(self, other: AbstractLexical):
        return self.TYPE >= other.TYPE or self.sort_tuple >= other.sort_tuple

    def __bool__(self):
        return True

    def __repr__(self):
        return _lexrepr(self)

class AbstractLexEnum(Lexical, EnumBase, metaclass = LexEnumMeta):
    spec: tuple[str]
    ident: tuple[str, tuple[str]]
    order: int
    label: str
    index: int

class LexEnum(AbstractLexEnum):
    """
    Base Lexical Enum class.
    """

    @classmethod
    def first(cls) -> AbstractLexEnum:
        """
        :implements: Lexical

        :rtype: LexEnum
        """
        return cls[0]

    def next(self, loop = False, **kw) -> AbstractLexEnum:
        """
        :implements: Lexical

        :rtype: LexEnum
        """
        cls = self.__class__
        i = self.index + 1
        if i == len(cls):
            if not loop:
                raise StopIteration
            i = 0
        return cls[i]

    def __init__(self, order, label, *_):
        self.spec = (self.name,)
        self.order, self.label = order, label
        self.sort_tuple = (self.order,)
        self.ident = LexItem.ident.fget(self)
        self.hash = LexItem.hash.fget(self)
        super().__init__()

    def __hash__(self):
        return self.hash

    def __eq__(self, other: Union[str, AbstractLexEnum]):
        if self is other:
            return True
        if isinstance(other, basestring):
            return other in (self.name, self.label)
        return EnumBase.__eq__(self, other)

    def __str__(self):
        return self.name

    def _keytypes() -> tuple[type, ...]:
        return (basestring, tuple)

    @staticmethod
    def _member_keys(member: AbstractLexEnum) -> tuple[Hashable, ...]:
        return (member.value, member.label, member.name, (member.name,))

    @classmethod
    def _members_init(cls, members: Sequence[AbstractLexEnum]):
        for member in members:
            member.index = members.index(member)

for annot, attr in (('spec', 'SpecType'), ('ident', 'IdentType')):
    setattr(LexEnum, attr, LexEnum.__annotations__[annot])
del(annot, attr)

class LexItem(Lexical, metaclass = LexItemMeta):
    """
    Base Lexical Item class.
    """

    __delattr__ = raises(AttributeError)
    __setattr__ = nochangeattr(Lexical.__setattr__, check = isreadonly, cls = True)

    @property
    @lazyget
    def ident(self) -> Lexical.IdentType:
        """
        :implements: Lexical
        """
        return (self.__class__.__name__, self.spec)

    @property
    @lazyget
    def hash(self) -> int:
        """
        :implements: Lexical
        """
        return hash((self.__class__.__name__, self.sort_tuple))

    def __hash__(self):
        return self.hash

    def __eq__(self, other: Lexical):
        return self is other or (
            self.TYPE == getattr(other, 'TYPE', None) and
            self.ident == other.ident
        )

    def __new__(cls, *args):
        if cls not in LexType:
            raise TypeError('Abstract type %s' % cls)
        return super().__new__(cls)

    def __str__(self):
        return _lexstr(self)

class SortBiCoords(NamedTuple):
    subscript : int
    index     : int
class BiCoords(NamedTuple):
    index     : int
    subscript : int
    Sorting = SortBiCoords
    def sorting(self) -> Tuple[int, ...]:
        return self.Sorting(self.subscript, self.index, *self[2:])
    first = (0, 0)
class PredSortCoords(NamedTuple):
    subscript : int
    index     : int
    arity     : int
class PredCoords(NamedTuple):
    index     : int
    subscript : int
    arity     : int
    Sorting = PredSortCoords
    sorting = BiCoords.sorting
    first = (0, 0, 1)
for cls in (BiCoords, PredCoords):
    cls.first = cls(*cls.first)
del(cls)

class CoordsItem(LexItem):

    SpecType = Coords = BiCoords
    SortType = Coords.Sorting

    @property
    def spec(self) -> SpecType:
        """
        :implements: Lexical
        """
        return self.coords

    @property
    @lazyget
    def sort_tuple(self) -> SortType:
        """
        :implements: Lexical
        """
        return self.scoords

    @classmethod
    def first(cls) -> LexItem:
        """
        :implements: Lexical

        :rtype: CoordsItem
        """
        return cls(cls.Coords.first)

    def next(self, **kw) -> LexItem:
        """
        :implements: Lexical

        :rtype: CoordsItem
        """
        idx, sub, *cargs = self.coords
        if idx < self.TYPE.maxi:
            idx += 1
        else:
            idx = 0
            sub += 1
        coords = self.Coords(idx, sub, *cargs)
        return self.__class__(coords)

    @property
    def coords(self) -> Coords:
        return self.__coords

    @property
    @lazyget
    def scoords(self) -> SortType:
        return self.coords.sorting()

    @property
    def index(self) -> int:
        return self.coords.index

    @property
    def subscript(self) -> int:
        return self.coords.subscript

    def __init__(self, *coords: Coords):
        if len(coords) == 1:
            coords, = coords
        index, sub, *_ = self.__coords = self.Coords(*coords)
        maxi = self.TYPE.maxi
        if not isinstance(index, int):
            raise TypeError(index, type(index), int)
        if not isinstance(sub, int):
            raise TypeError(sub, type(sub), int)
        if index > maxi:
            raise ValueError('%d > %d' % (index, maxi))
        if sub < 0:
            raise ValueError('%d < %d' % (sub, 0))

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

    SpecType = Coords = PredCoords
    SortType = Coords.Sorting

    spec: SpecType
    sort_tuple: SortType
    coords: Coords
    scoords: SortType

    NameType = Union[PredCoords, str]
    RefType = Union[Tuple[int, ...], str]
    NameClasses = (basestring, tuple)

    @property
    @lazyget
    def bicoords(self) -> BiCoords:
        return BiCoords(*self.spec[0:2])

    def next(self, **kw) -> CoordsItem:
        """
        :overrides: CoordsItem

        :rtype: Predicate
        """
        arity = self.arity
        if self.is_system:
            for pred in self.System:
                if pred > self and pred.arity == arity:
                    return pred

        return super().next(**kw)

    @property
    def arity(self) -> int:
        return self.coords.arity

    @property
    def name(self) -> NameType:
        return self.__name

    @property
    def is_system(self) -> bool:
        return self.index < 0

    @property
    @lazyget
    def refs(self) -> tuple[RefType, ...]:
        """
        The coords and other attributes, each of which uniquely identify this
        instance among other predicates. These are used to create hash indexes
        for retrieving predicates from predicate stores.

        .. _predicate-refs-list:

        - `spec` - A ``tuple`` with (index, subscript, arity).
        - `ident` - Includes class rank (``10``) plus `spec`.
        - `bicoords` - A ``tuple`` with (index, subscript).
        - `name` - For system predicates, e.g. `Identity`, but is legacy for
           user predicates.

        :type: tuple
        """
        return tuple({self.spec, self.ident, self.bicoords, self.name})

    System: EnumBase = EmptySet

    def __init__(self, *spec):
        if len(spec) == 1 and isinstance(spec[0], tuple):
            spec, = spec
        if len(spec) not in (3, 4):
            raise TypeError('need 3 or 4 elements, got %s' % len(spec))
        super().__init__(*spec[0:3])
        name = spec[3] if len(spec) == 4 else None
        if self.index < 0 and self.System:
            raise ValueError('`index` must be >= 0')
        arity = self.arity
        if not isinstance(arity, int):
            raise TypeError(arity, type(arity), int)
        if arity <= 0:
            raise ValueError('`arity` must be > 0')
        if name is not None:
            if name in self.System:
                raise ValueError('System predicate: %s' % name)
            if not isinstance(name, self.NameClasses):
                raise TypeError(name, type(name), self.NameClasses)
        else:
            name = self.spec
        self.__name = name

    def __str__(self):
        return self.name if self.is_system else super().__str__()

    def __call__(self, *spec) -> CoordsItem:
        """
        :rtype: Predicated
        """
        return Predicated(self, *spec)

class Parameter(CoordsItem):

    IdentType = tuple[str, BiCoords]

    is_constant: bool
    is_variable: bool

    def __init__(self, *coords: int):
        CoordsItem.__init__(self, *coords)

class Constant(Parameter):

    @property
    def is_constant(self) -> bool:
        """
        :implements: Parameter
        """
        return True

    @property
    def is_variable(self) -> bool:
        """
        :implements: Parameter
        """
        return False

class Variable(Parameter):

    @property
    def is_constant(self) -> bool:
        """
        :implements: Parameter
        """
        return False

    @property
    def is_variable(self) -> bool:
        """
        :implements: Parameter
        """
        return True

@unique
class Quantifier(LexEnum):

    Existential = (0, 'Existential')
    Universal   = (1, 'Universal')

    def __call__(self, *spec) -> LexItem:
        """
        :rtype: Quantified
        """
        return Quantified(self, *spec)

@unique
class Operator(LexEnum):

    arity: int

    Assertion             = (10,  'Assertion',    1)
    Negation              = (20,  'Negation',     1)
    Conjunction           = (30,  'Conjunction',  2)
    Disjunction           = (40,  'Disjunction',  2)
    MaterialConditional   = (50,  'Material Conditional',   2)
    MaterialBiconditional = (60,  'Material Biconditional', 2)
    Conditional           = (70,  'Conditional',   2)
    Biconditional         = (80,  'Biconditional', 2)
    Possibility           = (90,  'Possibility',   1)
    Necessity             = (100, 'Necessity',     1)

    def __init__(self, *value):
        self.arity = value[2]
        super().__init__(*value)

    def __call__(self, *spec) -> LexItem:
        """
        :rtype: Operated
        """
        return Operated(self, *spec)

class Sentence(LexItem):

    @property
    def operator(self) -> Union[Operator, None]:
        """
        The operator, if any.
        """
        return None

    @property
    def quantifier(self) -> Union[Quantifier, None]:
        """
        The quantifier, if any.
        """
        return None

    @property
    def predicate(self) -> Union[Predicate, None]:
        """
        The predicate, if any.
        """
        return None

    @property
    def is_atomic(self) -> bool:
        """
        Whether this is an atomic sentence.
        """
        return self.TYPE == Atomic

    @property
    def is_predicated(self) -> bool:
        """
        Whether this is a predicated sentence.
        """
        return self.TYPE == Predicated

    @property
    def is_quantified(self) -> bool:
        """
        Whether this a quantified sentence.
        """
        return self.TYPE == Quantified

    @property
    def is_operated(self) -> bool:
        """
        Whether this is an operated sentence.
        """
        return self.TYPE == Operated

    @property
    @lazyget
    def is_literal(self) -> bool:
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
    def is_negated(self) -> bool:
        """
        Whether this is a negated sentence.
        """
        return self.operator == Operator.Negation

    @property
    def predicates(self) -> Set[Predicate]:
        """
        Set of predicates, recursive.
        """
        return EmptySet

    @property
    def constants(self) -> Set[Constant]:
        """
        Set of constants, recursive.
        """
        return EmptySet

    @property
    def variables(self) -> Set[Variable]:
        """
        Set of variables, recursive.
        """
        return EmptySet

    @property
    def atomics(self) -> Set:
        """
        Set of atomic sentences, recursive.

        :type: set[Atomic]
        """
        return EmptySet

    @property
    def quantifiers(self) -> tuple[Quantifier, ...]:
        """
        Tuple of quantifiers, recursive.
        """
        return tuple()

    @property
    def operators(self) -> tuple[Operator, ...]:
        """
        Tuple of operators, recursive.
        """
        return tuple()

    def substitute(self, pnew: Parameter, pold: Parameter):
        """
        Recursively substitute ``pnew`` for all occurrences of ``pold``.
        May return self, or a new sentence.

        :rtype: Sentence
        """
        return self

    def negate(self):
        """
        Negate this sentence, returning the new sentence.

        :rtype: Operated
        """
        return Operated(Operator.Negation, (self,))

    def negative(self):
        """
        Either negate this sentence, or, if this is already a negated sentence
        return its negatum, i.e., "un-negate" the sentence.

        :rtype: Sentence
        """
        return self[0] if self.is_negated else self.negate()

    def asserted(self):
        """
        Apply the assertion operator to this sentence, and return the new sentence.

        :rtype: Sentence
        """
        return Operated(Operator.Assertion, (self,))

    def disjoin(self, rhs):
        """
        Apply disjunction.

        :param Sentence rhs: The right-hand sentence.
        :rtype: Operated
        """
        return Operated(Operator.Disjunction, (self, rhs))

    def conjoin(self, rhs):
        """
        Apply conjunction.

        :param Sentence rhs: The right-hand sentence.
        :rtype: Operated
        """
        return Operated(Operator.Conjunction, (self, rhs))

    def variable_occurs(self, v: Variable) -> bool:
        """
        Whether the variable occurs anywhere in the sentence (recursive).
        """
        return Variable(v) in self.variables

class Atomic(Sentence, CoordsItem):

    @property
    @lazyget
    def atomics(self) -> FrozenSet[Sentence]:
        """
        :overrides: Sentence

        :rtype: FrozenSet[Atomic]
        """
        return frozenset({self})

    def variable_occurs(self, v: Variable) -> bool:
        """
        :overrides: Sentence
        """
        return False

    def __init__(self, *coords: int):
        CoordsItem.__init__(self, *coords)

class Predicated(Sentence):

    SpecType = tuple[Predicate.SpecType, tuple[Parameter.IdentType, ...]]

    @property
    @lazyget
    def spec(self) -> SpecType:
        """
        :implements: Lexical
        """
        return (self.predicate.spec, tuple(p.ident for p in self))

    @property
    @lazyget
    def sort_tuple(self) -> Sentence.SortType:
        """
        :implements: Lexical
        """
        return tuple(flatiter(x.sort_tuple for x in (self.predicate, *self)))

    @classmethod
    def first(cls, predicate: Predicate = None) -> Sentence:
        """
        :overrides: CoordsItem

        :rtype: Predicated
        """
        pred = predicate or Predicate.first()
        c = Constant.first()
        params = tuple(c for i in range(pred.arity))
        return cls(pred, params)

    def next(self, **kw) -> Sentence:
        """
        :implements: Lexical

        :rtype: Predicated
        """
        pred = self.predicate.next(**kw)
        return self.__class__(pred, self.params)

    @property
    def predicate(self) -> Predicate:
        """
        :overrides: Sentence
        """
        return self.__pred

    @property
    @lazyget
    def predicates(self) -> FrozenSet[Predicate]:
        """
        :overrides: Sentence
        """
        return frozenset({self.predicate})

    @property
    @lazyget
    def constants(self) -> FrozenSet[Constant]:
        """
        :overrides: Sentence
        """
        return frozenset(p for p in self.paramset if p.is_constant)

    @property
    @lazyget
    def variables(self) -> FrozenSet[Variable]:
        """
        :overrides: Sentence
        """
        return frozenset(p for p in self.paramset if p.is_variable)

    def substitute(self, pnew: Parameter, pold: Parameter) -> Sentence:
        """
        :overrides: Sentence

        :rtype: Predicated
        """
        if pnew == pold or pold not in self:
            return self
        params = tuple(pnew if p == pold else p for p in self)
        return self.__class__(self.predicate, params)

    def variable_occurs(self, v: Variable) -> bool:
        """
        :overrides: Sentence
        """
        v = Variable(v)
        return v in self.paramset and v.is_variable

    @property
    def params(self) -> tuple[Parameter, ...]:
        """
        The sentence params.
        """
        return self.__params

    @property
    def arity(self) -> int:
        """
        The arity of the predicate.
        """
        return self.predicate.arity

    @property
    @lazyget
    def paramset(self) -> FrozenSet[Parameter]:
        return frozenset(self.params)

    def __iter__(self) -> Iterator[Parameter]:
        return iter(self.params)

    def __getitem__(self, index) -> Parameter:
        return self.params[index]

    def __len__(self):
        return len(self.params)

    def __contains__(self, p: Parameter):
        return p in self.paramset

    def __init__(self, pred, params: Union[Parameter, Iterable[Parameter]]):
        if isinstance(pred, basestring):
            self.__pred = Predicates.System(pred)
        else:
            self.__pred = Predicate(pred)
        if isinstance(params, Parameter):
            self.__params = (params,)
        else:
            self.__params = tuple(Parameter(param) for param in params)
        if len(self) != self.arity:
            raise TypeError(self.predicate, len(self), self.arity)

class Quantified(Sentence):

    SpecType = tuple[str, Variable.SpecType, Sentence.IdentType]

    @property
    @lazyget
    def spec(self) -> SpecType:
        """
        :implements: Lexical
        """
        return self.quantifier.spec + (self.variable.spec, self.sentence.ident)

    @property
    @lazyget
    def sort_tuple(self) -> Sentence.SortType:
        """
        :implements: Lexical
        """
        return tuple(flatiter(
            item.sort_tuple for item in
            (self.quantifier, self.variable, self.sentence)
        ))

    @classmethod
    def first(cls, quantifier: Quantifier = None) -> Sentence:
        """
        :implements: Lexical
        """
        q = Quantifier[quantifier or 0]
        v = Variable.first()
        pred: Predicate = Predicate.first()
        params = (v, *Constant.gen(pred.arity - 1))
        return cls(q, v, Predicated(pred, params))

    def next(self, **kw) -> Sentence:
        """
        :implements: Lexical
        """
        q = self.quantifier
        v = self.variable
        s: Sentence = self.sentence.next(**kw)
        if v not in s.variables:
            raise TypeError('%s no longer bound' % v)
        return self.__class__(q, v, s)

    @property
    def constants(self) -> FrozenSet[Sentence]:
        """
        :overrides: Sentence
        """
        return self.sentence.constants

    @property
    def variables(self) -> FrozenSet[Variable]:
        """
        :overrides: Sentence
        """
        return self.sentence.variables

    @property
    def atomics(self) -> FrozenSet[Atomic]:
        """
        :overrides: Sentence
        """
        return self.sentence.atomics

    @property
    def predicates(self) -> FrozenSet[Predicate]:
        """
        :overrides: Sentence
        """
        return self.sentence.predicates

    @property
    def operators(self) -> tuple[Operator, ...]:
        """
        :overrides: Sentence
        """
        return self.sentence.operators

    @property
    @lazyget
    def quantifiers(self) -> tuple[Quantifier, ...]:
        """
        :overrides: Sentence
        """
        return (self.quantifier, *(q for q in self.sentence.quantifiers))

    def substitute(self, pnew: Parameter, pold: Parameter) -> Sentence:
        """
        :overrides: Sentence

        :rtype: Quantified
        """
        if pnew == pold:
            return self
        r = self.sentence.substitute(pnew, pold)
        return self.__class__(self.quantifier, self.variable, r)

    def variable_occurs(self, v: Variable) -> bool:
        """
        :overrides: Sentence
        """
        v = Variable(v)
        return self.variable == v or self.sentence.variable_occurs(v)

    @property
    def quantifier(self) -> Quantifier:
        """
        The quantifier.
        """
        return self.__quantifier

    @property
    def variable(self) -> Variable:
        """
        The bound variable.
        """
        return self.__variable

    @property
    def sentence(self) -> Sentence:
        """
        The inner sentence.
        """
        return self.__sentence

    def unquantify(self, c: Constant) -> Sentence:
        """
        Instantiate the variable with a constant.
        """
        return self.sentence.substitute(Constant(c), self.variable)

    def __init__(self, q: Quantifier, v: Variable, s: Sentence):
        self.__quantifier = Quantifier(q)
        self.__variable = Variable(v)
        self.__sentence = Sentence(s)

class Operated(Sentence):

    SpecType = tuple[str, tuple[Sentence.IdentType, ...]]

    @property
    @lazyget
    def spec(self) -> SpecType:
        """
        :implements: Lexical
        """
        return self.operator.spec + (tuple(s.ident for s in self),)

    @property
    @lazyget
    def sort_tuple(self) -> Sentence.SortType:
        """
        :implements: Lexical
        """
        return tuple(flatiter(
            item.sort_tuple for item in
            (self.operator, *self)
        ))

    @classmethod
    def first(cls, operator: Operator = None) -> Sentence:
        """
        :implements: Lexical

        :rtype: Operated
        """
        operator = Operator[operator or 0]
        return cls(operator, Atomic.gen(operator.arity))

    def next(self, **kw) -> Sentence:
        """
        :implements: Lexical

        :rtype: Operated
        """
        operands = list(self.operands)
        operands[-1] = operands[-1].next(**kw)
        return self.__class__(self.operator, operands)

    @property
    def operator(self) -> Operator:
        """
        :overrides: Sentence
        """
        return self.__operator

    @property
    @lazyget
    def predicates(self) -> FrozenSet[Predicate]:
        """
        :overrides: Sentence
        """
        return frozenset(flatiter(s.predicates for s in self))

    @property
    @lazyget
    def constants(self) -> FrozenSet[Constant]:
        """
        :overrides: Sentence
        """
        return frozenset(flatiter(s.constants for s in self))

    @property
    @lazyget
    def variables(self) -> FrozenSet[Variable]:
        return frozenset(flatiter(s.variables for s in self))

    @property
    @lazyget
    def atomics(self) -> FrozenSet[Atomic]:
        """
        :overrides: Sentence
        """
        return frozenset(flatiter(s.atomics for s in self))

    @property
    @lazyget
    def quantifiers(self) -> tuple[Quantifier, ...]:
        """
        :overrides: Sentence
        """
        return tuple(flatiter(s.quantifiers for s in self))

    @property
    @lazyget
    def operators(self) -> tuple[Operator, ...]:
        """
        :overrides: Sentence
        """
        return (self.operator,) + tuple(flatiter(s.operators for s in self))

    def substitute(self, pnew: Parameter, pold: Parameter) -> Sentence:
        """
        :overrides: Sentence

        :rtype: Operated
        """
        if pnew == pold:
            return self
        operands = tuple(s.substitute(pnew, pold) for s in self)
        return self.__class__(self.operator, operands)

    def variable_occurs(self, v: Variable) -> bool:
        """
        :overrides: Sentence
        """
        for s in self:
            if s.variable_occurs(v):
                return True
        return False

    @property
    def operands(self) -> tuple[Sentence, ...]:
        """
        The operands.
        """
        return self.__operands

    @property
    def arity(self) -> int:
        """
        The arity of the operator.
        """
        return self.operator.arity

    @property
    def operand(self) -> Union[Sentence, None]:
        """
        The operand if only one, else None.
        """
        return self[0] if len(self) == 1 else None

    @property
    def negatum(self) -> Union[Sentence, None]:
        """
        The operand if is negated, else None.
        """
        return self[0] if self.is_negated else None

    @property
    def lhs(self) -> Sentence:
        """
        The first operand.
        """
        return self[0]

    @property
    def rhs(self) -> Sentence:
        """
        The last operand.
        """
        return self[-1]

    def __iter__(self) -> Iterator[Sentence]:
        return iter(self.operands)

    def __getitem__(self, index) -> Sentence:
        return self.operands[index]

    def __len__(self):
        return len(self.operands)

    def __contains__(self, s: Sentence):
        return s in self.operands

    def __init__(self, oper: Operator, operands: Union[Sentence, Iterable[Sentence]]):
        if isinstance(operands, Sentence):
            self.__operands = (operands,)
        else:
            self.__operands = tuple(Sentence(s) for s in operands)
        self.__operator = Operator(oper)
        if len(self) != self.arity:
            raise TypeError(self.operator, len(self), self.arity)

@unique
class LexType(AbstractLexType):

    Predicate   = (10,  Predicate,  Predicate,     3)
    Constant    = (20,  Constant,   Parameter,     3)
    Variable    = (30,  Variable,   Parameter,     3)
    Quantifier  = (33,  Quantifier, Quantifier, None)
    Operator    = (35,  Operator,   Operator,   None)
    Atomic      = (40,  Atomic,     Sentence,      4)
    Predicated  = (50,  Predicated, Sentence,   None)
    Quantified  = (60,  Quantified, Sentence,   None)
    Operated    = (70,  Operated,   Sentence,   None)

    def _keytypes() -> tuple[type, ...]:
        return (basestring, LexItemMeta, LexEnumMeta)

    def _members_init(cls, members: Iterable[AbstractLexType]):
        cls.byrank = MappingProxyType({
            member.rank: member
            for member in members
        })

    @staticmethod
    def _member_keys(member: AbstractLexType) -> tuple[Hashable, ...]:
        return (member.name, member.cls)

    def __init__(self, *value):
        super().__init__()
        self.rank, self.cls, self.generic, self.maxi = value
        self.role = self.generic.__name__
        self.hash = hash(self.__class__.__name__) + self.rank
 
    def __call__(self, *args, **kw) -> Lexical:
        return self.cls(*args, **kw)

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        cls = self.cls
        return (
            self is other or
            cls is other or
            cls is getattr(other, 'cls', None)
        )

    @cmperr
    def __lt__(self, other: AbstractLexType):
        return self.rank < other.rank

    @cmperr
    def __le__(self, other: AbstractLexType):
        return self.rank <= other.rank

    @cmperr
    def __gt__(self, other: AbstractLexType):
        return self.rank > other.rank

    @cmperr
    def __ge__(self, other: AbstractLexType):
        return self.rank >= other.rank

    def __repr__(self):
        return orepr(self,
            name = self.name,
            rank = self.rank,
            cls  = self.cls,
            role = self.role,
        )

class PredicatesMeta(MetaBase):

    def __getitem__(cls, key) -> Predicate: return Predicates.System[key]
    def __contains__(cls, key): return key in Predicates.System
    def __len__(cls): return len(Predicates.System)
    def __iter__(cls) -> Iterator[Predicate]: return iter(Predicates.System)

class Predicates(object, metaclass = PredicatesMeta):
    """
    Predicate store
    """

    ItemSpecType = Union[Predicate, PredCoords]

    @unique
    class System(EnumBase, metaclass = EnumMetaBase):

        Existence = (-2, 0, 1, 'Existence')
        Identity  = (-1, 0, 2, 'Identity')

        def __new__(self, *spec):
            pred = Predicate(spec)
            pred._value_ = pred
            setattr(Predicate, pred.name, pred)
            return pred

        @staticmethod
        def _member_keys(pred: Predicate) -> tuple[Hashable, ...]:
            return (*pred.refs, pred)

        def _keytypes():
            return (basestring, tuple, Predicate)

    def add(self, pred: ItemSpecType) -> Predicate:
        """
        Add a predicate.

        :param any pred: The predicate or spec to add.
        :return: The predicate
        :raises TypeError:
        :raises ValueError:
        """
        pred = Predicate(pred)
        check = self.get(pred.bicoords, pred)
        if check != pred:
            raise ValueError('%s != %s' % (pred, check))
        self.__idx.update({ref: pred for ref in pred.refs + (pred,)})
        self.__uset.add(pred)
        return pred

    def update(self, preds: Iterable[ItemSpecType]):
        for pred in preds:
            self.add(pred)

    def __init__(self, *specs: Iterable[ItemSpecType]):
        self.__idx = {}
        self.__uset = set()
        if len(specs) == 1 and isinstance(specs[0], (list, tuple)):
            if specs[0] and isinstance(specs[0][0], (list, tuple)):
                specs, = specs
        self.update(specs)

    def get(self, ref, default = None) -> Predicate:
        try:
            return self[ref]
        except KeyError:
            return default

    def __getitem__(self, ref) -> Predicate:
        try:
            return self.__idx[ref]
        except KeyError as err:
            try:
                return self.System[ref]
            except KeyError:
                raise err from None

    def __iter__(self) -> Iterator[Predicate]:
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

class ArgumentMeta(AbcMetaBase):
    def __call__(cls, *args, **kw):
        if len(args) == 1 and not len(kw) and isinstance(args[0], cls):
            return args[0]
        return super().__call__(*args, **kw)

class Argument(Sequence[Sentence], metaclass = ArgumentMeta):
    """
    Create an argument from sentence objects. For parsing strings into arguments,
    see ``Parser.argument``.
    """
    def __init__(self, conclusion: Sentence, premises: Iterable[Sentence] = None, title: str = None):
        self.__conclusion = Sentence(conclusion)
        self.__premises = tuple(Sentence(s) for s in premises or EmptySet)
        if title is not None and not isinstance(title, basestring):
            raise TypeError(title, type(title), str)
        self.title = title

    @property
    def conclusion(self) -> Sentence:
        return self.__conclusion

    @property
    def premises(self) -> tuple[Sentence, ...]:
        return self.__premises

    @property
    @lazyget
    def sentences(self) -> tuple[Sentence, ...]:
        return (self.conclusion, *self.premises)

    @property
    @lazyget
    def hash(self) -> int:
        return hash(tuple(self))

    def __len__(self):
        return len(self.sentences)

    def __iter__(self) -> Iterator[Sentence]:
        return iter(self.sentences)

    def __getitem__(self, key: Union[int, slice]) -> Sentence:
        return self.sentences[key]

    def _cmp(self, other) -> int:
        other = cast(Argument, other)
        cmp = bool(self.conclusion) - bool(other.conclusion)
        cmp = len(self) - len(other)
        if cmp: return cmp
        cmp = len(self.premises) - len(other.premises)
        if cmp: return cmp
        for a, b in zip(self, other):
            if a < b: return -1
            if a > b: return 1
        return cmp

    @cmptype
    def __lt__(self, other):
        return self._cmp(other) < 0

    @cmptype
    def __le__(self, other):
        return self._cmp(other) <= 0

    @cmptype
    def __gt__(self, other):
        return self._cmp(other) > 0

    @cmptype
    def __ge__(self, other):
        return self._cmp(other) >= 0

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        """
        Two arguments are considered equal just when their conclusions are equal, and their
        premises are equal (and in the same order). The title is not considered in equality.
        """
        return self is other or (
            isinstance(other, self.__class__) and
            self._cmp(other) == 0 and
            tuple(self) == tuple(other)
        )

    def __repr__(self):
        if self.title:
            desc = repr(self.title)
        else:
            desc = 'len(%d)' % len(self)
        return '<%s:%s>' % (self.__class__.__name__, desc)

Predicate.System = Predicates.System
for cls in (EnumBase, LexItem, Predicates, Argument):
    cls._readonly = cls._clsinit = True
del(cls)
# EnumBase._readonly = True
# EnumBase._clsinit = True

# LexItem._readonly = True
# LexItem._clsinit = True

# Predicates._clsinit = True
# Argument._clsinit = True



##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################

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

class RenderSet(CacheNotationData):

    default_fetch_name = 'ascii'

    def __init__(self, data: Mapping):
        if not isinstance(data, Mapping):
            raise TypeError(data, type(data), Mapping)
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

    def write(self, item: Lexical):
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

    @abstract
    def _write_operator(self, item): ...

    @abstract
    def _write_quantifier(self, item): ...

    @abstract
    def _write_constant(self, item): ...

    @abstract
    def _write_variable(self, item): ...

    @abstract
    def _write_predicate(self, item): ...

    @abstract
    def _write_sentence(self, item): ...

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

# def create_lexwriter(*args, **opts):
#     return LexWriter(*args, **opts)
def create_lexwriter(notn = None, enc = None, **opts) -> LexWriter:
    if not notn:
        notn = default_notation
    if notn not in notations:
        raise ValueError(notn)
    if not enc:
        enc = default_notn_encs[notn]
    if 'renderset' not in opts:
        opts['renderset'] = RenderSet.fetch(notn, enc)
    return lexwriter_classes[notn](**opts)
        
class BaseLexWriter(LexWriter):

    def __init__(self, renderset: RenderSet, **opts):
        super().__init__(**opts)
        self.renderset = renderset
        self.encoding = renderset.encoding

    # Base lex writer.
    def _strfor(self, *args, **kw) -> str:
        return self.renderset.strfor(*args, **kw)

    def _write_operator(self, item: Operator) -> str:
        return self._strfor(LexType.Operator, item)

    def _write_quantifier(self, item: Quantifier) -> str:
        return self._strfor(LexType.Quantifier, item)

    def _write_constant(self, item: Constant) -> str:
        return cat(
            self._strfor(LexType.Constant, item.index),
            self._write_subscript(item.subscript),
        )

    def _write_variable(self, item: Variable) -> str:
        return cat(
            self._strfor(LexType.Variable, item.index),
            self._write_subscript(item.subscript),
        )

    def _write_predicate(self, item: Predicate) -> str:
        # if item.is_system:
        #     typ, key = ('system_predicate', item)
        # else:
        #     typ, key = ('user_predicate', item.index)
        return cat(
            self._strfor((LexType.Predicate, item.is_system), item.index),
            self._write_subscript(item.subscript),
        )

    def _write_sentence(self, item: Sentence) -> str:
        if item.is_atomic:
            return self._write_atomic(item)
        if item.is_predicated:
            return self._write_predicated(item)
        if item.is_quantified:
            return self._write_quantified(item)
        if item.is_operated:
            return self._write_operated(item)
        raise TypeError('Unknown sentence type: {0}'.format(item))

    def _write_atomic(self, item: Atomic) -> str:
        return cat(
            self._strfor(LexType.Atomic, item.index),
            self._write_subscript(item.subscript)
        )

    def _write_quantified(self, item: Quantified) -> str:
        return cat(
            self._write_quantifier(item.quantifier),
            self._write_variable(item.variable),
            self._write_sentence(item.sentence),
        )

    def _write_predicated(self, item: Predicated) -> str:
        s = self._write_predicate(item.predicate)
        for param in item:
            s += self._write_parameter(param)
        return s

    def _write_subscript(self, s: int) -> str:
        if s == 0:
            return ''
        return self._strfor('subscript', s)

    @abstract
    def _write_operated(self, item: Operated): ...

class PolishLexWriter(BaseLexWriter):

    def _write_operated(self, item: Operated):
        return cat(
            self._write_operator(item.operator),
            *(self._write_sentence(s) for s in item),
        )

class StandardLexWriter(BaseLexWriter):

    opts = {'drop_parens': True}

    def write(self, item):
        if self.opts['drop_parens'] and isinstance(item, Operated):
            return self._write_operated(item, drop_parens = True)
        return super().write(item)

    def _write_predicated(self, item: Predicated):
        if len(item) < 2:
            return super()._write_predicated(item)
        # Infix notation for predicates of arity > 1
        pred = item.predicate
        # For Identity, add spaces (a = b instead of a=b)
        if pred == Predicates.System.Identity:
            ws = self._strfor('whitespace', 0)
        else:
            ws = ''
        return cat(
            self._write_parameter(item.params[0]),
            ws,
            self._write_predicate(pred),
            ws,
            *(self._write_parameter(param) for param in item.params[1:]),
        )

    def _write_operated(self, item: Operated, drop_parens = False):
        oper = item.operator
        arity = oper.arity
        if arity == 1:
            operand = item.operand
            if (oper == Operator.Negation and
                operand.predicate == Predicates.System.Identity):
                return self._write_negated_identity(item)
            else:
                return self._write_operator(oper) + self._write_sentence(operand)
        elif arity == 2:
            lhs, rhs = item
            return cat(
                self._strfor('paren_open', 0) if not drop_parens else '',
                self._strfor('whitespace', 0).join((
                    self._write_sentence(lhs),
                    self._write_operator(oper),
                    self._write_sentence(rhs),
                )),
                self._strfor('paren_close', 0) if not drop_parens else '',
            )
        raise NotImplementedError('arity %s' % arity)

    def _write_negated_identity(self, item: Operated):
        si: Predicated = item.operand
        params = si.params
        return cat(
            self._write_parameter(params[0]),
            self._strfor('whitespace', 0),
            self._strfor((LexType.Predicate, True), (item.operator, si.predicate)),
            self._strfor('whitespace', 0),
            self._write_parameter(params[1]),
        )

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
                (LexType.Predicate, True) : {
                    Predicates.System.Identity.index  : 'I',
                    Predicates.System.Existence.index : 'J',
                    (Operator.Negation, Predicates.System.Identity): NotImplemented,
                },
                (LexType.Predicate, False) : ('F', 'G', 'H', 'O'),
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
                (LexType.Predicate, True) : {
                    Predicates.System.Identity.index  : '=',
                    Predicates.System.Existence.index : 'E!',
                    (Operator.Negation, Predicates.System.Identity): '!=',
                },
                (LexType.Predicate, False) : ('F', 'G', 'H', 'O'),
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
                (LexType.Predicate, True) : {
                    Predicates.System.Identity.index  : '=',
                    Predicates.System.Existence.index : 'E!',
                    (Operator.Negation, Predicates.System.Identity): '≠',
                },
                (LexType.Predicate, False) : ('F', 'G', 'H', 'O'),
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
                (LexType.Predicate, True) : {
                    Predicates.System.Identity.index  : '=',
                    Predicates.System.Existence.index : 'E!',
                    (Operator.Negation, Predicates.System.Identity): '&ne;',
                },
                (LexType.Predicate, False) : ('F', 'G', 'H', 'O'),
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



del(isreadonly, raises)