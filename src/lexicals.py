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
    'Operator', 'Quantifier',
    'Parameter', 'Constant', 'Variable', 'Predicate',
    'Sentence', 'Atomic', 'Predicated', 'Quantified', 'Operated',
    'LexType', 'Predicates', 'Argument', 
    'Notation', 'LexWriter', 'BaseLexWriter', 'PolishLexWriter', 'StandardLexWriter',
)
##############################################################

from errors import (
    Emsg,
    instcheck,
)
import tools.abcs as abcs
from tools.abcs import (
    abcm, abcf,
    T, NotImplType
)
from tools.decorators import (
    abstract, closure, final, overload, static,
    fixed, lazy, membr, raisr, wraps, NoSetAttr
)
from tools.hybrids   import qsetf, qset
from tools.mappings  import dmap, MapCover, MapProxy
from tools.sequences import SequenceApi, seqf, EMPTY_SEQ
from tools.sets      import setf, setm, EMPTY_SET

import enum as _enum
from functools import (
    partial,
)
from itertools import (
    chain,
    repeat,
)
import operator as opr
from types import (
    DynamicClassAttribute as DynClsAttr,
)
from typing import (
    Annotated,
    Any,
    Callable,
    ClassVar,
    Collection,
    Iterable,
    Iterator,
    Mapping,
    NamedTuple,
    Sequence,
    SupportsIndex,
    TypeVar,
)

NOARG = object()
EMPTY_IT = iter(EMPTY_SEQ)
ITEM_CACHE_SIZE = 10000

nosetattr = NoSetAttr(attr = '_readonly', enabled = False)

@overload
def sorttmap(it: Iterable[Bases.Lexical]) -> Iterator[Types.IntTuple]: ...
sorttmap = partial(map, opr.attrgetter('sort_tuple'))

@static
class Types:

    from tools.patch    import EnumDictType
    from tools.mappings import DequeCache as ItemCache

    class BiCoords(NamedTuple):
        index     : int
        subscript : int
    
        class Sorting(NamedTuple):
            subscript : int
            index     : int

        def sorting(self) -> Types.BiCoords.Sorting:
            return self.Sorting(self.subscript, self.index)

        first = (0, 0)

    BiCoords.first = BiCoords._make(BiCoords.first)

    class TriCoords(NamedTuple):
        index     : int
        subscript : int
        arity     : int

        class Sorting(NamedTuple):
            subscript : int
            index     : int
            arity     : int

        def sorting(self) -> Types.TriCoords.Sorting:
            return self.Sorting(self.subscript, self.index, self.arity)

        first = (0, 0, 1)

    TriCoords.first = TriCoords._make(TriCoords.first)

    IntTuple = tuple[int, ...]
    IndexType = SupportsIndex | slice

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

    # Deferred

    Lexical        : type[Bases.Lexical]

    PredsItemRef:  type[PredicateRef | Predicate]  = PredicateRef
    PredsItemSpec: type[PredicateSpec | Predicate] = PredicateSpec

    QuantifiedItem : type[Quantifier | Variable | Sentence]

##############################################################

@static
class Metas:

    class Abc(abcs.AbcMeta):

        _readonly : bool
    
        __delattr__ = raisr(AttributeError)
        __setattr__ = nosetattr(abcs.AbcMeta)

    class Enum(abcs.AbcEnumMeta):

        _readonly : bool

        __delattr__ = raisr(AttributeError)
        __setattr__ = nosetattr(abcs.AbcEnumMeta)

    class LexicalItem(Abc):
        'Metaclass for LexicalItem classes (Constant, Predicate, Sentence, etc.).'

        Cache: ClassVar[Types.ItemCache]

        def __call__(cls: LexItT, *spec) -> LexItT:
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
            try: inst = super().__call__(*spec)
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
                return Notation(
                    notn or Notation.default
                ).default_writer(*args, **kw)
            return super().__call__(*args, **kw)

        @lazy.dynca
        def _sys(cls) -> LexWriter:
            'The system LexWriter instance for representing.'
            try: return LexWriter()
            except NameError: raise AttributeError

        @_sys.setter
        def _sys(cls, value: LexWriter):
            try: instcheck(value, LexWriter)
            except NameError: raise AttributeError
            setattr(LexWriter, '__sys', value)

