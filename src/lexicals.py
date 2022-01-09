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

__all__ = (
    'Operator', 'Quantifier', 'Parameter', 'Constant', 'Variable', 'Predicate',
    'Sentence', 'Atomic', 'Predicated', 'Quantified', 'Operated',
    'LexType', 'Predicates', 'Argument', 
    'Notation', 'LexWriter', 'BaseLexWriter', 'PolishLexWriter', 'StandardLexWriter',
)
##############################################################


import operator as opr
from errors import instcheck as _instcheck
from typing import overload

class cons:
    'constants'
    NOARG = object()
    NOGET = object()
    from tools.sets import EMPTY_SET
    ITEM_CACHE_SIZE = 10000

    __new__ = None

class std:
    'Various standard/common imports'

    from typing import (
        Annotated, Any, Callable, ClassVar, Iterable, Iterator, Mapping, 
        NamedTuple, Sequence, SupportsIndex, TypeVar
        
    )
    from enum import auto, Enum, EnumMeta, _EnumDict

    __new__ = None

class errors:
    'errors'

    from errors import (
        ReadOnlyAttributeError, ValueMismatchError, ValueCollisionError
    )

    __new__ = None

class d:
    'decorators'

    from decorators import (
        fixed, lazyget as lazy, membr, operd as oper,
        raisr, rund as run, wraps
    )

    def nodelattr():
        return d.raisr(AttributeError)

    def nosetattr(basecls, cls = None, changeonly = False,  **kw):
        forigin = basecls.__setattr__
        def fset(self, attr, val):
            if cls:
                if cls == True: checkobj = type(self)
                else: checkobj = cls
            else:
                checkobj = self
            try:
                acheck = checkobj._readonly
            except AttributeError: pass
            else:
                if acheck:
                    if changeonly:
                        if getattr(self, attr, val) is not val:
                            raise AttributeError('%s.%s is immutable' % (self, attr))
                    else:
                        raise AttributeError("%s is readonly" % checkobj)
            forigin(self, attr, val)
        return fset

    __new__ = None

from tools.abcs import abcm, abcf
from tools.sets import setf

class fict:
    '(f)unction, (i)terable, and (c)ontainer (t)ools'

    from functools import partial, reduce
    from itertools import chain, repeat, starmap, zip_longest as lzip
    from tools.hybrids import qsetf, qset
    from tools.sets import setm
    from utils import it_drain as drain

    flat = chain.from_iterable

    @overload
    def sorttmap(it: std.Iterable[Bases.Lexical]) -> std.Iterable[Types.IntTuple]: ...
    sorttmap = partial(map, opr.attrgetter('sort_tuple'))

    __new__ = None

_T = std.TypeVar('_T')
_F = std.TypeVar('_F', bound = std.Callable[..., std.Any])

class Types:

    from types import \
        DynamicClassAttribute as DynClsAttr, \
        MappingProxyType      as MapProxy

    from tools.abcs import AbcMeta
    from tools.hybrids import SequenceSetApi
    from tools.sets import SetApi, MutableSetApi
    from tools.sequences import SequenceApi
    from tools.mappings import DequeCache

    from utils import CacheNotationData

    class EnumEntry(std.NamedTuple):
        member : Bases.Enum
        index  : int
        nextmember: Bases.Enum | None

    class BiCoords(std.NamedTuple):
        index     : int
        subscript : int
    
        class Sorting(std.NamedTuple):
            subscript : int
            index     : int

        def sorting(self) -> Types.BiCoords.Sorting:
            return self.Sorting(self.subscript, self.index)

        first = (0, 0)

    BiCoords.first = BiCoords._make(BiCoords.first)

    class TriCoords(std.NamedTuple):
        index     : int
        subscript : int
        arity     : int

        class Sorting(std.NamedTuple):
            subscript : int
            index     : int
            arity     : int

        def sorting(self) -> Types.TriCoords.Sorting:
            return self.Sorting(self.subscript, self.index, self.arity)

        first = (0, 0, 1)

    TriCoords.first = TriCoords._make(TriCoords.first)

    IntTuple = tuple[int, ...]
    IndexType = std.SupportsIndex | slice
    FieldItemSequence = std.Sequence[tuple[int, str]]

    Spec = tuple
    Ident = tuple[str, tuple]

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

    deferred = {
        'Lexical', 'PredsItemRef', 'PredsItemSpec', 'QuantifiedItem', 'LexType',
    }

    Lexical        : type[Bases.Lexical]

    PredsItemRef:  type[PredicateRef | Predicate]  = PredicateRef
    PredsItemSpec: type[PredicateSpec | Predicate] = PredicateSpec

    QuantifiedItem : type[Quantifier | Variable | Sentence]

    LexType     : type[LexType]

    def __new__(cls):
        attrs = dict(cls.__dict__)
        try: todo: set = attrs.pop('deferred')
        except KeyError: raise TypeError from None
        reader = cls.MapProxy(attrs)
        def setitem(key, value):
            todo.remove(key)
            attrs[key] = value
        class Journal:
            __slots__ = cons.EMPTY_SET
            __new__ = object.__new__
            def __dir__(self):
                return list(reader)
            def __setattr__(self, name, value):
                try: return setitem(name, value)
                except KeyError: raise AttributeError(name) from None
            def __getattribute__(self, name) -> type:
                try: return reader[name]
                except KeyError: raise AttributeError(name) from None

        Journal.__qualname__ = cls.__qualname__
        Journal.__name__ = cls.__name__
        return Journal()

