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
from __future__ import annotations

import abc, enum
# from abc import ABCMeta
# from enum import Enum
from copy import deepcopy
from collections.abc import Callable, Collection, Generator, Hashable, \
    Iterable, Iterator, Mapping, MutableMapping, Sequence \

from itertools import chain
import operator as opr
from types import MappingProxyType
from typing import Any, ClassVar, Final, Literal, NamedTuple, Union, cast, final

from containers import UniqueList
from utils import CacheNotationData, Decorators, DequeCache, \
    BiCoords, TriCoords, \
    EmptySet, IndexType, IndexTypes, RetType, strtype, \
    cat, orepr, instcheck, subclscheck
from pprint import pp

ITEM_CACHE_SIZE = 10000

abstract = Decorators.abstract
lazyget = Decorators.lazyget
setonce = Decorators.setonce
cmperr = Decorators.cmperr
cmptypes = Decorators.cmptypes
cmptype = Decorators.cmptype
flatiter = chain.from_iterable

def isreadonly(cls: type) -> bool:
    return all(getattr(cls, attr, 0) for attr in ('_clsinit', '_readonly'))

def nosetattr(basecls, **kw):
    forigin = basecls.__setattr__
    opts = {'check': isreadonly, 'cls': None} | kw
    return Decorators.nosetattr(forigin, **opts)

def nochangeattr(basecls, **kw):
    opts = {'changeonly': True} | kw
    return nosetattr(basecls, **opts)

def raises(errcls = AttributeError) -> Callable:
    def fraise(cls, *args, **kw):
        raise errcls('Unsupported operation for %s' % cls)
    return fraise

def fixedreturn(val: Hashable) -> Callable:
    try: return fixedreturn.__dict__[val]
    except KeyError: pass
    def fnfixed(*_, **_k): return val
    return fixedreturn.__dict__.setdefault(val, fnfixed)

def fixedprop(val):
    try: return fixedprop.__dict__[val]
    except KeyError: pass
    prop = property(fixedreturn(val))
    return fixedprop.__dict__.setdefault(val, prop)
    
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
    except (AttributeError, NameError):
        return '<%s: ?>' % item.__class__.__name__


##############################################################

EnumIndexValueType = tuple[enum.Enum, int, enum.Enum]

class ABCMeta(abc.ABCMeta):
    """General-purpose base Metaclass for all (non-Enum) classes."""
    _readonly : bool
    _clsinit  : bool
    __delattr__ = raises(AttributeError)
    __setattr__ = nosetattr(type)

class EnumMeta(enum.EnumMeta):
    """General-purpose base Metaclass for all Enum classes."""
    _readonly : bool
    _clsinit  : bool
    __delattr__ = raises(AttributeError)
    __setattr__ = nosetattr(enum.EnumMeta)

    _ktypes  : tuple[type, ...]
    _Index   : MappingProxyType[Any, EnumIndexValueType]
    _Ordered : Sequence[enum.Enum]
    _Set     : frozenset[enum.Enum]

    @final
    @staticmethod
    def _init_keytypes(Enumcls):
        Enumcls: EnumMeta = Enumcls
        keytypes = Enumcls._keytypes()
        for keytype in keytypes:
            subclscheck(keytype, Hashable)
            if issubclass(keytype, IndexTypes):
                raise TypeError('Illegal keytype %s' % keytype)
        Enumcls._ktypes = tuple(UniqueList(keytypes))

    @final
    @staticmethod
    def _create_index(Enumcls, members: Iterable[enum.Enum]) -> dict:
        Enumcls: EnumMeta = Enumcls
        index = {}
        for i, member in enumerate(members):
            next = members[i + 1] if i < len(members) - 1 else None
            value = (member, i, next)
            keys = Enumcls._member_keys(member)
            index.update({key: value for key in keys})
        return index

    def __new__(cls, clsname, bases, attrs, **kw):
        Enumcls = super().__new__(cls, clsname, bases, attrs, **kw)
        names = Enumcls._member_names_
        if len(names):
            cls._init_keytypes(Enumcls)
            members = tuple(Enumcls._member_map_[name] for name in names)
            Enumcls._members_init(members)
            index = MappingProxyType(cls._create_index(Enumcls, members))
            Enumcls._Index = index
            Enumcls._Ordered = members
            Enumcls._Set = frozenset(members)
        Enumcls._after_init()
        return Enumcls

    # Class Init Hooks.
    def _keytypes(cls) -> Iterable[type]: return (strtype,)
    def _member_keys(cls, member: enum.Enum) -> Iterable[Hashable]:
        return EmptySet
    def _members_init(cls, members: Sequence[enum.Enum]): pass
    def _after_init(cls): pass

    def get(cls, key, default = None) -> enum.Enum:
        try: return cls[key]
        except (KeyError, IndexError): return default

    def index(cls, member: enum.Enum) -> int:
        return cls._Index[member.name][1]

    def __getitem__(cls, key) -> enum.Enum:
        if isinstance(key, cls):         return key
        if isinstance(key, cls._ktypes): return cls._Index[key][0]
        if isinstance(key, IndexTypes):  return cls._Ordered[key]
        return super().__getitem__(key)

    def __contains__(cls, key):
        if isinstance(key, cls._ktypes):
            return key in cls._Index
        return super().__contains__(key)

    def __call__(cls, *args, **kw) -> enum.Enum:
        if len(args) == 1 and isinstance(args[0], cls._ktypes):
            key, = args
            try: return cls[key]
            except KeyError: pass
        return super().__call__(*args, **kw)


