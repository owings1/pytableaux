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

# import enum
# from collections.abc import Sequence

# import itertools
# import functools
# from collections import \
#     deque
# from functools import \
#     partial as ft_partial, \
#     reduce  as ft_reduce

# repeat      as it_repeat, \
# from itertools import \
#     chain       as it_chain, \
#     starmap     as it_smap, \
#     zip_longest as it_lzip


# from typing import ClassVar

# import callables
# from containers import setf, setm, qsetf, qsetm



# import utils

# from pprint import pp

# from errors import \
#     DuplicateKeyError, \
#     DuplicateValueError, \
#     ReadOnlyAttributeError, \
#     ValueMismatchError

# from collections import deque
# from typing import Final, NamedTuple, 
# from callables import calls#, preds
# from containers import cqset
# from itertools import chain
# from functools import wraps
# import types
# from types import DynamicClassAttribute, MappingProxyType

# flatiter = it_chain.from_iterable
# NOARG = enum.auto()
# NOGET = enum.auto()
ITEM_CACHE_SIZE = 10000


# def isreadonly(cls: type) -> bool:
#     return all(getattr(cls, attr, None) for attr in ('_clsinit', '_readonly'))



# def nochangeattr(basecls, **kw):
#     opts = {'changeonly': True} | kw
#     return nosetattr(basecls, **opts)

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

import operator as opr
from utils import instcheck as _instcheck

class errors:
    'errors'

    from errors import  DuplicateKeyError, DuplicateValueError, \
        ReadOnlyAttributeError, ValueMismatchError

    __slots__ = __new__ = ()

class d:
    'decorators'

    from decorators import  abstract, fixed, lazyget as lazy, metad as meta, \
        operd as oper, raisen as raises, rund as run, wraps

    from typing import final

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

    __slots__ = __new__ = ()

class fict:
    '(f)unction, (i)terable, and (c)ontainer (t)ools'

    from functools import partial, reduce
    from itertools import chain, repeat, starmap, zip_longest as lzip
    from containers import setf, setm, qsetf
    from utils import it_drain as drain

    def flat(): ...
    flat = chain.from_iterable
    __slots__ = __new__ = ()

class std:
    'misc standard/common imports'

    from typing import Annotated, Any, ClassVar, NamedTuple
    from enum import auto, Enum, EnumMeta
    from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence

    __slots__ = ()

class Types:

    NOARG = object()
    NOGET = object()

    from types import \
        DynamicClassAttribute as DynClsAttr, \
        MappingProxyType      as MapProxy

    from utils import \
        ABCMeta,           \
        BiCoords,          \
        CacheNotationData, \
        EmptySet,          \
        FieldItemSequence, \
        IndexType,         \
        IntTuple,          \
        SortBiCoords,      \
        TriCoords

    from collections.abc import \
        Callable

    from containers import \
        DequeCache,         \
        MutableSequenceSet, \
        MutSetSeqPair,      \
        SequenceApi,        \
        SequenceSet,    \
        SetApi

    class EnumLookupValue(std.NamedTuple):
        member: std.Enum
        index: int
        nextmember: std.Enum | None

    EnumMemberLookup = MapProxy[std.Any, EnumLookupValue]

    Spec = tuple
    Ident = tuple[str, tuple]

    ParameterCoords = BiCoords
    AtomicCoords    = BiCoords
    PredicateCoords = TriCoords

    ParameterSpec   = BiCoords
    ParameterIdent  = tuple[str, BiCoords]


    QuantifierSpec = tuple[str]
    OperatorSpec   = tuple[str]

    PredicateSpec   = TriCoords
    PredicateRef    = IntTuple | str

    AtomicSpec     = BiCoords
    PredicatedSpec = tuple[TriCoords, tuple[ParameterIdent, ...]]
    QuantifiedSpec = tuple[str, BiCoords, Ident]
    OperatedSpec   = tuple[str, tuple[Ident, ...]]

    Lexical        : type # ...

    PredsItemRef  = PredicateRef  # | Predicate
    PredsItemSpec = PredicateSpec # | Predicate

    QuantifiedItem : type #= Quantifier | Variable | Sentence

    LexType     : type # ...

    deferred = {
        'Lexical', 'PredsItemRef', 'PredsItemSpec', 'QuantifiedItem', 'LexType',
    }

    def __new__(cls):
        attrs = dict(cls.__dict__)
        try: todo: set = attrs.pop('deferred')
        except KeyError: raise TypeError() from None
        reader = cls.MapProxy(attrs)
        def setitem(key, value):
            todo.remove(key)
            attrs[key] = value
        class Journal:
            __slots__ = ()
            def __dir__(self):
                return list(reader)
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
        return object.__new__(Journal)

    __slots__ = ()

Types = Types()