@static
class Bases:

    class Abc(abcs.Abc, metaclass = Metas.Abc):
        __slots__ = EMPTY_SET

    class Enum(abcs.AbcEnum, metaclass = Metas.Enum):

        __slots__   = (
            'value', '_value_', '_name_', '__objclass__'
        )
        __delattr__ = raisr(AttributeError)
        __setattr__ = nosetattr(abcs.AbcEnum, cls = True)

    @abcm.clsafter
    class Lexical:
        'Lexical mixin class for both ``LexicalEnum`` and ``LexicalItem`` classes.'

        __slots__ = EMPTY_SET

        def __init__(self):
            raise TypeError(self)

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        #: LexType Enum instance.
        TYPE: ClassVar[LexType]

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

        @static
        def identitem(item: LexT) -> Types.Ident:
            'Build an ``ident`` tuple from the class name and ``spec``.'
            return type(item).__name__, item.spec

        @static
        def hashitem(item: LexT):
            'Compute a hash based on class name and ``sort_tuple``.'
            return hash((type(item).__name__, item.sort_tuple))

        @static
        @closure
        def orderitems():

            from itertools import starmap

            def cmpgen(a: LexT, b: LexT, sm = starmap, sub = opr.sub):
                if a is b:
                    yield 0
                    return
                yield a.TYPE.rank - b.TYPE.rank
                a = a.sort_tuple
                b = b.sort_tuple
                yield from sm(sub, zip(a, b))
                yield len(a) - len(b)

            def orderitems(item: LexT, other: LexT) -> int:
                '''Pairwise ordering comparison based on type rank and ``sort_tuple``.
                Raises TypeError.'''
                try:
                    for cmp in cmpgen(item, other):
                        if cmp: return cmp
                    return cmp
                except AttributeError:
                    raise TypeError

            return orderitems

        @abcf.temp
        @membr.defer
        def ordr(member: membr[type[Bases.Lexical], Callable[[Bases.Lexical, Any], bool|NotImplType]]):
            oper: Callable[[int, int], bool] = getattr(opr, member.name)
            Lexical = member.owner
            @wraps(oper)
            def f(self: Bases.Lexical, other: Any, /):
                if not isinstance(other, Lexical):
                    return NotImplemented
                return oper(Lexical.orderitems(self, other), 0)
            return f

        __lt__ = __le__ = __gt__ = __ge__ = __eq__ = ordr()

        def __hash__(self):
            return self.hash

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Generation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @classmethod
        def gen(cls: type[LexT], stop: SupportsIndex, first: LexT = None, **nextkw) -> Iterator[LexT]:
            'Generate items.'
            if stop is not None:
                stop = int(stop)
                if stop < 1:
                    return
                inc = 1
            else:
                stop = 1
                inc = 0
            if first is None:
                item = cls.first()
            else:
                item = instcheck(first, cls)
            i = 0
            try:
                while i < stop:
                    yield item
                    item = item.next(**nextkw)
                    i += inc
            except StopIteration:
                pass

        @classmethod
        @abstract
        def first(cls: type[LexT]) -> LexT: ...

        @abstract
        def next(self: LexT, **kw) -> LexT: ...

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎  Behaviors ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __copy__(self):
            'Return self.'
            return self

        def __deepcopy__(self, memo):
            'Return self.'
            memo[id(self)] = self
            return self

        def __bool__(self):
            'Return True.'
            return True

        def __repr__(self):
            try:
                return '<%s: %s>' % (self.TYPE.role, str(self))
            except AttributeError:
                return '<%s: ERR>' % type(self).__name__

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Attribute Access ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        __delattr__ = raisr(AttributeError)
        __setattr__ = nosetattr(object, cls = Metas.LexicalItem)

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Subclass Init ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __init_subclass__(subcls: type[Bases.Lexical], /, *,
            lexcopy = False, skipnames = {'__init_subclass__'},
        **kw):
            '''With lexcopy = True, copy the class members to the next class,
            since our protection is limited without metaclass flexibility.
            Only applies if this class is in the bases of the subcls.'''
            super().__init_subclass__(**kw)
            cls = __class__
            if not lexcopy or cls not in subcls.__bases__:
                return
            from types import FunctionType
            ftypes = classmethod, staticmethod, FunctionType
            src = dmap(cls.__dict__)
            src -= set(subcls.__dict__)
            src -= set(skipnames)

            cpnames = {'__copy__', '__deepcopy__'}
            for name in cpnames:
                if name not in src:
                    src -= cpnames
                    break

            for name, value in src.items():
                if isinstance(value, ftypes):
                    setattr(subcls, name, value)


    Types.Lexical = Lexical
    Metas.LexicalItem.Cache = Types.ItemCache(Lexical, ITEM_CACHE_SIZE)

    class LexicalEnum(Lexical, Enum, lexcopy = False):
        'Base Enum implementation of Lexical. For Quantifier and Operator classes.'

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        # Lexical Instance Variables

        spec       : tuple[str]
        ident      : tuple[str, tuple[str]]
        sort_tuple : Types.IntTuple
        hash       : int

        # Enum Instance Variables

        #: Label with spaces allowed.
        label: str
        #: A number to signify relative member order (need not be sequence index).
        order: int
        #: The member index in the member sequence.
        index: int
        #: Name, label, or other strings unique to a member.
        strings: setf[str]

        __slots__ = (
            'spec', 'ident', 'sort_tuple', 'hash',
            'label', 'order', 'index', 'strings',
        )

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Comparison ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __eq__(self, other):
            'Allow equality with the string name.'
            if self is other:
                return True
            if isinstance(other, str):
                return other in self.strings
            return NotImplemented

        def __hash__(self):
            return self.hash

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Generation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @classmethod
        def first(cls):
            'Return the first instance of this type.'
            return cls.seq[0]

        def next(self, loop = False):
            seq: Sequence[Bases.LexicalEnum] = self.seq
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

        def __init__(self, order: int, label: str, *_):
            self.spec = self.name,
            self.order = order
            self.label = label
            # Prepended with rank in LexType init
            self.sort_tuple = self.order,
            self.ident = self.identitem(self)
            self.hash = self.hashitem(self)
            self.strings = setf((self.name, self.label))


        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Enum Meta Hooks ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @classmethod
        def _member_keys(cls, member: Bases.LexicalEnum):
            'Enum init hook. Index keys for Enum members lookups.'
            return super()._member_keys(member) | {member.label}

        @classmethod
        def _on_init(cls, subcls: type[Bases.LexicalEnum]):
            'Enum init hook. Store the sequence index of each member.'
            # raise TypeError
            super()._on_init(subcls)
            for i, member in enumerate(subcls.seq): member.index = i

    class LexicalItem(Lexical, Abc, metaclass = Metas.LexicalItem, lexcopy = True):
        'Base Lexical Item class.'

        __slots__ = '_ident', '_hash',

        @lazy.prop
        def ident(self):
            return self.identitem(self)

        @lazy.prop
        def hash(self):
            return self.hashitem(self)

        @abstract
        def __init__(self): ...

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Behaviors ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __str__(self):
            'Write the item with the default LexWriter.'
            try: return LexWriter._sys(self)
            except NameError:
                try: return str(self.ident)
                except AttributeError as e:
                    return '%s(%s)' % (type(self).__name__, e)

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Attribute Access ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        __delattr__ = raisr(AttributeError)

        def __setattr__(self, name, value):
            if getattr(self, name, value) is not value:
                if isinstance(getattr(type(self), name, None), property):
                    pass
                else:
                    raise Emsg.ReadOnlyAttr(name, self)
            super().__setattr__(name, value)

    class CoordsItem(LexicalItem):

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        Coords = Types.BiCoords

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        #: The item spec.
        spec: Types.BiCoords

        #: The item coordinates.
        coords: Types.BiCoords

        #: The coords index.
        index: int

        #: The coords subscript.
        subscript: int

        __slots__ = 'spec', 'coords', 'index', 'subscript', '_sort_tuple',
 
        @lazy.prop
        def sort_tuple(self: Bases.CoordsItem):
            return self.TYPE.rank, *self.coords.sorting()
            
        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Generation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @classmethod
        def first(cls: type[CrdT]) -> CrdT:
            'Return the first instance of this type.'
            return cls(cls.Coords.first)

        def next(self: CrdT) -> CrdT:
            cls = type(self)
            idx, sub, *cargs = self.coords
            if idx < cls.TYPE.maxi:
                idx += 1
            else:
                idx = 0
                sub += 1
            return cls(idx, sub, *cargs)

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @overload
        def __init__(self, *coords: int):...
        @overload
        def __init__(self, coords: Iterable[int]):...
        def __init__(self, *coords):
            self.coords = self.spec = coords = self.Coords._make(
                coords[0] if len(coords) == 1 else coords
            )
            for field, value in zip(coords._fields, coords):
                setattr(self, field, instcheck(value, int))
            try:
                if coords.index > self.TYPE.maxi:
                    raise ValueError('%d > %d' % (coords.index, self.TYPE.maxi))
                if coords.subscript < 0:
                    raise ValueError('%d < %d' % (coords.subscript, 0))
            except AttributeError:
                raise TypeError(self) from None

    class CacheNotationData(Abc):

        default_fetch_name = 'default'
        _instances: dict[Notation, dict[str, CnT]]

        __slots__ = EMPTY_SET

        @classmethod
        def load(cls: type[CnT], notn: Notation, name: str, data: Mapping) -> CnT:
            instcheck(name, str)
            idx = cls._instances[notn]
            if name in idx:
                raise Emsg.DuplicateKey((notn, name))
            return idx.setdefault(name, cls(data))

        @classmethod
        def fetch(cls: type[CnT], notn: Notation, name: str = None) -> CnT:
            if name is None:
                name = cls.default_fetch_name
            try:
                return cls._instances[notn][name]
            except KeyError:
                pass
            return cls.load(notn, name, cls._builtin[notn][name])

        @classmethod
        def available(cls, notn: Notation) -> list[str]:
            return sorted(set(cls._instances[notn]).union(cls._builtin[notn]))

        @classmethod
        def _initcache(cls,
            notns: Iterable[Notation],
            builtin: Mapping[Notation, Mapping[str, Mapping]]
        ):
            if cls is __class__ or hasattr(cls, '_builtin'):
                raise TypeError
            cls._builtin = builtin = MapCover(dict(builtin))
            notns = set(notns).union(builtin)
            cls._instances = {notn: {} for notn in notns}

