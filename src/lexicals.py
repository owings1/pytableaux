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

import enum
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence

# import itertools
# import functools
# from collections import \
#     deque
from functools import \
    partial as ft_partial, \
    reduce  as ft_reduce

from itertools import \
    chain       as it_chain, \
    repeat      as it_repeat, \
    starmap     as it_smap, \
    zip_longest as it_lzip
import operator as opr
from typing import Annotated, Any, ClassVar, final

import callables
from containers import cset, cqset, zqset, zset

from errors import \
    DuplicateKeyError, \
    DuplicateValueError, \
    ReadOnlyAttributeError, \
    ValueMismatchError

from decorators import abstract, fixed, lazyget, metad, raisen, wraps

import utils
from utils import instcheck, subclscheck

# from pprint import pp

# from collections import deque
# from typing import Final, NamedTuple, 
# from callables import calls#, preds
# from containers import cqset
# from itertools import chain
# from functools import wraps
# import types
# from types import DynamicClassAttribute, MappingProxyType

ITEM_CACHE_SIZE = 10000
NOARG = enum.auto()
NOGET = enum.auto()

# flatiter = it_chain.from_iterable

def isreadonly(cls: type) -> bool:
    return all(getattr(cls, attr, None) for attr in ('_clsinit', '_readonly'))

def nosetattr(basecls, cls = None, changeonly = False,  **kw):
    forigin = basecls.__setattr__
    def fset(self, attr, val):
        if cls:
            if cls == True: checkobj = self.__class__
            else: checkobj = cls
        else:
            checkobj = self
        try:
            acheck = checkobj._readonly
        except AttributeError: pass
        else:
            # if acheck:
            if acheck:
                if changeonly:
                    if getattr(self, attr, val) is not val:
                        raise AttributeError('%s.%s is immutable' % (self, attr))
                else:
                    raise AttributeError("%s is readonly" % checkobj)
        forigin(self, attr, val)
    return fset

def nochangeattr(basecls, **kw):
    opts = {'changeonly': True} | kw
    return nosetattr(basecls, **opts)

_syslw: LexWriter
def _lexstr(item: Bases.Lexical):
    try:
        if isinstance(item, Bases.Enum):
            return item.name
        return _syslw.write(item)
    except NameError:
        try:
            return str(item.ident)
        except AttributeError as e:
            try:
                return '%s(%s)' % (item.TYPE.name, e)
            except AttributeError as e:
                return '%s(%s)' % (item.__class__.__name__, e)

def _lexrepr(item: Bases.Lexical):
    try:
        return '<%s: %s>' % (item.TYPE.role, str(item))
    except (AttributeError, NameError):
        return '<%s: ?>' % item.__class__.__name__


##############################################################

class Types:

    from types import \
        DynamicClassAttribute as DynClsAttr, \
        MappingProxyType      as MapProxy

    from utils import \
        BiCoords, \
        CacheNotationData, \
        EmptySet, \
        IndexType, \
        IntTuple, \
        SortBiCoords, \
        TriCoords

    from containers import \
        ABCMeta as ABCMetaBase, \
        DequeCache, \
        MutableSequenceSet, \
        MutSetSeqPair

    Spec = tuple
    Ident = tuple[str, tuple]

    PredicateSpec  = TriCoords
    PredicateRef   = IntTuple | str
    ParameterIdent = tuple[str, BiCoords]

    PredicatedSpec = tuple[PredicateSpec, tuple[ParameterIdent, ...]]
    QuantifiedSpec = tuple[str, BiCoords, Ident]
    OperatedSpec   = tuple[str, tuple[Ident, ...]]

    Lexical        : type

    PredsItemRef  = PredicateRef  # | Predicate
    PredsItemSpec = PredicateSpec # | Predicate

    QuantifiedItem : type #= Quantifier | Variable | Sentence

    LexType     : type

    _todo = {
        'Lexical', 'PredsItemRef', 'PredsItemSpec',
        'QuantifiedItem', 'LexType',
    }

    def __new__(cls):
        attrs = dict(cls.__dict__)
        todo: set = attrs.pop('_todo')
        reader = cls.MapProxy(attrs)
        def setitem(key, value):
            todo.remove(key)
            attrs[key] = value
        class Journal:
            __slots__ = ()
            def __setattr__(self, name, value):
                try: return setitem(name, value)
                except KeyError: pass
                raise AttributeError(name)   
            def __getattribute__(self, name) -> type:
                try: return reader[name]
                except KeyError: pass
                raise AttributeError(name)
                # return object.__getattribute__(self, name)
        Journal.__qualname__ = cls.__qualname__
        Journal.__name__ = cls.__name__
        inst = object.__new__(Journal)
        return inst

Types = Types()

