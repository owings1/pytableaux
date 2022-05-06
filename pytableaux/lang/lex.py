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
pytableaux.lang.lex
^^^^^^^^^^^^^^^^^^^

Lexical item and enum classes.
"""
from __future__ import annotations

import operator as opr
from itertools import chain, repeat
from types import DynamicClassAttribute as dynca
from types import FunctionType
from typing import (TYPE_CHECKING, Annotated, Any, ClassVar, Iterable,
                    Iterator, Literal, Mapping, Sequence, SupportsIndex, final)

from pytableaux import _ENV, __docformat__, tools
from pytableaux.errors import Emsg, check
from pytableaux.lang import *
from pytableaux.tools import abcs, MapProxy
from pytableaux.tools.abcs import abcm
from pytableaux.tools.decorators import lazy, membr, wraps
from pytableaux.tools.hybrids import qsetf
from pytableaux.tools.mappings import DequeCache, dmap
from pytableaux.tools.sequences import EMPTY_SEQ, seqf
from pytableaux.tools.sets import EMPTY_SET, setf
from pytableaux.tools.typing import IcmpFunc, IndexType, T

if TYPE_CHECKING:
    from typing import overload

__all__ = (
    'Atomic',
    'Constant',
    'Lexical',
    'LexicalEnum',
    'LexicalItem',
    'LexType',
    'Notation',
    'Operated',
    'Operator',
    'Parameter',
    'Predicate',
    'Predicated',
    'Quantified',
    'Quantifier',
    'Quantifier',
    'Sentence',
    'Variable',
)

NOARG = object()

if TYPE_CHECKING:
    pass

_Ranks: Mapping[str, int] = MapProxy(dict(
    Predicate  = 10,
    Constant   = 20,
    Variable   = 30,
    Quantifier = 40,
    Operator   = 50,
    Atomic     = 60,
    Predicated = 70,
    Quantified = 80,
    Operated   = 90,
))

##############################################################

@abcm.clsafter
class Lexical:
    'Base Lexical interface for :class:`LexicalItem` and :class:`LexicalEnum` (mixin)'

    __slots__ = EMPTY_SET

    __init__ = NotImplemented

    TYPE: ClassVar[LexType]
    ":class:`LexType` enum instance for concrete classes."

    spec: SpecType
    """The arguments roughly needed to construct, given that we know the
    type, i.e. in intuitive order. A tuple, possibly nested, containing
    numbers or strings.
    """

    ident: IdentType
    """Equality identifier able to compare across types. Equivalent to
    ``(classname, spec)``.
    """

    sort_tuple: tuple[int, ...]
    """Sorting identifier, to order tokens of the same type. Numbers only
    (no strings). This is also used in hashing, so equal objects should
    have equal sort_tuples.

    **NB**: The first value must be the lexical rank of the type as specified
    in the :class:`LexType` enum class.
    """

    hash: int
    "The integer hash."

    #******   Equality, Ordering, & Comparison

    @staticmethod
    def identitem(item: Lexical, /) -> IdentType:
        'Build an :attr:`ident` tuple from the class name and :attr:`spec`.'
        return type(item).__name__, item.spec

    @staticmethod
    def hashitem(item: Lexical, /) -> int:
        'Compute a hash based on class name and :attr:`sort_tuple`.'
        return hash((type(item).__name__, item.sort_tuple))

    @staticmethod
    @tools.closure
    def orderitems():

        def cmpgen(a: Lexical, b: Lexical, /) -> Iterator[int]:
            yield a.TYPE.rank - b.TYPE.rank
            it = zip(ast := a.sort_tuple, bst := b.sort_tuple)
            yield from (ai - bi for ai, bi in it)
            yield len(ast) - len(bst)

        def orderitems(inst: Lexical, other: Lexical, /) -> int:
            """Pairwise ordering comparison based on type rank and :attr:`sort_tuple`.

            Args:
                inst (Lexical): The first :class:`Lexical` instance.
                other (Lexical): The second :class:`Lexical` instance.

            Returns:
                int: The relative order of ``inst`` and ``other``. The return value
                will be either:

                   * Less than ``0`` if ``inst`` is less than (ordered before) ``other``.
                   * Greater than ``0`` if ``inst`` is greater than (ordered after) ``other``.
                   * Equal to ``0`` if `inst` is equal to ``other``.

            Raises:
                TypeError: if an argument is not an instance of :class:`Lexical` with
                    a valid :attr:`TYPE` attribute.
            """
            if inst is other:
                return 0
            try:
                for cmp in cmpgen(inst, other):
                    if cmp:
                        return cmp
                return 0
            except AttributeError:
                raise TypeError

        return orderitems

    @abcm.f.temp
    @membr.defer
    def ordr(member: membr):
        oper: IcmpFunc = getattr(opr, member.name)
        def f(self: Lexical, other: Any, /):
            try:
                return oper(Lexical.orderitems(self, other), 0)
            except TypeError:
                if isinstance(other, Lexical):
                    raise
                return NotImplemented
        return wraps(oper)(f)

    __lt__ = __le__ = __gt__ = __ge__ = __eq__ = ordr()

    def __hash__(self):
        return self.hash

    #******  Item Generation

    if TYPE_CHECKING:

        @classmethod
        @overload
        def gen(cls: type[T], stop: int|None, /, first: T = None, **nextkw) -> Iterator[T]: ...

        @classmethod
        @overload
        def first(cls: type[T]) -> T: ...

        @overload
        def next(self: T, **kw) -> T: ...

    @classmethod
    def gen(cls, stop: int|None, /, first = None, **nextkw):
        """Generate items of the type, using :func:`first` and :func:`next` methods.

        Args:
            stop (int|None): The number at which to stop generating. If ``None``,
                never stop.
            first (Lexical): The first item. If ``None``, starts with :func:`first`.
            **nextkw: Parameters to pass to each call to :func:`next`.

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
    def first(cls):
        "Get the canonically first item of the type."
        raise NotImplementedError

    @tools.abstract
    def next(self, **kw):
        "Get the canonically next item of the type."
        raise NotImplementedError

    #******   Behaviors

    __delattr__ = raiseae
    __setattr__ = nosetattr(object, cls = LexicalItemMeta)

    __copy__ = abcs.Ebc.__copy__
    __deepcopy__ = abcs.Ebc.__deepcopy__

    def __bool__(self):
        'Always returns ``True``.'
        return True

    def for_json(self):
        "JSON Compatibility. Returns :attr:`ident` tuple."
        return self.ident

    #******  Subclass Init

    def __init_subclass__(subcls: type[Lexical], /, *,
        lexcopy: bool = False,
        skipnames: set[str] = set(tools.dund('init_subclass')),
        _cpnames: set[str] = set(tools.dund('copy', 'deepcopy')),
        _ftypes: tuple[type, ...] = (classmethod, staticmethod, FunctionType),
        **kw
    ):
        """Subclass init hook.

        If `lexcopy` is ``True``, copy the class members to the next class,
        since our protection is limited without metaclass flexibility.
        Only applies if this class is in the bases of the subclass.
        """
        super().__init_subclass__(**kw)
    
        if not lexcopy or __class__ not in subcls.__bases__:
            return

        src = dmap(__class__.__dict__)
        src -= set(subcls.__dict__)
        src -= set(skipnames)

        for name in _cpnames:
            if name not in src:
                src -= _cpnames
                break

        for name, value in src.items():
            if isinstance(value, _ftypes):
                setattr(subcls, name, value)