Types = Types()

##############################################################

class Metas:

    __new__ = None

    class Abc(Types.AbcMeta):
        'General-purpose base Metaclass for all Abc (non-Enum) classes.'

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Creation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @staticmethod
        def nsclean(Class, ns, bases, deleter = type.__delattr__, **kw):
            'MetaFlag cleanup method.'
            # Use `type` as deleter for cleanup hook.
            # kw = dict(deleter = type.__delattr__) | kw
            Types.AbcMeta.nsclean(Class, ns, bases, deleter = deleter, **kw)

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Attrbute Access ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        _readonly : bool
        __delattr__ = d.nodelattr()
        __setattr__ = d.nosetattr(type)

    class Enum(std.EnumMeta):
        'General-purpose base Metaclass for all Enum classes.'

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        _lookup : Types.MapProxy[std.Any, Types.EnumEntry]
        _seq    : tuple[Bases.Enum, ...]

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Creation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __new__(cls, clsname, bases, ns, **kw):

            # Run MetaFlag namespace init hooks.
            Metas.Abc.nsinit(ns, bases, **kw)
            # Create class.
            Class = super().__new__(cls, clsname, bases, ns, **kw)
            # Run MetaFlag clean hook.
            Metas.Abc.nsclean(Class, ns, bases, **kw)

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
        @abcm.final
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
            value_it = fict.starmap(Types.EnumEntry, fict.lzip(
                Class, range(len(Class)), Class.seq[1:]
            ))
            # Fill in the member entries for all keys and merge the dict.
            merge_it = fict.reduce(opr.or_,
                fict.starmap(dict.fromkeys, zip(keys_it, value_it))
            )
            return Types.MapProxy(merge_it)

        @staticmethod
        @abcm.final
        def _default_keys(member: Bases.Enum):
            'Default member lookup keys'
            return fict.setm((
                member._name_, (member._name_,), member,
                member._value_, # hash(member),
            ))

        @classmethod
        @abcm.final
        def _clear_hooks(cls, Class: Metas.Enum):
            'Cleanup spent hook methods.'
            fdel = fict.partial(type(cls).__delattr__, Class)
            names = cls._hooks & Class.__dict__
            fict.drain(map(fdel, names))

        _hooks = setf((
            '_member_keys', '_on_init', '_after_init'
        ))

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Subclass Init Hooks ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def _member_keys(cls, member: Bases.Enum) -> Types.SetApi:
            'Init hook to get the index lookup keys for a member.'
            return cons.EMPTY_SET

        def _on_init(cls, Class: Metas.Enum):
            '''Init hook after all members have been initialized, before index
            is created. Skips abstract classes.'''
            pass

        def _after_init(cls):
            'Init hook once the class is initialized. Includes abstract classes.'
            pass

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Container Behavior ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __contains__(cls, key):
            return cls.get(key, cons.NOGET) is not cons.NOGET

        def __getitem__(cls, key):
            if type(key) is cls: return key
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

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Member Methods ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @Types.DynClsAttr
        def names(cls):
            'The member names.'
            return cls._member_names_

        @Types.DynClsAttr
        def seq(cls):
            'The sequence of member objects.'
            try: return cls._seq
            except AttributeError: return ()

        def get(cls, key, default = cons.NOARG) -> Bases.Enum:
            '''Get a member by an indexed reference key. Raises KeyError if not
            found and no default specified.'''
            try: return cls[key]
            except KeyError:
                if default is cons.NOARG: raise
                return default

        def indexof(cls, member) -> int:
            'Get the sequence index of the member. Raises ValueError if not found.'
            try:
                try:
                    return cls._lookup[member][1]
                except KeyError:
                    return cls._lookup[cls[member]][1]
                except AttributeError:
                    return cls.seq.index(cls[member])
            except KeyError:
                raise ValueError(member)

        index = indexof

        def entryof(cls, key) -> Types.EnumEntry:
            try:
                return cls._lookup[key]
            except KeyError:
                return cls._lookup[cls[key]]
            except AttributeError:
                raise KeyError(key)

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Attrbute Access ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        _readonly : bool

        __delattr__ = d.nodelattr()
        __setattr__ = d.nosetattr(std.EnumMeta)

    class LexicalItem(Abc):
        'Metaclass for LexicalItem classes (Constant, Predicate, Sentence, etc.).'

        Cache: std.ClassVar[Types.DequeCache]

        def __call__(cls, *spec) -> Bases.LexicalItem:
            if len(spec) == 1:
                if isinstance(spec[0], cls):
                    # Passthrough
                    return spec[0]
                if isinstance(spec[0], str):
                    if cls is Predicate:
                        # System Predicate string
                        return Predicate.System(spec[0])
            # cache = LexicalItem.Cache
            cache = __class__.Cache
            clsname = cls.__name__
            # Try cache
            try: return cache[clsname, spec]
            except KeyError: pass
            # Construct
            try: inst: Bases.Lexical = super().__call__(*spec)
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
                inst = lextypecls(*spec)
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

        @d.lazy.dynca
        def _sys(cls) -> LexWriter:
            'The system LexWriter instance for representing.'
            try: return LexWriter()
            except NameError: raise AttributeError

        @_sys.setter
        def _sys(cls, value: LexWriter):
            try: _instcheck(value, LexWriter)
            except NameError: raise AttributeError
            setattr(LexWriter, '__sys', value)

    class Notation(Enum):
        'Notation Enum Metaclass.'

        @Types.DynClsAttr
        def default(cls: type[Notation]) -> Notation:
            return cls.polish