class Enum(enum.Enum, metaclass = EnumMeta):
    """Generic base class for all Enum classes."""

    __delattr__ = raises(AttributeError)
    __setattr__ = nosetattr(enum.Enum, cls = True)

    # Propagate class hooks up to metaclass, so they can be implemented
    # in either the meta or concrete classes.

    @classmethod
    def _keytypes(cls: EnumMeta) -> Iterable[type]:
        return cls.__class__._keytypes(cls)

    @classmethod
    def _members_init(cls: EnumMeta, members: Sequence[enum.Enum]):
        cls.__class__._members_init(cls, members)

    @classmethod
    def _member_keys(cls: EnumMeta, member: enum.Enum) -> Iterable[Hashable]:
        return cls.__class__._member_keys(cls, member)

    @classmethod
    def _after_init(cls: EnumMeta):
        cls.__class__._after_init(cls)


##############################################################

class LexTypeAbc(Enum):
    """LexType Enum abstract base class."""
    rank    : int
    cls     : type
    generic : type
    role    : str
    maxi    : Union[int, None]
    hash    : int

    @classmethod
    def _keytypes(cls) -> Iterable[type]:
        return (*super()._keytypes(), LexicalItemMeta, LexicalEnumMeta)

    @classmethod
    def _members_init(cls, members):
        """Add _byrank index"""
        members: Iterable[LexTypeAbc] = members
        super()._members_init(members)
        cls._byrank = MappingProxyType({m.rank: m for m in members})

    @classmethod
    def _member_keys(cls, member) -> set:
        member: LexTypeAbc = member
        return set(super()._member_keys(member)) | {member.name, member.cls}

class LexicalEnumMeta(EnumMeta):
    """
    Metaclass for LexicalEnum classes (Operator, Quantifier).
    """
    def __new__(cls, clsname, bases, attrs: MutableMapping, **kw):
        if Lexical in bases:
            Lexical._copyattrs(attrs)
        Enumcls = super().__new__(cls, clsname, bases, attrs, **kw)
        return Enumcls

    # ----------------
    # Class Attributes
    # ----------------

    SpecType: ClassVar[type]
    SortType: ClassVar[type]
    IdentType: ClassVar[type]

    TYPE: ClassVar[LexTypeAbc]

class LexicalItemMeta(ABCMeta):
    """
    Metaclass for LexicalItem classes (Constant, Predicate, Sentence, etc.).
    """

    def __new__(cls, clsname, bases, attrs: dict, **kw):
        identtype = attrs.get('IdentType', None)
        if Lexical in bases:
            Lexical._copyattrs(attrs)
        ItemCls = super().__new__(cls, clsname, bases, attrs, **kw)
        if identtype is None:
            ItemCls.IdentType = tuple[str, ItemCls.SpecType]
        return ItemCls

    def __call__(cls, *spec, **kw):
        # Passthrough
        if len(spec) == 1 and isinstance(spec[0], cls): return spec[0]
        cache = LexicalItem.Cache
        clsname = cls.__name__
        # Try cache
        try: return cache[clsname, spec]
        except KeyError: pass
        # Construct
        try: inst: Lexical = super().__call__(*spec, **kw)
        except TypeError:
            if cls in LexType or len(spec) != 1: raise
            # Try arg as ident tuple (clsname, spec)
            clsname, spec = spec[0]
            lextypecls = LexType[clsname].cls
            subclscheck(lextypecls, cls)
            # Try cache
            try: return cache[clsname, spec]
            except KeyError: pass
            # Construct
            inst = lextypecls(*spec, **kw)
        # Try cache, store in cache.
        try: inst = cache[inst.ident]
        except KeyError: cache[inst.ident] = inst
        cache[clsname, spec] = inst
        return inst

    # ----------------
    # Class Attributes
    # ----------------

    SpecType: ClassVar[type]
    SortType: ClassVar[type]
    IdentType: ClassVar[type]

    TYPE: ClassVar[LexTypeAbc]