class LexicalEnum(Lexical, LangCommonEnum, lexcopy = True):
    """Base Enum implementation of Lexical. Subclassed by ``Quantifier``
    and ``Operator`` classes.
    """

    spec: tuple[str]
    ident: tuple[str, tuple[str]]
    # sort_tuple : tuple[int, ...]
    # hash       : int

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
        'hash',
        'ident',
        'index',
        'label',
        'order',
        'sort_tuple',
        'spec',
        'strings',
    )

    #******  Item Comparison

    def __eq__(self, other):
        'Allow equality with the string name.'
        if self is other:
            return True
        if type(self) is type(other):
            return False
        try:
            if other in self.strings:
                return True
        except TypeError:
            return NotImplemented
        if isinstance(other, str):
            return False
        return NotImplemented

    __hash__ = Lexical.__hash__

    #******  Item Generation

    @classmethod
    def first(cls):
        return cls._seq[0]

    def next(self, /, *, loop: bool = False):
        """Return the next member item.

        Args:
            loop (bool): If ``True``, returns the first member after the last.
        
        Returns:
            The member instance.
        
        Raises:
            StopIteration: If called on the last member and ``loop`` is ``False``.
        """
        seq = type(self)._seq
        try:
            return seq[self.index + 1]
        except IndexError:
            pass
        if loop:
            return seq[0]
        raise StopIteration

    #******  Instance Init

    def __init__(self, order: int, label: str, /):
        self.spec = self.name,
        self.order = order
        self.sort_tuple = _Ranks[type(self).__name__], order
        self.label = label
        self.strings = setf((self.name, self.label))
        self.ident = self.identitem(self)
        self.hash = self.hashitem(self)

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
        for i, member in enumerate(subcls._seq):
            member.index = i