class Bases:

    __new__ = None

    class Enum(std.Enum, metaclass = Metas.Enum):
        'Generic base class for all Enum classes.'

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Copy Behavior ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __copy__(self):
            return self

        def __deepcopy__(self, memo):
            memo[id(self)] = self
            return self

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Attrbute Access ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        __delattr__ = d.nodelattr()
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

        def __init__(self): raise TypeError(self)

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        #: LexType Enum instance.
        TYPE: std.ClassVar[LexType]

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

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
        #: have equal sort_tuples.
        #:
        #: **NB**: The first value must be the lexical rank of the type.
        sort_tuple: Types.IntTuple

        #: The integer hash property.
        hash: int

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Comparison ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @staticmethod
        def identitem(item: Bases.Lexical) -> Types.Ident:
            'Build an ``ident`` tuple from the class name and ``spec``.'
            return type(item).__name__, item.spec

        @staticmethod
        def hashitem(item: Bases.Lexical) -> int:
            'Compute a hash based on class name and ``sort_tuple``.'
            return hash((type(item).__name__, item.sort_tuple))

        @staticmethod
        @abcm.final
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

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Generation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @classmethod
        def gen(cls, n: int, first: Bases.Lexical = None, **opts) \
            -> std.Iterator[Bases.Lexical]:
            'Generate items.'
            if first is not None:
                _instcheck(first, cls)
            for i in range(n):
                item = item.next(**opts) if i else (first or cls.first())
                if item: yield item

        @classmethod
        @abcm.abstract
        def first(cls): ...

        @abcm.abstract
        def next(self, **kw): ...

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Copy Behavior ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __copy__(self):
            'Return self.'
            return self

        def __deepcopy__(self, memo):
            'Return self.'
            memo[id(self)] = self
            return self

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Other Behaviors ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __bool__(self):
            'Return True.'
            return True

        def __repr__(self):
            try:
                return '<%s: %s>' % (self.TYPE.role, str(self))
            except AttributeError:
                return '<%s: ERR>' % type(self).__name__

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Attribute Access ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        __delattr__ = d.nodelattr()
        __setattr__ = d.nosetattr(object, cls = Metas.LexicalItem)
        __slots__ = cons.EMPTY_SET

    Types.Lexical = Lexical
    Metas.LexicalItem.Cache = Types.DequeCache(Lexical, cons.ITEM_CACHE_SIZE)

    class LexicalEnum(Lexical, Enum):
        'Base Enum implementation of Lexical. For Quantifier and Operator classes.'

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        # Lexical Instance Variables

        spec       : tuple[str]
        ident      : tuple[str, tuple[str]]
        sort_tuple : Types.IntTuple
        hash       : int

        # Enum Instance Variables

        #: The member name.
        name: str
        #: Label with spaces allowed.
        label: str
        #: A number to signify order independenct of source or other constraints.
        order: int
        #: Name, label, or other strings unique to a member.
        strings: Types.SetApi[str]

        @Types.DynClsAttr
        def index(self) -> int:
            'Index of the member in the enum list, in source order, 0-based.'
            return self._index

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Comparison ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __eq__(self, other):
            'Allow equality with the string name.'
            if self is other: return True
            if isinstance(other, str):
                return other in self.strings
            return NotImplemented

        def __hash__(self):
            return self.hash

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Generation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @classmethod
        def first(cls) -> Bases.LexicalEnum:
            'Return the first instance of this type.'
            return cls.seq[0]

        def next(self, loop = False) -> Bases.LexicalEnum:
            seq = self.__class__.seq
            i = self.index + 1
            if i == len(seq):
                if not loop: raise StopIteration
                i = 0
            return seq[i]

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Other Behaviors ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __str__(self):
            'Returns the name.'
            return self.name

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __init__(self, order, label, *_):
            self.spec = self.name,
            self.order, self.label = order, label
            # Prepended with rank in LexType init
            self.sort_tuple = self.order,
            self.ident = Bases.Lexical.identitem(self)
            self.hash = Bases.Lexical.hashitem(self)
            self.strings = setf((self.name, self.label))

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Attribute Access ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        __slots__ = (
            'spec', 'ident', 'sort_tuple', 'hash',
            'label', '_index', 'order', 'strings',
        )

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Enum Meta Hooks ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @classmethod
        def _member_keys(cls, member: Bases.LexicalEnum) -> Types.SetApi:
            'Enum init hook. Index keys for Enum members lookups.'
            return super()._member_keys(member) | {member.label, member.value}

        @classmethod
        def _on_init(cls, Class: type[Bases.LexicalEnum]):
            'Enum init hook. Store the sequence index of each member.'
            super()._on_init(Class)
            for i, member in enumerate(Class): member._index = i

    class LexicalItem(Lexical, metaclass = Metas.LexicalItem):
        'Base Lexical Item class.'

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        ident: Types.Ident = d.lazy.prop(Types.Lexical.identitem, '_ident')
        hash: int = d.lazy.prop(Types.Lexical.hashitem, '_hash')

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Other Behaviors ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __str__(self):
            'Write the item with the default LexWriter.'
            try: return LexWriter._sys(self)
            except NameError:
                try: return str(self.ident)
                except AttributeError as e:
                    return '%s(%s)' % (self.__class__.__name__, e)

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @abcm.abstract
        def __init__(self): ...

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Attribute Access ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        __slots__ = '_ident', '_hash'

        __delattr__ = d.nodelattr()

        def __setattr__(self, name, value):
            if getattr(self, name, value) is not value:
                if isinstance(getattr(type(self), name, None), property):
                    pass
                else:
                    raise errors.ReadOnlyAttributeError(name, self)
            super().__setattr__(name, value)

    class CoordsItem(LexicalItem):

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        Coords: std.ClassVar[type[Types.BiCoords]] = Types.BiCoords
        _fieldsenumerated: std.ClassVar[Types.FieldItemSequence]

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        #: The item coordinates.
        coords: Types.BiCoords
        spec: Types.BiCoords

        #: The coords index.
        index: int

        #: The coords subscript.
        subscript: int

        #: The reversed coords for sorting.
        scoords: Types.BiCoords.Sorting

        @d.lazy.prop
        def sort_tuple(self) -> Types.BiCoords:
            return self.TYPE.rank, *self.scoords

        @d.lazy.prop
        def scoords(self) -> Types.BiCoords.Sorting:
            return self.coords.sorting()

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Generation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @classmethod
        def first(cls) -> Bases.CoordsItem:
            'Return the first instance of this type.'
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

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __init__(self, *coords: Types.IntTuple):
            if len(coords) == 1: coords, = coords
            self.coords = self.spec = self.Coords(*coords)
            for val in self.coords: _instcheck(val, int)
            for i, f in self._fieldsenumerated:
                setattr(self, f, coords[i])
            try:
                if self.index > self.TYPE.maxi:
                    raise ValueError('%d > %d' % (self.index, self.TYPE.maxi))
                if self.subscript < 0:
                    raise ValueError('%d < %d' % (self.subscript, 0))
            except AttributeError:
                raise TypeError(self) from None

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Attribute Access ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        __slots__ = (
            'spec', 'coords', 'index', 'subscript', '_sort_tuple', '_scoords',
        )

        # --------------------------
        # Class init.
        # --------------------------
        def __init_subclass__(subcls: type[Bases.CoordsItem], **kw):
            super().__init_subclass__(**kw)
            subcls._fieldsenumerated = tuple(enumerate(subcls.Coords._fields))

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