CnT  = TypeVar('CnT',  bound = Bases.CacheNotationData)
CrdT = TypeVar('CrdT', bound = Bases.CoordsItem)
LexT = TypeVar('LexT', bound = Bases.Lexical)
LexItT = TypeVar('LexItT', bound = Bases.LexicalItem)

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

    __slots__ = 'arity',

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


##############################################################

class Parameter(Bases.CoordsItem):

    is_constant: bool
    is_variable: bool

    __slots__ = EMPTY_SET

@final
class Constant(Parameter):

    __slots__ = 'is_constant', 'is_variable'

    def __init__(self, *args):
        super().__init__(*args)
        self.is_constant = True
        self.is_variable = False

@final
class Variable(Parameter):

    __slots__ = Constant.__slots__

    def __init__(self, *args):
        super().__init__(*args)
        self.is_constant = False
        self.is_variable = True

@final
class Predicate(Bases.CoordsItem):
    """
    Predicate

    The parameters can be passed either expanded, or as a single
    ``tuple``. A valid spec consists of 3 integers in
    the order of `index`, `subscript`, `arity`, for example::

        Predicate(0, 0, 1)
        Predicate((0, 0, 1))
    """
    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    Coords = Types.TriCoords

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    spec    : Types.TriCoords
    coords  : Types.TriCoords

    #: The coords arity.
    arity: int

    #: Whether this is a system predicate.
    is_system: bool

    #: The name or spec
    name: Types.IntTuple | str

    #: The coords and other attributes, each of which uniquely identify this
    #: instance among other predicates. These are used to create hash indexes
    #: for retrieving predicates from predicate stores.
    #:
    #: .. _predicate-refs-list:
    #:
    #: - `spec` - A ``tuple`` with (index, subscript, arity).
    #: - `ident` - Includes class rank (``10``) plus `spec`.
    #: - `bicoords` - A ``tuple`` with (index, subscript).
    #: - `name` - For system predicates, e.g. `Identity`, but is legacy for
    #:     user predicates.
    refs: seqf[Types.PredicateRef]

    bicoords: Types.BiCoords

    #: The ``refs`` plus the predicate object.
    refkeys: qsetf[Types.PredicateRef | Predicate]

    __slots__ = 'arity', 'is_system', 'name', 'bicoords', '_refs', '_refkeys', 'value'

    @lazy.prop
    def refs(self: Predicate):
        return seqf({self.spec, self.ident, self.bicoords, self.name})

    @lazy.prop
    def refkeys(self: Predicate):
        return qsetf({*self.refs, self})

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Behaviors ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __call__(self, *spec: Types.PredicatedSpec):
        'Apply the predicate to parameters to make a predicated sentence.'
        return Predicated(self, *spec)

    def __str__(self):
        return str(self.name) if self.is_system else super().__str__()

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Generation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def next(self) -> Predicate:
        arity = self.arity
        if self.is_system:
            # pred: Predicate
            for pred in self.System:
                if pred > self and pred.arity == arity:
                    return pred
        return super().next()

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    @overload
    def __init__(self, spec: Types.PredicateSpec): ...

    @overload
    def __init__(self, index: int, subscipt: int, arity: int, name: str = None,/): ...

    def __init__(self, *spec):
        if len(spec) == 1:
            if isinstance(spec[0], tuple):
                spec = spec[0]
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
            instcheck(name, (tuple, str))
        self.bicoords = Types.BiCoords(self.index, self.subscript)


    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ System Enum ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    class System(Bases.Enum):
        'System predicates enum.'

        Existence : Annotated[Predicate, (-2, 0, 1, 'Existence')]
        Identity  : Annotated[Predicate, (-1, 0, 2, 'Identity')]

    @DynClsAttr
    def _value_(self: Predicate.System):
        try:
            if self.is_system: return self
        except AttributeError: return self
        raise AttributeError('_value_')

    @DynClsAttr
    def _name_(self: Predicate.System):
        if self.is_system: return self.name
        raise AttributeError('_name_')

    @DynClsAttr
    def __objclass__(self: Predicate.System):
        if self.is_system: return __class__.System
        raise AttributeError('__objclass__')

    @abcf.temp
    def sysset(prop: T) -> T:
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

