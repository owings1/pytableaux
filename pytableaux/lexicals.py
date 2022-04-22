# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
"""
pytableaux.lexicals
^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

__docformat__ = 'google'
__all__ = (
    'Argument',
    'Atomic',
    'Constant',
    'Lexical',
    'LexicalEnum',
    'LexicalItem',
    'LexType',
    'LexWriter',
    'Notation',
    'Operated',
    'Operator',
    'Quantifier',
    'Parameter',
    'Predicate',
    'Predicated',
    'Predicates',
    'Quantified',
    'Quantifier',
    'Sentence',
    'Variable',
)

import enum
import operator as opr
from itertools import chain, repeat
from types import DynamicClassAttribute as dynca
from typing import (TYPE_CHECKING, Annotated, Any, ClassVar, Iterable,
                    Iterator, Literal, Sequence, SupportsIndex, final,
                    overload)

import pytableaux.tools.misc
from pytableaux import tools
from pytableaux.errors import Emsg, check
from pytableaux.lang._aux import *
from pytableaux.tools import MapProxy
from pytableaux.tools.abcs import abcm
from pytableaux.tools.decorators import NoSetAttr, lazy, membr, raisr, wraps
from pytableaux.tools.hybrids import qset, qsetf
from pytableaux.tools.mappings import DequeCache, dmap
from pytableaux.tools.sequences import EMPTY_SEQ, SequenceApi, seqf
from pytableaux.tools.sets import EMPTY_SET, setf
from pytableaux.tools.typing import EnumDictType, IcmpFunc, IndexType, T

NOARG = object()
EMPTY_IT = iter(EMPTY_SEQ)
ITEM_CACHE_SIZE = 10000

if TYPE_CHECKING:
    pass

##############################################################

class LexicalItemMeta(LangCommonMeta):
    """Common metaclass for non-Enum lexicals.
    """

    Cache: ClassVar[DequeCache] = DequeCache(maxlen = ITEM_CACHE_SIZE)

    def __call__(cls, *spec):
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
        # Invoked class name.
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
            # Don't, for example, create a Predicate
            # from a Sentence class.
            if not issubclass(lextypecls, cls) and (
                # With the exception for Enum classes,
                # if we are invoking the LexicalItem
                # class directly.
                cls is not LexicalItem or
                not issubclass(lextypecls, LexicalEnum)
            ):
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

class LexWriterMeta(LangCommonMeta):
    'LexWriter Metaclass.'

    def __call__(cls, *args, **kw):
        if cls is LexWriter:
            if args:
                notn = Notation(args[0])
                args = args[1:]
            else:
                notn = Notation.default
            return notn.DefaultWriter(*args, **kw)
        return super().__call__(*args, **kw)

    @tools.closure
    def _sys():

        def checkcls(cls):
            try:
                if cls is not LexWriter:
                    raise AttributeError
            except NameError:
                raise AttributeError

        syslws = dict(set = None, unset = None)

        def fget(cls) -> LexWriter:
            'The system instance for representing.'
            checkcls(cls)
            # print(syslws)
            if syslws['set'] is not None:
                return syslws['set']
            if syslws['unset'] is None:
                syslws['unset'] = LexWriter()
            return syslws['unset']

        def fset(cls, lw: LexWriter|None):
            checkcls(cls)
            # print('SET', syslws)
            if lw is not None:
                check.inst(lw, LexWriter)
            syslws['unset'] = None
            syslws['set'] = lw
            pytableaux.tools.misc.drepr.lw = lw

        def fdel(cls):
            syslws.pop('unset')

        return dynca(fget, fset, fdel, doc = fget.__doc__)

@abcm.clsafter
class Lexical:
    'Lexical mixin class for both ``LexicalEnum`` and ``LexicalItem`` classes.'

    __slots__ = EMPTY_SET

    TYPE: ClassVar[LexType]
    "``LexType`` enum instance for concrete classes."

    spec: tuple
    """The arguments roughly needed to construct, given that we know the
    type, i.e. in intuitive order. A tuple, possibly nested, containing
    digits or strings.
    """

    ident: IdentType
    """Equality identifier able to compare across types. A tuple, possibly
    nested, containing digits and possibly strings. The first should be
    the class name. Most naturally this would be followed by the spec.
    """

    sort_tuple: tuple[int, ...]
    """Sorting identifier, to order tokens of the same type. Numbers only
    (no strings). This is also used in hashing, so equal objects should
    have equal sort_tuples.

    **NB**: The first value must be the lexical rank of the type as specified
    in the `LexType` enum class.
    """

    hash: int
    "The integer hash."

    #******   Comparison

    @staticmethod
    def identitem(item: Lexical) -> IdentType:
        'Build an ``ident`` tuple from the class name and ``spec``.'
        return type(item).__name__, item.spec

    @staticmethod
    def hashitem(item: Lexical) -> int:
        'Compute a hash based on class name and ``sort_tuple``.'
        # Note, string hashes are not constant across restarts.
        return hash((type(item).__name__, item.sort_tuple))

    @staticmethod
    @tools.closure
    def orderitems():

        def cmpgen(a: Lexical, b: Lexical, /):
            if a is b:
                yield 0
                return
            yield a.TYPE.rank - b.TYPE.rank
            ast = a.sort_tuple
            bst = b.sort_tuple
            yield from (ai - bi for ai, bi in zip(ast, bst))
            yield len(ast) - len(bst)

        def orderitems(inst: Lexical, other: Lexical, /) -> int:
            """Pairwise ordering comparison based on type rank and ``sort_tuple``.

            Args:
                inst: The first ``Lexical`` instance.
                other: The second ``Lexical`` instance.

            Returns:
                int: The relative order of ``inst`` and ``other``. The return value
                   will be either:

                   - Less than 0 if `inst` is less than (ordered before) `other`.
                   - Greater than > 0 if `inst` is greater than (ordered after) `other`.
                   - Equal to 0 if `inst` is equal to `other`.

            Raises:
                TypeError: if an argument is not an instance of ``Lexical`` with
                    a valid ``LexType``.
            """
            try:
                for cmp in cmpgen(inst, other):
                    if cmp:
                        return cmp
                return cmp
            except AttributeError:
                raise TypeError

        return orderitems

    #******   Equality & Ordering

    @abcm.f.temp
    @membr.defer
    def ordr(member: membr):
        oper: IcmpFunc = getattr(opr, member.name)
        Lexical: type[Lexical] = member.owner
        @wraps(oper)
        def f(self: Lexical, other: Any, /):
            if not isinstance(other, Lexical):
                return NotImplemented
            return oper(Lexical.orderitems(self, other), 0)
        return f

    __lt__ = __le__ = __gt__ = __ge__ = __eq__ = ordr()

    def __hash__(self):
        return self.hash

    #******  Item Generation

    @classmethod
    def gen(cls: type[LexT], stop: SupportsIndex, /, first: LexT = None, **nextkw) -> Iterator[LexT]:
        """Generate items of the type, using ``first()`` and ``next()`` methods.

        Args:
            stop: The number at which to stop generating. If ``None``, never stop.
            first: The first item. If ``None``, starts with ``cls.first()``.
            **nextkw: Parameters to pass to each call to ``.next()``.

        Returns:
            The generator instance.
        """
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
            item = check.inst(first, cls)
        i = 0
        try:
            while i < stop:
                yield item
                item = item.next(**nextkw)
                i += inc
        except StopIteration:
            pass

    @classmethod
    @tools.abstract
    def first(cls: type[LexT]) -> LexT:
        "Get the canonically first item of the type."
        raise NotImplementedError

    @tools.abstract
    def next(self: LexT, **kw) -> LexT:
        "Get the canonically next item of the type."
        raise NotImplementedError

    #******   Behaviors

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

    def __forjson__(self, **kw):
        return self.ident

    def __init__(self):
        raise TypeError(self)

    #******  Attribute Access

    __delattr__ = raiseae
    __setattr__ = nosetattr(object, cls = LexicalItemMeta)

    #******  Subclass Init

    def __init_subclass__(subcls: type[Lexical], /, *,
        lexcopy = False, skipnames = {'__init_subclass__'}, **kw
    ):
        """Subclass init hook.

        With `lexcopy` = ``True``, copy the class members to the next class,
        since our protection is limited without metaclass flexibility.
        Only applies if this class is in the bases of the subclass.
        """
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

class LexicalEnum(Lexical, LangCommonEnum, lexcopy = True):
    """Base Enum implementation of Lexical. Subclassed by ``Quantifier``
    and ``Operator`` classes.
    """

    spec       : tuple[str]
    ident      : tuple[str, tuple[str]]
    sort_tuple : tuple[int, ...]
    hash       : int

    # Enum Instance Variables

    order: int
    "A number to signify relative member order (need not be sequence index)."

    label: str
    "Label with spaces allowed."

    index: int
    "The member index in the members sequence."

    strings: setf[str]
    """Name, label, or other strings unique to a member. These are automatically
    added as member keys.
    """

    __slots__ = (
        'spec', 'ident', 'sort_tuple', 'hash',
        'label', 'order', 'index', 'strings',
    )

    #******  Item Comparison

    def __eq__(self, other):
        'Allow equality with the string name.'
        if self is other:
            return True
        if isinstance(other, str):
            return other in self.strings
        return NotImplemented

    def __hash__(self):
        return self.hash

    #******  Item Generation

    @classmethod
    def first(cls):
        'Return the first member instance of this type.'
        return cls.seq[0]

    def next(self, /, *, loop: bool = False):
        """Return the next member item.

        Args:
            loop: If ``True``, returns the first member after the last.
        
        Return:
            The member instance.
        
        Raises:
            StopIteration: If called on the last member and ``loop`` is ``False``.
        """
        seq: Sequence[LexicalEnum] = self.seq
        i = self.index + 1
        if i == len(seq):
            if not loop: raise StopIteration
            i = 0
        return seq[i]

    #******  Instance Init

    def __init__(self, order: int, label: str, /):
        self.spec = self.name,
        self.order = order
        self.label = label
        self.ident = self.identitem(self)
        self.strings = setf((self.name, self.label))
        # NB: The value of hashitem would change after LexType modifies
        #     the sort_tuple. To workaround, we delay enum lookup index
        #     build until LexType init.
        # self.sort_tuple = <self.TYPE.rank>, self.order
        # self.hash = self.hashitem(self)
        pass

    @classmethod
    def _member_keys(cls, member: LexicalEnum):
        """``EbcMeta`` hook.
        
        Add any values in ``.strings`` as keys for the member index.
        """
        return super()._member_keys(member) | member.strings

    @classmethod
    def _on_init(cls, subcls: type[LexicalEnum]):
        """``EbcMeta`` hook.
        
        Store the sequence index of each member to ``.index``.
        """
        super()._on_init(subcls)
        for i, member in enumerate(subcls.seq):
            member.index = i

class LexicalItem(Lexical, metaclass = LexicalItemMeta, lexcopy = True):
    'Base lexical item class.'

    __slots__ = '_ident', '_hash',

    @lazy.prop
    def ident(self):
        return self.identitem(self)

    @lazy.prop
    def hash(self):
        return self.hashitem(self)

    @tools.abstract
    def __init__(self): ...

    #******  Attribute Access

    __delattr__ = raiseae

    def __setattr__(self, name, value):
        if getattr(self, name, value) is not value:
            if isinstance(getattr(type(self), name, None), property):
                pass
            else:
                raise Emsg.ReadOnlyAttr(name, self)
        super().__setattr__(name, value)

class CoordsItem(LexicalItem):
    """Common implementation for lexical types that are based on integer
    coordinates. For constants, variables and atomics, the coordinates
    are index, subscript. For Predicates, index, subscript, and arity.
    """

    Coords: ClassVar = BiCoords
    "The coords class for this type."

    spec: BiCoords
    "The item spec."

    coords: BiCoords
    "The item coordinates."

    index: int
    "The coords index."

    subscript: int
    "The coords subscript."

    __slots__ = 'spec', 'coords', 'index', 'subscript', '_sort_tuple',

    @lazy.prop
    def sort_tuple(self) -> tuple[int, ...]:
        return self.TYPE.rank, *self.coords.sorting()

    #******  Item Generation

    @classmethod
    def first(cls: type[CrdT]) -> CrdT:
        """Return the first item of this type according to ``.Coords.first``.

        For constants, variables, and atomics, the first coords are ``(0, 0)``.
        For predicates, the first coords are ``(0, 0, 1)``.
        """
        return cls(cls.Coords.first)

    def next(self: CrdT) -> CrdT:
        """Return the next item by incrementing the coords. The `index` coordinate
        is incremented until``.TYPE.maxi`` is reached. Then it index is set to ``0``,
        and the `subscript` coordinate is incremented.
        """
        cls = type(self)
        idx, sub, *cargs = self.coords
        if idx < cls.TYPE.maxi:
            idx += 1
        else:
            idx = 0
            sub += 1
        return cls(idx, sub, *cargs)

    #******  Instance Init

    @overload
    def __init__(self, *coords: int):...

    @overload
    def __init__(self, coords: Iterable[int], /):...

    @tools.abstract
    def __init__(self, *coords):
        self.coords = self.spec = coords = self.Coords._make(
            coords[0] if len(coords) == 1 else coords
        )
        for field, value in zip(coords._fields, coords):
            setattr(self, field, check.inst(value, int))
        try:
            if coords.index > self.TYPE.maxi:
                raise ValueError('%d > %d' % (coords.index, self.TYPE.maxi))
        except AttributeError:
            raise TypeError(f'Abstract: {type(self)}') from None
        if coords.subscript < 0:
            raise ValueError('subscript %d < %d' % (coords.subscript, 0))

##############################################################

class Quantifier(LexicalEnum, noidxbuild = True):
    'Quantifier lexical enum class.'

    Existential = 0, 'Existential'
    "The existential quantifier :s:`X`"

    Universal   = 1, 'Universal'
    "The universal quantifier :s:`L`"

    def __call__(self, *spec: QuantifiedSpec) -> Quantified:
        'Quantify a variable over a sentence.'
        return Quantified(self, *spec)

class Operator(LexicalEnum, noidxbuild = True):
    """Operator lexical enum class. Member definitions correspond to
    (`order`, `label`, `arity`, `libname`).
    """

    __slots__ = 'arity', 'libname'

    arity   : int
    "The operator arity."

    libname : str|None
    """If the operator implemented a Python arithmetic operator, this
    will be the special `"dunder"` name corresponding to Python's
    built-in :class:`operator` module. For example, for ``Conjunction``,
    which implements ``&``, the value is ``'__and__'``.
    """

    Assertion             = 10,  'Assertion',              1, None
    "Assertion :s:`*`"

    Negation              = 20,  'Negation',               1, '__invert__'
    "Negation :s:`~`"

    Conjunction           = 30,  'Conjunction',            2, '__and__'
    "Conjunction :s:`&`"

    Disjunction           = 40,  'Disjunction',            2, '__or__'
    "Disjunction :s:`V`"

    MaterialConditional   = 50,  'Material Conditional',   2, None
    "Material Conditional :s:`>`"

    MaterialBiconditional = 60,  'Material Biconditional', 2, None
    "Material Biconditional :s:`<`"

    Conditional           = 70,  'Conditional',            2, None
    "Conditional :s:`$`"

    Biconditional         = 80,  'Biconditional',          2, None
    "Biconditional :s:`%`"

    Possibility           = 90,  'Possibility',            1, None
    "Possibility :s:`P`"

    Necessity             = 100, 'Necessity',              1, None
    "Necessity :s:`N`"


    def __init__(self, order: int, label: str, arity: int, libname: str|None, /):
        super().__init__(order, label)
        self.arity = arity
        self.libname = libname
        if libname is not None:
            self.strings |= {libname}

    @overload
    def __call__(self, operands: OperCallArg, /) -> Operated:...

    @overload
    def __call__(self, *operands: Sentence) -> Operated:...

    def __call__(self, *args) -> Operated:
        'Apply the operator to make a new sentence.'
        if len(args) > 1:
            return Operated(self, args)
        return Operated(self, *args)

##############################################################

class Parameter(CoordsItem):
    """Parameter base class for Constant & Variable."""

    is_constant: bool
    "Whether the parameter is a ``Constant``."

    is_variable: bool
    "Whether the parameter is a ``Variable``."

    __slots__ = EMPTY_SET

@final
class Constant(Parameter):
    """Constant parameter implementation."""

    __slots__ = 'is_constant', 'is_variable'

    def __init__(self, *args):
        super().__init__(*args)
        self.is_constant = True
        self.is_variable = False

    def __rshift__(self, other):
        'Same as other.unquantify(self).'
        if not isinstance(other, Quantified):
            return NotImplemented
        return other.unquantify(self)

@final
class Variable(Parameter):
    """Variable parameter implementation."""

    __slots__ = Constant.__slots__

    def __init__(self, *args):
        super().__init__(*args)
        self.is_constant = False
        self.is_variable = True

@final
class Predicate(CoordsItem):
    """Predicate implementation.
    """
    Coords: ClassVar = TriCoords

    spec   : TriCoords
    coords : TriCoords

    arity: int
    "The coords arity."

    is_system: bool
    "Whether this is a system predicate."

    name: tuple[int, ...] | str
    "The name or spec"

    refs: seqf[PredicateRef]
    """The coords and other attributes, each of which uniquely identify this
    instance among other predicates. These are used to create hash indexes
    for retrieving predicates from predicate stores.

    .. _predicate-refs-list:

    - `spec` - A ``tuple`` with (index, subscript, arity).
    - `ident` - Includes class rank (``10``) plus `spec`.
    - `bicoords` - A ``tuple`` with (index, subscript).
    - `name` - For system predicates, e.g. `Identity`, but is legacy for
        user predicates.
    """

    refkeys: qsetf[PredicateRef | Predicate]
    "The ``refs`` plus the predicate object."

    bicoords: BiCoords
    "The ``(index, subscript)`` coords."

    __slots__ = (
        'arity', 'is_system', 'name', 'bicoords', '_refs', '_refkeys', 'value'
    )

    @lazy.prop
    def refs(self: Predicate):
        return seqf({self.spec, self.ident, self.bicoords, self.name})

    @lazy.prop
    def refkeys(self: Predicate):
        return qsetf({*self.refs, self})

    #******  Behaviors

    def __call__(self, *spec: PredicatedSpec):
        'Apply the predicate to parameters to make a predicated sentence.'
        return Predicated(self, *spec)

    #******  Item Generation

    def next(self) -> Predicate:
        arity = self.arity
        if self.is_system:
            # pred: Predicate
            for pred in self.System:
                if pred > self and pred.arity == arity:
                    return pred
        return super().next()

    #******  Instance Init

    @overload
    def __init__(self, spec: PredicateSpec, /): ...

    @overload
    def __init__(self, index: int, subscript: int, arity: int, name: str = None,/): ...

    def __init__(self, *spec):
        """Create a predicate.

        The parameters can be passed either expanded, or as a single
        ``tuple``. A valid spec consists of 3 integers in
        the order of `index`, `subscript`, `arity`, for example::

            Predicate(0, 0, 1)
            Predicate((0, 0, 1))
        """
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
            check.inst(name, (tuple, str))
        self.bicoords = BiCoords(self.index, self.subscript)

    #******  System Predicate enum

    class System(LangCommonEnum):
        'System predicates enum.'

        Existence : Annotated[Predicate, (-2, 0, 1, 'Existence')]
        "The Existence predicate :s:`!`"

        Identity  : Annotated[Predicate, (-1, 0, 2, 'Identity')]
        "The Identity predicate :s:`=`"

    @dynca
    def _value_(self: Predicate.System):
        try:
            if self.is_system: return self
        except AttributeError: return self
        raise AttributeError('_value_')

    @dynca
    def _name_(self: Predicate.System):
        if self.is_system: return self.name
        raise AttributeError('_name_')

    @dynca
    def __objclass__(self: Predicate.System):
        if self.is_system: return __class__.System
        raise AttributeError('__objclass__')

    @abcm.f.temp
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

##############################################################

class Sentence(LexicalItem):
    'Sentence base class.'

    predicates: setf[Predicate]
    "Set of predicates, recursive."

    constants: setf[Constant]
    "Set of constants, recursive."

    variables: setf[Variable]
    "Set of variables, recursive."

    atomics: setf[Atomic]
    "Set of atomic sentences, recursive."

    quantifiers: seqf[Quantifier]
    "Sequence of quantifiers, recursive."

    operators: seqf[Operator]
    "Sequence of operators, recursive."

    __slots__ = EMPTY_SET

    def negate(self) -> Operated:
        'Negate this sentence, returning the new sentence.'
        return Operated(Operator.Negation, (self,))

    def asserted(self) -> Operated:
        'Apply assertion operator to the sentence.'
        return Operated(Operator.Assertion, (self,))

    def disjoin(self, rhs: Sentence, /) -> Operated:
        'Apply disjunction to the right-hand sentence.'
        return Operated(Operator.Disjunction, (self, rhs))

    def conjoin(self, rhs: Sentence, /) -> Operated:
        'Apply conjunction to the right-hand sentence.'
        return Operated(Operator.Conjunction, (self, rhs))

    @overload
    def negative(self) -> Sentence:
        """Either negate this sentence, or, if this is already a negated
        sentence return its negatum, i.e., "un-negate" the sentence."""
    negative = negate

    def substitute(self: SenT, pnew: Parameter, pold: Parameter, /) -> SenT:
        """Return the recursive substitution of ``pnew`` for all occurrences
        of ``pold``."""
        return self

    def variable_occurs(self, v: Variable, /) -> bool:
        'Whether the variable occurs anywhere in the sentence (recursive).'
        return v in self.variables

    #******  Item Generation

    @staticmethod
    def first() -> Atomic:
        "Returns the first ``Atomic`` sentence."
        return Atomic.first()

    #******  Built-in Operator Symbols

    opmap = {
        # Ad hoc mapping since Operator index is not yet built.
        o.libname: o for o in Operator.seq if o.libname is not None
    }

    @abcm.f.temp
    @membr.defer
    def libopers1(member: membr, opmap: dict[str, Operator] = opmap):
        oper = opmap[member.name]
        @wraps(oper)
        def f(self: Sentence) -> Operated:
            return Operated(oper, self)
        return f

    @abcm.f.temp
    @membr.defer
    def libopers2(member: membr, opmap: dict[str, Operator] = opmap):
        oper = opmap[member.name]
        @wraps(oper)
        def f(self: Sentence, other: Sentence, /) -> Operated:
            if not isinstance(other, Sentence):
                return NotImplemented
            return Operated(oper, (self, other))
        return f

    __invert__ = libopers1()
    __and__ = __or__ = libopers2()

    del(opmap)

    # xor      ^
    # mul      *
    # matmul   @
    # truediv  /  -- conditional/materialconditional?
    # floordiv // -- biconditional/materialbiconditional?
    # mod      %
    # pow      **
    # rshift   >> -- conditional/materialconditional?
    # lshift   << -- biconditional/materialbiconditional?
    # neg      - -- negative?
    # pos      + -- assertion?
    pass

@final
class Atomic(CoordsItem, Sentence):
    'Atomic sentence.'

    __slots__ = (
        'predicates', 'constants', 'variables',
        'quantifiers', 'operators',
        'atomics',
    )

    def __init__(self, *coords):
        super().__init__(*coords)
        self.predicates = self.constants = self.variables = EMPTY_SET
        self.quantifiers = self.operators = EMPTY_SEQ
        self.atomics = setf((self,))

    def variable_occurs(self, v: Variable, /) -> bool:
        return False

@final
class Predicated(Sentence, Sequence[Parameter]):
    'Predicated sentence.'

    spec: PredicatedSpec
    "The sentence spec."

    predicate: Predicate
    "The predicate."

    params: tuple[Parameter, ...]
    "The parameters."

    paramset: setf[Parameter]
    "A set view of parameters."

    __slots__ = (
        '_spec', '_sort_tuple',
        'predicate', 'params', 'paramset',
        'quantifiers', 'operators', 'atomics',
        '_constants', '_variables', 'predicates',
    )

    @lazy.prop
    def spec(self):
        return self.predicate.spec, tuple(p.ident for p in self.params)

    @lazy.prop
    def sort_tuple(self: Predicated) -> tuple[int, ...]:
        return (
            self.TYPE.rank,
            *self.predicate.sort_tuple,
            *(n for param in self
                    for n in param.sort_tuple)
        )

    @lazy.prop
    def constants(self: Predicated) -> setf[Constant]:
        return setf(p for p in self.paramset if p.is_constant)

    @lazy.prop
    def variables(self: Predicated) -> setf[Variable]:
        return setf(p for p in self.paramset if p.is_variable)

    #******  Sentence Methods

    def substitute(self, pnew: Parameter, pold: Parameter, /) -> Predicated:
        if pnew == pold or pold not in self.paramset: return self
        return Predicated(self.predicate, tuple(
            (pnew if p == pold else p for p in self.params)
        ))

    #******  Instance Init

    def __init__(self, pred, params: Iterable[Parameter] | Parameter, /):
        self.predicate = pred = Predicate(pred)
        if isinstance(params, Parameter):
            self.params = params,
        else:
            self.params = tuple(map(Parameter, params))

        if len(self) != pred.arity:
            raise TypeError(self.predicate, len(self), pred.arity)

        self.predicates = setf((pred,))
        self.paramset = setf(self.params)
        self.operators = self.quantifiers = EMPTY_SEQ
        self.atomics = EMPTY_SET

    #******  Item Generation

    @classmethod
    def first(cls, pred: Predicate = None, /) -> Predicated:
        if pred is None:
            pred = Predicate.first()
        return cls(pred, tuple(repeat(Constant.first(), pred.arity)))

    def next(self):
        return Predicated(self.predicate.next(), self.params)

    #******  Sequence Behavior

    @overload
    def __getitem__(self, i: SupportsIndex, /) -> Parameter:...

    @overload
    def __getitem__(self, s: slice, /) -> tuple[Parameter, ...]:...

    def __getitem__(self, index: IndexType, /):
        return self.params[index]

    def __len__(self):
        return len(self.params)

    def __contains__(self, p: Any, /):
        return p in self.paramset

@final
class Quantified(Sentence, Sequence[QuantifiedItem]):
    'Quantified sentence.'

    #******  Instance Variables

    spec: QuantifiedSpec
    "The sentence spec."

    quantifier: Quantifier
    "The quantifier."

    variable: Variable
    "The bound variable."

    sentence: Sentence
    "The inner sentence."

    items: tuple[Quantifier, Variable, Sentence]
    "The items sequence: Quantifer, Variable, Sentence."

    __slots__ =  (
        'spec', '_sort_tuple',
        'quantifier', 'variable', 'sentence', 'items',
        '_quantifiers'
    )

    @lazy.prop
    def sort_tuple(self: Quantified) -> tuple[int, ...]:
        return tuple(chain(
            (self.TYPE.rank,),
            self.quantifier.sort_tuple,
            self.variable.sort_tuple,
            self.sentence.sort_tuple
        ))

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
        return seqf(chain((self.quantifier,), self.sentence.quantifiers))

    def unquantify(self, c: Constant, /) -> Sentence:
        'Instantiate the variable with a constant.'
        return self.sentence.substitute(Constant(c), self.variable)

    #******  Sentence Methods

    def substitute(self, pnew: Parameter, pold: Parameter, /) -> Quantified:
        if pnew == pold: return self
        return Quantified(
            self.quantifier, self.variable, self.sentence.substitute(pnew, pold)
        )

    def variable_occurs(self, v: Variable, /) -> bool:
        return self.variable == v or self.sentence.variable_occurs(v)

    #******  Instance Init

    def __init__(self, q: Quantifier, v: Variable, s: Sentence, /):
        self.quantifier, self.variable, self.sentence = self.items = (
            Quantifier(q), Variable(v), Sentence(s)
        )
        self.spec = *self.quantifier.spec, self.variable.spec, self.sentence.ident

    #******  Item Generation

    @classmethod
    def first(cls, q: Quantifier = Quantifier.seq[0],/) -> Quantified:
        """Returns the first quantified sentence.
        
        Args:
            q (Quantifier): The Quantifier, default is the first quantifier.

        Returns:
            Sentence: Then sentence instance.
        """
        v = Variable.first()
        return cls(q, v, Predicate.first()(v))

    def next(self, **kw) -> Quantified:
        """Returns the next quantified sentence.
        
        Args:
            **kw: Parameters for ``Sentence.next()`` to create the inner sentence.

        Returns:
            The sentence instance.
        
        Raises:
            TypeError: if ``Sentence.next()`` returns a sentence for which the
                variable is no longer bound.
        """
        s = self.sentence.next(**kw)
        v = self.variable
        if v not in s.variables:
            raise TypeError('%s no longer bound' % v)
        return Quantified(self.quantifier, v, s)

    #******  Sequence Behavior

    def __len__(self):
        return 3

    def __contains__(self, item: Any, /):
        return item in self.items

    @overload
    def __getitem__(self, i: Literal[0], /) -> Quantifier: ...

    @overload
    def __getitem__(self, i: Literal[1], /) -> Variable: ...

    @overload
    def __getitem__(self, i: Literal[2], /) -> Sentence: ...

    def __getitem__(self, i: SupportsIndex, /):
        return self.items[i]

    def count(self, item: Any, /) -> Literal[0]|Literal[1]:
        return int(item in self.items)

@final
class Operated(Sentence, Sequence[Sentence]):
    'Operated sentence.'

    spec: OperatedSpec
    "The sentence spec."

    operator: Operator
    "The operator."

    operands: tuple[Sentence, ...]
    "The operands."

    lhs: Sentence
    "The first (left-most) operand."

    rhs: Sentence
    "The last (right-most) operand."

    __slots__ =  setf((
        '_spec', '_sort_tuple',
        'operator', 'operands', 'lhs', 'rhs',
        '_predicates', '_constants', '_variables', '_quantifiers',
        '_operators', '_atomics',
    ))

    @lazy.prop
    def spec(self: Operated) -> OperatedSpec:
        return *self.operator.spec, tuple(s.ident for s in self)

    @lazy.prop
    def sort_tuple(self: Operated) -> tuple[int, ...]:
        return (
            self.TYPE.rank,
            *self.operator.sort_tuple,
            *(n for s in self
                    for n in s.sort_tuple)
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

    #******  Item Generation

    @classmethod
    def first(cls, oper: Operator = Operator.seq[0],/) -> Operated:
        return cls(oper, Atomic.gen(Operator(oper).arity))

    def next(self, **kw) -> Operated:
        return Operated(self.operator,
            (*self.operands[0:-1], self.operands[-1].next(**kw))
        )

    #******  Sentence Methods

    def substitute(self, pnew: Parameter, pold: Parameter,/) -> Operated:
        if pnew == pold: return self
        operands = (s.substitute(pnew, pold) for s in self)
        return Operated(self.operator, tuple(operands))

    def negative(self) -> Sentence:
        """Either negate this sentence, or, if this is already a negated
        sentence return its negatum, i.e., "un-negate" the sentence.
        """
        if self.operator is Operator.Negation:
            return self.lhs
        return self.negate()

    #******  Instance Init

    @overload
    def __init__(self, oper: Operator, operands: Iterable[Sentence], /):...

    @overload
    def __init__(self, oper: Operator, spec: OperandsSpec, /):...

    @overload
    def __init__(self, oper: Operator, *operands: Sentence):...

    def __init__(self, oper: Operator, *operands):
        if len(operands) == 1:
            operands, = operands
        self.operator = oper = Operator(oper)
        if isinstance(operands, Sentence):
            self.operands = operands,
        else:
            self.operands = tuple(map(Sentence, operands))
        self.lhs = self.operands[0]
        self.rhs = self.operands[-1]
        if len(self.operands) != oper.arity:
            raise Emsg.WrongLength(self.operands, oper.arity)

    #******  Sequence Behavior

    @overload
    def __getitem__(self, i: SupportsIndex,/) -> Sentence:...

    @overload
    def __getitem__(self, s: slice,/) -> tuple[Sentence, ...]:...

    def __getitem__(self, index: IndexType,/):
        return self.operands[index]

    def __len__(self):
        return len(self.operands)

    def __contains__(self, s: Any, /):
        return s in self.operands

##############################################################
##############################################################

class LexType(LangCommonEnum):
    'LexType metadata enum class for concrete types.'

    classes: ClassVar[qsetf[type[Lexical]]]
    "List of all the classes, unique, ordered."

    __slots__ = ('rank', 'cls', 'generic', 'maxi', 'role', 'hash')

    rank: int
    "A number to order items of different types."

    cls: type[Lexical]
    "The class reference."

    generic: type[Lexical]
    "The category class, such as ``Sentence`` for ``Atomic``."

    role: str
    "The category class name, such as ``'Sentence'`` for ``'Atomic'``."

    maxi: int | None
    "For coordinate classes, the maximum index."

    hash: int
    "The member hash."

    Predicate   = (10,  Predicate,  Predicate,     3)
    Constant    = (20,  Constant,   Parameter,     3)
    Variable    = (30,  Variable,   Parameter,     3)
    Quantifier  = (33,  Quantifier, Quantifier, None)
    Operator    = (35,  Operator,   Operator,   None)
    Atomic      = (40,  Atomic,     Sentence,      4)
    Predicated  = (50,  Predicated, Sentence,   None)
    Quantified  = (60,  Quantified, Sentence,   None)
    Operated    = (70,  Operated,   Sentence,   None)

    def __call__(self, *args, **kw) -> Lexical:
        return self.cls(*args, **kw)

    @abcm.f.temp
    @membr.defer
    def ordr(member: membr):
        oper: IcmpFunc = getattr(opr, member.name)
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

    def __init__(self, rank: int, cls: type[Lexical], generic: type[Lexical], maxi: int|None):
        super().__init__()
        self.rank, self.cls, self.generic, self.maxi = rank, cls, generic, maxi
        self.role = self.generic.__name__
        self.hash = hash(type(self).__name__) + self.rank
        self.cls.TYPE = self

    def __repr__(self, /):
        name = type(self).__name__
        try:
            return f'<{name}.{self.cls.__name__}>'
        except AttributeError:
            return f'<{name} ?ERR?>'

    @classmethod
    def _after_init(cls):
        """``EbcMeta`` hook.
        
        - Build `.classes` list.
        - For enum classes Operator & Quantifier:
            - write ``sort_tuple`` and ``hash``
            - build defered enum lookup
        """
        super()._after_init()
        cls.classes = qsetf(m.cls for m in cls.seq)
        for encls in (Operator, Quantifier):
            for member in encls.seq:
                member.sort_tuple = member.TYPE.rank, member.order
                member.hash = encls.hashitem(member)
            encls._lookup.build()

    @classmethod
    def _member_keys(cls, member: LexType):
        """``EbcMeta`` hook.
        
        Add the class object to the member lookup keys.
        """
        return super()._member_keys(member) | {member.cls}

##############################################################

class Predicates(qset[Predicate], metaclass = LangCommonMeta,
    hooks = {qset: dict(cast = Predicate)}
):
    'Predicate store. An ordered set with a multi-keyed lookup index.'

    _lookup: dmap[PredsItemRef, Predicate]
    __slots__ = '_lookup',

    def __init__(self, values: Iterable[PredsItemSpec] = None, /, *,
        sort: bool = False, key = None, reverse: bool = False):
        """Create a new store from an iterable of predicate objects
        or specs
        
        Args:
            values: Iterable of predicates or specs.
            sort: Whether to sort. Default is ``False``.
            key: Optional sort key.
            reverse: Whether to reverse sort.
        """
        self._lookup = dmap()
        super().__init__(values)
        if sort:
            self.sort(key = key, reverse = reverse)

    def get(self, ref: PredsItemRef, default = NOARG, /) -> Predicate:
        """Get a predicate by any reference. Also searches system predicates.

        Args:
            ref: Predicate reference. See ``Predicate.ref``.
            default: Value to return if not found.

        Returns:
            The Predicate instance.

        Raises:
            KeyError: if missing and no default specified.
        """
        try: return self._lookup[ref]
        except KeyError:
            try: return self.System[ref]
            except KeyError: pass
            if default is NOARG: raise
            return default

    def specs(self):
        return tuple(p.spec for p in self)

    @abcm.f.temp
    @qset.hook('done')
    def after_change(self, arriving: Iterable[Predicate], leaving: Iterable[Predicate]):
        'Implement after change (done) hook. Update lookup index.'
        for pred in leaving or EMPTY_IT:
            self._lookup -= pred.refkeys
        for pred in arriving or EMPTY_IT:
            # Is there a distinct predicate that matches any lookup keys,
            # viz. BiCoords or name, that does not equal pred, e.g. arity
            # mismatch.
            for other in filter(None, map(self._lookup.get, pred.refkeys)):
                if other != pred:
                    raise Emsg.ValueConflictFor(pred, pred.coords, other.coords)
            self._lookup |= zip(pred.refkeys, repeat(pred))

    #******  Override qset

    def clear(self):
        super().clear()
        self._lookup.clear()

    def __contains__(self, ref, /):
        return ref in self._lookup

    def copy(self):
        inst = super().copy()
        inst._lookup = self._lookup.copy()
        return inst

    #******  System Enum

    class System(Predicate.System):
        'System Predicates enum container class.'

        def __new__(cls, *spec):
            'Set the Enum value to the predicate instance.'
            return LexicalItem.__new__(Predicate)

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

        @abcm.f.before
        def expand(ns: EnumDictType, bases, **kw):
            'Inject members from annotations in Predicate.System class.'
            annots = abcm.annotated_attrs(Predicate.System)
            members = {
                name: spec for name, (vtype, spec)
                in annots.items() if vtype is Predicate
            }
            ns |= members
            ns._member_names += members.keys()

class Argument(SequenceApi[Sentence], metaclass = ArgumentMeta):
    """Argument class.
    
    A container of sentences with sequence and full ordering implementation.
    """

    def __init__(self,
        conclusion: Sentence,
        premises: Iterable[Sentence] = None,
        title: str = None
    ):
        self.seq = seqf(
            (Sentence(conclusion),) if premises is None
            else map(Sentence, (conclusion, *premises))
        )
        self.premises = seqf(self.seq[1:])
        if title is not None:
            check.inst(title, str)
        self.title = title

    __slots__ = 'seq', 'title', 'premises', '_hash', 

    sentences: seqf[Sentence]
    premises: seqf[Sentence]

    @property
    def conclusion(self) -> Sentence:
        return self.seq[0]

    @lazy.prop
    def hash(self) -> int:
        return hash(tuple(self))

    def predicates(self, **kw):
        """Return the predicates occuring in the argument.
        
        Args:
            **kw: sort keywords to pass to ``Predicates`` constructor.
        
        Returns:
            ``Predicates`` instance.
        """
        return Predicates((p for s in self for p in s.predicates), **kw)

    #******  Equality & Ordering

    # Two arguments are considered equal just when their conclusions are
    # equal, and their premises are equal (and in the same order). The
    # title is not considered in equality.

    @abcm.f.temp
    @tools.closure
    def ordr():

        sorder = Sentence.orderitems

        def cmpgen(a: Argument, b: Argument, /,):
            if a is b:
                yield 0 ; return
            yield bool(a.conclusion) - bool(b.conclusion)
            yield len(a) - len(b)
            yield from (sorder(sa, sb) for sa, sb in zip(a, b))

        @membr.defer
        def ordr(member: membr):
            oper: IcmpFunc = getattr(opr, member.name)
            @wraps(oper)
            def f(self: Argument, other: Any, /):
                if not isinstance(other, Argument):
                    return NotImplemented
                for cmp in cmpgen(self, other):
                    if cmp:
                        break
                else:
                    cmp = 0
                return oper(cmp, 0)
            return f

        return ordr

    __lt__ = __le__ = __gt__ = __ge__ = __eq__ = ordr() # type: ignore

    def __hash__(self):
        return self.hash

    #******  Sequence Behavior

    def __len__(self):
        return len(self.seq)

    @overload
    def __getitem__(self, s: slice, /) -> seqf[Sentence]: ...

    @overload
    def __getitem__(self, i: SupportsIndex, /) -> Sentence: ...

    def __getitem__(self, index: IndexType, /):
        if isinstance(index, slice):
            return seqf(self.seq[index])
        return self.seq[index]

    @classmethod
    def _concat_res_type(cls, othrtype: type[Iterable], /):
        if issubclass(othrtype, Sentence):
            # Protect against adding an Operated sentence, which counts
            # as a sequence of sentences. It would add just the operands
            # but not the sentence.
            return NotImplemented
        return super()._concat_res_type(othrtype)

    @classmethod
    def _rconcat_res_type(cls, othrtype: type[Iterable], /):
        if issubclass(othrtype, Sentence):
            return NotImplemented
        if othrtype is tuple or othrtype is list:
            return othrtype
        return seqf

    @classmethod
    def _from_iterable(cls, it):
        '''Build an argument from an non-empty iterable using the first element
        as the conclusion, and the others as the premises.'''
        it = iter(it)
        try:
            conc = next(it)
        except StopIteration:
            raise TypeError('empty iterable') from None
        return cls(conc, it)

    #******  Other

    def __forjson__(self, **_):
        return dict(
            conclusion = self.conclusion,
            premises = self.premises
        )

    def __repr__(self):
        if self.title:
            desc = repr(self.title)
        else:
            desc = f'len({len(self)})'
        return f'<{type(self).__name__}:{desc}>'

    def __setattr__(self, attr, value):
        if hasattr(self, attr):
            raise AttributeError(attr)
        super().__setattr__(attr, value)

    __delattr__ = raiseae

class LexWriter(metaclass = LexWriterMeta):
    'LexWriter interface and coordinator.'

    __slots__ = 'opts', 'renderset'

    #******  Class Variables

    notation: ClassVar[Notation]
    defaults: ClassVar[dict[str, Any]] = {}
    _methodmap = MapProxy[LexType, str](dict(
        zip(LexType, repeat(NotImplemented))
    ))
    _sys: ClassVar[LexWriter]

    #******  Instance Variables

    renderset: RenderSet
    opts: dict[str, Any]
    charset: str

    @property
    def charset(self) -> str:
        return self.renderset.charset

    #******  External API

    def write(self, item: Lexical) -> str:
        'Write a lexical item.'
        return self._write(item)

    @overload
    def __call__(self, item: Lexical) -> str: ...
    __call__ = write

    @classmethod
    def canwrite(cls, obj: Any) -> bool:
        "Whether the object can be written."
        try: return obj.TYPE in cls._methodmap
        except AttributeError: return False

    #******  Instance Init

    def __init__(self, charset: str = None, renderset: RenderSet = None, **opts):
        if renderset is None:
            notn = self.notation
            if charset is None:
                charset = notn.default_charset
            renderset = RenderSet.fetch(notn, charset)
        elif charset is not None and charset != renderset.charset:
            raise Emsg.WrongValue(charset, renderset.charset)
        self.opts = dict(self.defaults, **opts)
        self.renderset = renderset

    #******  Internal API

    def _write(self, item: Lexical) -> str:
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

    #******  Class Init

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
        if notn.DefaultWriter is None:
            notn.DefaultWriter = subcls
        return subcls

    def __init_subclass__(subcls: type[LexWriter], **kw):
        'Merge and freeze method map from mro. Sync ``__call__()``.'
        super().__init_subclass__(**kw)
        abcm.merge_mroattr(
            subcls, '_methodmap', supcls = __class__, transform = MapProxy
        )
        subcls.__call__ = subcls.write

class BaseLexWriter(LexWriter):
    "Common lexical writer abstract class."

    __slots__ = EMPTY_SET

    _methodmap = {
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

    @tools.abstract
    def _write_operated(self, item: Operated) -> str: ...

    def _strfor(self, *args, **kw) -> str:
        return self.renderset.string(*args, **kw)

    def _write_plain(self, item: Lexical) -> str:
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
        return self._strfor(Marking.subscript, s)

@LexWriter.register
class PolishLexWriter(BaseLexWriter):
    "Polish notation lexical writer implementation."

    __slots__ = EMPTY_SET

    notation = Notation.polish
    defaults = {}

    def _write_operated(self, item: Operated) -> str:
        return ''.join(map(self._write, (item.operator, *item)))

@LexWriter.register
class StandardLexWriter(BaseLexWriter):
    "Standard notation lexical writer implementation."

    __slots__ = EMPTY_SET

    notation = Notation.standard
    defaults = dict(drop_parens = True)

    def write(self, item: Lexical) -> str:
        if self.opts['drop_parens'] and isinstance(item, Operated):
            return self._write_operated(item, drop_parens = True)
        return super().write(item)

    def _write_predicated(self, item: Predicated) -> str:
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

    def _write_operated(self, item: Operated, drop_parens = False) -> str:
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

    def _write_negated_identity(self, item: Operated) -> str:
        si: Predicated = item.lhs
        params = si.params
        return self._strfor(Marking.whitespace, 0).join((
            self._write(params[0]),
            self._strfor((LexType.Predicate, True), (item.operator, si.predicate)),
            self._write(params[1]),
        ))

    def _test(self) -> list[str]:
        s1 = Predicate.System.Identity(Constant.gen(2)).negate()
        s2 = Operator.Conjunction(Atomic.gen(2))
        s3 = s2.disjoin(Atomic.first())
        return super()._test() + list(map(self, [s1, s2, s3]))


del(
    # _,
    overload, final,
    NoSetAttr, lazy, membr, raisr, wraps,
    # nosetattr,
    enum,
)