class Parameter(Bases.CoordsItem):

    is_constant: bool
    is_variable: bool

class Constant(Parameter):

    is_constant = d.fixed.prop(True)
    is_variable = d.fixed.prop(False)

class Variable(Parameter):

    is_constant = d.fixed.prop(False)
    is_variable = d.fixed.prop(True)

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
    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    Coords: std.ClassVar[type[Types.TriCoords]] = Types.TriCoords

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    spec    : Types.TriCoords
    coords  : Types.TriCoords
    scoords : Types.TriCoords.Sorting
    refs    : tuple[Types.PredicateRef, ...]

    #: The coords arity.
    arity: int

    #: Whether this is a system predicate.
    is_system: bool

    #: The name or spec
    name: Types.IntTuple | str

    @d.lazy.prop
    def bicoords(self) -> Types.BiCoords:
        return Types.BiCoords(self.index, self.subscript)

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
    def refkeys(self) -> fict.qsetf[Types.PredicateRef | Predicate]:
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

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Generation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def next(self, **kw) -> Predicate:
        arity = self.arity
        if self.is_system:
            pred: Predicate
            for pred in self.System:
                if pred > self and pred.arity == arity:
                    return pred
        return super().next(**kw)

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __init__(self, *spec: Types.PredicatedSpec):
        if len(spec) == 1:
            if isinstance(spec[0], tuple):
                spec, = spec
        if len(spec) not in (3, 4):
            raise TypeError('need 3 or 4 elements, got %s' % len(spec))
        super().__init__(*spec[0:3])
        self.is_system = self.index < 0
        if self.is_system and len(self.System):
            raise ValueError('`index` must be >= 0')
        if self.arity <= 0:
            raise ValueError('`arity` must be > 0')
        name = spec[3] if len(spec) == 4 else None
        self.name = self.spec if name is None else name
        if name is not None:
            if len(self.System) and name in self.System:
                raise ValueError('System predicate: %s' % name)
            _instcheck(name, (tuple, str))

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Attribute Access ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    __slots__ = 'arity', 'is_system', 'name', '_bicoords', '_refs', '_refkeys'

    # --------------------------
    # System Enum properties.
    # --------------------------
    class System(Bases.Enum):

        Existence : std.Annotated[Predicate, (-2, 0, 1, 'Existence')]
        Identity  : std.Annotated[Predicate, (-1, 0, 2, 'Identity')]

    @Types.DynClsAttr
    def _value_(self: Predicate.System) -> Predicate.System:
        try:
            if self.is_system: return self
        except AttributeError: return self
        raise AttributeError('_value_')

    @Types.DynClsAttr
    def _name_(self: Predicate.System) -> str:
        if self.is_system: return self.name
        raise AttributeError('_name_')

    @Types.DynClsAttr
    def __objclass__(self: Predicate.System) -> type[Predicate.System]:
        if self.is_system: return __class__.System
        raise AttributeError('__objclass__')

    @abcf.temp
    def sysset(prop: property) -> property:
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