class Metas:

    __new__ = None

    class Abc(Types.ABCMeta):
        'General-purpose base Metaclass for all Abc (non-Enum) classes.'

        # ----------------------
        #  Class Creation
        # ----------------------
        @staticmethod
        def nsclean(Class, attrs: dict, bases, **kw):
            'MetaFlag cleanup method.'
            # Force `type` as deleter for cleanup hook.
            kw = dict(deleter = type.__delattr__) | kw
            Types.ABCMeta.nsclean(Class, attrs, bases, **kw)

        # -----------------------
        # Attribute Access
        # -----------------------
        _readonly : bool
        __delattr__ = d.raises(AttributeError)
        __setattr__ = d.nosetattr(type)

    class Enum(std.EnumMeta):
        'General-purpose base Metaclass for all Enum classes.'

        # ----------------------------
        #  Class Instance Variables
        # ----------------------------
        _lookup : Types.EnumMemberLookup
        _seq    : tuple[Bases.Enum, ...]

        # ----------------------
        #  Class Creation
        # ----------------------
        def __new__(cls, clsname, bases, attrs, **kw):

            # Run MetaFlag namespace init hooks.
            Metas.Abc.nsinit(attrs, bases, **kw)
            # Create class.
            Class = super().__new__(cls, clsname, bases, attrs, **kw)
            # Run MetaFlag clean hook.
            Metas.Abc.nsclean(Class, attrs, bases, **kw)

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

        @classmethod
        @d.final
        def _create_index(cls, Class: Metas.Enum) -> Types.MapProxy:
            'Create the member lookup index'
            # Member to key set functions.
            keys_funcs = (
                cls._default_keys,
                Class._member_keys,
            )
            # Merges keys per member from all key_funcs.
            keys_it = map(fict.setm, map(
                fict.flat, zip(*(
                    map(f, Class) for f in keys_funcs
                ))
            ))
            # Builds the member cache entry: (member, i, next-member).
            value_it = fict.starmap(Types.EnumLookupValue, fict.lzip(
                Class, range(len(Class)), Class.seq[1:]
            ))
            # Fill in the member entries for all keys and merge the dict.
            merge_it = fict.reduce(opr.or_,
                fict.starmap(dict.fromkeys, zip(keys_it, value_it))
            )
            return Types.MapProxy(merge_it)

        @staticmethod
        @d.final
        def _default_keys(member: Bases.Enum):
            'Default member lookup keys'
            return fict.setm({
                member._name_, (member._name_,), member,
                member._value_, # hash(member),
            })

        @classmethod
        @d.final
        def _clear_hooks(cls, Class: Metas.Enum):
            'Cleanup spent hook methods.'
            fdel = fict.partial(type(cls).__delattr__, Class)
            names = cls._hooks & Class.__dict__
            fict.drain(map(fdel, names))

        _hooks = fict.setf({
            '_member_keys', '_on_init', '_after_init'
        })

        #----------------------
        # Subclass Init Hooks       
        #----------------------

        def _member_keys(cls, member: Bases.Enum) -> std.Iterable:
            'Init hook to get the index lookup keys for a member.'
            return Types.EmptySet

        def _on_init(cls, Class: Metas.Enum):
            '''Init hook after all members have been initialized, before index
            is created. Skips abstract classes.'''

        def _after_init(cls):
            'Init hook once the class is initialized. Includes abstract classes.'

        #----------------------
        # Container behavior   
        #----------------------
        def __contains__(cls, key):
            return cls.get(key, Types.NOGET) is not Types.NOGET

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

        def __iter__(cls) -> std.Iterator[Bases.Enum]:
            return iter(cls.seq)

        def __reversed__(cls) -> std.Iterator[Bases.Enum]:
            return reversed(cls.seq)

        def __call__(cls, value, *args, **kw) -> Bases.Enum:
            if not args:
                try: return cls[value]
                except KeyError: pass
            return super().__call__(value, *args, **kw)

        def __dir__(cls):
            return list(cls.names)

        @property
        def __members__(cls):
            # Override to not double-proxy
            return cls._member_map_

        #--------------------
        # Member methods   
        #--------------------

        @Types.DynClsAttr
        def names(cls):
            'The member names.'
            return cls._member_names_

        @Types.DynClsAttr
        def seq(cls):
            'The sequence of member objects.'
            try: return cls._seq
            except AttributeError: return ()

        def get(cls, key, default = Types.NOARG) -> Bases.Enum:
            '''Get a member by an indexed reference key. Raises KeyError if not
            found and no default specified.'''
            try: return cls[key]
            except KeyError:
                if default is Types.NOARG: raise
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

        # -----------------------
        # Attribute Access
        # -----------------------

        _readonly : bool

        __delattr__ = d.raises(AttributeError)
        __setattr__ = d.nosetattr(std.EnumMeta)

    class LexicalItem(Abc):
        'Metaclass for LexicalItem classes (Constant, Predicate, Sentence, etc.).'

        Cache: std.ClassVar[Types.DequeCache]

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
                if not issubclass(lextypecls, cls):
                    raise TypeError(lextypecls, cls)
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