class Metas:

    __new__ = None

    class Abc(Types.ABCMetaBase):
        'General-purpose base Metaclass for all Abc (non-Enum) classes.'
        _readonly : bool
        __delattr__ = raisen(AttributeError)
        __setattr__ = nosetattr(type)

    class Enum(enum.EnumMeta):
        'General-purpose base Metaclass for all Enum classes.'

        _readonly : bool

        __delattr__ = raisen(AttributeError)
        __setattr__ = nosetattr(enum.EnumMeta)

        _lookup : Types.MapProxy[Any, tuple[Bases.Enum, int, Bases.Enum]]
        _seq    : tuple[Bases.Enum, ...]

        #----------------------#
        # Class creation       #
        #----------------------#

        def __new__(cls, clsname, bases, attrs, **kw):

            # Process meta flags.
            Metas.Abc.init_attrs(attrs, bases, **kw)

            # Create class.
            Class = super().__new__(cls, clsname, bases, attrs, **kw)

            # Freeze Enum class attributes.
            Class._member_map_ = Types.MapProxy(Class._member_map_)
            Class._member_names_ = tuple(Class._member_names_)

            if not len(Class):
                # No members to process.
                Class._after_init()
                return Class

            # Store the fixed member sequence.
            Class._seq = tuple(map(Class._member_map_.get, Class.names))
            # Init hook to process members before index is created.
            Class._on_init(Class)
            # Create index.
            Class._lookup = cls._create_index(Class)
            # After init hook.
            Class._after_init()
            # Cleanup.
            cls._clear_hooks(Class)

            return Class

        @final
        @classmethod
        def _create_index(cls, Class: Metas.Enum) -> Types.MapProxy:
            'Create the member lookup index'
            # Member to key set functions.
            keys_funcs = (
                cls._default_keys,
                Class._member_keys,
            )
            # Merges keys per member from all key_funcs.
            keys_it = map(cqset, map(
                it_chain.from_iterable, zip(*(
                    map(f, Class) for f in keys_funcs
                ))
            ))
            # Builds the member cache entry: (member, i, next-member).
            value_it = it_lzip(
                Class, range(len(Class)), Class.seq[1:]
            )
            # Fill in the member entries for all keys and merge the dict.
            merge_it = ft_reduce(opr.or_,
                it_smap(dict.fromkeys, zip(keys_it, value_it))
            )
            return Types.MapProxy(merge_it)

        @staticmethod
        def _default_keys(member: Bases.Enum):
            'Default member lookup keys'
            return cset({
                member._name_, (member._name_,), member,
                # member._value_, hash(member),
            })

        @final
        @classmethod
        def _clear_hooks(cls, Class: Metas.Enum):
            'Cleanup spent hook methods.'
            fdel = ft_partial(type(cls).__delattr__, Class)
            names = cls._hooks & Class.__dict__
            utils.it_drain(map(fdel, names))

        _hooks = zset({
            '_member_keys', '_on_init', '_after_init'
        })

        #----------------------#
        # Subclass Hooks       #
        #----------------------#

        def _member_keys(cls, member: Bases.Enum) -> Iterable:
            'Init hook to get the index lookup keys for a member.'
            return Types.EmptySet

        def _on_init(cls, Class: Metas.Enum):
            '''Init hook after all members have been initialized, before index
            is created. Skips abstract classes.'''

        def _after_init(cls):
            'Init hook once the class is initialized. Includes abstract classes.'

        #----------------------#
        # Container behavior   #
        #----------------------#

        def __getitem__(cls, key):
            if key.__class__ is cls: return key
            try: return cls._lookup[key][0]
            except (AttributeError, KeyError): pass
            return super().__getitem__(key)

        def __getattr__(cls, name):
            if name == 'index':
                # Allow DynClsAttr for member.index.
                try: return cls.indexof
                except AttributeError: pass
            return super().__getattr__(name)

        def __contains__(cls, key):
            return cls.get(key, NOGET) is not NOGET

        def __call__(cls, value, *args, **kw) -> Bases.Enum:
            if not args:
                try: return cls[value]
                except KeyError: pass
            return super().__call__(value, *args, **kw)

        def __dir__(cls):
            return list(cls.names)

        def __iter__(cls) -> Iterator[Bases.Enum]:
            return iter(cls.seq)

        def __reversed__(cls) -> Iterator[Bases.Enum]:
            return reversed(cls.seq)

        @property
        def __members__(cls):
            # Override 
            return cls._member_map_

        #--------------------#
        # Instance methods   #
        #--------------------#

        @Types.DynClsAttr
        def names(cls):
            'The member names.'
            return cls._member_names_

        @Types.DynClsAttr
        def seq(cls):
            'The sequence of member objects.'
            try: return cls._seq
            except AttributeError: return ()

        def get(cls, key, default = NOARG) -> Bases.Enum:
            '''Get a member by an indexed reference key. Raises KeyError if not
            found and no default specified.'''
            try: return cls[key]
            except KeyError:
                if default is NOARG: raise
                return default

        def indexof(cls, key) -> int:
            'Get the sequence index of the member. Raises ValueError if not found.'
            try:
                return cls._lookup[key][1]
            except KeyError:
                return cls._lookup[cls[key]][1]
            except AttributeError:
                return cls.seq.index(cls[key])
            except KeyError:
                raise ValueError(key)

        index = indexof

    class LexicalItem(Abc):
        'Metaclass for LexicalItem classes (Constant, Predicate, Sentence, etc.).'

        Cache: ClassVar[Types.DequeCache]

        def __call__(cls, *spec, **kw) -> Bases.LexicalItem:
            # Passthrough
            if len(spec) == 1 and isinstance(spec[0], cls): return spec[0]
            # cache = LexicalItem.Cache
            cache = __class__.Cache
            clsname = cls.__name__
            # Try cache
            try: return cache[clsname, spec]
            except KeyError: pass
            # Construct
            try: inst: Bases.Lexical = super().__call__(*spec, **kw)
            except TypeError:
                if cls in LexType or len(spec) != 1: raise
                # Try arg as ident tuple (clsname, spec)
                clsname, spec = spec[0]
                lextypecls = LexType(clsname).cls
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

    class Argument(Abc):
        'Argument Metaclass.'

        def __call__(cls, *args, **kw):
            if len(args) == 1 and not len(kw) and isinstance(args[0], cls):
                return args[0]
            return super().__call__(*args, **kw)

    class LexWriter(Abc):
        'LexWriter Metaclass.'

        def __call__(cls, notn = None, *args, **kw):
            if cls is LexWriter:
                notn = Notation(notn or Notation.default)
                return notn.default_writer(*args, **kw)
            return super().__call__(*args, **kw)

    class Notation(Enum):
        'Notation Enum Metaclass.'

        @Types.DynClsAttr
        def default(cls: type[Notation]) -> Notation:
            return cls.polish

        # __getitem__: Callable[..., Notation]