# Predicate()._value_
##############################################################

class Sentence(Bases.LexicalItem):

    __slots__ = ()

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

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
    #: Whether this is a negated sentence.
    is_negated = d.fixed.prop(False)
    #: Set of predicates, recursive.
    predicates: setf[Predicate] = d.fixed.prop(cons.EMPTY_SET)
    #: Set of constants, recursive.
    constants: setf[Constant] = d.fixed.prop(cons.EMPTY_SET)
    #: Set of variables, recursive.
    variables: setf[Variable] = d.fixed.prop(cons.EMPTY_SET)
    #: Set of atomic sentences, recursive.
    atomics: setf[Atomic] = d.fixed.prop(cons.EMPTY_SET)
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
    def atomics(self) -> setf[Atomic]:
        return setf({self})

    __init__ = Bases.CoordsItem.__init__

    __slots__ = '_atomics',

class Predicated(Sentence, Types.SequenceApi[Parameter]):
    'Predicated sentence.'

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    #: The predicate.
    predicate: Predicate

    #: The parameters
    params: tuple[Parameter, ...]

    @property
    def arity(self) -> int:
        'The arity of the predicate'
        return self.predicate.arity

    @d.lazy.prop
    def paramset(self) -> setf[Parameter]:
        'The set of parameters.'
        return setf(self.params)

    quantifier    = d.fixed.prop(None)
    operator      = d.fixed.prop(None)
    is_predicated = d.fixed.prop(True)
    is_literal    = d.fixed.prop(True)

    @d.lazy.prop
    def spec(self) -> Types.PredicatedSpec:
        return self.predicate.spec, tuple(p.ident for p in self.params)

    @d.lazy.prop
    def sort_tuple(self) -> Types.IntTuple:
        return self.TYPE.rank, *fict.flat(fict.sorttmap((self.predicate, *self.params)))

    @d.lazy.prop
    def predicates(self) -> setf[Predicate]:
        return setf({self.predicate})

    @d.lazy.prop
    def constants(self) -> setf[Constant]:
        return setf(p for p in self.paramset if p.is_constant)

    @d.lazy.prop
    def variables(self) -> setf[Variable]:
        return setf(p for p in self.paramset if p.is_variable)

    # --------------------
    #  Sentence methods
    # --------------------
    def substitute(self, pnew: Parameter, pold: Parameter) -> Predicated:
        if pnew == pold or pold not in self: return self
        return Predicated(self.predicate, tuple(
            (pnew if p == pold else p for p in self)
        ))

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __init__(self, pred, params: std.Iterable[Parameter] | Parameter):
        if isinstance(pred, str):
            self.predicate = Predicate.System(pred)
        else:
            self.predicate = Predicate(pred)
        if isinstance(params, Parameter):
            self.params = params,
        else:
            self.params = tuple(map(Parameter, params))
        if len(self) != self.predicate.arity:
            raise TypeError(self.predicate, len(self), self.arity)

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Generation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    @classmethod
    def first(cls, pred: Predicate = None,/) -> Predicated:
        if pred is None: pred = Predicate.first()
        return cls(pred, tuple(fict.repeat(Constant.first(), pred.arity)))

    def next(self, **kw) -> Predicated:
        return Predicated(self.predicate.next(**kw), self.params)

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Sequence Behavior ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __iter__(self) -> std.Iterator[Parameter]:
        return iter(self.params)

    @overload
    def __getitem__(self, i: int) -> Parameter: ...
    @overload
    def __getitem__(self, s: slice) -> tuple[Parameter, ...]: ...

    def __getitem__(self, index):
        return self.params[index]

    def __len__(self):
        return len(self.params)

    def __contains__(self, p):
        return p in self.paramset

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Attribute Access ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    __slots__ = (
        'predicate', 'params',
        '_spec', '_sort_tuple', '_paramset',
        '_predicates', '_constants', '_variables'
    )