class LexicalItem(Lexical, metaclass = LexicalItemMeta, lexcopy = True):
    'Base lexical item class.'

    __slots__ = (
        '_ident',
        '_hash',
    )

    @lazy.prop
    def ident(self):
        return self.identitem(self)

    @lazy.prop
    def hash(self):
        return self.hashitem(self)

    @tools.abstract
    def __init__(self): ...

    __delattr__ = raiseae

    def __setattr__(self, name, value, /):
        if getattr(self, name, NOARG) is not NOARG:
            if getattr(LexicalItem, '_readonly', False):
                raise Emsg.ReadOnly(self, name)
        super().__setattr__(name, value)

class CoordsItem(LexicalItem):
    """Common implementation for lexical types that are based on integer
    coordinates. For :class:`Constant`, :class:`Variable`, and :class:`Atomic`,
    the coordinates are `(index, subscript)`. For :class:`Predicate`, the
    coordinates are `(index, subscript, arity)`.
    """

    Coords: ClassVar = BiCoords

    spec: BiCoords

    index: int
    "The coords index."

    subscript: int
    "The coords subscript."

    __slots__ = (
        'coords',
        'index',
        'sort_tuple',
        'spec',
        'subscript',
    )

    if TYPE_CHECKING:
        @overload
        def __init__(self, *spec: int): ...

        @overload
        def __init__(self, spec: Iterable[int], /): ...

    #******  Item Generation

    @classmethod
    def first(cls):
        return cls(cls.Coords.first)

    def next(self):
        cls = type(self)
        idx, sub, *cargs = self.spec
        if idx < cls.TYPE.maxi:
            idx += 1
        else:
            idx = 0
            sub += 1
        return cls(idx, sub, *cargs)

    #******  Instance Init

    @tools.abstract
    def __init__(self, *spec):
        self.spec = spec = self.Coords._make(
            spec[0] if len(spec) == 1 else spec
        )
        try:
            for field, value in zip(spec._fields, spec):
                setattr(self, field, value.__index__())
        except:
            check.inst(value, int)
            raise
        try:
            if spec.index > self.TYPE.maxi:
                raise ValueError(f'{spec.index} > {self.TYPE.maxi}')
        except AttributeError:
            raise TypeError(f'Abstract: {type(self)}') from None
        if spec.subscript < 0:
            raise ValueError(f'subscript {spec.subscript} < 0')
        self.sort_tuple = (self.TYPE.rank, *spec.sorting())