class Bases:

    __new__ = None

    class Lexical:
        'Lexical mixin class for both ``LexicalEnum`` and ``LexicalItem`` classes.'

        __delattr__ = raisen(AttributeError)
        __setattr__ = nosetattr(object, cls = Metas.LexicalItem)

        __slots__ = ()

        #: Type for attribute ``spec``
        SpecType: ClassVar[type[tuple]] = tuple
        #: Type for attribute ``ident``
        IdentType: ClassVar[type[Types.Ident]] = Types.Ident
        # LexType instance populated below.
        TYPE: ClassVar[LexType]

        @staticmethod
        @final
        def cmpitems(item: Bases.Lexical, other: Bases.Lexical) -> int:
            'Pairwise sorting comparison based on LexType and numeric sort tuple.'
            if item is other: return 0
            cmp = item.TYPE.rank - other.TYPE.rank
            if cmp: return cmp
            a, b = item.sort_tuple, other.sort_tuple
            for x, y in zip(a, b):
                cmp = x - y
                if cmp: return cmp
            return len(a) - len(b)

        def cmpwrap(oper: Callable) -> Callable[[Bases.Lexical, Bases.Lexical], int]:
            fname = '__%s__' % oper.__name__
            qname = 'Lexical.%s' % fname
            def f(self, other):
                try:
                    return oper(Lexical.cmpitems(self, other), 0)
                except AttributeError:
                    return NotImplemented
            f.__name__ = fname
            f.__qualname__ = qname
            return f

        __lt__ = cmpwrap(opr.lt)
        __le__ = cmpwrap(opr.le)
        __gt__ = cmpwrap(opr.gt)
        __ge__ = cmpwrap(opr.ge)

        del(cmpwrap)

        @staticmethod
        def identitem(item: Bases.Lexical) -> Types.Ident:
            'Build an ``ident`` tuple from the class name and initialization spec.'
            return (item.__class__.__name__, item.spec)

        @staticmethod
        def hashitem(item: Bases.Lexical) -> int:
            'Compute a hash based on class name and sort tuple.'
            return hash((item.__class__.__name__, item.sort_tuple))

        @classmethod
        def gen(cls, n: int, first: Bases.Lexical = None, **opts) -> Iterator[Bases.Lexical]:
            'Generate items.'
            if first is not None:
                instcheck(first, cls)
            for i in range(n):
                item = item.next(**opts) if i else (first or cls.first())
                if item: yield item

        # -----------------
        # Default Methods
        # -----------------

        __bool__ = fixed.value(True)
        __repr__ = _lexrepr
        __str__  = _lexstr

        # -------------------------------
        # Abstract instance attributes
        # -------------------------------

        #: The arguments roughly needed to construct, given that we know the
        #: type, i.e. in intuitive order. A tuple, possibly nested, containing
        #: digits or strings.
        spec: Types.Spec

        #: Sorting identifier, to order tokens of the same type. Numbers only
        #: (no strings). This is also used in hashing, so equal objects should
        #: have equal sort_tuples. The first value must be the lexical rank of
        # the type.
        sort_tuple: Types.IntTuple

        #: Equality identifier able to compare across types. A tuple, possibly
        #: nested, containing digits and possibly strings. The first should be
        #: the class name. Most naturally this would be followed by the spec.
        ident: Types.Ident

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

        # ----------------------------------------
        # Mixin attributes for Metaclasses to copy.
        # ----------------------------------------
        __copyattrs__ = callables.calls.now(
            lambda d, keys: Types.MapProxy({k:d[k] for k in keys}),
            locals(), (
                'gen', '__repr__', '__str__', '__bool__',
                'identitem', 'hashitem', 'cmpitems',
                '__lt__', '__le__', '__gt__', '__ge__',
            )
        )

    Types.Lexical = Lexical
    Metas.LexicalItem.Cache = Types.DequeCache(Lexical, ITEM_CACHE_SIZE)

    class Enum(enum.Enum, metaclass = Metas.Enum):
        'Generic base class for all Enum classes.'

        __delattr__ = raisen(AttributeError)
        __setattr__ = nosetattr(enum.Enum, cls = True)

        __slots__   = '_value_', '_name_', '__objclass__'

        def __copy__(self):
            return self

        def __deepcopy__(self, memo):
            memo[id(self)] = self
            return self

        # Propagate class hooks up to metaclass, so they can be implemented
        # in either the meta or concrete classes.

        @classmethod
        def _on_init(cls: Metas.Enum, Class):
            'Propagate hook up to metaclass.'
            type(cls)._on_init(cls, Class)

        @classmethod
        def _member_keys(cls: Metas.Enum, member: Bases.Enum) -> Iterable:
            'Propagate hook up to metaclass.'
            return type(cls)._member_keys(cls, member)

        @classmethod
        def _after_init(cls: Metas.Enum):
            'Propagate hook up to metaclass.'
            type(cls)._after_init(cls)


    class LexicalEnum(Lexical, Enum):
        'Base Enum implementation of Lexical. For Quantifier and Operator classes.'

        @metad.init_attrs
        def copy_lexical(attrs, bases, **kw):
            Lexical, = Metas.Abc.basesmap(bases)['Lexical']
            attrs |= Lexical.__copyattrs__

        # ----------------------
        # Lexical Implementation
        # ----------------------

        spec       : tuple[str]
        ident      : tuple[str, tuple[str]]
        sort_tuple : Types.IntTuple
        hash       : int

        def __eq__(self, other):
            'Allow equality with the string name.'
            return self is other or other in self.strings

        def __hash__(self):
            return self.hash

        @classmethod
        def first(cls) -> Bases.LexicalEnum:
            return cls.seq[0]

        def next(self, loop = False) -> Bases.LexicalEnum:
            seq = self.__class__.seq
            i = self.index + 1
            if i == len(seq):
                if not loop: raise StopIteration
                i = 0
            return seq[i]

        # ---------------------------------------
        # Enum Attributes and Class Init Methods
        # ---------------------------------------

        #: The member name.
        name: str
        #: Label with spaces allowed.
        label: str
        #: Index of the member in the enum list, in source order, 0-based.
        _index: int
        #: A number to signify order independenct of source or other constraints.
        order: int
        #: Name, label, or other strings unique to a member.
        strings: frozenset[str]

        __slots__ = (
            'spec', 'ident', 'sort_tuple', 'hash',
            'label', '_index', 'order', 'strings',
        )

        @Types.DynClsAttr
        def index(self) -> int:
            'Index of the member in the enum list, in source order, 0-based.'
            return self._index

        def __init__(self, order, label, *_):
            self.spec = (self.name,)
            self.order, self.label = order, label
            self.sort_tuple = (self.order,)
            self.ident = Bases.Lexical.identitem(self)
            self.hash = Bases.Lexical.hashitem(self)
            self.strings = zqset({self.name, self.label})
            super().__init__()

        # --------------------------
        # Enum meta hooks.
        # --------------------------

        @classmethod
        def _member_keys(cls, member: Bases.LexicalEnum) -> set:
            'Enum init hook. Index keys for Enum members lookups.'
            return cqset(super()._member_keys(member)) | {
                # member.name,
                # (member.name,),
                member.label,
                member.value,
            }

        @classmethod
        def _on_init(cls, Class: type[Bases.LexicalEnum]):
            'Enum init hook. Store the sequence index of each member.'
            super()._on_init(Class)
            for i, member in enumerate(Class): member._index = i

        @classmethod
        def _after_init(cls):
            'Enum init hook. Add class attributes after init, else EnumMeta complains.'
            super()._after_init()
            if cls is __class__:
                annot = cls.__annotations__
                cls.SpecType = annot['spec']
                cls.IdentType = annot['ident']


    class LexicalItem(Lexical, metaclass = Metas.LexicalItem):
        'Base Lexical Item class.'

        @metad.init_attrs
        def copy_lexical(attrs, bases, **kw):
            'Copy mixin Lexical attributes.'
            Lexical, = Metas.Abc.basesmap(bases)['Lexical']
            attrs |= Lexical.__copyattrs__

        def __init_subclass__(subcls, **kw):
            'Populate the IdentType from the SpecType.'
            super().__init_subclass__(**kw)
            subcls.IdentType = tuple[str, subcls.SpecType]

        __delattr__ = raisen(AttributeError)

        def __setattr__(self, name, value):
            if getattr(self, name, value) is not value:
                if isinstance(getattr(self.__class__, name, None), property):
                    pass
                else:
                    raise ReadOnlyAttributeError(name, self)
            super().__setattr__(name, value)

        def __new__(cls, *args):
            if cls not in LexType:
                raise TypeError('Abstract type %s' % cls)
            return super().__new__(cls)

        @abstract
        def __init__(self): ...

        # -------------------------------
        # Lexical Implementation
        # -------------------------------

        __slots__ = '_ident', '_hash'

        @lazyget.prop
        def ident(self) -> Types.Ident:
            return Lexical.identitem(self)

        @lazyget.prop
        def hash(self) -> int:
            return Lexical.hashitem(self)

        def __hash__(self):
            return self.hash

        def __eq__(self, other: Bases.Lexical):
            return self is other or (
                self.TYPE == LexType.get(other.__class__, ...) and
                self.ident == other.ident
            )

Lexical = Bases.Lexical