class Quantified(Sentence, Types.SequenceApi[Types.QuantifiedItem]):
    'Quantified sentence.'

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

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
        return *self.quantifier.spec, self.variable.spec, self.sentence.ident

    @d.lazy.prop
    def sort_tuple(self) -> Types.IntTuple:
        return self.TYPE.rank, *fict.flat(fict.sorttmap(self))

    @property
    def constants(self) -> setf[Sentence]:
        return self.sentence.constants

    @property
    def variables(self) -> setf[Variable]:
        return self.sentence.variables

    @property
    def atomics(self) -> setf[Atomic]:
        return self.sentence.atomics

    @property
    def predicates(self) -> setf[Predicate]:
        return self.sentence.predicates

    @property
    def operators(self) -> tuple[Operator, ...]:
        return self.sentence.operators

    @d.lazy.prop
    def quantifiers(self) -> tuple[Quantifier, ...]:
        return self.quantifier, *self.sentence.quantifiers

    # --------------------
    #  Sentence methods
    # --------------------
    def substitute(self, pnew: Parameter, pold: Parameter) -> Quantified:
        if pnew == pold: return self
        return self.__class__(
            self.quantifier, self.variable, self.sentence.substitute(pnew, pold)
        )

    def variable_occurs(self, v: Variable) -> bool:
        return self.variable == v or self.sentence.variable_occurs(v)

    def unquantify(self, c: Constant) -> Sentence:
        'Instantiate the variable with a constant.'
        return self.sentence.substitute(Constant(c), self.variable)

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __init__(self, q: Quantifier, v: Variable, s: Sentence):
        self.quantifier, self.variable, self.sentence = self.items = (
            Quantifier(q), Variable(v), Sentence(s)
        )

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Generation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    @classmethod
    def first(cls, q: Quantifier = Quantifier.seq[0],/) -> Quantified:
        pred: Predicate = Predicate.first()
        return cls(q, Variable.first(), pred(
            (Variable.first(), *Constant.gen(pred.arity - 1))
        ))

    def next(self, **kw) -> Quantified:
        s: Sentence = self.sentence.next(**kw)
        v = self.variable
        if v not in s.variables:
            raise TypeError('%s no longer bound' % v)
        return self.__class__(self.quantifier, v, s)

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Sequence Behavior ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __iter__(self) -> std.Iterator[Types.QuantifiedItem]:
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __contains__(self, item: Types.QuantifiedItem):
        return item in self.items

    @overload
    def __getitem__(self, i: std.SupportsIndex) -> Types.QuantifiedItem: ...
    @overload
    def __getitem__(self, s: slice) -> std.Sequence[Types.QuantifiedItem]: ...

    def __getitem__(self, index):
        return self.items[index]

    def count(self, item: Types.QuantifiedItem) -> int:
        return int(item in self)

    def index(self, item: Types.QuantifiedItem) -> int:
        return self.items.index(item)

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Attribute Access ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    __slots__ = (
        'quantifier', 'variable', 'sentence', 'items',
        '_spec', '_sort_tuple', '_quantifiers',
    )

class Operated(Sentence, Types.SequenceApi[Sentence]):
    'Operated sentence.'

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

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
        return self.operands[0]
    @property
    def rhs(self) -> Sentence:
        'The last (right-most) operand.'
        return self.operands[-1]
    @property
    def operand(self) -> Sentence | None:
        'The operand if only one, else None.'
        return self.operands[0] if len(self.operands) == 1 else None
    @property
    def negatum(self) -> Sentence | None:
        'The operand if is negated, else None.'
        return self.operands[0] if self.is_negated else None
    @property
    def is_negated(self) -> bool:
        return self.operator == Operator.Negation

    predicate   = d.fixed.prop(None)
    quantifier  = d.fixed.prop(None)
    is_operated = d.fixed.prop(True)

    @d.lazy.prop
    def is_literal(self) -> bool:
        return self.is_negated and self.operands[0].TYPE in (Atomic, Predicated)

    @d.lazy.prop
    def spec(self) -> Types.OperatedSpec:
        return *self.operator.spec, tuple(s.ident for s in self)

    @d.lazy.prop
    def sort_tuple(self) -> Types.IntTuple:
        return self.TYPE.rank, *fict.flat(fict.sorttmap((self.operator, *self)))

    @d.lazy.prop
    def predicates(self) -> setf[Predicate]:
        return setf(fict.flat(s.predicates for s in self))

    @d.lazy.prop
    def constants(self) -> setf[Constant]:
        return setf(fict.flat(s.constants for s in self))

    @d.lazy.prop
    def variables(self) -> setf[Variable]:
        return setf(fict.flat(s.variables for s in self))

    @d.lazy.prop
    def atomics(self) -> setf[Atomic]:
        return setf(fict.flat(s.atomics for s in self))

    @d.lazy.prop
    def quantifiers(self) -> tuple[Quantifier, ...]:
        return *fict.flat(s.quantifiers for s in self),

    @d.lazy.prop
    def operators(self) -> tuple[Operator, ...]:
        return self.operator, *fict.flat(s.operators for s in self)

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Generation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    @classmethod
    def first(cls, oper: Operator = Operator.seq[0],/) -> Operated:
        return cls(oper, tuple(Atomic.gen(Operator(oper).arity)))

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

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __init__(self, oper: Operator, operands: std.Iterable[Sentence] | Sentence):
        if isinstance(operands, Sentence):
            self.operands = operands,
        else:
            self.operands = tuple(map(Sentence, operands))
        self.operator = Operator(oper)
        if len(self.operands) != self.operator.arity:
            raise TypeError(self.operator, len(self.operands), self.operator.arity)

    # -----------------------
    #  Sequence Behavior
    # -----------------------
    # def __iter__(self) -> std.Iterator[Sentence]:
    #     return iter(self.operands)

    def __getitem__(self, index: Types.IndexType) -> Sentence:
        return self.operands[index]

    def __len__(self):
        return len(self.operands)

    def __contains__(self, s: Sentence):
        return s in self.operands

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Attribute Access ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    __slots__ = (
        'operator', 'operands', '_is_literal', '_spec', '_sort_tuple',
        '_predicates', '_constants', '_variables', '_atomics', '_quantifiers',
        '_operators',
    )

##############################################################
##############################################################