##############################################################

class Quantifier(LexicalEnum):
    'Quantifier lexical enum class.'

    Existential = (0, 'Existential')
    "The Existential quantifier :s:`X`"

    Universal   = (1, 'Universal')
    "The Universal quantifier :s:`L`"

    def __call__(self, *spec: QuantifiedSpec) -> Quantified:
        'Quantify a variable over a sentence.'
        return Quantified(self, *spec)

class Operator(LexicalEnum):
    """Operator lexical enum class. Member definitions correspond to
    (`order`, `label`, `arity`, `libname`).
    """

    __slots__ = (
        'arity',
        'libname',
    )

    arity: int
    "The operator arity."

    libname: str|None
    """If the operator implements a Python arithmetic operator, this
    will be the special `"dunder"` name corresponding to Python's
    built-in :obj:`operator` module. For example, for :attr:`Conjunction`,
    which implements ``&``, the value is ``'__and__'``.
    """

    Assertion             = (10,  'Assertion',              1, None)
    "Assertion (:s:`*`) operator"

    Negation              = (20,  'Negation',               1, '__invert__')
    "Negation (:s:`~`) operator"

    Conjunction           = (30,  'Conjunction',            2, '__and__')
    "Conjunction (:s:`&`) operator"

    Disjunction           = (40,  'Disjunction',            2, '__or__')
    "Disjunction (:s:`V`) operator"

    MaterialConditional   = (50,  'Material Conditional',   2, None)
    "Material Conditional (:s:`>`) operator"

    MaterialBiconditional = (60,  'Material Biconditional', 2, None)
    "Material Biconditiona (:s:`<`) operator"

    Conditional           = (70,  'Conditional',            2, None)
    "Conditional (:s:`$`) operator"

    Biconditional         = (80,  'Biconditional',          2, None)
    "Biconditional (:s:`%`) operator"

    Possibility           = (90,  'Possibility',            1, None)
    "Possibility (:s:`P`) operator"

    Necessity             = (100, 'Necessity',              1, None)
    "Necessity (:s:`N`) operator"

    lib_opmap: ClassVar[Mapping[str, Operator]]

    def __init__(self, order: int, label: str, arity: int, libname: str|None, /):
        super().__init__(order, label)
        self.arity = arity
        self.libname = libname
        if libname is not None:
            self.strings |= {libname}

    if TYPE_CHECKING:
        @overload
        def __call__(self, operands: OperCallArg, /) -> Operated: ...

        @overload
        def __call__(self, *operands: Sentence) -> Operated: ...

    def __call__(self, *args) -> Operated:
        'Apply the operator to make a new sentence.'
        if len(args) > 1:
            return Operated(self, args)
        return Operated(self, *args)

    @classmethod
    def _after_init(cls):
        "Class init hook. Build the :attr:`lib_opmap`."
        super()._after_init()
        cls.lib_opmap = MapProxy({
            o.libname: o for o in cls if o.libname is not None
        })

##############################################################

class Parameter(CoordsItem):
    """Parameter base class for Constant & Variable."""

    __slots__ = EMPTY_SET

    Coords: ClassVar = BiCoords
    spec: ParameterSpec

    is_constant: bool
    "Whether the parameter is a :class:`Constant`."

    is_variable: bool
    "Whether the parameter is a :class:`Variable`."

@final
class Constant(Parameter):
    """Constant parameter implementation."""

    __slots__ = (
        'is_constant',
        'is_variable',
    )

    def __init__(self, *spec):
        super().__init__(*spec)
        self.is_constant = True
        self.is_variable = False

    def __rshift__(self, other):
        'Same as ``other.unquantify(self)``.'
        if not isinstance(other, Quantified):
            return NotImplemented
        return other.unquantify(self)