class CoordsItem(Bases.LexicalItem):

    Coords: ClassVar[type[Types.BiCoords]] = Types.BiCoords

    SpecType: ClassVar[type[Types.BiCoords]] = Types.BiCoords

    #: The item coordinates.
    coords: Types.BiCoords

    #: The coords index.
    index: int

    #: The coords subscript.
    subscript: int

    scoords: Types.SortBiCoords
    spec: Types.BiCoords

    __slots__ = 'spec', 'coords', 'index', 'subscript', '_sort_tuple', '_scoords'

    @lazyget.prop
    def sort_tuple(self):
        return self.scoords

    @lazyget.prop
    def scoords(self) -> Types.SortBiCoords:
        return self.coords.sorting()

    @classmethod
    def first(cls) -> CoordsItem:
        return cls(cls.Coords.first)

    def next(self, **kw) -> CoordsItem:
        idx, sub, *cargs = self.coords
        if idx < self.TYPE.maxi:
            idx += 1
        else:
            idx = 0
            sub += 1
        coords = self.Coords(idx, sub, *cargs)
        return self.__class__(coords)

    def __init__(self, *coords: Types.IntTuple):
        if len(coords) == 1: coords, = coords
        self.coords = self.spec = self.Coords(*coords)
        for val in self.coords: instcheck(val, int)
        for i, f in self._fieldsenumerated:
            setattr(self, f, coords[i])
        if self.index > self.TYPE.maxi:
            raise ValueError('%d > %d' % (self.index, self.TYPE.maxi))
        if self.subscript < 0:
            raise ValueError('%d < %d' % (self.subscript, 0))

    _fieldsenumerated: ClassVar[tuple[tuple[int, str], ...]]
    def __init_subclass__(subcls: type[CoordsItem], **kw):
        super().__init_subclass__(**kw)
        subcls._fieldsenumerated = tuple(enumerate(subcls.Coords._fields))

##############################################################
##############################################################

class Quantifier(Bases.LexicalEnum):

    Existential = (0, 'Existential')
    Universal   = (1, 'Universal')

    def __call__(self, *spec: Types.QuantifiedSpec) -> Quantified:
        return Quantified(self, *spec)
    