##############################################################

class Sentence(Bases.LexicalItem):

    #: Set of predicates, recursive.
    predicates: setf[Predicate]
    #: Set of constants, recursive.
    constants: setf[Constant]
    #: Set of variables, recursive.
    variables: setf[Variable]
    #: Tuple of quantifiers, recursive.
    quantifiers: seqf[Quantifier]
    #: Tuple of operators, recursive.
    operators: seqf[Operator]
    #: Set of atomic sentences, recursive.
    atomics: setf[Atomic]

    __slots__ = EMPTY_SET

    def substitute(self: SenT, pnew: Parameter, pold: Parameter) -> SenT:
        """Return the recursive substitution of ``pnew`` for all occurrences
        of ``pold``."""
        return self

    def negate(self) -> Operated:
        'Negate this sentence, returning the new sentence.'
        return Operated(Operator.Negation, (self,))

    @overload
    def negative(self) -> Sentence:
        """Either negate this sentence, or, if this is already a negated
        sentence return its negatum, i.e., "un-negate" the sentence."""
    negative = negate

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

SenT = TypeVar('SenT', bound = Sentence)
Types.QuantifiedItem = Quantifier | Variable | Sentence

@final
class Atomic(Bases.CoordsItem, Sentence):

    __slots__ = (
        'predicates', 'constants', 'variables',
        'quantifiers', 'operators',
        'atomics',
    )

    def __init__(self, *args):
        super().__init__(*args)
        self.predicates = self.constants = self.variables = EMPTY_SET
        self.quantifiers = self.operators = EMPTY_SEQ
        self.atomics = setf((self,))

    variable_occurs = fixed.value(False)

@final
class Predicated(Sentence, SequenceApi[Parameter]):
    'Predicated sentence.'

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    #: The item spec.
    spec: Types.PredicatedSpec

    #: The predicate.
    predicate: Predicate

    #: The parameters
    params: seqf[Parameter]

    #: The set of parameters.
    paramset: setf[Parameter]

    __slots__ = (
        '_spec', '_sort_tuple',
        'predicate', 'params', 'paramset',
        'quantifiers', 'operators', 'atomics',
        '_constants', '_variables', '_predicates',
    )

    @lazy.prop
    def spec(self):
        return self.predicate.spec, tuple(p.ident for p in self.params)

    @lazy.prop
    def sort_tuple(self: Predicated):
        return self.TYPE.rank, *chain.from_iterable(
            sorttmap((self.predicate, *self.params))
        )

    @lazy.prop
    def predicates(self: Predicated):
        return setf({self.predicate})

    @lazy.prop
    def constants(self: Predicated) -> setf[Constant]:
        return setf(p for p in self.paramset if p.is_constant)

    @lazy.prop
    def variables(self: Predicated) -> setf[Variable]:
        return setf(p for p in self.paramset if p.is_variable)

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Sentence Methods ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def substitute(self, pnew: Parameter, pold: Parameter) -> Predicated:
        if pnew == pold or pold not in self.paramset: return self
        return Predicated(self.predicate, tuple(
            (pnew if p == pold else p for p in self.params)
        ))

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __init__(self, pred, params: Iterable[Parameter] | Parameter):
        self.predicate = Predicate(pred)
        self.params = seqf(
            (params,) if isinstance(params, Parameter)
            else map(Parameter, params)
        )
        if len(self) != self.predicate.arity:
            raise TypeError(self.predicate, len(self), self.predicate.arity)

        self.paramset = setf(self.params)
        self.operators = self.quantifiers = EMPTY_SEQ
        self.atomics = EMPTY_SET

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Generation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    @classmethod
    def first(cls, pred: Predicate = None, /) -> Predicated:
        if pred is None: pred = Predicate.first()
        return cls(pred, tuple(repeat(Constant.first(), pred.arity)))

    def next(self):
        return Predicated(self.predicate.next(), self.params)

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Sequence Behavior ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __getitem__(self, index: Types.IndexType):
        return self.params[index]

    def __len__(self):
        return len(self.params)

    def __contains__(self, p):
        return p in self.paramset

    @classmethod
    def _from_iterable(cls, it):
        try:
            pred = it.predicate
        except AttributeError:
            raise TypeError
        else:
            return cls(pred, it)