@final
class Variable(Parameter):
    """Variable parameter implementation."""

    __slots__ = Constant.__slots__

    def __init__(self, *spec):
        super().__init__(*spec)
        self.is_constant = False
        self.is_variable = True

@final
class Predicate(CoordsItem):
    """Predicate implementation.
    """
    Coords: ClassVar = TriCoords

    spec: PredicateSpec

    arity: int
    "The coords arity."

    bicoords: BiCoords
    "The `(index, subscript)` coords."

    is_system: bool
    "Whether this is a system predicate."

    name: tuple[int, ...] | str
    "The name, for system predicates, or the :attr:`spec` for user predicates."

    # refs: seqf[PredicateRef]
    # refkeys: qsetf[PredicateRef | Predicate]

    __slots__ = (
        '__objclass__',
        '_name_',
        '_refkeys',
        '_refs',
        '_value_',
        'arity',
        'bicoords',
        'is_system',
        'name',
        'value',
    )

    @lazy.prop
    def refs(self: Predicate) -> seqf[PredicateRef]:
        """The coords and other attributes, each of which uniquely identify this
        instance among other predicates. These are used to create hash indexes
        for retrieving predicates from predicate stores.

        .. _predicate-refs-list:

        - `spec` - The :attr:`spec` tuple.
        - `ident` - The :attr:`ident` tuple.
        - `bicoords` - The :attr:`bicoords` tuple `(index, subscript)`.
        - `name` - For system predicates, the name.
        """
        return seqf({self.spec, self.ident, self.bicoords, self.name})

    @lazy.prop
    def refkeys(self: Predicate) -> qsetf[PredicateRef | Predicate]:
        "The :attr:`refs` plus the predicate object."
        return qsetf({*self.refs, self})

    def __call__(self, *spec: PredicatedSpec) -> Predicated:
        'Apply the predicate to parameters to make a predicated sentence.'
        return Predicated(self, *spec)

    #******  Item Generation

    def next(self):
        if self.is_system:
            arity = self.arity
            for pred in self.System:
                if pred is not self and pred.arity == arity and pred > self:
                    return pred
        return super().next()

    #******  Instance Init

    if TYPE_CHECKING:
        @overload
        def __init__(self, spec: PredicateSpec, /): ...

        @overload
        def __init__(self, index: int, subscript: int, arity: int, name: str = None, /): ...

    def __init__(self, *spec):
        """Create a predicate.

        The parameters can be passed either expanded, or as a single
        ``tuple``. A valid spec consists of 3 integers in
        the order of `index`, `subscript`, `arity`, for example::

            Predicate(0, 0, 1)
            Predicate((0, 0, 1))
        """
        if (speclength := len(spec)) == 1:
            try:
                speclength = len(spec := spec[0])
            except:
                check.inst(spec, tuple)
                raise

        super().__init__(*spec[0:3])

        if self.arity <= 0:
            raise ValueError('`arity` must be > 0')

        self.bicoords = BiCoords(self.index, self.subscript)

        if self.index < 0:
            if len(self.System):
                raise ValueError('`index` must be >= 0')
            if speclength != 4:
                raise TypeError(f'need 4 elements, got {speclength}')
            self.is_system = True
            self.name = spec[3]
        else:
            if speclength != 3:
                raise TypeError(f'need 3 elements, got {speclength}')
            self.is_system = False
            self.name = self.spec
            self.__objclass__ = __class__

        self._name_ = self.name
        self._value_ = self

    #******  System Predicate enum

    class System(LangCommonEnum, metaclass = SysPredEnumMeta):
        'System predicates enum.'

        Existence : Annotated[Predicate, (-2, 0, 1, 'Existence')]
        "The Existence predicate :s:`!`"

        Identity  : Annotated[Predicate, (-1, 0, 2, 'Identity')]
        "The Identity predicate :s:`=`"