class LexType(Bases.Enum):

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    classes: std.ClassVar[Types.SequenceSetApi[type[Bases.Lexical]]]

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

    @abcf.temp
    @d.membr.defer
    def ordr(member: d.membr[type[LexType]]):
        oper = getattr(opr, member.name)
        @d.wraps(oper)
        def f(self: LexType, other):
            if not isinstance(other, LexType):
                return NotImplemented
            return oper(self.rank, other.rank)
        return f

    __lt__ = __le__ = __gt__ = __ge__ = ordr()

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
        try: return cls._lookup[type(obj)].member
        except KeyError:
            raise TypeError(type(obj)) from None

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Enum Meta Hooks ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    @classmethod
    def _after_init(cls):
        'Build classes list, expand sort_tuple.'
        super()._after_init()
        cls.classes = fict.qsetf((m.cls for m in cls))
        for inst in fict.chain[Bases.LexicalEnum](Operator, Quantifier):
            inst.sort_tuple = inst.TYPE.rank, *inst.sort_tuple

    @classmethod
    def _member_keys(cls, member: LexType) -> Types.SetApi:
        'Enum lookup index init hook.'
        return super()._member_keys(member) | {member.cls}

Types.LexType = LexType

##############################################################
##############################################################

class Predicates(fict.qset[Predicate], metaclass = Metas.Abc):
    'Predicate store'

    _lookup: dict[Types.PredsItemRef, Predicate]
    __slots__ = '_lookup',

    def __init__(self, values: std.Iterable[Types.PredsItemSpec] = None, /):
        self._lookup = {}
        super().__init__(values)

    def get(self, ref: Types.PredsItemRef, default = cons.NOARG, /) -> Predicate:
        """Get a predicate by any reference. Also searches System predicates.
        Raises KeyError when no default specified."""
        try: return self._lookup[ref]
        except KeyError:
            try: return self.System[ref]
            except KeyError: pass
            if default is cons.NOARG: raise
            return default

    # -------------------------------
    #  qset hooks.
    # -------------------------------
    def _new_value(self, value: Types.PredsItemSpec) -> Predicate:
        'Implement new_value conversion hook. Ensure the value is a Predicate.'
        return Predicate(value)

    def _before_add(self, pred: Predicate):
        'Implement before_add hook. Check for arity/value conflicts.'
        for other in filter(None, map(self._lookup.get, pred.refkeys)):
            # Is there a distinct predicate that matches any lookup keys,
            # viz. BiCoords or name, that does not equal pred, e.g. arity
            # mismatch.
            if other != pred:
                raise errors.ValueMismatchError(other.coords, pred.coords)

    def _after_add(self, pred: Predicate):
        'Implement after_add hook. Add keys to lookup index.'
        self._lookup |= zip(pred.refkeys, fict.repeat(pred))

    def _after_remove(self, pred: Predicate):
        'Implement after_remove hook. Remove keys from lookup index.'
        for other in map(self._lookup.pop, pred.refkeys):
            # Is there a key we are removing that unexpectedly matches
            # a distinct predicate. This would have to be the result of
            # a failed removal or addition.
            if other != pred:
                raise errors.ValueCollisionError(other.coords, pred.coords)

    # -------------------------------
    #  Override qset
    # -------------------------------

    def clear(self):
        super().clear()
        self._lookup.clear()

    def __contains__(self, ref: Types.PredsItemRef):
        return ref in self._lookup

    def copy(self) -> Predicates:
        inst = super().copy()
        inst._lookup = self._lookup.copy()
        return inst

    # -------------------------
    #  Predicates.System Enum
    # -------------------------

    class System(Predicate.System):
        'System Predicates enum container class.'

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __new__(cls, *spec):
            'Set the Enum value to the predicate instance.'
            return Bases.LexicalItem.__new__(Predicate)

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Enum Meta Hooks ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @classmethod
        def _member_keys(cls, pred: Predicate) -> Types.SetApi[Types.PredsItemRef]:
            'Enum lookup index init hook. Add all predicate keys.'
            return super()._member_keys(pred) | pred.refkeys

        @classmethod
        def _after_init(cls):
            'Enum after init hook. Set Predicate class attributes.'
            super()._after_init()
            for pred in cls:
                setattr(Predicate, pred.name, pred)
            Predicate.System = cls

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Abc Meta Hooks ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @abcf.nsinit
        def expand(ns: std._EnumDict, bases, **kw):
            'Inject members from annotations in Predicate.System class.'
            annots = abcm.annotated_attrs(Predicate.System)
            members = {
                name: spec for name, (vtype, spec)
                in annots.items() if vtype is Predicate
            }
            ns |= members
            ns._member_names += members.keys()

class Argument(Types.SequenceApi[Sentence], metaclass = Metas.Argument):
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

    @overload
    def __getitem__(self, s: slice) -> Types.SequenceApi[Sentence]: ...
    @overload
    def __getitem__(self, i: std.SupportsIndex) -> Sentence: ...

    def __getitem__(self, index):
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

    @abcf.temp
    @d.membr.defer
    def ordr(member: d.membr[type[Argument]]):
        oper = getattr(opr, member.name)
        @d.wraps(oper)
        def f(self: Argument, other):
            if not isinstance(self, type(other)):
                return NotImplemented
            return oper(self._cmp(other), 0)
        return f
    # Two arguments are considered equal just when their conclusions are
    # equal, and their premises are equal (and in the same order). The
    # title is not considered in equality.
    __lt__ = __le__ = __gt__ = __ge__ = __eq__ = ordr()

    def __hash__(self): return self.hash

    def __repr__(self):
        if self.title: desc = repr(self.title)
        else: desc = 'len(%d)' % len(self)
        return '<%s:%s>' % (type(self).__name__, desc)

    def __setattr__(self, attr, value):
        if hasattr(self, attr): raise AttributeError(attr)
        super().__setattr__(attr, value)

    __delattr__ = d.nodelattr