class Lexical:
    """
    Lexical abstract base class for both LexicalEnum and LexicalItem classes.
    """

    # -----------------------------------
    # General Methods & Class Attributes
    # -----------------------------------

    #: Type for attribute ``sort_tuple``
    SortType : Final[type] = tuple[int, ...]

    #: Type for attribute ``spec``
    SpecType  : ClassVar[type] = tuple

    #: Type for attribute ``ident``
    IdentType : ClassVar[type] = tuple[str, SpecType]

    # LexType instance populated below.
    TYPE: ClassVar[LexTypeAbc]

    @staticmethod
    @final
    def cmpitems(item, other) -> int:
        """Pairwise sorting comparison based on LexType and numeric sort tuple."""
        item: Lexical = item ; other: Lexical = other
        if item is other: return 0
        cmp = item.TYPE.rank - other.TYPE.rank
        if cmp: return cmp
        a, b = item.sort_tuple, other.sort_tuple
        for x, y in zip(a, b):
            cmp = x - y
            if cmp: return cmp
        return len(a) - len(b)

    def cmpwrap(oper):
        fname = '__%s__' % oper.__name__
        def f(self, other):
            return oper(Lexical.cmpitems(self, other), 0)
        f.__qualname__ = fname
        return f

    __lt__ = cmpwrap(opr.lt)
    __le__ = cmpwrap(opr.le)
    __gt__ = cmpwrap(opr.gt)
    __ge__ = cmpwrap(opr.ge)

    del(cmpwrap)

    @staticmethod
    @final
    def identitem(item) -> IdentType:
        """Build an ``ident`` tuple from the class name and initialization spec."""
        item: Lexical = item
        return (item.__class__.__name__, item.spec)

    @staticmethod
    @final
    def hashitem(item) -> int:
        """Compute a hash based on class name and sort tuple."""
        item: Lexical = item
        return hash((item.__class__.__name__, item.sort_tuple))

    @classmethod
    @final
    def gen(cls, n: int, first = None, **opts) -> Generator:
        """Generate items"""
        if first is not None: instcheck(first, cls)
        item: Lexical
        for i in range(n):
            item = item.next(**opts) if i else (first or cls.first())
            if item: yield item

    # -----------------
    # Default Methods
    # -----------------

    def __bool__(self): return True
    def __repr__(self): return _lexrepr(self)
    def __str__(self):  return self.name if isinstance(self, Enum) else _lexstr(self)

    # -------------------------------
    # Abstract instance attributes
    # -------------------------------

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

    #: The integer hash property.
    hash: int

    # ------------------
    # Abstract methods
    # -----------------

    @classmethod
    @abstract
    def first(cls): ...
    @abstract
    def next(self, **kw): ...

    @abstract
    def __eq__(self, other): ...
    @abstract
    def __hash__(self): ...

    # --------------
    # Metaclass Util
    # --------------

    @classmethod
    def _copyattrs(cls, attrs: dict):
        """Copy this class's contents to an uninitialized class dict."""
        attrs |= (
            (k, v) for k, v in cls.__dict__.items()
            if v in cls.__copyvals__ and k not in attrs
        )
        attrs['__annotations__'] |= (
            (k, v) for k, v in cls.__annotations__.items()
            if k not in attrs['__annotations__']
        )
    __copyvals__ = (
        gen, __repr__, __str__, __bool__,
        identitem, hashitem, cmpitems,
        __lt__, __le__, __gt__, __ge__,
    )

    __delattr__ = raises(AttributeError)
    __setattr__ = nosetattr(object, cls = LexicalItemMeta)

class LexicalEnum(Lexical, Enum, metaclass = LexicalEnumMeta):
    """
    Base Enum implementation of Lexical. For Quantifier and Operator classes.
    """
    # ----------------------
    # Lexical Implementation
    # ----------------------

    spec       : tuple[str]
    ident      : tuple[str, tuple[str]]
    sort_tuple : tuple[int]
    hash       : int

    def __eq__(self, other: Union[str, Lexical]):
        """Allow equality with the string name."""
        return self is other or other in self.strings

    def __hash__(self):
        return self.hash

    @classmethod
    def first(cls) -> Lexical: return cls[0]

    def next(self, loop = False, **kw) -> Lexical:
        cls = self.__class__
        i = self.index + 1
        if i == len(cls):
            if not loop: raise StopIteration
            i = 0
        return cls[i]

    # ---------------------------------------
    # Enum Attributes and Class Init Methods
    # ---------------------------------------

    #: The member name.
    name: str
    #: Label with spaces allowed.
    label: str
    #: Index of the member in the enum list, in source order, 0-based.
    index: int
    #: A number to signify order independenct of source or other constraints.
    order: int
    #: Name, label, or other strings unique to a member.
    strings: frozenset[str]

    @classmethod
    def _keytypes(cls) -> Iterable[type]:
        """Allow tuples as lookup keys for Enum __getitem__."""
        return (*super()._keytypes(), tuple)

    @classmethod
    def _member_keys(cls, member) -> set:
        """Index keys for Enum members lookups."""
        member: LexicalEnum = member
        return set(super()._member_keys(member)) | {
            member.value, member.label, member.name, (member.name,)
        }

    @classmethod
    def _members_init(cls, members):
        """Store the list index of each member."""
        super()._members_init(members)
        members: Sequence[LexicalEnum] = members
        for member in members:
            member.index = members.index(member)

    @classmethod
    def _after_init(cls):
        """Add class attributes after init, else EnumMeta complains."""
        super()._after_init()
        if cls is __class__:
            annot = cls.__annotations__
            cls.SpecType = annot['spec']
            cls.IdentType = annot['ident']

    def __init__(self, order, label, *_):
        self.spec = (self.name,)
        self.order, self.label = order, label
        self.sort_tuple = (self.order,)
        self.ident = Lexical.identitem(self)
        self.hash = Lexical.hashitem(self)
        self.strings = (self.name, self.label)
        super().__init__()