class Sentence(LexicalItem):
    'Sentence base class.'

    __slots__ = EMPTY_SET

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

    def negative(self) -> Sentence:
        """Either negate this sentence, or, if this is already a negated
        sentence return its negatum, i.e., "un-negate" the sentence.
        """
        return Operated(Operator.Negation, (self,))

    def substitute(self: SenT, pnew: Parameter, pold: Parameter, /) -> SenT:
        """Return the recursive substitution of ``pnew`` for all occurrences
        of ``pold``."""
        return self

    def variable_occurs(self, v: Variable, /) -> bool:
        'Whether the variable occurs anywhere in the sentence (recursive).'
        return v in self.variables

    #******  Item Generation

    @staticmethod
    def first():
        return Atomic.first()

    #******  Built-in Operator Symbols

    @abcm.f.temp
    @membr.defer
    def libopers_1(member: membr):
        oper = Operator.lib_opmap[member.name]
        def f(self: Sentence) -> Operated:
            return Operated(oper, self)
        return wraps(oper)(f)

    @abcm.f.temp
    @membr.defer
    def libopers_2(member: membr):
        oper = Operator.lib_opmap[member.name]
        def f(self: Sentence, other: Sentence, /) -> Operated:
            if not isinstance(other, Sentence):
                return NotImplemented
            return Operated(oper, (self, other))
        return wraps(oper)(f)

    __invert__ = libopers_1()
    __and__ = __or__ = libopers_2()