@final
class Quantified(Sentence, SequenceApi[Types.QuantifiedItem]):
    'Quantified sentence.'

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    #: The item sepc
    spec: Types.QuantifiedSpec

    #: The quantifier
    quantifier: Quantifier

    #: The bound variable
    variable: Variable

    #: The inner sentence
    sentence: Sentence

    #: The items sequence: Quantifer, Variable, Sentence.
    items: tuple[Quantifier, Variable, Sentence]

    __slots__ =  (
        'spec', '_sort_tuple',
        'quantifier', 'variable', 'sentence', 'items',
        '_quantifiers'
    )

    @lazy.prop
    def sort_tuple(self: Quantified) -> Types.IntTuple:
        return self.TYPE.rank, *chain.from_iterable(sorttmap(self))

    @property
    def constants(self: Quantified):
        return self.sentence.constants

    @property
    def variables(self: Quantified):
        return self.sentence.variables

    @property
    def atomics(self: Quantified):
        return self.sentence.atomics

    @property
    def predicates(self: Quantified):
        return self.sentence.predicates

    @property
    def operators(self: Quantified):
        return self.sentence.operators

    @lazy.prop
    def quantifiers(self: Quantified):
        return seqf((self.quantifier, *self.sentence.quantifiers))

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Sentence Methods ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def substitute(self, pnew: Parameter, pold: Parameter) -> Quantified:
        if pnew == pold: return self
        return type(self)(
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
        self.spec = *self.quantifier.spec, self.variable.spec, self.sentence.ident

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Generation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    @classmethod
    def first(cls, q: Quantifier = Quantifier.seq[0],/) -> Quantified:
        pred = Predicate.first()
        v = Variable.first()
        return cls(q, v, pred(
            (v, *Constant.gen(pred.arity - 1))
        ))

    def next(self, **kw) -> Quantified:
        s = self.sentence.next(**kw)
        v = self.variable
        if v not in s.variables:
            raise TypeError('%s no longer bound' % v)
        return Quantified(self.quantifier, v, s)

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Sequence Behavior ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __len__(self):
        return len(self.items)

    def __contains__(self, item):
        return item in self.items

    def __getitem__(self, index: Types.IndexType):
        return self.items[index]

    def count(self, item) -> int:
        return int(item in self.items)

    @classmethod
    def _from_iterable(cls, it):
        return cls(*it)

@final
class Operated(Sentence, SequenceApi[Sentence]):
    'Operated sentence.'

    #: The item sepc
    spec: Types.OperatedSpec

    #: The operator
    operator: Operator

    #: The operands.
    operands: tuple[Sentence, ...]

    #: The first (left-most) operand.
    lhs: Sentence

    #: The last (right-most) operand.
    rhs: Sentence

    __slots__ =  setf((
        '_spec', '_sort_tuple',
        'operator', 'operands', 'lhs', 'rhs',
        '_predicates', '_constants', '_variables', '_quantifiers',
        '_operators', '_atomics',
    ))

    @lazy.prop
    def spec(self: Operated) -> Types.OperatedSpec:
        return *self.operator.spec, tuple(s.ident for s in self)

    @lazy.prop
    def sort_tuple(self: Operated) -> Types.IntTuple:
        return self.TYPE.rank, *chain.from_iterable(
            sorttmap((self.operator, *self))
        )

    @lazy.prop
    def predicates(self: Operated):
        return setf(chain.from_iterable(s.predicates for s in self))

    @lazy.prop
    def constants(self: Operated):
        return setf(chain.from_iterable(s.constants for s in self))

    @lazy.prop
    def variables(self: Operated):
        return setf(chain.from_iterable(s.variables for s in self))

    @lazy.prop
    def quantifiers(self: Operated):
        return *chain.from_iterable(s.quantifiers for s in self),

    @lazy.prop
    def operators(self: Operated):
        return seqf(
            (self.operator, *chain.from_iterable(
                s.operators for s in self
            ))
        )

    @lazy.prop
    def atomics(self: Operated):
        return setf(chain.from_iterable(s.atomics for s in self))

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Item Generation ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    @classmethod
    def first(cls, oper: Operator = Operator.seq[0],/) -> Operated:
        return cls(oper, Atomic.gen(Operator(oper).arity))

    def next(self, **kw) -> Operated:
        return Operated(self.operator,
            (*self.operands[0:-1], self.operands[-1].next(**kw))
        )

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Sentence Methods. ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def substitute(self, pnew: Parameter, pold: Parameter) -> Operated:
        if pnew == pold: return self
        operands = (s.substitute(pnew, pold) for s in self)
        return Operated(self.operator, tuple(operands))

    def negative(self) -> Sentence:
        """Either negate this sentence, or, if this is already a negated
        sentence return its negatum, i.e., "un-negate" the sentence."""
        if self.operator is Operator.Negation:
            return self.lhs
        return self.negate()

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __init__(self, oper: Operator, operands: Iterable[Sentence] | Sentence):
        if isinstance(operands, Sentence):
            self.operands = operands,
        else:
            self.operands = tuple(map(Sentence, operands))
        self.operator = Operator(oper)
        self.lhs = self.operands[0]
        self.rhs = self.operands[-1]
        if len(self.operands) != self.operator.arity:
            raise Emsg.WrongLength(self.operands, self.operator.arity)

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Sequence Behavior ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __getitem__(self, index: Types.IndexType):
        return self.operands[index]

    def __len__(self):
        return len(self.operands)

    def __contains__(self, s: Sentence):
        return s in self.operands

    def _from_iterable(self, it):
        return type(self)(self.operator, it)
        # try:
        #     oper = it.operator
        # except AttributeError:
        #     raise TypeError
        # else:
        #     return cls(oper, it)

##############################################################
##############################################################

class LexType(Bases.Enum):

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    classes: ClassVar[qsetf[type[Bases.Lexical]]]

    __slots__ = setf({'rank', 'cls', 'generic', 'maxi', 'role', 'hash'})
    rank    : int
    cls     : type[Bases.Lexical]
    generic : type[Bases.Lexical]
    role    : str
    maxi    : int | None
    hash    : int


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
    @membr.defer
    def ordr(member: membr):
        oper = getattr(opr, member.name)
        @wraps(oper)
        def f(self: LexType, other):
            if type(other) is not LexType:
                return NotImplemented
            return oper(self.rank, other.rank)
        return f

    __lt__ = __le__ = __gt__ = __ge__ = ordr()

    def __eq__(self, other):
        return (
            self is other or
            self.cls is other or
            self is LexType.get(other, None)
        )

    def __hash__(self):
        return self.hash

    def __init__(self, rank: int, cls: type[Bases.Lexical], generic: type[Bases.Lexical], maxi: int|None):
        super().__init__()
        self.rank, self.cls, self.generic, self.maxi = rank, cls, generic, maxi
        self.role = self.generic.__name__
        self.hash = hash(type(self).__name__) + self.rank
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
        cls.classes = qsetf((m.cls for m in cls.seq))
        for inst in chain(Operator.seq, Quantifier.seq):
            inst.sort_tuple = inst.TYPE.rank, *inst.sort_tuple

    @classmethod
    def _member_keys(cls, member: LexType):
        'Enum lookup index init hook.'
        return super()._member_keys(member) | {member.cls}


##############################################################
##############################################################

class Predicates(qset[Predicate], Bases.Abc,
    hooks = {qset: dict(cast = Predicate)}
):
    'Predicate store'

    _lookup: dmap[Types.PredsItemRef, Predicate]
    __slots__ = '_lookup',

    def __init__(self, values: Iterable[Types.PredsItemSpec] = None, /):
        self._lookup = dmap()
        super().__init__(values)

    def get(self, ref: Types.PredsItemRef, default = NOARG, /) -> Predicate:
        """Get a predicate by any reference. Also searches System predicates.
        Raises KeyError when no default specified."""
        try: return self._lookup[ref]
        except KeyError:
            try: return self.System[ref]
            except KeyError: pass
            if default is NOARG: raise
            return default

    @abcf.temp
    @qset.hook('done')
    def after_change(self, arriving: Iterable[Predicate], leaving: Iterable[Predicate]):
        'Implement after change (done) hook. Update lookup index.'
        for pred in leaving or EMPTY_IT:
            if False: # - check disabled for performance
                # Is there a key we are removing that unexpectedly matches
                # a distinct predicate. This would have to be the result of
                # a failed removal or addition.
                for other in map(self._lookup.pop, pred.refkeys):
                    if other != pred:
                        raise Emsg.ValueConflictFor(pred, pred.coords, other.coords)
            self._lookup -= pred.refkeys
        for pred in arriving or EMPTY_IT:
            # Is there a distinct predicate that matches any lookup keys,
            # viz. BiCoords or name, that does not equal pred, e.g. arity
            # mismatch.
            for other in filter(None, map(self._lookup.get, pred.refkeys)):
                if other != pred:
                    raise Emsg.ValueConflictFor(pred, pred.coords, other.coords)
            self._lookup |= zip(pred.refkeys, repeat(pred))

    # -------------------------------
    #  Override qset
    # -------------------------------

    def clear(self):
        super().clear()
        self._lookup.clear()

    def __contains__(self, ref):
        return ref in self._lookup

    def copy(self):
        inst = super().copy()
        inst._lookup = self._lookup.copy()
        return inst

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ System Enum ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    class System(Predicate.System):
        'System Predicates enum container class.'

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        def __new__(cls, *spec):
            'Set the Enum value to the predicate instance.'
            return Bases.LexicalItem.__new__(Predicate)

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Enum Meta Hooks ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @classmethod
        def _member_keys(cls, pred: Predicate):
            'Enum lookup index init hook. Add all predicate keys.'
            return super()._member_keys(pred) | pred.refkeys

        @classmethod
        def _after_init(cls):
            'Enum after init hook. Set Predicate class attributes.'
            super()._after_init()
            for pred in cls.seq:
                setattr(Predicate, pred.name, pred)
            Predicate.System = cls

        #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Abc Meta Hooks ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

        @abcf.before
        def expand(ns: Types.EnumDictType, bases, **kw):
            'Inject members from annotations in Predicate.System class.'
            annots = abcm.annotated_attrs(Predicate.System)
            members = {
                name: spec for name, (vtype, spec)
                in annots.items() if vtype is Predicate
            }
            ns |= members
            ns._member_names += members.keys()

class Argument(SequenceApi[Sentence], metaclass = Metas.Argument):
    'Create an argument from sentence objects.'

    def __init__(self,
        conclusion: Sentence,
        premises: Iterable[Sentence] = None,
        title: str = None
    ):
        self.seq = seqf(
            (Sentence(conclusion),) if premises is None
            else map(Sentence, (conclusion, *premises))
        )
        self.premises = self.seq[1:]
        if title is not None:
            instcheck(title, str)
        self.title = title

    __slots__ = 'seq', 'title', 'premises', '_hash'

    sentences: seqf[Sentence]
    premises: seqf[Sentence]

    @property
    def conclusion(self) -> Sentence:
        return self.seq[0]

    @lazy.prop
    def hash(self) -> int:
        return hash(tuple(self))

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Sequence Behavior ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __len__(self):
        return len(self.seq)

    @overload
    def __getitem__(self, s: slice, /) -> seqf[Sentence]: ...

    @overload
    def __getitem__(self, i: SupportsIndex, /) -> Sentence: ...

    def __getitem__(self, index: slice|SupportsIndex, /):
        return self.seq[index]

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Equality & Ordering ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    # Two arguments are considered equal just when their conclusions are
    # equal, and their premises are equal (and in the same order). The
    # title is not considered in equality.

    @abcf.temp
    @membr.defer
    @closure

    def ordr():

        from itertools import starmap

        def cmpgen(a: Argument, b: Argument, /, *,
            sm: Callable[..., Iterator[int]] = starmap,
            sorder = Sentence.orderitems
        ):
            if a is b:
                yield 0 ; return
            yield bool(a.conclusion) - bool(b.conclusion)
            yield len(a.seq) - len(b.seq)
            yield from sm(sorder, zip(a.seq, b.seq))

        def ordr(
            member: membr[type[Argument], Callable[[Argument, Any], bool|NotImplType]]
        ):
            oper: Callable[[int, int], bool] = getattr(opr, member.name)
            @wraps(oper)
            def f(self: Argument, other: Any):
                if not isinstance(other, Argument):
                    return NotImplemented
                for cmp in cmpgen(self, other):
                    if cmp: break
                else:
                    cmp = 0
                return oper(cmp, 0)
            return f

        return ordr

    __lt__ = __le__ = __gt__ = __ge__ = __eq__ = ordr() # type: ignore

    def __hash__(self):
        return self.hash

    def __repr__(self):
        if self.title: desc = repr(self.title)
        else: desc = 'len(%d)' % len(self)
        return '<%s:%s>' % (type(self).__name__, desc)

    def __setattr__(self, attr, value):
        if hasattr(self, attr):
            raise AttributeError(attr)
        super().__setattr__(attr, value)

    __delattr__ = raisr(AttributeError)

    @classmethod
    def _from_iterable(cls, it):
        '''Build an argument from an non-empty iterable using the first element
        as the conclusion, and the others as the premises.'''
        it = iter(it)
        try:
            return cls(next(it), it)
        except StopIteration:
            raise TypeError

##############################################################
#                                                            #
#       LexWriters                                           #
#                                                            #
##############################################################

class Marking(Bases.Enum):
    paren_open  = _enum.auto()
    paren_close = _enum.auto()
    whitespace  = _enum.auto()
    digit       = _enum.auto()
    meta        = _enum.auto()
    subscript   = _enum.auto()

class Notation(Bases.Enum):
    'Notation (polish/standard) enum class.'

    default: ClassVar[Notation]
    @abcf.after
    def _(cls): cls.default = cls.polish

    encodings        : setm[str]
    default_encoding : str
    writers          : setm[type[LexWriter]]
    default_writer   : type[LexWriter]
    rendersets       : setm[RenderSet]
    Parser           : type[Parser]

    polish   = _enum.auto(), 'ascii'
    standard = _enum.auto(), 'unicode'

    def __init__(self, num, default_encoding):
        self.encodings = setm((default_encoding,))
        self.default_encoding = default_encoding
        self.writers = setm()
        self.default_writer = None
        self.rendersets = setm()

    __slots__ = (
        'encodings', 'default_encoding', 'writers',
        'default_writer', 'rendersets', 'Parser',
    )

    def __setattr__(self, name, value):
        if name == 'Parser' and not hasattr(self, name):
            _enum.Enum.__setattr__(self, name, value)
        else:
            super().__setattr__(name, value)

class LexWriter(metaclass = Metas.LexWriter):
    'LexWriter Api and Coordinator class.'

    __slots__ = EMPTY_SET

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    notation: ClassVar[Notation]
    _methodmap = MapProxy[LexType, str](dict(
        zip(LexType, repeat(NotImplemented))
    ))
    _sys: ClassVar[LexWriter]

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    encoding: str

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Exteneral API ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def write(self, item: Bases.Lexical) -> str:
        'Write a lexical item.'
        return self._write(item)

    __call__ = write

    @classmethod
    def canwrite(cls, item) -> bool:
        try: return item.TYPE in cls._methodmap
        except AttributeError: return False

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init. ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    @abstract
    def __init__(self): ...

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Internal API ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def _write(self, item: Bases.Lexical) -> str:
        'Wrapped internal write method.'
        try:
            method = self._methodmap[item.TYPE]
        except AttributeError:
            raise TypeError(type(item))
        except KeyError:
            raise NotImplementedError(type(item))
        return getattr(self, method)(item)

    def _test(self):
        'Smoke test. Returns a rendered list of each lex type.'
        return list(map(self, (t.cls.first() for t in LexType)))

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Init. ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

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
        abcm.merge_mroattr(
            subcls, '_methodmap', supcls = __class__, transform = MapProxy
        )

class RenderSet(Bases.CacheNotationData):

    default_fetch_name = 'ascii'

    def __init__(self, data: Mapping):
        self.name: str = data['name']
        self.notation = Notation(data['notation'])
        self.encoding: str = data['encoding']
        self.renders: Mapping[Any, Callable[..., str]] = data.get('renders', {})
        self.formats: Mapping[Any, str] = data.get('formats', {})
        self.strings: Mapping[Any, str] = data.get('strings', {})
        self.data = data
        self.notation.encodings.add(self.encoding)
        self.notation.rendersets.add(self)

    def strfor(self, ctype, value):
        if ctype in self.renders:
            return self.renders[ctype](value)
        if ctype in self.formats:
            return self.formats[ctype].format(value)
        return self.strings[ctype][value]

class BaseLexWriter(LexWriter, metaclass = Metas.LexWriter):

    __slots__ = 'opts', 'renderset'

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Class Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    defaults: ClassVar[dict] = {}
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

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Variables ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    opts: dict
    renderset: RenderSet

    @property
    def encoding(self) -> str:
        return self.renderset.encoding

    #◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎ Instance Init. ◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎◀︎▶︎#

    def __init__(self, enc = None, renderset: RenderSet = None, **opts):
        notation = self.notation
        if renderset is None:
            if enc is None:
                enc = notation.default_encoding
            renderset = RenderSet.fetch(notation, enc)
        elif enc is not None and enc != renderset.encoding:
            raise Emsg.WrongValue(enc, renderset.encoding)
        self.opts = self.defaults | opts
        self.renderset = renderset

    # --------------------------
    #  Default implementations.
    # --------------------------
    @abstract
    def _write_operated(self, item: Operated): ...

    def _strfor(self, *args, **kw):
        return self.renderset.strfor(*args, **kw)

    def _write_plain(self, item: Bases.Lexical):
        return self._strfor(item.TYPE, item)

    def _write_coordsitem(self, item: Bases.CoordsItem):
        return ''.join((
            self._strfor(item.TYPE, item.index),
            self._write_subscript(item.subscript),
        ))

    def _write_predicate(self, item: Predicate):
        return ''.join((
            self._strfor((LexType.Predicate, item.is_system), item.index),
            self._write_subscript(item.subscript),
        ))

    def _write_quantified(self, item: Quantified):
        return ''.join(map(self._write, item.items))

    def _write_predicated(self, item: Predicated):
        return ''.join(map(self._write, (item.predicate, *item)))

    def _write_subscript(self, s: int):
        if s == 0: return ''
        return self._strfor('subscript', s)

@LexWriter.register
class PolishLexWriter(BaseLexWriter):

    __slots__ = EMPTY_SET

    notation = Notation.polish

    def _write_operated(self, item: Operated):
        return ''.join(map(self._write, (item.operator, *item)))

@LexWriter.register
class StandardLexWriter(BaseLexWriter):

    __slots__ = EMPTY_SET
    notation = Notation.standard
    defaults = dict(drop_parens = True)

    def write(self, item: Bases.Lexical):
        if self.opts['drop_parens'] and isinstance(item, Operated):
            return self._write_operated(item, drop_parens = True)
        return super().write(item)

    def _write_predicated(self, item: Predicated):
        if len(item) < 2:
            return super()._write_predicated(item)
        # Infix notation for predicates of arity > 1
        pred = item.predicate
        # For Identity, add spaces (a = b instead of a=b)
        if pred == Predicate.System.Identity:
            ws = self._strfor(Marking.whitespace, 0)
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
            s = item.lhs
            if (
                oper == Operator.Negation and
                type(s) is Predicated and
                s.predicate == Predicate.System.Identity
            ):
                return self._write_negated_identity(item)
            else:
                return self._write(oper) + self._write(s)
        elif arity == 2:
            lhs, rhs = item
            return ''.join((
                self._strfor(Marking.paren_open, 0) if not drop_parens else '',
                self._strfor(Marking.whitespace, 0).join(map(self._write, (lhs, oper, rhs))),
                self._strfor(Marking.paren_close, 0) if not drop_parens else '',
            ))
        raise NotImplementedError('arity %s' % arity)

    def _write_negated_identity(self, item: Operated):
        si: Predicated = item.lhs
        params = si.params
        return self._strfor(Marking.whitespace, 0).join((
            self._write(params[0]),
            self._strfor((LexType.Predicate, True), (item.operator, si.predicate)),
            self._write(params[1]),
        ))

    def _test(self):
        s1 = Predicate.System.Identity(Constant.gen(2)).negate()
        s2 = Operator.Conjunction(Atomic.gen(2))
        s3 = s2.disjoin(Atomic.first())
        return super()._test() + list(map(self, [s1, s2, s3]))

class Parser(Bases.Abc):

    __slots__ = EMPTY_SET

    @abstract
    def parse(self, input: str) -> Sentence:
        """Parse a sentence from an input string.

        :param input: The input string.
        :return: The parsed sentence.
        :raises errors.ParseError:
        :raises TypeError:
        """
        raise NotImplementedError

    def __call__(self, input: str):
        return self.parse(input)

    def argument(self, conclusion: str, premises: Iterable[str] = None, title: str = None) -> Argument:
        """Parse the input strings and create an argument.

        :param conclusion: The argument's conclusion.
        :param premises: Premise strings, if any.
        :return: The argument.
        :raises errors.ParseError:
        :raises TypeError:
        """
        return Argument(
            self.parse(conclusion),
            premises and tuple(map(self.parse, premises)),
            title = title,
        )

@closure
def _():

    data = {
        Notation.polish: {
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
                    Marking.paren_open  : (NotImplemented,),
                    Marking.paren_close : (NotImplemented,),
                    Marking.whitespace  : (' ',),
                    Marking.meta: {
                        'conseq': '|-',
                        'non-conseq': '|/-',
                    },
                },
            }
        }
    }

    data[Notation.polish] |= dict(
        unicode = data[Notation.polish]['ascii'],
        html    = data[Notation.polish]['ascii'] | dict(
            name = 'polish.html',
            encoding = 'html',
            formats = dict(subscript = '<sub>{0}</sub>')
        ),
    )

    def unisub(sub):
        # ['₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉'],
        return ''.join(chr(0x2080 + int(d)) for d in str(sub))

    data.update({
        Notation.standard: dict(
            ascii = {
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
                    Marking.paren_open      : ('(',),
                    Marking.paren_close     : (')',),
                    Marking.whitespace      : (' ',),
                    Marking.meta: {
                        'conseq': '|-',
                        'non-conseq': '|/-'
                    },
                },
            },
            unicode = {
                'name'    : 'standard.unicode',
                'notation': Notation.standard,
                'encoding': 'utf8',
                'renders': {
                    'subscript': unisub
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
                    Marking.paren_open  : ('(',),
                    Marking.paren_close : (')',),
                    Marking.whitespace  : (' ',),
                    Marking.meta: {
                        'conseq': '⊢',
                        'nonconseq': '⊬',
                        # 'weak-assertion' : '»',
                    },
                },
            },
            html = dict(
                name     = 'standard.html',
                notation = Notation.standard,
                encoding = 'html',
                formats  = dict(
                    subscript = '<sub>{0}</sub>',
                ),
                strings = {
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
                    Marking.paren_open   : ('(',),
                    Marking.paren_close  : (')',),
                    Marking.whitespace   : (' ',),
                    Marking.meta: {
                        'conseq': '⊢',
                        'nonconseq': '⊬',
                    },
                },
            )
        )
    })
    RenderSet._initcache(Notation, data)


##############################################################

@closure
def _():
    for cls in (Bases.Enum, Bases.LexicalItem, Predicates, Argument, Bases.Lexical):
        cls._readonly = True
    nosetattr.enabled = True

del(
    _,
    abstract, closure, overload, final, static,
    NoSetAttr, fixed, lazy, membr, raisr, wraps,
    # nosetattr,
    abcf,
)