##############################################################
#                                                            #
#       LexWriters                                           #
#                                                            #
##############################################################

class Notation(Bases.Enum, metaclass = Metas.Notation):
    'Notation (polish/standard) enum class.'

    default: std.ClassVar[Notation]

    encodings        : Types.MutableSetApi[str]
    default_encoding : str
    writers          : Types.MutableSetApi[type[LexWriter]]
    default_writer   : type[LexWriter]
    rendersets       : Types.MutableSetApi[RenderSet]

    polish   = (std.auto(), 'ascii')
    standard = (std.auto(), 'unicode')

    def __init__(self, num, default_encoding):
        self.encodings = fict.setm((default_encoding,))
        self.default_encoding = default_encoding
        self.writers = fict.setm()
        self.default_writer = None
        self.rendersets = fict.setm()

    __slots__ = (
        'encodings', 'default_encoding', 'writers',
        'default_writer', 'rendersets',
    )

class LexWriter(metaclass = Metas.LexWriter):
    'LexWriter Api and Coordinator class.'

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    notation: Notation
    _methodmap: std.Mapping[LexType, str] = Types.MapProxy({
        ltype: NotImplemented for ltype in LexType
    })
    _sys: std.ClassVar[LexWriter]

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
    @abcm.abstract
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
    __slots__ = cons.EMPTY_SET

    # --------------------------
    # Class init.
    # --------------------------
    @classmethod
    def register(cls, subcls: type[LexWriter]):
        'Update available writers.'
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
        type(cls).register(cls, subcls)
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

class BaseLexWriter(LexWriter, metaclass = Metas.LexWriter):

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

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
    @abcm.abstract
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
                operand.predicate == Predicate.System.Identity):
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
            self._strfor((LexType.Predicate, True), (item.operator, si.predicate)),
            self._write(params[1]),
        ))

    def _test(self):
        s1 = Predicate.System.Identity(Constant.gen(2)).negate()
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
                    LexType.Atomic   : tuple('abcde'),
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
                    LexType.Variable   : tuple('xyzv'),
                    LexType.Constant   : tuple('mnos'),
                    LexType.Quantifier : {
                        Quantifier.Universal   : 'V',
                        Quantifier.Existential : 'S',
                    },
                    (LexType.Predicate, True) : {
                        Predicate.System.Identity.index  : 'I',
                        Predicate.System.Existence.index : 'J',
                        (Operator.Negation, Predicate.System.Identity): NotImplemented,
                    },
                    (LexType.Predicate, False) : tuple('FGHO'),
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

    data['polish']['html'] = deepcopy(data['polish']['ascii']) | {
        'name'     : 'polish.html',
        'encoding' : 'html',
        'formats'  : {'subscript': '<sub>{0}</sub>'},
    }

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
                    LexType.Atomic : tuple('ABCDE'),
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
                    LexType.Variable : tuple('xyzv'),
                    LexType.Constant : tuple('abcd'),
                    LexType.Quantifier : {
                        Quantifier.Universal   : 'L',
                        Quantifier.Existential : 'X',
                    },
                    (LexType.Predicate, True) : {
                        Predicate.System.Identity.index  : '=',
                        Predicate.System.Existence.index : 'E!',
                        (Operator.Negation, Predicate.System.Identity): '!=',
                    },
                    (LexType.Predicate, False) : tuple('FGHO'),
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
                    LexType.Atomic   : tuple('ABCDE'),
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
                    LexType.Variable   : tuple('xyzv'),
                    LexType.Constant   : tuple('abcd'),
                    LexType.Quantifier : {
                        Quantifier.Universal   : '∀' ,
                        Quantifier.Existential : '∃' ,
                    },
                    (LexType.Predicate, True) : {
                        Predicate.System.Identity.index  : '=',
                        Predicate.System.Existence.index : 'E!',
                        (Operator.Negation, Predicate.System.Identity): '≠',
                    },
                    (LexType.Predicate, False) : tuple('FGHO'),
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
                    LexType.Atomic   : tuple('ABCDE'),
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
                    LexType.Variable   : tuple('xyzv'),
                    LexType.Constant   : tuple('abcd'),
                    LexType.Quantifier : {
                        Quantifier.Universal   : '&forall;' ,
                        Quantifier.Existential : '&exist;'  ,
                    },
                    (LexType.Predicate, True) : {
                        Predicate.System.Identity.index  : '=',
                        Predicate.System.Existence.index : 'E!',
                        (Operator.Negation, Predicate.System.Identity): '&ne;',
                    },
                    (LexType.Predicate, False) : tuple('FGHO'),
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


##############################################################

@d.run
def _():
    for cls in (Bases.Enum, Bases.LexicalItem, Predicates, Argument, Bases.Lexical):
        cls._readonly = True

del(_, overload, abcf)