class Operator(Bases.LexicalEnum):

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

    def __call__(self, *spec: Types.OperatedSpec) -> Operated:
        return Operated(self, *spec)

    arity: int
    __slots__ = ('arity',)

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

    Coords   : ClassVar[type[Types.TriCoords]] = Types.TriCoords
    SpecType : ClassVar[type[Types.TriCoords]] = Types.TriCoords
    RefType  : ClassVar[type[Types.PredicateRef]] = Types.PredicateRef

    spec    : Types.TriCoords
    coords  : Types.TriCoords
    scoords : Types.SortBiCoords
    refs    : tuple[Types.PredicateRef, ...]

    #: The coords arity.
    arity: int
    #: Whether this is a system predicate.
    is_system: bool
    #: The name or spec
    name: Types.IntTuple | str

    __slots__ = 'arity', 'is_system', 'name', '_bicoords', '_refs'

    @lazyget.prop
    def bicoords(self) -> Types.BiCoords:
        return Types.BiCoords(*self.spec[0:2])

    def next(self, **kw) -> Predicate:
        arity = self.arity
        if self.is_system:
            pred: Predicate
            for pred in self.System:
                if pred > self and pred.arity == arity:
                    return pred
        return super().next(**kw)

    @lazyget.prop
    def refs(self) -> tuple[Types.PredicateRef, ...]:
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
        """
        return tuple({self.spec, self.ident, self.bicoords, self.name})

    def refkeys(self):
        return cset({*self.refs, self})

    class System(Bases.Enum):

        Existence : Annotated[Predicate, (-2, 0, 1, 'Existence')]
        Identity  : Annotated[Predicate, (-1, 0, 2, 'Identity')]

    def __init__(self, *spec):
        if len(spec) == 1 and isinstance(spec[0], tuple):
            spec, = spec
        if len(spec) not in (3, 4):
            raise TypeError('need 3 or 4 elements, got %s' % len(spec))
        super().__init__(*spec[0:3])
        self.is_system = self.index < 0
        if self.is_system and len(self.System):
            raise ValueError('`index` must be >= 0')
        if instcheck(self.arity, int) <= 0:
            raise ValueError('`arity` must be > 0')
        name = spec[3] if len(spec) == 4 else None
        self.name = self.spec if name is None else name
        if name is not None:
            if len(self.System) and name in self.System:
                raise ValueError('System predicate: %s' % name)
            instcheck(name, (tuple, str))

    def __str__(self):
        return self.name if self.is_system else super().__str__()

    def __call__(self, *spec: Types.PredicatedSpec) -> Predicated:
        return Predicated(self, *spec)

    # --------------------------
    # System Enum properties.
    # --------------------------

    @Types.DynClsAttr
    def _value_(self):
        try:
            if self.is_system: return self
        except AttributeError: return self
        raise AttributeError('_value_')

    @Types.DynClsAttr
    def _name_(self):
        if self.is_system: return self.name
        raise AttributeError('_name_')

    @Types.DynClsAttr
    def __objclass__(self):
        if self.is_system: return __class__.System
        raise AttributeError('__objclass__')

    @metad.temp
    def sysset(prop: property):
        name = prop.fget.__name__
        @wraps(prop.fget)
        def f(self, value):
            try: self.is_system
            except AttributeError: return
            raise AttributeError(name)
        return prop.setter(f)

    _value_ = sysset(_value_)
    _name_  = sysset(_name_)
    __objclass__ = sysset(__objclass__)

Types.PredsItemSpec |= Predicate
Types.PredsItemRef  |= Predicate

class Parameter(CoordsItem):

    is_constant: bool
    is_variable: bool

    __init__ = CoordsItem.__init__

class Constant(Parameter):

    is_constant = fixed.prop(True)
    is_variable = fixed.prop(False)

class Variable(Parameter):

    is_constant = fixed.prop(False)
    is_variable = fixed.prop(True)

##############################################################

class Sentence(Bases.LexicalItem):

    __slots__ = ()

    predicate  : Predicate  | None
    quantifier : Quantifier | None
    operator   : Operator   | None

    #: Whether this is an atomic sentence.
    is_atomic = fixed.prop(False)
    #: Whether this is a predicated sentence.
    is_predicated = fixed.prop(False)
    #: Whether this is a quantified sentence.
    is_quantified = fixed.prop(False)
    #: Whether this is an operated sentence.
    is_operated = fixed.prop(False)
    #: Whether this is a literal sentence. Here a literal is either a
    #: predicated sentence, the negation of a predicated sentence,
    #: an atomic sentence, or the negation of an atomic sentence.
    is_literal = fixed.prop(False)
    #: Whether this is an atomic sentence.
    is_negated = fixed.prop(False)

    #: Set of predicates, recursive.
    predicates: frozenset[Predicate] = fixed.prop(Types.EmptySet)
    #: Set of constants, recursive.
    constants: frozenset[Constant] = fixed.prop(Types.EmptySet)
    #: Set of variables, recursive.
    variables: frozenset[Variable] = fixed.prop(Types.EmptySet)
    #: Set of atomic sentences, recursive.
    atomics: frozenset[Atomic] = fixed.prop(Types.EmptySet)
    #: Tuple of quantifiers, recursive.
    quantifiers: tuple[Quantifier, ...] = fixed.prop(tuple())
    #: Tuple of operators, recursive.
    operators: tuple[Operator, ...] = fixed.prop(tuple())

    def substitute(self, pnew: Parameter, pold: Parameter) -> Sentence:
        """Return the recursive substitution of ``pnew`` for all occurrences
        of ``pold``."""
        return self

    def negate(self) -> Operated:
        'Negate this sentence, returning the new sentence.'
        return Operated(Operator.Negation, (self,))

    def negative(self) -> Sentence:
        """Either negate this sentence, or, if this is already a negated
        sentence return its negatum, i.e., "un-negate" the sentence."""
        return self[0] if self.is_negated else self.negate()

    def asserted(self) -> Operated:
        'Apply assertion operator to the sentence.'
        return Operated(Operator.Assertion, (self,))

    def disjoin(self, rhs: Sentence) -> Operated:
        'Apply disjunction to the right-hand sentence.'
        return Operated(Operator.Disjunction, (self, rhs))

    def conjoin(self, rhs: Sentence) -> Operated:
        'Apply conjunction to the right-hand sentence.'
        return Operated(Operator.Conjunction, (self, rhs))

    def variable_occurs(self, v: Variable) -> bool:
        'Whether the variable occurs anywhere in the sentence (recursive).'
        return v in self.variables

Types.QuantifiedItem = Quantifier | Variable | Sentence

class Atomic(Sentence, CoordsItem):

    predicate  = fixed.prop(None)
    quantifier = fixed.prop(None)
    operator   = fixed.prop(None)

    is_atomic  = fixed.prop(True)
    is_literal = fixed.prop(True)
    variable_occurs = fixed.value(False)

    __slots__ = '_atomics',

    @lazyget.prop
    def atomics(self) -> frozenset[Atomic]:
        return frozenset({self})

    __init__ = CoordsItem.__init__

class Predicated(Sentence, Sequence[Parameter]):

    SpecType: ClassVar[type[Types.PredicatedSpec]] = Types.PredicatedSpec

    #: The predicate.
    predicate: Predicate

    #: The parameters
    params: tuple[Parameter, ...]

    #: The set of parameters.
    paramset: frozenset[Parameter]

    spec: Types.PredicatedSpec

    @property
    def arity(self) -> int:
        'The arity of the predicate'
        return self.predicate.arity

    @lazyget.prop
    def paramset(self) -> frozenset[Parameter]:
        'The set of parameters.'
        return frozenset(self.params)

    __slots__ = (
        'predicate', 'params',
        '_spec', '_sort_tuple', '_paramset',
        '_predicates', '_constants', '_variables'
    )

    quantifier    = fixed.prop(None)
    operator      = fixed.prop(None)
    is_predicated = fixed.prop(True)
    is_literal    = fixed.prop(True)

    @lazyget.prop
    def spec(self) -> Types.PredicatedSpec:
        return (self.predicate.spec, tuple(p.ident for p in self))

    @lazyget.prop
    def sort_tuple(self):
        items = (self.predicate, *self)
        return tuple(it_chain.from_iterable(it.sort_tuple for it in items))

    @classmethod
    def first(cls, predicate: Predicate = None) -> Predicated:
        pred = predicate or Predicate.first()
        c = Constant.first()
        params = tuple(c for i in range(pred.arity))
        return cls(pred, params)

    def next(self, **kw) -> Predicated:
        return Predicated(self.predicate.next(**kw), self.params)

    @lazyget.prop
    def predicates(self) -> frozenset[Predicate]:
        return frozenset({self.predicate})

    @lazyget.prop
    def constants(self) -> frozenset[Constant]:
        return frozenset(p for p in self.paramset if p.is_constant)

    @lazyget.prop
    def variables(self) -> frozenset[Variable]:
        return frozenset(p for p in self.paramset if p.is_variable)

    def substitute(self, pnew: Parameter, pold: Parameter) -> Predicated:
        if pnew == pold or pold not in self: return self
        params = (pnew if p == pold else p for p in self)
        return Predicated(self.predicate, tuple(params))

    def __iter__(self) -> Iterator[Parameter]:
        return iter(self.params)

    def __getitem__(self, index: Types.IndexType) -> Parameter:
        return self.params[index]

    def __len__(self):
        return len(self.params)

    def __contains__(self, p: Parameter):
        return p in self.paramset

    def __init__(self, pred, params: Iterable[Parameter] | Parameter):
        if isinstance(pred, str):
            self.predicate = Predicates.System(pred)
        else:
            self.predicate = Predicate(pred)
        if isinstance(params, Parameter):
            self.params = (params,)
        else:
            self.params = tuple(Parameter(param) for param in params)
        if len(self) != self.predicate.arity:
            raise TypeError(self.predicate, len(self), self.arity)

class Quantified(Sentence, Sequence[Types.QuantifiedItem]):

    SpecType: ClassVar[type[Types.QuantifiedSpec]] = Types.QuantifiedSpec

    ItemsType: ClassVar[type[Types.QuantifiedItem]] = Types.QuantifiedItem

    spec: Types.QuantifiedSpec

    #: The quantifier
    quantifier: Quantifier

    #: The bound variable
    variable: Variable

    #: The inner sentence
    sentence: Sentence

    #: The items sequence: Quantifer, Variable, Sentence.
    items: tuple[Quantifier, Variable, Sentence]

    __slots__ = (
        'quantifier', 'variable', 'sentence', 'items',
        '_spec', '_sort_tuple', '_quantifiers',
    )

    predicate     = fixed.prop(None)
    operator      = fixed.prop(None)
    is_quantified = fixed.prop(True)

    @lazyget.prop
    def spec(self) -> Types.QuantifiedSpec:
        return self.quantifier.spec + (self.variable.spec, self.sentence.ident)

    @lazyget.prop
    def sort_tuple(self) -> Types.IntTuple:
        return tuple(it_chain.from_iterable(item.sort_tuple for item in self))

    @classmethod
    def first(cls, quantifier: Quantifier = None) -> Quantified:
        if quantifier is None:
            quantifier = Quantifier.seq[0]
        q = Quantifier(quantifier)
        v = Variable.first()
        pred: Predicate = Predicate.first()
        params = (v, *Constant.gen(pred.arity - 1))
        return cls(q, v, pred(params))

    def next(self, **kw) -> Quantified:
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

    @lazyget.prop
    def quantifiers(self) -> tuple[Quantifier, ...]:
        return (self.quantifier, *self.sentence.quantifiers)

    def substitute(self, pnew: Parameter, pold: Parameter) -> Quantified:
        if pnew == pold: return self
        q, v, s = self
        return self.__class__(q, v, s.substitute(pnew, pold))

    def variable_occurs(self, v: Variable) -> bool:
        return self.variable == v or self.sentence.variable_occurs(v)

    def unquantify(self, c: Constant) -> Sentence:
        'Instantiate the variable with a constant.'
        return self.sentence.substitute(Constant(c), self.variable)

    def __iter__(self) -> Iterator[Types.QuantifiedItem]:
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __contains__(self, item: Types.QuantifiedItem):
        return item in self.items

    def __getitem__(self, index: Types.IndexType) -> Types.QuantifiedItem:
        return self.items[index]

    def __init__(self, q: Quantifier, v: Variable, s: Sentence):
        self.quantifier, self.variable, self.sentence = self.items = (
            Quantifier(q), Variable(v), Sentence(s)
        )

    def count(self, item: Types.QuantifiedItem) -> int:
        return int(item in self)

    def index(self, item: Types.QuantifiedItem) -> int:
        return self.items.index(item)

class Operated(Sentence, Sequence[Sentence]):

    SpecType: ClassVar[type[Types.OperatedSpec]] = Types.OperatedSpec

    #: The operator
    operator: Operator
    #: The operands.
    operands: tuple[Sentence, ...]

    spec: Types.OperatedSpec

    @property
    def arity(self) -> int:
        'The arity of the operator.'
        return self.operator.arity
    @property
    def lhs(self) -> Sentence:
        'The first (left-most) operand.'
        return self[0]
    @property
    def rhs(self) -> Sentence:
        'The last (right-most) operand.'
        return self[-1]
    @property
    def operand(self) -> Sentence | None:
        'The operand if only one, else None.'
        return self[0] if len(self) == 1 else None
    @property
    def negatum(self) -> Sentence | None:
        'The operand if is negated, else None.'
        return self[0] if self.is_negated else None
    @property
    def is_negated(self) -> bool:
        return self.operator == Operator.Negation

    predicate   = fixed.prop(None)
    quantifier  = fixed.prop(None)
    is_operated = fixed.prop(True)

    __slots__ = (
        'operator', 'operands', '_is_literal', '_spec', '_sort_tuple',
        '_predicates', '_constants', '_variables', '_atomics', '_quantifiers',
        '_operators',
    )

    @lazyget.prop
    def is_literal(self) -> bool:
        return self.is_negated and self[0].TYPE in (Atomic, Predicated)

    @lazyget.prop
    def spec(self) -> Types.OperatedSpec:
        return self.operator.spec + (tuple(s.ident for s in self),)

    @lazyget.prop
    def sort_tuple(self) -> Types.IntTuple:
        return tuple(it_chain.from_iterable(it.sort_tuple for it in (self.operator, *self)))

    @classmethod
    def first(cls, operator: Operator = None) -> Operated:
        if operator is None: operator = Operator.seq[0]
        oper = Operator(operator)
        operands = Atomic.gen(oper.arity)
        return cls(oper, tuple(operands))

    def next(self, **kw) -> Operated:
        operands = list(self)
        operands[-1] = operands[-1].next(**kw)
        return self.__class__(self.operator, tuple(operands))

    @lazyget.prop
    def predicates(self) -> frozenset[Predicate]:
        return frozenset(it_chain.from_iterable(s.predicates for s in self))

    @lazyget.prop
    def constants(self) -> frozenset[Constant]:
        return frozenset(it_chain.from_iterable(s.constants for s in self))

    @lazyget.prop
    def variables(self) -> frozenset[Variable]:
        return frozenset(it_chain.from_iterable(s.variables for s in self))

    @lazyget.prop
    def atomics(self) -> frozenset[Atomic]:
        return frozenset(it_chain.from_iterable(s.atomics for s in self))

    @lazyget.prop
    def quantifiers(self) -> tuple[Quantifier, ...]:
        return tuple(it_chain.from_iterable(s.quantifiers for s in self))

    @lazyget.prop
    def operators(self) -> tuple[Operator, ...]:
        return (self.operator,) + tuple(it_chain.from_iterable(s.operators for s in self))

    def substitute(self, pnew: Parameter, pold: Parameter) -> Operated:
        if pnew == pold: return self
        operands = (s.substitute(pnew, pold) for s in self)
        return self.__class__(self.operator, tuple(operands))

    def __iter__(self) -> Iterator[Sentence]:
        return iter(self.operands)

    def __getitem__(self, index: Types.IndexType) -> Sentence:
        return self.operands[index]

    def __len__(self):
        return len(self.operands)

    def __contains__(self, s: Sentence):
        return s in self.operands

    def __init__(self, oper: Operator, operands: Iterable[Sentence] | Sentence):
        if isinstance(operands, Sentence):
            self.operands = (operands,)
        else:
            self.operands = tuple(map(Sentence, operands))
        self.operator = Operator(oper)
        if len(self.operands) != self.operator.arity:
            raise TypeError(self.operator, len(self.operands), self.operator.arity)

##############################################################
##############################################################

class LexType(Bases.Enum):

    rank    : int
    cls     : type[Bases.Lexical]
    generic : type[Bases.Lexical]
    role    : str
    maxi    : int | None
    hash    : int

    __slots__ = 'rank', 'cls', 'generic', 'maxi', 'role', 'hash'

    Predicate   = (10,  Predicate,  Predicate,     3)
    Constant    = (20,  Constant,   Parameter,     3)
    Variable    = (30,  Variable,   Parameter,     3)
    Quantifier  = (33,  Quantifier, Quantifier, None)
    Operator    = (35,  Operator,   Operator,   None)
    Atomic      = (40,  Atomic,     Sentence,      4)
    Predicated  = (50,  Predicated, Sentence,   None)
    Quantified  = (60,  Quantified, Sentence,   None)
    Operated    = (70,  Operated,   Sentence,   None)

    def __call__(self, *args, **kw) -> Bases.Lexical:
        return self.cls(*args, **kw)

    @metad.temp
    def compare(method):
        oper = getattr(opr, method.__name__)
        @wraps(method)
        def f(self: LexType, other: LexType):
            if not isinstance(other, LexType):
                return NotImplemented
            return oper(self.rank, other.rank)
        return f
    @compare
    def __lt__(): pass
    @compare
    def __le__(): pass
    @compare
    def __gt__(): pass
    @compare
    def __ge__(): pass

    def __eq__(self, other):
        return self is other or (
            self.cls is other or
            self is LexType.get(other, None)
        )

    def __hash__(self): return self.hash

    def __init__(self, *value):
        super().__init__()
        self.rank, self.cls, self.generic, self.maxi = value
        self.role = self.generic.__name__
        self.hash = hash(self.__class__.__name__) + self.rank
        self.cls.TYPE = self

    def __repr__(self):
        name = self.__class__.__name__
        try: return utils.orepr(name, _ = self.cls)
        except: return '<%s ?ERR?>' % name

    # --------------------------
    # Enum meta hooks.
    # --------------------------

    @classmethod
    def _member_keys(cls, member: LexType) -> set:
        'Enum lookup index init hook.'
        return cqset(super()._member_keys(member)) | {
            member.cls
        }

Types.LexType = LexType

##############################################################
##############################################################

class Predicates(Types.MutableSequenceSet[Predicate], metaclass = Metas.Abc):
    'Predicate store'

    def __init__(self, specs: Iterable[Types.PredsItemSpec] = None):
        super().__init__(Types.MutSetSeqPair(set(), []))
        self._lookup = {}
        if specs is not None:
            self.update(specs)

    _lookup: dict[Types.PredsItemRef, Predicate]
    __slots__ = '_lookup',

    def get(self, ref: Types.PredsItemRef, default = NOARG) -> Predicate:
        """Get a predicate by any reference. Also searches System predicates.
        Raises KeyError when no default specified."""
        try: return self._lookup[ref]
        except KeyError:
            try: return self.System[ref]
            except KeyError: pass
            if default is NOARG: raise
            return default

    # -------------------------------
    #  MutableSequenceSet hooks.
    # -------------------------------

    def _new_value(self, value: Types.PredsItemSpec) -> Predicate:
        'Implement new_value hook. Return a predicate.'
        return Predicate(value)

    def _before_add(self, pred: Predicate):
        'Implement before_add hook. Check for arity/value conflicts.'
        m, keys = self._lookup, pred.refkeys()
        conflict = cset(filter(None, map(m.get, keys))) - {pred}
        if len(conflict):
            other = next(iter(conflict))
            raise ValueMismatchError(other.coords, pred.coords)

    def _after_add(self, pred: Predicate):
        'Implement after_add hook. Add keys to lookup index.'
        m, keys = self._lookup, pred.refkeys()
        # ---------- extra check
        conflict = keys & m
        if len(conflict):
            raise DuplicateKeyError(pred, *conflict)
        # ----------
        m.update(zip(keys, it_repeat(pred)))

    def _after_remove(self, pred: Predicate):
        'Implement after_remove hook. Remove keys from lookup index.'
        m, keys = self._lookup, pred.refkeys()
        conflict = cset(map(m.pop, keys)) - {pred}
        if len(conflict):
            raise DuplicateValueError(pred, *conflict)

    # -------------------------------
    #  Override MutableSequenceSet
    # -------------------------------

    def clear(self):
        super().clear()
        self._lookup.clear()

    def __contains__(self, ref: Types.PredsItemRef):
        return ref in self._lookup

    def __copy__(self):
        inst = super().__copy__()
        inst._lookup = self._lookup.copy()
        return inst

    # -------------------------------

    class System(Predicate.System):
        'System Predicates enum container class.'

        @metad.init_attrs
        def expand(attrs, bases, **kw):
            annots = Metas.Abc.annotated_attrs(Predicate.System)
            members = {
                name: spec for name, (vtype, spec)
                in annots.items() if vtype is Predicate
            }
            attrs |= members
            attrs._member_names.extend(members.keys())

        def __new__(cls, *spec):
            return Bases.LexicalItem.__new__(Predicate)

        # --------------------------
        # Enum meta hooks.
        # --------------------------

        @classmethod
        def _member_keys(cls, pred: Predicate) -> set:
            'Enum lookup index init hook.'
            return cqset(super()._member_keys(pred)) | \
                pred.refkeys()

        @classmethod
        def _after_init(cls):
            'Enum after init hook.'
            super()._after_init()
            for pred in cls:
                setattr(Predicate, pred.name, pred)
            Predicate.System = cls

class Argument(Sequence[Sentence], metaclass = Metas.Argument):
    """
    Create an argument from sentence objects. For parsing strings into arguments,
    see ``Parser.argument``.
    """
    def __init__(self,
        conclusion: Sentence,
        premises: Iterable[Sentence] = tuple(),
        title: str = None
    ):
        if premises is None:
            self.sentences = (Sentence(conclusion),)
        else:
            self.sentences = tuple(map(Sentence, (conclusion, *premises)))
        if title is not None:
            instcheck(title, str)
        self.title = title

    __slots__ = 'sentences', 'title', '_hash'

    @property
    def conclusion(self) -> Sentence:
        return self.sentences[0]

    @property
    def premises(self) -> tuple[Sentence, ...]:
        return self.sentences[1:]

    @lazyget.prop
    def hash(self) -> int:
        return hash(tuple(self))

    def __len__(self):
        return len(self.sentences)

    def __iter__(self) -> Iterator[Sentence]:
        return iter(self.sentences)

    def __getitem__(self, index: Types.IndexType) -> Sentence:
        return self.sentences[index]

    def _cmp(self, other: Argument) -> int:
        if self is other: return 0
        cmp = bool(self.conclusion) - bool(other.conclusion)
        cmp = len(self) - len(other)
        if cmp: return cmp
        cmp = len(self.premises) - len(other.premises)
        if cmp: return cmp
        for a, b in zip(self, other):
            if a < b: return -1
            if a > b: return 1
        return cmp

    @metad.temp
    def compare(method):
        oper = getattr(opr, method.__name__)
        @wraps(method)
        def f(self: Argument, other: Argument):
            if not isinstance(self, other.__class__):
                return NotImplemented
            return oper(self._cmp(other), 0)
        return f
    @compare
    def __lt__(): ...
    @compare
    def __le__(): ...
    @compare
    def __gt__(): ...
    @compare
    def __ge__(): ...
    @compare
    def __eq__():
        """Two arguments are considered equal just when their conclusions are
        equal, and their premises are equal (and in the same order). The
        title is not considered in equality."""

    def __hash__(self): return self.hash

    def __repr__(self):
        if self.title: desc = repr(self.title)
        else: desc = 'len(%d)' % len(self)
        return '<%s:%s>' % (self.__class__.__name__, desc)

    def __setattr__(self, attr, value):
        if hasattr(self, attr): raise AttributeError(attr)
        super().__setattr__(attr, value)

    def __delattr__(self, attr): raise AttributeError(attr)

##############################################################
##############################################################

class Notation(Bases.Enum, metaclass = Metas.Notation):

    encodings        : set[str]
    default_encoding : str
    writers          : set[type[LexWriter]]
    default_writer   : type[LexWriter]
    rendersets       : set[RenderSet]
    __slots__ = (
        'encodings', 'default_encoding', 'writers',
        'default_writer', 'rendersets',
    )

    default: ClassVar[Notation]

    polish   = (enum.auto(), 'ascii')
    standard = (enum.auto(), 'unicode')

    def __init__(self, num, default_encoding):
        self.encodings = {default_encoding}
        self.default_encoding = default_encoding
        self.writers = set()
        self.default_writer = None
        self.rendersets = set()

    def __repr__(self):
        return utils.orepr(self.__class__.__name__, _=self.name)

class LexWriter(metaclass = Metas.LexWriter):

    notation: Notation
    encoding: str

    __slots__ = ()

    def __call__(self, item: Bases.Lexical) -> str:
        return self.write(item)

    def write(self, item: Bases.Lexical) -> str:
        'Write a lexical item.'
        return self._write(item)

    def _write(self, item: Bases.Lexical) -> str:
        try:
            method = self._methodmap[item.TYPE]
        except AttributeError:
            raise TypeError(type(item))
        except KeyError:
            raise NotImplementedError(type(item))
        return getattr(self, method)(item)

    @classmethod
    def canwrite(cls, item) -> bool:
        try: return item.TYPE in cls._methodmap
        except AttributeError: return False

    _methodmap: Mapping[LexType, str] = Types.MapProxy({
        ltype: NotImplemented for ltype in LexType
    })

    def _test(self):
        return list(map(self, (t.cls.first() for t in LexType)))

    @final
    @classmethod
    def register(cls, subcls: type[LexWriter]) -> type[LexWriter]:
        subclscheck(subcls, __class__)
        for ltype, meth in subcls._methodmap.items():
            try:
                getattr(subcls, meth)
            except TypeError:
                raise TypeError(meth, ltype)
            except AttributeError:
                raise TypeError('Missing method', meth, subcls)
        notn = subcls.notation = Notation(subcls.notation)
        notn.writers.add(subcls)
        if notn.default_writer is None:
            notn.default_writer = subcls
        return subcls

    def __init_subclass__(subcls: type[LexWriter], **kw):
        super().__init_subclass__(**kw)
        cls = __class__
        methmap: dict = cls.merge_mroattr(subcls, '_methodmap', supcls = cls)
        subcls._methodmap = Types.MapProxy(methmap)

class RenderSet(Types.CacheNotationData):

    default_fetch_name = 'ascii'

    def __init__(self, data: Mapping):
        instcheck(data, Mapping)
        self.name: str = data['name']
        self.notation = Notation(data['notation'])
        self.encoding: str = data['encoding']
        self.renders: Mapping[Any, Callable] = data.get('renders', {})
        self.formats: Mapping[Any, str] = data.get('formats', {})
        self.strings: Mapping[Any, str] = data.get('strings', {})
        self.data = data
        self.notation.encodings.add(self.encoding)
        self.notation.rendersets.add(self)

    def strfor(self, ctype, value) -> str:
        if ctype in self.renders:
            return self.renders[ctype](value)
        if ctype in self.formats:
            return self.formats[ctype].format(value)
        return self.strings[ctype][value]

class BaseLexWriter(LexWriter):

    notation: ClassVar[Notation]

    opts: dict
    renderset: RenderSet
    __slots__ = 'opts', 'renderset'

    defaults: dict = {}

    @property
    def encoding(self) -> str:
        return self.renderset.encoding

    def __init__(self, enc = None, renderset: RenderSet = None, **opts):
        notation = self.notation
        if renderset is None:
            if enc is None: enc = notation.default_encoding
            renderset = RenderSet.fetch(notation.name, enc)
        elif enc is not None and enc != renderset.encoding:
            raise ValueError('encoding', enc, renderset.encoding)
        self.opts = self.defaults | opts
        self.renderset = renderset

    _methodmap: ClassVar = {
        LexType.Operator   : '_write_plain',
        LexType.Quantifier : '_write_plain',
        LexType.Predicate  : '_write_predicate',
        LexType.Constant   : '_write_coordsitem',
        LexType.Variable   : '_write_coordsitem',
        LexType.Atomic     : '_write_coordsitem',
        LexType.Predicated : '_write_predicated',
        LexType.Quantified : '_write_quantified',
        LexType.Operated   : '_write_operated',
    }
    # Base lex writer.
    def _strfor(self, *args, **kw) -> str:
        return self.renderset.strfor(*args, **kw)

    def _write_plain(self, item: Bases.Lexical):
        return self._strfor(item.TYPE, item)

    def _write_coordsitem(self, item: CoordsItem) -> str:
        return ''.join((
            self._strfor(item.TYPE, item.index),
            self._write_subscript(item.subscript),
        ))

    def _write_predicate(self, item: Predicate) -> str:
        return ''.join((
            self._strfor((LexType.Predicate, item.is_system), item.index),
            self._write_subscript(item.subscript),
        ))

    def _write_quantified(self, item: Quantified) -> str:
        return ''.join(map(self._write, item.items))

    def _write_predicated(self, item: Predicated) -> str:
        return ''.join(map(self._write, (item.predicate, *item)))

    def _write_subscript(self, s: int) -> str:
        if s == 0: return ''
        return self._strfor('subscript', s)

    @abstract
    def _write_operated(self, item: Operated): ...

@LexWriter.register
class PolishLexWriter(BaseLexWriter):

    notation = Notation.polish
    def _write_operated(self, item: Operated):
        return ''.join(map(self._write, (item.operator, *item)))

@LexWriter.register
class StandardLexWriter(BaseLexWriter):

    notation = Notation.standard
    defaults = {'drop_parens': True}

    def write(self, item: Bases.Lexical) -> str:
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
        return ''.join((
            self._write(item.params[0]),
            ws,
            self._write(pred),
            ws,
            ''.join(map(self._write, item.params[1:])),
        ))

    def _write_operated(self, item: Operated, drop_parens = False):
        oper = item.operator
        arity = oper.arity
        if arity == 1:
            operand = item.operand
            if (oper == Operator.Negation and
                operand.predicate == Predicates.System.Identity):
                return self._write_negated_identity(item)
            else:
                return self._write(oper) + self._write(operand)
        elif arity == 2:
            lhs, rhs = item
            return ''.join((
                self._strfor('paren_open', 0) if not drop_parens else '',
                self._strfor('whitespace', 0).join(map(self._write, (lhs, oper, rhs))),
                self._strfor('paren_close', 0) if not drop_parens else '',
            ))
        raise NotImplementedError('arity %s' % arity)

    def _write_negated_identity(self, item: Operated):
        si: Predicated = item.operand
        params = si.params
        return self._strfor('whitespace', 0).join((
            self._write(params[0]),
            # self._strfor('whitespace', 0),
            self._strfor((LexType.Predicate, True), (item.operator, si.predicate)),
            # self._strfor('whitespace', 0),
            self._write(params[1]),
        ))

    def _test(self):
        s1 = Predicates.System.Identity(Constant.gen(2)).negate()
        s2 = Operator.Conjunction(Atomic.gen(2))
        s3 = s2.disjoin(Atomic.first())
        return super()._test() + list(map(self, [s1, s2, s3]))

@callables.calls.now
def _():
    from copy import deepcopy
    data = {
        'polish': {
            'ascii': {
                'name'     : 'polish.ascii',
                'notation' : Notation.polish,
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
    data['polish']['html'] = deepcopy(data['polish']['ascii'])
    data['polish']['html'].update({
        'name': 'polish.html',
        'encoding': 'html',
        'formats': {'subscript': '<sub>{0}</sub>'},
    })
    data['polish']['unicode'] = data['polish']['ascii']
    data.update({
        'standard': {
            'ascii': {
                'name'     : 'standard.ascii',
                'notation' : Notation.standard,
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
                'notation': Notation.standard,
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
                'notation': Notation.standard,
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
    RenderSet._initcache(Notation.names, data)


_syslw = LexWriter()

##############################################################

@callables.calls.now
def _():
    for cls in (Bases.Enum, Bases.LexicalItem, Predicates, Argument, Bases.Lexical):
        # cls._readonly = cls._clsinit = True
        cls._readonly = True

del(_, isreadonly, raisen, enum, callables, final,
wraps, metad, abstract, fixed, lazyget)