@final
class Atomic(CoordsItem, Sentence):
    'Atomic sentence.'

    spec: AtomicSpec
    "The sentence spec."

    __slots__ = (
        'atomics',
        'constants',
        'operators',
        'predicates',
        'quantifiers',
        'variables',
    )

    def __init__(self, *spec):
        super().__init__(*spec)
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
        '_constants',
        '_variables',
        'atomics',
        'operators',
        'params',
        'paramset',
        'predicate',
        'predicates',
        'quantifiers',
        'sort_tuple',
        'spec',
    )

    @lazy.prop
    def constants(self: Predicated) -> setf[Constant]:
        return setf(p for p in self.paramset if p.is_constant)

    @lazy.prop
    def variables(self: Predicated) -> setf[Variable]:
        return setf(p for p in self.paramset if p.is_variable)

    #******  Sentence Methods

    def substitute(self, pnew: Parameter, pold: Parameter, /) -> Predicated:
        if pnew == pold or pold not in self.paramset:
            return self
        return Predicated(self.predicate, tuple(
            (pnew if p == pold else p for p in self.params)
        ))

    #******  Instance Init

    def __init__(self, pred, params: Iterable[Parameter] | Parameter, /):
        self.predicate = pred = Predicate(pred)
        if isinstance(params, Parameter):
            self.params = params = params,
        else:
            self.params = params = tuple(map(Parameter, params))

        if len(params) != pred.arity:
            raise TypeError(self.predicate, len(params), pred.arity)

        self.predicates = setf((pred,))
        self.paramset = setf(params)
        self.operators = self.quantifiers = EMPTY_SEQ
        self.atomics = EMPTY_SET
        self.spec = (
            pred.spec,
            tuple(p.ident for p in params),
        )
        self.sort_tuple = (
            self.TYPE.rank,
            *pred.sort_tuple,
            *(n for p in params for n in p.sort_tuple),
        )

    #******  Item Generation

    @classmethod
    def first(cls, pred: Predicate = None, /):
        if pred is None:
            pred = Predicate.first()
        return cls(pred, tuple(repeat(Constant.first(), pred.arity)))

    def next(self):
        return Predicated(self.predicate.next(), self.params)

    #******  Sequence Behavior

    if TYPE_CHECKING:
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

    spec: QuantifiedSpec
    "The sentence spec."

    quantifier: Quantifier
    "The quantifier."

    variable: Variable
    "The bound variable."

    sentence: Sentence
    "The inner sentence."

    items: tuple[Quantifier, Variable, Sentence]
    "The items sequence: :class:`Quantifer`, :class:`Variable`, :class:`Sentence`."

    __slots__ = (
        '_quantifiers',
        'items',
        'quantifier',
        'sentence',
        'sort_tuple',
        'spec',
        'variable',
    )

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
            q := Quantifier(q), v := Variable(v), s := Sentence(s)
        )
        self.spec = (*q.spec, v.spec, s.ident)
        self.sort_tuple = (
            self.TYPE.rank,
            *q.sort_tuple,
            *v.sort_tuple,
            *s.sort_tuple
        )

    #******  Item Generation

    @classmethod
    def first(cls, q: Quantifier = Quantifier.first(), /):
        pass
        """Returns the first quantified sentence.
        
        Args:
            q (Quantifier): The Quantifier, default is the first quantifier.

        Returns:
            Sentence: Then sentence instance.
        """
        return cls(q, v := Variable.first(), Predicate.first()(v))

    def next(self, **kw):
        pass
        """Returns the next quantified sentence.
        
        Args:
            **kw: Parameters for :func:`Sentence.next()` to create the inner sentence.

        Returns:
            The sentence instance.
        
        Raises:
            TypeError: if :func:`Sentence.next()` returns a sentence for which the
                variable is no longer bound.
        """
        s = self.sentence.next(**kw)
        v = self.variable
        if v not in s.variables:
            raise TypeError(f'{v} no longer bound')
        return Quantified(self.quantifier, v, s)

    #******  Sequence Behavior

    def __len__(self):
        return len(self.items)

    def __contains__(self, item: Any, /):
        return item in self.items

    if TYPE_CHECKING:
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

    __slots__ =  (
        '_atomics',
        '_constants',
        '_operators',
        '_predicates',
        '_quantifiers',
        '_variables',
        'lhs',
        'operands',
        'operator',
        'rhs',
        'sort_tuple',
        'spec',
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
    def first(cls, oper: Operator = Operator.first(), /):
        return cls(oper, Atomic.gen(Operator(oper).arity))

    def next(self, **kw):
        return Operated(self.operator,
            (*self.operands[0:-1], self.operands[-1].next(**kw))
        )

    #******  Sentence Methods

    def substitute(self, pnew: Parameter, pold: Parameter, /) -> Operated:
        if pnew == pold:
            return self
        return Operated(self.operator, tuple(
            s.substitute(pnew, pold) for s in self)
        )

    def negative(self) -> Sentence:
        """Either negate this sentence, or, if this is already a negated
        sentence return its negatum, i.e., "un-negate" the sentence.
        """
        if self.operator is Operator.Negation:
            return self.lhs
        return self.negate()

    #******  Instance Init

    if TYPE_CHECKING:
        @overload
        def __init__(self, oper: Operator, operands: Iterable[Sentence], /): ...

        @overload
        def __init__(self, oper: Operator, spec: OperandsSpec, /): ...

        @overload
        def __init__(self, oper: Operator, *operands: Sentence): ...

    def __init__(self, oper: Operator, *operands):
        if len(operands) == 1:
            operands, = operands
        self.operator = oper = Operator(oper)
        if isinstance(operands, Sentence):
            self.operands = operands = operands,
        else:
            self.operands = operands = tuple(map(Sentence, operands))
        self.lhs = operands[0]
        self.rhs = operands[-1]
        if len(operands) != oper.arity:
            raise Emsg.WrongLength(operands, oper.arity)
        self.spec = *oper.spec, tuple(s.ident for s in operands)
        self.sort_tuple = (
            self.TYPE.rank,
            *oper.sort_tuple,
            *(n for s in operands
                for n in s.sort_tuple)
        )

    #******  Sequence Behavior

    if TYPE_CHECKING:
        @overload
        def __getitem__(self, i: SupportsIndex,/) -> Sentence:...

        @overload
        def __getitem__(self, s: slice,/) -> tuple[Sentence, ...]:...

    def __getitem__(self, index: IndexType, /):
        return self.operands[index]

    def __len__(self):
        return len(self.operands)

    def __contains__(self, s: Any, /):
        return s in self.operands

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

    pcls: type[Lexical] | None
    "The partner class, if any, e.g. `Operated` and `Operator` are partners."

    hash: int
    "The member hash."

    Predicate  = (_Ranks['Predicate'],  Predicate,  Predicate,     3, Predicated)
    "Predicate LexType."

    Constant   = (_Ranks['Constant'],   Constant,   Parameter,     3, None)
    "Constant LexType."

    Variable   = (_Ranks['Variable'],   Variable,   Parameter,     3, None)
    "Variable LexType."

    Quantifier = (_Ranks['Quantifier'], Quantifier, Quantifier, None, Quantified)
    "Quantifier LexType."

    Operator   = (_Ranks['Operator'],   Operator,   Operator,   None, Operated)
    "Operator LexType."

    Atomic     = (_Ranks['Atomic'],     Atomic,     Sentence,      4, None)
    "Atomic LexType."

    Predicated = (_Ranks['Predicated'], Predicated, Sentence,   None, Predicate[1])
    "Predicated LexType."

    Quantified = (_Ranks['Quantified'], Quantified, Sentence,   None, Quantifier[1])
    "Quantified LexType."

    Operated   = (_Ranks['Operated'],   Operated,   Sentence,   None, Operator[1])
    "Operated LexType."

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

    def __init__(self, rank: int, cls: type[Lexical], generic: type[Lexical], maxi: int|None, pcls: type[Sentence]|None, /):
        self.rank = rank
        self.cls = cls
        self.generic = generic
        self.maxi = maxi
        self.pcls = pcls
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
        """``EbcMeta`` hook. Build :attr:`classes` list."""
        super()._after_init()
        cls.classes = qsetf(m.cls for m in cls)

    @classmethod
    def _member_keys(cls, member: LexType):
        """``EbcMeta`` hook. Add the class object to the member lookup keys."""
        return super()._member_keys(member) | {member.cls}

@tools.closure
def caller():

    cache = DequeCache(maxlen = _ENV.ITEM_CACHE_SIZE)
    supercall = LangCommonMeta.__call__

    def call(cls, *spec):

        if len(spec) == 1:

            if isinstance(spec[0], cls):
                # Passthrough
                return spec[0]

            if isinstance(spec[0], str):
                if cls is Predicate:
                    # System Predicate string
                    return Predicate.System(spec[0])

        # Invoked class name.
        clsname = cls.__name__

        # Try cache
        try:
            return cache[clsname, spec]
        except KeyError:
            pass

        # Construct
        try:
            inst: LexicalItem = supercall(cls, *spec)
        except TypeError:
            if (
                # If a concrete LexType raised the error, propagate.
                cls in LexType or
                # Creating from spec supports only length 1.
                len(spec) != 1
            ):
                raise

            # Try arg as ident tuple (clsname, spec)
            clsname, spec = spec[0]
            Class = LexType(clsname).cls

            # Don't, for example, create a Predicate from a Sentence class.
            if not issubclass(Class, cls) and (
                # With the exception for Enum classes, if we are invoking the
                # LexicalItem class directly.
                cls is not LexicalItem
                    or
                not issubclass(Class, LexicalEnum)
            ):
                raise TypeError(Class, cls)

            # Try cache
            try:
                return cache[clsname, spec]
            except KeyError:
                pass

            # Construct
            inst = Class(*spec)
        else:
            pass

        cache[clsname, spec] = cache[inst.ident] = inst

        return inst


    call._cache = cache

    return call

LexicalItemMeta.__call__ = caller


del(
    _ENV,
    _Ranks,
    caller,
    dynca,
    final,
    FunctionType,
    lazy,
    membr,
    opr,
    tools,
    wraps,
)