class Bases:

    __new__ = None

    class Enum(std.Enum, metaclass = Metas.Enum):
        'Generic base class for all Enum classes.'

        # -----------------------
        # Copy Behavior
        # -----------------------
        def __copy__(self):
            return self

        def __deepcopy__(self, memo):
            memo[id(self)] = self
            return self

        # -----------------------
        # Attribute Access
        # -----------------------
        __delattr__ = d.raises(AttributeError)
        __setattr__ = d.nosetattr(std.Enum, cls = True)
        __slots__   = '_value_', '_name_', '__objclass__'

        #----------------------
        # Metaclass Hooks       
        #----------------------
        # Propagate class hooks up to metaclass, so they can be implemented
        # in either the meta or concrete classes.
        @classmethod
        def _on_init(cls: Metas.Enum, Class):
            'Propagate hook up to metaclass.'
            type(cls)._on_init(cls, Class)

        @classmethod
        def _member_keys(cls: Metas.Enum, member: Bases.Enum) -> Types.SetApi:
            'Propagate hook up to metaclass.'
            return type(cls)._member_keys(cls, member)

        @classmethod
        def _after_init(cls: Metas.Enum):
            'Propagate hook up to metaclass.'
            type(cls)._after_init(cls)

        def __repr__(self):
            name, fmt = self.__class__.__name__, '<%s.%s>'
            try: return fmt % (name, self.name)
            except AttributeError: return '<%s ?ERR?>' % name

    class Lexical:
        'Lexical mixin class for both ``LexicalEnum`` and ``LexicalItem`` classes.'

        # ---------------------
        # Class Variables
        # ---------------------

        #: LexType Enum instance.
        TYPE: std.ClassVar[LexType]

        # --------------------
        # Instance Variables
        # --------------------

        #: The arguments roughly needed to construct, given that we know the
        #: type, i.e. in intuitive order. A tuple, possibly nested, containing
        #: digits or strings.
        spec: Types.Spec

        #: Equality identifier able to compare across types. A tuple, possibly
        #: nested, containing digits and possibly strings. The first should be
        #: the class name. Most naturally this would be followed by the spec.
        ident: Types.Ident

        #: Sorting identifier, to order tokens of the same type. Numbers only
        #: (no strings). This is also used in hashing, so equal objects should
        #: have equal sort_tuples. The first value must be the lexical rank of
        # the type.
        sort_tuple: Types.IntTuple

        #: The integer hash property.
        hash: int

        # -------------------
        # Item Comparison
        # -------------------
        @staticmethod
        def identitem(item: Bases.Lexical) -> Types.Ident:
            'Build an ``ident`` tuple from the class name and ``spec``.'
            return (item.__class__.__name__, item.spec)

        @staticmethod
        def hashitem(item: Bases.Lexical) -> int:
            'Compute a hash based on class name and ``sort_tuple``.'
            return hash((item.__class__.__name__, item.sort_tuple))

        @staticmethod
        @d.final
        def orderitems(item: Bases.Lexical, other: Bases.Lexical) -> int:
            '''Pairwise ordering comparison based on type rank and ``sort_tuple``.
            Raises TypeError.'''
            if item is other: return 0
            a, b = map(LexType.foritem, (item, other))
            cmp = a.rank - b.rank
            if cmp: return cmp
            a, b = item.sort_tuple, other.sort_tuple
            for x, y in zip(a, b):
                cmp = x - y
                if cmp: return cmp
            return len(a) - len(b)

        __lt__ = d.oper.order(opr.lt)(orderitems)
        __le__ = d.oper.order(opr.le)(orderitems)
        __gt__ = d.oper.order(opr.gt)(orderitems)
        __ge__ = d.oper.order(opr.ge)(orderitems)
        __eq__ = d.oper.order(opr.eq)(orderitems)

        def __hash__(self):
            return self.hash
        # @d.abstract
        # def __eq__(self, other): ...

        # @d.abstract
        # def __hash__(self): ...

        # --------------------
        # Item Generation
        # --------------------
        @classmethod
        def gen(cls,
            n: int,
            first: Bases.Lexical = None,
            **opts
        ) -> std.Iterator[Bases.Lexical]:
            'Generate items.'
            if first is not None:
                _instcheck(first, cls)
            for i in range(n):
                item = item.next(**opts) if i else (first or cls.first())
                if item: yield item

        @classmethod
        @d.abstract
        def first(cls): ...

        @d.abstract
        def next(self, **kw): ...

        # -----------------------
        # Copy Behavior
        # -----------------------
        def __copy__(self):
            return self

        def __deepcopy__(self, memo):
            memo[id(self)] = self
            return self

        # ----------------
        # Other Behaviors
        # ----------------
        __bool__ = d.fixed.value(True)
        __repr__ = _lexrepr
        __str__  = _lexstr

        # -----------------------
        # Attribute Access
        # -----------------------

        __delattr__ = d.raises(AttributeError)
        __setattr__ = d.nosetattr(object, cls = Metas.LexicalItem)
        __slots__ = ()
        # ----------------------------------------
        # Mixin attributes for Metaclasses to copy.
        # ----------------------------------------

        __copyattrs__ = d.run(
            lambda d, keys: Types.MapProxy(
                # {'_lexicalattrcopy_': True} |
                {k:d[k] for k in keys}
            ),
            locals(), (
                'gen', '__repr__', '__str__', '__bool__',
                'identitem', 'hashitem', 'orderitems',
                '__lt__', '__le__', '__gt__', '__ge__',
            )
        )

    Types.Lexical = Lexical
    Metas.LexicalItem.Cache = Types.DequeCache(Lexical, ITEM_CACHE_SIZE)

    class LexicalEnum(Lexical, Enum):
        'Base Enum implementation of Lexical. For Quantifier and Operator classes.'

        # ---------------------------
        # Lexical Instance Variables
        # ---------------------------
        spec       : tuple[str]
        ident      : tuple[str, tuple[str]]
        sort_tuple : Types.IntTuple
        hash       : int

        # -------------------------------
        # Enum Instance Variables
        # -------------------------------
        #: The member name.
        name: str
        #: Label with spaces allowed.
        label: str
        #: Index of the member in the enum list, in source order, 0-based.
        _index: int
        #: A number to signify order independenct of source or other constraints.
        order: int
        #: Name, label, or other strings unique to a member.
        strings: Types.SetApi[str]

        @Types.DynClsAttr
        def index(self) -> int:
            'Index of the member in the enum list, in source order, 0-based.'
            return self._index

        # -------------------
        # Item Comparison
        # -------------------
        def __eq__(self, other):
            'Allow equality with the string name.'
            return self is other or other in self.strings

        def __hash__(self):
            return self.hash

        # --------------------
        # Item Generation
        # --------------------
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

        # --------------------------
        # Instance init.
        # --------------------------
        def __init__(self, order, label, *_):
            self.spec = (self.name,)
            self.order, self.label = order, label
            self.sort_tuple = (self.order,)
            self.ident = Bases.Lexical.identitem(self)
            self.hash = Bases.Lexical.hashitem(self)
            self.strings = fict.setf({self.name, self.label})
            super().__init__()

        # -----------------------
        # Attribute Access
        # -----------------------
        # Inherited from ``Bases.Enum``::
        #
        #   __setattr__()   __delattr__()

        __slots__ = (
            'spec', 'ident', 'sort_tuple', 'hash',
            'label', '_index', 'order', 'strings',
        )

        # --------------------------
        # Enum meta hooks.
        # --------------------------
        @classmethod
        def _member_keys(cls, member: Bases.LexicalEnum) -> set:
            'Enum init hook. Index keys for Enum members lookups.'
            return fict.setm(super()._member_keys(member)) | {
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

        # --------------------------
        # Class init.
        # --------------------------
        @d.meta.nsinit
        def copy_lexical(attrs, bases, **kw):
            'Copy mixin Lexical attributes.'
            Lexical, = Metas.Abc.basesmap(bases)['Lexical']
            attrs |= Lexical.__copyattrs__

    class LexicalItem(Lexical, metaclass = Metas.LexicalItem):
        'Base Lexical Item class.'

        # -------------------------
        # Instance Variables
        # -------------------------
        @d.lazy.prop
        def ident(self) -> Types.Ident:
            return Lexical.identitem(self)

        @d.lazy.prop
        def hash(self) -> int:
            return Lexical.hashitem(self)

        # -------------------
        # Item Comparison
        # -------------------
        # def __hash__(self):
        #     return self.hash

        # def __eq__(self, other: Bases.Lexical):
        #     return self is other or (
        #         self.TYPE == LexType.get(other.__class__, ...) and
        #         self.ident == other.ident
        #     )

        # --------------------------
        # Instance init.
        # --------------------------
        def __new__(cls, *args):
            if cls not in LexType:
                raise TypeError('Abstract type %s' % cls)
            return super().__new__(cls)

        @d.abstract
        def __init__(self): ...

        # -----------------------
        # Attribute Access
        # -----------------------
        __slots__ = '_ident', '_hash'

        __delattr__ = d.raises(AttributeError)

        def __setattr__(self, name, value):
            if getattr(self, name, value) is not value:
                if isinstance(getattr(self.__class__, name, None), property):
                    pass
                else:
                    raise errors.ReadOnlyAttributeError(name, self)
            super().__setattr__(name, value)

        # --------------------------
        # Class init.
        # --------------------------
        @d.meta.nsinit
        def copy_lexical(attrs, bases, **kw):
            'Copy mixin Lexical attributes.'
            Lexical, = Metas.Abc.basesmap(bases)['Lexical']
            attrs |= Lexical.__copyattrs__


    class CoordsItem(LexicalItem):

        # -------------------------
        # Class Variables
        # -------------------------
        Coords: std.ClassVar = Types.BiCoords
        _fieldsenumerated: std.ClassVar[Types.FieldItemSequence]

        # -------------------------
        # Instance Variables
        # -------------------------

        #: The item coordinates.
        coords: Types.BiCoords
        spec: Types.BiCoords

        #: The coords index.
        index: int

        #: The coords subscript.
        subscript: int

        #: The reversed coords for sorting.
        scoords: Types.SortBiCoords

        @d.lazy.prop
        def sort_tuple(self) -> Types.BiCoords:
            return self.scoords

        @d.lazy.prop
        def scoords(self) -> Types.SortBiCoords:
            return self.coords.sorting()

        # --------------------
        # Item Generation
        # --------------------
        @classmethod
        def first(cls) -> Bases.CoordsItem:
            return cls(cls.Coords.first)

        def next(self, **kw) -> Bases.CoordsItem:
            idx, sub, *cargs = self.coords
            if idx < self.TYPE.maxi:
                idx += 1
            else:
                idx = 0
                sub += 1
            coords = self.Coords(idx, sub, *cargs)
            return self.__class__(coords)

        # --------------------------
        # Instance init.
        # --------------------------
        def __init__(self, *coords: Types.IntTuple):
            if len(coords) == 1: coords, = coords
            self.coords = self.spec = self.Coords(*coords)
            for val in self.coords: _instcheck(val, int)
            for i, f in self._fieldsenumerated:
                setattr(self, f, coords[i])
            if self.index > self.TYPE.maxi:
                raise ValueError('%d > %d' % (self.index, self.TYPE.maxi))
            if self.subscript < 0:
                raise ValueError('%d < %d' % (self.subscript, 0))

        # -----------------------
        # Attribute Access
        # -----------------------
        __slots__ = (
            'spec', 'coords', 'index', 'subscript',
            '_sort_tuple', '_scoords',
        )

        # --------------------------
        # Class init.
        # --------------------------
        def __init_subclass__(subcls: type[Bases.CoordsItem], **kw):
            super().__init_subclass__(**kw)
            subcls._fieldsenumerated = tuple(enumerate(subcls.Coords._fields))

Lexical = Bases.Lexical

##############################################################
##############################################################

class Quantifier(Bases.LexicalEnum):
    'Quantifier Lexical Enum class.'

    Existential = (0, 'Existential')
    Universal   = (1, 'Universal')

    def __call__(self, *spec: Types.QuantifiedSpec) -> Quantified:
        'Quantify a variable over a sentence.'
        return Quantified(self, *spec)
    
class Operator(Bases.LexicalEnum):
    'Operator Lexical Enum class.'

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
        'Apply the operator to make a new sentence.'
        return Operated(self, *spec)

    arity: int

    def __init__(self, *value):
        self.arity = value[2]
        super().__init__(*value)

    __slots__ = 'arity',

##############################################################

class Predicate(Bases.CoordsItem):
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
    # -------------------
    # Class Variables
    # -------------------
    Coords   : std.ClassVar[type[Types.TriCoords]] = Types.TriCoords

    # -------------------------
    # Instance Variables
    # -------------------------
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

    @d.lazy.prop
    def bicoords(self) -> Types.BiCoords:
        return Types.BiCoords(*self.spec[0:2])

    @d.lazy.prop
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

    @d.lazy.prop
    def refkeys(self) -> Types.SequenceSet[Types.PredicateRef | Predicate]:
        'The ``refs`` plus the predicate object.'
        return fict.qsetf({*self.refs, self})

    # -----------------------
    # Behaviors
    # -----------------------
    def __call__(self, *spec: Types.PredicatedSpec) -> Predicated:
        'Apply the predicate to parameters to make a predicated sentence.'
        return Predicated(self, *spec)

    def __str__(self):
        return self.name if self.is_system else super().__str__()

    # --------------------
    # Item Generation
    # --------------------
    def next(self, **kw) -> Predicate:
        arity = self.arity
        if self.is_system:
            pred: Predicate
            for pred in self.System:
                if pred > self and pred.arity == arity:
                    return pred
        return super().next(**kw)

    # --------------------------
    # Instance init.
    # --------------------------
    def __init__(self, *spec: Types.PredicatedSpec):
        if len(spec) == 1 and isinstance(spec[0], tuple):
            spec, = spec
        if len(spec) not in (3, 4):
            raise TypeError('need 3 or 4 elements, got %s' % len(spec))
        super().__init__(*spec[0:3])
        self.is_system = self.index < 0
        if self.is_system and len(self.System):
            raise ValueError('`index` must be >= 0')
        if _instcheck(self.arity, int) <= 0:
            raise ValueError('`arity` must be > 0')
        name = spec[3] if len(spec) == 4 else None
        self.name = self.spec if name is None else name
        if name is not None:
            if len(self.System) and name in self.System:
                raise ValueError('System predicate: %s' % name)
            _instcheck(name, (tuple, str))

    # -----------------------
    # Attribute Access
    # -----------------------
    __slots__ = 'arity', 'is_system', 'name', '_bicoords', '_refs', '_refkeys'

    # --------------------------
    # System Enum properties.
    # --------------------------
    class System(Bases.Enum):

        Existence : std.Annotated[Predicate, (-2, 0, 1, 'Existence')]
        Identity  : std.Annotated[Predicate, (-1, 0, 2, 'Identity')]

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

    @d.meta.temp
    def sysset(prop: property):
        name = prop.fget.__name__
        @d.wraps(prop.fget)
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

class Parameter(Bases.CoordsItem):

    is_constant: bool
    is_variable: bool

    __init__ = Bases.CoordsItem.__init__

class Constant(Parameter):

    is_constant = d.fixed.prop(True)
    is_variable = d.fixed.prop(False)

class Variable(Parameter):

    is_constant = d.fixed.prop(False)
    is_variable = d.fixed.prop(True)

##############################################################

class Sentence(Bases.LexicalItem):

    __slots__ = ()

    predicate  : Predicate  | None
    quantifier : Quantifier | None
    operator   : Operator   | None

    #: Whether this is an atomic sentence.
    is_atomic = d.fixed.prop(False)
    #: Whether this is a predicated sentence.
    is_predicated = d.fixed.prop(False)
    #: Whether this is a quantified sentence.
    is_quantified = d.fixed.prop(False)
    #: Whether this is an operated sentence.
    is_operated = d.fixed.prop(False)
    #: Whether this is a literal sentence. Here a literal is either a
    #: predicated sentence, the negation of a predicated sentence,
    #: an atomic sentence, or the negation of an atomic sentence.
    is_literal = d.fixed.prop(False)
    #: Whether this is an atomic sentence.
    is_negated = d.fixed.prop(False)

    #: Set of predicates, recursive.
    predicates: frozenset[Predicate] = d.fixed.prop(Types.EmptySet)
    #: Set of constants, recursive.
    constants: frozenset[Constant] = d.fixed.prop(Types.EmptySet)
    #: Set of variables, recursive.
    variables: frozenset[Variable] = d.fixed.prop(Types.EmptySet)
    #: Set of atomic sentences, recursive.
    atomics: frozenset[Atomic] = d.fixed.prop(Types.EmptySet)
    #: Tuple of quantifiers, recursive.
    quantifiers: tuple[Quantifier, ...] = d.fixed.prop(tuple())
    #: Tuple of operators, recursive.
    operators: tuple[Operator, ...] = d.fixed.prop(tuple())

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

class Atomic(Sentence, Bases.CoordsItem):

    predicate  = d.fixed.prop(None)
    quantifier = d.fixed.prop(None)
    operator   = d.fixed.prop(None)

    is_atomic  = d.fixed.prop(True)
    is_literal = d.fixed.prop(True)
    variable_occurs = d.fixed.value(False)

    @d.lazy.prop
    def atomics(self) -> frozenset[Atomic]:
        return frozenset({self})

    __init__ = Bases.CoordsItem.__init__

    __slots__ = '_atomics',

class Predicated(Sentence, std.Sequence[Parameter]):
    'Predicated sentence.'

    # -------------------------
    #  Instance Variables
    # -------------------------
    spec: Types.PredicatedSpec

    #: The predicate.
    predicate: Predicate

    #: The parameters
    params: tuple[Parameter, ...]

    @property
    def arity(self) -> int:
        'The arity of the predicate'
        return self.predicate.arity

    @d.lazy.prop
    def paramset(self) -> frozenset[Parameter]:
        'The set of parameters.'
        return frozenset(self.params)

    quantifier    = d.fixed.prop(None)
    operator      = d.fixed.prop(None)
    is_predicated = d.fixed.prop(True)
    is_literal    = d.fixed.prop(True)

    @d.lazy.prop
    def spec(self) -> Types.PredicatedSpec:
        return (self.predicate.spec, tuple(p.ident for p in self))

    @d.lazy.prop
    def sort_tuple(self) -> Types.IntTuple:
        items = (self.predicate, *self)
        return tuple(fict.flat(it.sort_tuple for it in items))

    @d.lazy.prop
    def predicates(self) -> frozenset[Predicate]:
        return frozenset({self.predicate})

    @d.lazy.prop
    def constants(self) -> frozenset[Constant]:
        return frozenset(p for p in self.paramset if p.is_constant)

    @d.lazy.prop
    def variables(self) -> frozenset[Variable]:
        return frozenset(p for p in self.paramset if p.is_variable)

    # --------------------
    #  Sentence methods
    # --------------------
    def substitute(self, pnew: Parameter, pold: Parameter) -> Predicated:
        if pnew == pold or pold not in self: return self
        params = (pnew if p == pold else p for p in self)
        return Predicated(self.predicate, tuple(params))

    # --------------------
    #  Instance init.
    # --------------------
    def __init__(self, pred, params: std.Iterable[Parameter] | Parameter):
        if isinstance(pred, str):
            self.predicate = Predicates.System(pred)
        else:
            self.predicate = Predicate(pred)
        if isinstance(params, Parameter):
            self.params = (params,)
        else:
            self.params = tuple(map(Parameter, params))
        if len(self) != self.predicate.arity:
            raise TypeError(self.predicate, len(self), self.arity)

    # --------------------
    #  Item Generation
    # --------------------
    @classmethod
    def first(cls, predicate: Predicate = None) -> Predicated:
        pred = predicate or Predicate.first()
        c = Constant.first()
        params = tuple(c for i in range(pred.arity))
        return cls(pred, params)

    def next(self, **kw) -> Predicated:
        return Predicated(self.predicate.next(**kw), self.params)

    # -----------------------
    #  Sequence Behavior
    # -----------------------
    def __iter__(self) -> std.Iterator[Parameter]:
        return iter(self.params)

    def __getitem__(self, index: Types.IndexType) -> Parameter:
        return self.params[index]

    def __len__(self):
        return len(self.params)

    def __contains__(self, p: Parameter):
        return p in self.paramset

    # -----------------------
    #  Attribute Access
    # -----------------------
    __slots__ = (
        'predicate', 'params',
        '_spec', '_sort_tuple', '_paramset',
        '_predicates', '_constants', '_variables'
    )

class Quantified(Sentence, std.Sequence[Types.QuantifiedItem]):
    'Quantified sentence.'
    # -------------------------
    # Instance Variables
    # -------------------------
    spec: Types.QuantifiedSpec

    #: The quantifier
    quantifier: Quantifier

    #: The bound variable
    variable: Variable

    #: The inner sentence
    sentence: Sentence

    #: The items sequence: Quantifer, Variable, Sentence.
    items: tuple[Quantifier, Variable, Sentence]

    predicate     = d.fixed.prop(None)
    operator      = d.fixed.prop(None)
    is_quantified = d.fixed.prop(True)

    @d.lazy.prop
    def spec(self) -> Types.QuantifiedSpec:
        return self.quantifier.spec + (self.variable.spec, self.sentence.ident)

    @d.lazy.prop
    def sort_tuple(self) -> Types.IntTuple:
        return tuple(fict.flat(item.sort_tuple for item in self))

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

    @d.lazy.prop
    def quantifiers(self) -> tuple[Quantifier, ...]:
        return (self.quantifier, *self.sentence.quantifiers)

    # --------------------
    #  Sentence methods
    # --------------------
    def substitute(self, pnew: Parameter, pold: Parameter) -> Quantified:
        if pnew == pold: return self
        q, v, s = self
        return self.__class__(q, v, s.substitute(pnew, pold))

    def variable_occurs(self, v: Variable) -> bool:
        return self.variable == v or self.sentence.variable_occurs(v)

    def unquantify(self, c: Constant) -> Sentence:
        'Instantiate the variable with a constant.'
        return self.sentence.substitute(Constant(c), self.variable)

    # --------------------
    #  Instance init.
    # --------------------
    def __init__(self, q: Quantifier, v: Variable, s: Sentence):
        self.quantifier, self.variable, self.sentence = self.items = (
            Quantifier(q), Variable(v), Sentence(s)
        )

    # --------------------
    #  Item Generation
    # --------------------
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

    # -----------------------
    #  Sequence Behavior
    # -----------------------
    def __iter__(self) -> std.Iterator[Types.QuantifiedItem]:
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __contains__(self, item: Types.QuantifiedItem):
        return item in self.items

    def __getitem__(self, index: Types.IndexType) -> Types.QuantifiedItem:
        return self.items[index]

    def count(self, item: Types.QuantifiedItem) -> int:
        return int(item in self)

    def index(self, item: Types.QuantifiedItem) -> int:
        return self.items.index(item)

    # -----------------------
    #  Attribute Access
    # -----------------------
    __slots__ = (
        'quantifier', 'variable', 'sentence', 'items',
        '_spec', '_sort_tuple', '_quantifiers',
    )

class Operated(Sentence, std.Sequence[Sentence]):
    'Operated sentence.'

    # -------------------------
    # Instance Variables
    # -------------------------
    spec: Types.OperatedSpec

    #: The operator
    operator: Operator

    #: The operands.
    operands: tuple[Sentence, ...]

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

    predicate   = d.fixed.prop(None)
    quantifier  = d.fixed.prop(None)
    is_operated = d.fixed.prop(True)

    @d.lazy.prop
    def is_literal(self) -> bool:
        return self.is_negated and self[0].TYPE in (Atomic, Predicated)

    @d.lazy.prop
    def spec(self) -> Types.OperatedSpec:
        return self.operator.spec + (tuple(s.ident for s in self),)

    @d.lazy.prop
    def sort_tuple(self) -> Types.IntTuple:
        return tuple(fict.flat(it.sort_tuple for it in (self.operator, *self)))

    @d.lazy.prop
    def predicates(self) -> frozenset[Predicate]:
        return frozenset(fict.flat(s.predicates for s in self))

    @d.lazy.prop
    def constants(self) -> frozenset[Constant]:
        return frozenset(fict.flat(s.constants for s in self))

    @d.lazy.prop
    def variables(self) -> frozenset[Variable]:
        return frozenset(fict.flat(s.variables for s in self))

    @d.lazy.prop
    def atomics(self) -> frozenset[Atomic]:
        return frozenset(fict.flat(s.atomics for s in self))

    @d.lazy.prop
    def quantifiers(self) -> tuple[Quantifier, ...]:
        return tuple(fict.flat(s.quantifiers for s in self))

    @d.lazy.prop
    def operators(self) -> tuple[Operator, ...]:
        return (self.operator,) + tuple(fict.flat(s.operators for s in self))

    # --------------------
    #  Item Generation
    # --------------------
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

    # --------------------
    #  Sentence methods
    # --------------------
    def substitute(self, pnew: Parameter, pold: Parameter) -> Operated:
        if pnew == pold: return self
        operands = (s.substitute(pnew, pold) for s in self)
        return self.__class__(self.operator, tuple(operands))

    # --------------------
    #  Instance init.
    # --------------------
    def __init__(self, oper: Operator, operands: std.Iterable[Sentence] | Sentence):
        if isinstance(operands, Sentence):
            self.operands = (operands,)
        else:
            self.operands = tuple(map(Sentence, operands))
        self.operator = Operator(oper)
        if len(self.operands) != self.operator.arity:
            raise TypeError(self.operator, len(self.operands), self.operator.arity)

    # -----------------------
    #  Sequence Behavior
    # -----------------------
    def __iter__(self) -> std.Iterator[Sentence]:
        return iter(self.operands)

    def __getitem__(self, index: Types.IndexType) -> Sentence:
        return self.operands[index]

    def __len__(self):
        return len(self.operands)

    def __contains__(self, s: Sentence):
        return s in self.operands

    # -----------------------
    #  Attribute Access
    # -----------------------
    __slots__ = (
        'operator', 'operands', '_is_literal', '_spec', '_sort_tuple',
        '_predicates', '_constants', '_variables', '_atomics', '_quantifiers',
        '_operators',
    )

##############################################################
##############################################################

class LexType(Bases.Enum):

    classes: std.ClassVar[Types.SequenceSet[type[Bases.Lexical]]]

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

    @d.meta.temp
    def compare(method):
        oper = getattr(opr, method.__name__)
        @d.wraps(method)
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
        name, fmt = __class__.__name__, '<%s.%s>'
        try: return fmt % (name, self.cls)
        except AttributeError: return '<%s ?ERR?>' % name

    @classmethod
    def foritem(cls, obj) -> LexType:
        '''Get the LexType for a Lexical instance. Performance focused.
        Raises TypeError.'''
        try: return cls._lookup[obj.__class__].member
        except KeyError:
            raise TypeError(obj.__class__, LexType) from None

    # --------------------------
    # Enum meta hooks.
    # --------------------------

    @classmethod
    def _after_init(cls: type[LexType]):
        super()._after_init()
        cls.classes = fict.qsetf((m.cls for m in cls))
        pass

    @classmethod
    def _member_keys(cls, member: LexType) -> set:
        'Enum lookup index init hook.'
        return fict.setm(super()._member_keys(member)) | {
            member.cls
        }

Types.LexType = LexType

##############################################################
##############################################################

class Predicates(Types.MutableSequenceSet[Predicate], metaclass = Metas.Abc):
    'Predicate store'

    def __init__(self, specs: std.Iterable[Types.PredsItemSpec] = None):
        super().__init__(Types.MutSetSeqPair(set(), []))
        self._lookup = {}
        if specs is not None:
            self.update(specs)

    _lookup: dict[Types.PredsItemRef, Predicate]
    __slots__ = '_lookup',

    def get(self, ref: Types.PredsItemRef, default = Types.NOARG) -> Predicate:
        """Get a predicate by any reference. Also searches System predicates.
        Raises KeyError when no default specified."""
        try: return self._lookup[ref]
        except KeyError:
            try: return self.System[ref]
            except KeyError: pass
            if default is Types.NOARG: raise
            return default

    # -------------------------------
    #  MutableSequenceSet hooks.
    # -------------------------------
    def _new_value(self, value: Types.PredsItemSpec) -> Predicate:
        'Implement new_value hook. Return a predicate.'
        return Predicate(value)

    def _before_add(self, pred: Predicate):
        'Implement before_add hook. Check for arity/value conflicts.'
        m, keys = self._lookup, pred.refkeys
        conflict = fict.setm(filter(None, map(m.get, keys))) - {pred}
        if len(conflict):
            other = next(iter(conflict))
            raise errors.ValueMismatchError(other.coords, pred.coords)

    def _after_add(self, pred: Predicate):
        'Implement after_add hook. Add keys to lookup index.'
        m, keys = self._lookup, pred.refkeys
        # ---------- extra check
        conflict = keys & m
        if len(conflict):
            raise errors.DuplicateKeyError(pred, *conflict)
        # ----------
        m.update(zip(keys, fict.repeat(pred)))

    def _after_remove(self, pred: Predicate):
        'Implement after_remove hook. Remove keys from lookup index.'
        m, keys = self._lookup, pred.refkeys
        conflict = fict.setm(map(m.pop, keys)) - {pred}
        if len(conflict):
            raise errors.DuplicateValueError(pred, *conflict)

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

    # -------------------------
    #  Predicates.System Enum
    # -------------------------
    class System(Predicate.System):
        'System Predicates enum container class.'

        # --------------------------
        # Instance init.
        # --------------------------
        def __new__(cls, *spec):
            'Set the Enum value to the predicate instance.'
            return Bases.LexicalItem.__new__(Predicate)

        # --------------------------
        # Enum meta hooks.
        # --------------------------
        @classmethod
        def _member_keys(cls, pred: Predicate) -> Types.SetApi[Types.PredsItemRef]:
            'Enum lookup index init hook. Add all predicate keys.'
            return fict.setm(super()._member_keys(pred)) | \
                pred.refkeys

        @classmethod
        def _after_init(cls):
            'Enum after init hook. Set Predicate class attributes.'
            super()._after_init()
            for pred in cls:
                setattr(Predicate, pred.name, pred)
            Predicate.System = cls

        # --------------------------
        # Class init.
        # --------------------------
        @d.meta.nsinit
        def expand(attrs, bases, **kw):
            'Inject members from annotations in Predicate.System class.'
            annots = Metas.Abc.annotated_attrs(Predicate.System)
            members = {
                name: spec for name, (vtype, spec)
                in annots.items() if vtype is Predicate
            }
            attrs |= members
            attrs._member_names.extend(members.keys())

class Argument(std.Sequence[Sentence], metaclass = Metas.Argument):
    'Create an argument from sentence objects.'

    def __init__(self,
        conclusion: Sentence,
        premises: std.Iterable[Sentence] = tuple(),
        title: str = None
    ):
        if premises is None:
            self.sentences = (Sentence(conclusion),)
        else:
            self.sentences = tuple(map(Sentence, (conclusion, *premises)))
        if title is not None:
            _instcheck(title, str)
        self.title = title

    __slots__ = 'sentences', 'title', '_hash'

    @property
    def conclusion(self) -> Sentence:
        return self.sentences[0]

    @property
    def premises(self) -> tuple[Sentence, ...]:
        return self.sentences[1:]

    @d.lazy.prop
    def hash(self) -> int:
        return hash(tuple(self))

    # -----------------------
    #  Sequence Behavior
    # -----------------------
    def __len__(self):
        return len(self.sentences)

    def __iter__(self) -> std.Iterator[Sentence]:
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

    @d.meta.temp
    def compare(method):
        oper = getattr(opr, method.__name__)
        @d.wraps(method)
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
#                                                            #
#       LexWriters                                           #
#                                                            #
##############################################################

class Notation(Bases.Enum, metaclass = Metas.Notation):
    'Notation (polish/standard) enum class.'

    default: std.ClassVar[Notation]

    encodings        : set[str]
    default_encoding : str
    writers          : set[type[LexWriter]]
    default_writer   : type[LexWriter]
    rendersets       : set[RenderSet]

    polish   = (std.auto(), 'ascii')
    standard = (std.auto(), 'unicode')

    def __init__(self, num, default_encoding):
        self.encodings = {default_encoding}
        self.default_encoding = default_encoding
        self.writers = set()
        self.default_writer = None
        self.rendersets = set()

    __slots__ = (
        'encodings', 'default_encoding', 'writers',
        'default_writer', 'rendersets',
    )

class LexWriter(metaclass = Metas.LexWriter):
    'LexWriter Api and Coordinator class.'

    # --------------------------
    # Class Variables.
    # --------------------------
    notation: Notation
    _methodmap: std.Mapping[LexType, str] = Types.MapProxy({
        ltype: NotImplemented for ltype in LexType
    })

    # --------------------------
    # Instance Variables.
    # --------------------------
    encoding: str

    # --------------------------
    # Public API.
    # --------------------------
    def __call__(self, item: Bases.Lexical) -> str:
        return self.write(item)

    def write(self, item: Bases.Lexical) -> str:
        'Write a lexical item.'
        return self._write(item)

    @classmethod
    def canwrite(cls, item) -> bool:
        try: return item.TYPE in cls._methodmap
        except AttributeError: return False

    # --------------------------
    # Instance init.
    # --------------------------
    @d.abstract
    def __init__(self): ...

    # --------------------------
    # Internal API.
    # --------------------------
    def _write(self, item: Bases.Lexical) -> str:
        'Wrapped internal write method.'
        try:
            method = self._methodmap[item.TYPE]
        except AttributeError:
            raise TypeError(type(item))
        except KeyError:
            raise NotImplementedError(type(item))
        return getattr(self, method)(item)

    def _test(self) -> list[str]:
        'Smoke test. Returns a rendered list of each lex type.'
        return list(map(self, (t.cls.first() for t in LexType)))

    # --------------------------
    # Attribute access.
    # --------------------------
    __slots__ = ()

    # --------------------------
    # Class init.
    # --------------------------
    @d.final
    @classmethod
    def register(cls, subcls: type[LexWriter]) -> type[LexWriter]:
        'Class decorator to update available writers.'
        if not issubclass(subcls, __class__):
            raise TypeError(subcls, __class__)
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
        'Subclass init hook. Merge and freeze method map from mro.'
        super().__init_subclass__(**kw)
        cls = __class__
        methmap: dict = cls.merge_mroattr(subcls, '_methodmap', supcls = cls)
        subcls._methodmap = Types.MapProxy(methmap)

class RenderSet(Types.CacheNotationData):

    default_fetch_name = 'ascii'

    def __init__(self, data: std.Mapping):
        _instcheck(data, std.Mapping)
        self.name: str = data['name']
        self.notation = Notation(data['notation'])
        self.encoding: str = data['encoding']
        self.renders: std.Mapping[std.Any, std.Callable] = data.get('renders', {})
        self.formats: std.Mapping[std.Any, str] = data.get('formats', {})
        self.strings: std.Mapping[std.Any, str] = data.get('strings', {})
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

    # --------------------------
    #  Class Variables
    # --------------------------
    notation: std.ClassVar[Notation]
    defaults: std.ClassVar[dict] = {}
    _methodmap: std.ClassVar = {
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

    # --------------------------
    #  Instance Variables
    # --------------------------
    opts: dict
    renderset: RenderSet

    @property
    def encoding(self) -> str:
        return self.renderset.encoding

    # --------------------------
    #  Instance init.
    # --------------------------
    def __init__(self, enc = None, renderset: RenderSet = None, **opts):
        notation = self.notation
        if renderset is None:
            if enc is None: enc = notation.default_encoding
            renderset = RenderSet.fetch(notation.name, enc)
        elif enc is not None and enc != renderset.encoding:
            raise ValueError('encoding', enc, renderset.encoding)
        self.opts = self.defaults | opts
        self.renderset = renderset

    # --------------------------
    #  Attribute access.
    # --------------------------
    __slots__ = 'opts', 'renderset'

    # --------------------------
    #  Default implementations.
    # --------------------------
    @d.abstract
    def _write_operated(self, item: Operated): ...

    def _strfor(self, *args, **kw) -> str:
        return self.renderset.strfor(*args, **kw)

    def _write_plain(self, item: Bases.Lexical):
        return self._strfor(item.TYPE, item)

    def _write_coordsitem(self, item: Bases.CoordsItem) -> str:
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

@d.run
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
    # return data
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

# foo = _
##############################################################

@d.run
def _():
    for cls in (Bases.Enum, Bases.LexicalItem, Predicates, Argument, Bases.Lexical):
        cls._readonly = True

del(_, )