class LexicalItem(Lexical, metaclass = LexicalItemMeta):
    """
    Base Lexical Item class.
    """

    Cache: Final[DequeCache[Lexical]] = DequeCache(Lexical, ITEM_CACHE_SIZE)

    __delattr__ = raises(AttributeError)
    __setattr__ = nochangeattr(Lexical, cls = True)

    def __new__(cls, *args):
        if cls not in LexType: raise TypeError('Abstract type %s' % cls)
        return super().__new__(cls)

    # ----------------------------------------------------
    # Lexical Implementation

    @property
    @lazyget
    def ident(self) -> Lexical.IdentType: return Lexical.identitem(self)

    @property
    @lazyget
    def hash(self) -> int: return Lexical.hashitem(self)

    def __hash__(self):
        return self.hash

    def __eq__(self, other: Lexical):
        return self is other or (
            self.TYPE == LexType.get(other.__class__) and
            self.ident == other.ident
        )

##############################################################

class CoordsItem(LexicalItem):

    SpecType = Coords = BiCoords

    #: The item coordinates.
    coords: Coords

    #: The coords index.
    index: int

    #: The coords subscript.
    subscript: int

    spec: SpecType

    @property
    @lazyget
    def sort_tuple(self) -> LexicalItem.SortType: return self.scoords

    @property
    @lazyget
    def scoords(self) -> LexicalItem.SortType: return self.coords.sorting()

    @classmethod
    def first(cls) -> LexicalItem:
        """
        :rtype: CoordsItem
        """
        return cls(cls.Coords.first)

    def next(self, **kw) -> LexicalItem:
        """
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

    def __init__(self, *coords: Coords):
        if len(coords) == 1: coords, = coords
        self.coords = self.spec = self.Coords(*coords)
        for val in self.coords: instcheck(val, int)
        self.__dict__.update(self.coords._asdict())
        if self.index > self.TYPE.maxi:
            raise ValueError('%d > %d' % (self.index, self.TYPE.maxi))
        if self.subscript < 0:
            raise ValueError('%d < %d' % (self.subscript, 0))

##############################################################
##############################################################

class Quantifier(LexicalEnum):

    Existential = (0, 'Existential')
    Universal   = (1, 'Universal')

    def __call__(self, *spec) -> LexicalItem:
        return Quantified(self, *spec)

class Operator(LexicalEnum):

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

    def __call__(self, *spec) -> LexicalItem:
        return Operated(self, *spec)

    arity: int

    def __init__(self, *value):
        self.arity = value[2]
        super().__init__(*value)

##############################################################

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

    SpecType  = Coords = TriCoords
    RefType   = Union[tuple[int, ...], str]
    NameType  = Union[TriCoords, str]
    NameTypes = (strtype, tuple)

    spec       : SpecType
    sort_tuple : CoordsItem.SortType
    coords     : Coords
    scoords    : CoordsItem.SortType

    #: The coords arity.
    arity: int

    #: Whether this is a system predicate.
    is_system: bool

    #: The name or spec
    name: NameType

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
            pred: Predicate
            for pred in self.System:
                if pred > self and pred.arity == arity:
                    return pred
        return super().next(**kw)

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

    System: Collection[CoordsItem] = EmptySet

    def __init__(self, *spec):
        if len(spec) == 1 and isinstance(spec[0], tuple):
            spec, = spec
        if len(spec) not in (3, 4):
            raise TypeError('need 3 or 4 elements, got %s' % len(spec))
        super().__init__(*spec[0:3])
        self.is_system = self.index < 0
        if self.is_system and self.System:
            raise ValueError('`index` must be >= 0')
        arity = self.arity
        instcheck(arity, int)
        if arity <= 0:
            raise ValueError('`arity` must be > 0')
        name = spec[3] if len(spec) == 4 else None
        self.name = self.spec if name is None else name
        if name is not None:
            if name in self.System:
                raise ValueError('System predicate: %s' % name)
            instcheck(name, self.NameTypes)

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

    __init__ = CoordsItem.__init__
    # def __init__(self, *coords: int):
    #     CoordsItem.__init__(self, *coords)

class Constant(Parameter):

    is_constant: Literal[True]  = fixedprop(True)
    is_variable: Literal[False] = fixedprop(False)

class Variable(Parameter):

    is_constant: Literal[False] = fixedprop(False)
    is_variable: Literal[True]  = fixedprop(True)

##############################################################

class Sentence(LexicalItem):

    predicate  : Union[Predicate, None]
    quantifier : Union[Quantifier, None]
    operator   : Union[Operator, None]

    #: Whether this is an atomic sentence.
    is_atomic: bool = fixedprop(False)
    #: Whether this is a predicated sentence.
    is_predicated: bool = fixedprop(False)
    #: Whether this is a quantified sentence.
    is_quantified: bool = fixedprop(False)
    #: Whether this is an operated sentence.
    is_operated: bool = fixedprop(False)
    #: Whether this is a literal sentence. Here a literal is either a
    #: predicated sentence, the negation of a predicated sentence,
    #: an atomic sentence, or the negation of an atomic sentence.
    is_literal: bool = fixedprop(False)
    #: Whether this is an atomic sentence.
    is_negated: bool = fixedprop(False)

    #: Set of predicates, recursive.
    predicates: frozenset[Predicate] = fixedprop(EmptySet)
    #: Set of constants, recursive.
    constants: frozenset[Constant] = fixedprop(EmptySet)
    #: Set of variables, recursive.
    variables: frozenset[Variable] = fixedprop(EmptySet)
    #: Set of atomic sentences, recursive.
    atomics: frozenset = fixedprop(EmptySet)
    #: Tuple of quantifiers, recursive.
    quantifiers: tuple[Quantifier, ...] = fixedprop(tuple())
    #: Tuple of operators, recursive.
    operators: tuple[Operator, ...] = fixedprop(tuple())

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
        return v in self.variables

class Atomic(Sentence, CoordsItem):

    predicate  : Literal[None] = fixedprop(None)
    quantifier : Literal[None] = fixedprop(None)
    operator   : Literal[None] = fixedprop(None)

    is_atomic : Literal[True] = fixedprop(True)
    is_literal: Literal[True] = fixedprop(True)
    variable_occurs: Literal[False] = fixedreturn(False)

    @property
    @lazyget
    def atomics(self) -> frozenset[Sentence]: return frozenset({self})

    __init__ = CoordsItem.__init__

class Predicated(Sentence, Sequence[Parameter]):

    SpecType = tuple[Predicate.SpecType, tuple[Parameter.IdentType, ...]]

    #: The predicate.
    predicate: Predicate

    #: The parameters
    params: tuple[Parameter, ...]

    #: The set of parameters.
    paramset: frozenset[Parameter]

    #: The arity of the predicate.
    arity: int

    quantifier    : Literal[None] = fixedprop(None)
    operator      : Literal[None] = fixedprop(None)
    is_predicated : Literal[True] = fixedprop(True)
    is_literal    : Literal[True] = fixedprop(True)

    @property
    @lazyget
    def paramset(self) -> frozenset[Parameter]:
        return frozenset(self.params)

    @property
    @lazyget
    def spec(self) -> SpecType:
        return (self.predicate.spec, tuple(p.ident for p in self))

    @property
    @lazyget
    def sort_tuple(self) -> Sentence.SortType:
        items = (self.predicate, *self)
        return tuple(flatiter(it.sort_tuple for it in items))

    @classmethod
    def first(cls, predicate: Predicate = None) -> Sentence:
        """
        :rtype: Predicated
        """
        pred = predicate or Predicate.first()
        c = Constant.first()
        params = tuple(c for i in range(pred.arity))
        return cls(pred, params)

    def next(self, **kw) -> Sentence:
        """
        :rtype: Predicated
        """
        return self.__class__(self.predicate.next(**kw), self.params)

    @property
    @lazyget
    def predicates(self) -> frozenset[Predicate]:
        return frozenset({self.predicate})

    @property
    @lazyget
    def constants(self) -> frozenset[Constant]:
        return frozenset(p for p in self.paramset if p.is_constant)

    @property
    @lazyget
    def variables(self) -> frozenset[Variable]:
        return frozenset(p for p in self.paramset if p.is_variable)

    def substitute(self, pnew: Parameter, pold: Parameter) -> Sentence:
        """"
        :rtype: Predicated
        """
        if pnew == pold or pold not in self: return self
        params = (pnew if p == pold else p for p in self)
        return self.__class__(self.predicate, tuple(params))

    def __iter__(self) -> Iterator[Parameter]:
        return iter(self.params)

    def __getitem__(self, index: IndexType) -> Parameter:
        return self.params[index]

    def __len__(self):
        return len(self.params)

    def __contains__(self, p: Parameter):
        return p in self.paramset

    def __init__(self, pred, params: Union[Parameter, Iterable[Parameter]]):
        if isinstance(pred, strtype):
            self.predicate = Predicates.System(pred)
        else:
            self.predicate = Predicate(pred)
        if isinstance(params, Parameter):
            self.params = (params,)
        else:
            self.params = tuple(Parameter(param) for param in params)
        self.arity = self.predicate.arity
        if len(self) != self.arity:
            raise TypeError(self.predicate, len(self), self.arity)

QuantifiedItemsType = Union[Quantifier, Variable, Sentence]

class Quantified(Sentence, Sequence[QuantifiedItemsType]):

    SpecType = tuple[str, Variable.SpecType, Sentence.IdentType]
    ItemTypes = (Quantifier, Variable, Sentence)
    ItemsType = QuantifiedItemsType

    #: The quantifier
    quantifier: Quantifier

    #: The bound variable
    variable: Variable

    #: The inner sentence
    sentence: Sentence

    #: The items sequence: Quantifer, Variable, Sentence.
    items: tuple[ItemTypes]

    predicate     : Literal[None] = fixedprop(None)
    operator      : Literal[None] = fixedprop(None)
    is_quantified : Literal[True] = fixedprop(True)

    @property
    @lazyget
    def spec(self) -> SpecType:
        return self.quantifier.spec + (self.variable.spec, self.sentence.ident)

    @property
    @lazyget
    def sort_tuple(self) -> Sentence.SortType:
        return tuple(flatiter(item.sort_tuple for item in self))

    @classmethod
    def first(cls, quantifier: Quantifier = None) -> Sentence:
        q = Quantifier[quantifier or 0]
        v = Variable.first()
        pred: Predicate = Predicate.first()
        params = (v, *Constant.gen(pred.arity - 1))
        return cls(q, v, Predicated(pred, params))

    def next(self, **kw) -> Sentence:
        q, v, s = self
        s: Sentence = s.next(**kw)
        if v not in s.variables:
            raise TypeError('%s no longer bound' % v)
        return self.__class__(q, v, s)

    @property
    def constants(self) -> frozenset[Sentence]:
        return self.sentence.constants

    @property
    def variables(self) -> frozenset[Variable]:
        return self.sentence.variables

    @property
    def atomics(self) -> frozenset[Atomic]:
        return self.sentence.atomics

    @property
    def predicates(self) -> frozenset[Predicate]:
        return self.sentence.predicates

    @property
    def operators(self) -> tuple[Operator, ...]:
        return self.sentence.operators

    @property
    @lazyget
    def quantifiers(self) -> tuple[Quantifier, ...]:
        return (self.quantifier, *self.sentence.quantifiers)

    def substitute(self, pnew: Parameter, pold: Parameter) -> Sentence:
        """"
        :rtype: Quantified
        """
        if pnew == pold: return self
        q, v, s = self
        return self.__class__(q, v, s.substitute(pnew, pold))

    def variable_occurs(self, v: Variable) -> bool:
        return self.variable == v or self.sentence.variable_occurs(v)

    def unquantify(self, c: Constant) -> Sentence:
        """
        Instantiate the variable with a constant.
        """
        return self.sentence.substitute(Constant(c), self.variable)

    def __iter__(self) -> Iterator[ItemsType]:
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    @cmptypes(ItemTypes)
    def __contains__(self, item: ItemsType):
        return item in self.items

    def __getitem__(self, index: IndexType) -> ItemsType:
        return self.items[index]

    def __init__(self, q: Quantifier, v: Variable, s: Sentence):
        self.quantifier, self.variable, self.sentence = self.items = (
            Quantifier(q), Variable(v), Sentence(s)
        )

    def count(self, item: ItemsType) -> int:
        return int(item in self)

    def index(self, item: ItemsType) -> int:
        return self.items.index(item)

class Operated(Sentence, Sequence[Sentence]):

    SpecType = tuple[str, tuple[Sentence.IdentType, ...]]

    @property
    def arity(self) -> int: return self.operator.arity
    @property
    def operand(self) -> Union[Sentence, None]:
        return self[0] if len(self) == 1 else None
    @property
    def negatum(self) -> Union[Sentence, None]:
        return self[0] if self.is_negated else None
    @property
    def lhs(self) -> Sentence: return self[0]
    @property
    def rhs(self) -> Sentence: return self[-1]

    predicate  : Literal[True] = fixedprop(None)
    quantifier : Literal[True] = fixedprop(None)
    is_operated: Literal[True] = fixedprop(True)

    #: The operator
    operator: Operator
    #: The operands.
    operands: tuple[Sentence, ...]
    #: The first (left-most) operand.
    lhs: Sentence
    #: The last (right-most) operand.
    rhs: Sentence
    #: The operand if only one, else None.
    operand: Union[Sentence, None]
    #: The operand if is negated, else None.
    negatum: Union[Sentence, None]
    #: The arity of the operator.
    arity: int

    @property
    def is_negated(self) -> bool: return self.operator == Operator.Negation

    @property
    @lazyget
    def is_literal(self) -> bool:
        return self.is_negated and self[0].TYPE in (Atomic, Predicated)

    @property
    @lazyget
    def spec(self) -> SpecType:
        return self.operator.spec + (tuple(s.ident for s in self),)

    @property
    @lazyget
    def sort_tuple(self) -> Sentence.SortType:
        return tuple(flatiter(it.sort_tuple for it in (self.operator, *self)))

    @classmethod
    def first(cls, operator: Operator = None) -> Sentence:
        operator = Operator[operator or 0]
        operands = Atomic.gen(operator.arity)
        return cls(operator, tuple(operands))

    def next(self, **kw) -> Sentence:
        operands = list(self)
        operands[-1] = operands[-1].next(**kw)
        return self.__class__(self.operator, tuple(operands))

    @property
    @lazyget
    def predicates(self) -> frozenset[Predicate]:
        return frozenset(flatiter(s.predicates for s in self))

    @property
    @lazyget
    def constants(self) -> frozenset[Constant]:
        return frozenset(flatiter(s.constants for s in self))

    @property
    @lazyget
    def variables(self) -> frozenset[Variable]:
        return frozenset(flatiter(s.variables for s in self))

    @property
    @lazyget
    def atomics(self) -> frozenset[Atomic]:
        return frozenset(flatiter(s.atomics for s in self))

    @property
    @lazyget
    def quantifiers(self) -> tuple[Quantifier, ...]:
        return tuple(flatiter(s.quantifiers for s in self))

    @property
    @lazyget
    def operators(self) -> tuple[Operator, ...]:
        return (self.operator,) + tuple(flatiter(s.operators for s in self))

    def substitute(self, pnew: Parameter, pold: Parameter) -> Sentence:
        if pnew == pold: return self
        operands = (s.substitute(pnew, pold) for s in self)
        return self.__class__(self.operator, tuple(operands))

    def __iter__(self) -> Iterator[Sentence]:
        return iter(self.operands)

    def __getitem__(self, index: IndexType) -> Sentence:
        return self.operands[index]

    def __len__(self):
        return len(self.operands)

    def __contains__(self, s: Sentence):
        return s in self.operands

    def __init__(self, oper: Operator, operands: Union[Sentence, Iterable[Sentence]]):
        if isinstance(operands, Sentence):
            self.operands = (operands,)
        else:
            self.operands = tuple(Sentence(s) for s in operands)
        self.operator = Operator(oper)
        if len(self) != self.arity:
            raise TypeError(self.operator, len(self), self.arity)

##############################################################
##############################################################

class LexType(LexTypeAbc):

    # cls: LexicalItemMeta

    Predicate   = (10,  Predicate,  Predicate,     3)
    Constant    = (20,  Constant,   Parameter,     3)
    Variable    = (30,  Variable,   Parameter,     3)
    Quantifier  = (33,  Quantifier, Quantifier, None)
    Operator    = (35,  Operator,   Operator,   None)
    Atomic      = (40,  Atomic,     Sentence,      4)
    Predicated  = (50,  Predicated, Sentence,   None)
    Quantified  = (60,  Quantified, Sentence,   None)
    Operated    = (70,  Operated,   Sentence,   None)

    @classmethod
    def rankitem(cls, item) -> int: return cls(item.__class__).rank

    def __call__(self, *args, **kw) -> Lexical: return self.cls(*args, **kw)

    @cmperr
    def __lt__(self, b: LexTypeAbc): return self.rank < b.rank
    @cmperr
    def __le__(self, b: LexTypeAbc): return self.rank <= b.rank
    @cmperr
    def __gt__(self, b: LexTypeAbc): return self.rank > b.rank
    @cmperr
    def __ge__(self, b: LexTypeAbc): return self.rank >= b.rank

    def __hash__(self): return self.hash
    def __eq__(self, other):
        return self is other or self.cls is other or self is LexType.get(other)

    def __init__(self, *value):
        super().__init__()
        self.rank, self.cls, self.generic, self.maxi = value
        self.role = self.generic.__name__
        self.hash = hash(self.__class__.__name__) + self.rank
        self.cls.TYPE = self

    def __repr__(self):
        try:
            return orepr(self,
                name = self.name,
                rank = self.rank,
                cls  = self.cls,
                role = self.role,
            )
        except:
            return '<%s ?ERR?>' % self.__class__.__name__

##############################################################
##############################################################

class PredicatesMeta(ABCMeta):

    def __getitem__(cls, key) -> Predicate: return Predicates.System[key]
    def __contains__(cls, key): return key in Predicates.System
    def __len__(cls): return len(Predicates.System)
    def __iter__(cls) -> Iterator[Predicate]: return iter(Predicates.System)

class Predicates(Sequence[Predicate], metaclass = PredicatesMeta):
    """
    Predicate store
    """

    ItemSpecType = Union[Predicate, Predicate.SpecType]

    class System(Enum, metaclass = EnumMeta):

        Existence = (-2, 0, 1, 'Existence')
        Identity  = (-1, 0, 2, 'Identity')

        def __new__(self, *spec):
            pred = Predicate(spec)
            pred._value_ = pred
            setattr(Predicate, pred.name, pred)
            Predicate.__annotations__.update({pred.name: Predicate})
            return pred

        @classmethod
        def _member_keys(cls, pred: Predicate) -> set:
            return set(super()._member_keys(pred)).union(pred.refs) | {pred}

        @classmethod
        def _keytypes(cls) -> Iterable[type]:
            return (*super()._keytypes(), tuple, Predicate)

        @classmethod
        def _after_init(cls):
            super()._after_init()
            Predicate.__annotations__.update(System = EnumMeta)
            Predicate.System = cls

    def add(self, pred: ItemSpecType) -> Predicate:
        """
        Add a predicate.

        :param any pred: The predicate or spec to add.
        :return: The predicate
        :raises TypeError:
        :raises ValueError:
        """
        pred = Predicate(pred)
        if self.get(pred.bicoords, pred) != pred:
            raise ValueError('%s != %s' % (pred, self[pred.bicoords]))
        self.__idx.update({ref: pred for ref in pred.refs + (pred,)})
        self.__ulist.add(pred)
        return pred

    def update(self, preds: Iterable[ItemSpecType]):
        for pred in preds: self.add(pred)

    def get(self, ref, default = None) -> Predicate:
        try: return self[ref]
        except KeyError: return default

    def sort(self, *args, **kw):
        self.__ulist.sort(*args, **kw)

    def reverse(self):
        self.__ulist.reverse()

    def clear(self):
        self.__idx.clear()
        self.__ulist.clear()

    def count(self, pred) -> int:
        return int(pred in self)

    def index(self, ref):
        return self.__ulist.index(self.__idx[ref])

    def __getitem__(self, key) -> Predicate:
        if isinstance(key, IndexTypes):
            return self.__ulist[key]
        try: return self.__idx[key]
        except KeyError as err:
            try: return self.System[key]
            except KeyError: raise err from None

    def __iter__(self) -> Iterator[Predicate]:
        return iter(self.__ulist)

    def __len__(self):
        return len(self.__ulist)

    def __contains__(self, ref):
        return ref in self.__idx or ref in self.System

    def __bool__(self):
        return True

    def __copy__(self):
        cls = self.__class__
        inst = cls.__new__(cls)
        inst.__ulist = self.__ulist.copy()
        inst.__idx = self.__idx.copy()
        return inst

    def __init__(self, *specs: ItemSpecType):
        self.__idx = {}
        self.__ulist = UniqueList()
        if len(specs) == 1 and isinstance(specs[0], (list, tuple)):
            if specs[0] and isinstance(specs[0][0], (tuple)):
                specs, = specs
        self.update(specs)

    def __repr__(self):
        return orepr(self, len=len(self))

##############################################################

class ArgumentMeta(ABCMeta):
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
        if title is not None:
            instcheck(title, strtype)
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

    def __getitem__(self, index: IndexType) -> Sentence:
        return self.sentences[index]

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
    def __lt__(self, other): return self._cmp(other) < 0
    @cmptype
    def __le__(self, other): return self._cmp(other) <= 0
    @cmptype
    def __gt__(self, other): return self._cmp(other) > 0
    @cmptype
    def __ge__(self, other): return self._cmp(other) >= 0

    def __hash__(self): return self.hash

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
        if self.title: desc = repr(self.title)
        else: desc = 'len(%d)' % len(self)
        return '<%s:%s>' % (self.__class__.__name__, desc)

##############################################################

def ftmp():
    # for cls in (BiCoords, TriCoords):
    #     cls.first = cls(*cls.first)
    # Predicate.System = Predicates.System
    for cls in (Enum, LexicalItem, Predicates, Argument, Lexical):
        cls._readonly = cls._clsinit = True
ftmp()

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
        instcheck(data, Mapping)
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

class LexWriter(object, metaclass = ABCMeta):

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
    #         if isinstance(arg, strtype):
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
    if notn is None:
        notn = default_notation
    if notn not in notations:
        raise ValueError(notn)
    if enc is None:
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
lexwriter_classes.update({
    'polish'   : PolishLexWriter,
    'standard' : StandardLexWriter,
})
_syslw = create_lexwriter()

ftmp = None
del(_builtin, ftmp, isreadonly, raises)