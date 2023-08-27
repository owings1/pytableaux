# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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
from __future__ import annotations

"""
pytableaux.lang.lex
-------------------

Lexical classes.
"""
import operator as opr
from abc import abstractmethod
from functools import partial
from itertools import chain, repeat, starmap, zip_longest
from types import FunctionType
from types import MappingProxyType as MapProxy
from typing import (TYPE_CHECKING, Any, ClassVar, Iterator, Mapping, Self,
                    Sequence, Set, SupportsIndex)

from .. import errors
from ..errors import Emsg, check
from ..tools import (EMPTY_SEQ, EMPTY_SET, abcs, closure, inflect, lazy, membr,
                     qsetf, wraps)
from . import (BiCoords, LangCommonEnum, LangCommonMeta, LexicalAbcMeta,
               TriCoords, nosetattr)

__all__ = (
    'Atomic',
    'Constant',
    'CoordsItem',
    'Lexical',
    'LexicalEnum',
    'LexicalAbc',
    'LexType',
    'Operated',
    'Operator',
    'Parameter',
    'Predicate',
    'Predicated',
    'Quantified',
    'Quantifier',
    'Sentence',
    'Variable')

NOARG = object()

_Ranks: Mapping[str, int] = MapProxy(dict(
    Predicate  = 10,
    Constant   = 20,
    Variable   = 30,
    Quantifier = 40,
    Operator   = 50,
    Atomic     = 60,
    Predicated = 70,
    Quantified = 80,
    Operated   = 90))

#----------------------------------------------------------
#
#   Bases Classes
#
#----------------------------------------------------------

@abcs.clsafter
class Lexical:
    """Base Lexical class. This is the base class from which all concrete lexical
    classes inherit, including enum classes. It provides basic features of
    identitfying, comparing, and generating items.

    The :attr:`ident` and :attr:`spec` attributes provide canonical ways
    of specifying items with tuples of numbers, strings, and other
    tuples. This is useful for serialization and deserialization.

    The :meth:`first()`, :meth:`next()`, and :meth:`gen()` methods enable
    programatic creation of items.

    The :attr:`hash` and :attr:`sort_tuple` attributes allow for rich
    comparison and ordering of items, with consistency for comparing
    across different types.

    The :attr:`TYPE` refers to the corresponding member of the special
    :class:`LexType` enum class member, which holds meta information about
    each type.
    """

    __slots__ = EMPTY_SET

    __init__ = NotImplemented

    TYPE: ClassVar[LexType]
    ":class:`LexType` enum instance for concrete classes."

    spec: tuple
    """The arguments roughly needed to construct, given that we know the
    type, i.e. in intuitive order. A tuple, possibly nested, containing
    numbers or strings.
    """

    ident: tuple[str, tuple]
    """Equality identifier able to compare across types. Equivalent to
    ``(classname, spec)``.
    """

    sort_tuple: tuple[int, ...]
    """Sorting identifier, to order tokens of the same type, consisting of
    non-negative integers. This is also used in hashing, so equal objects
    must have equal `sort_tuple` values.
    """
    # **NB**: The first value of the sort_tuple must be the lexical rank of the
    # type as specified in the :class:`LexType` enum class.

    hash: int
    "The integer hash. Same as ``hash(obj)``."

    @classmethod
    def first(cls) -> Self:
        """Get the canonically first item of the type. This can be called on
        both concrete and abstract classes. For example:

        >>> Atomic.first()
        <Sentence: A>
        >>> Constant.first()
        <Parameter: a>
        >>> Constant.first() == Parameter.first()
        True
        >>> Operated.first()
        <Sentence: ⚬A>
        >>> Lexical.first()
        <Predicate: F>
        >>> LexicalEnum.first()
        <Quantifier: Existential>
        """
        if cls is __class__:
            return Predicate.first()
        raise TypeError(f'Abstract type {cls}')

    @abstractmethod
    def next(self, **kw) -> Self:
        """Get the canonically next item of the type. Various subclasses may
        provide optional keyword arguments.
        """
        raise NotImplementedError

    @classmethod
    def gen(cls, stop: int|None, /, first: Self|None = None, **nextkw) -> Iterator[Self]:
        """Generate items of the type, using :meth:`first` and :meth:`next` methods.

        This is convenient for making sequential lexical items quickly, without
        going through parsing.

        >>> Predicate(1,0,4)(Constant.gen(4))
        <Sentence: Gabcd>

        Args:
            stop: The number at which to stop generating. If ``None``,
                never stop.
            first: The first item. If ``None``, starts with :meth:`first`.
            **nextkw: Parameters to pass to each call to :meth:`next`.

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

    @staticmethod
    def identitem(item: Lexical, /) -> tuple[str, tuple]:
        """Build an :attr:`ident` tuple for the item from the class name and :attr:`spec`.

        This method should generally not need to be called, as it is used to
        generate and cache the instance :attr:`ident` property.
        """
        return (type(item).__name__, item.spec)

    @staticmethod
    def hashitem(item: Lexical, /) -> int:
        """Compute a hash for the item based on :attr:`sort_tuple`.

        This method should generally not need to be called, as it is used to
        generate and cache the instance :attr:`hash` property.
        """
        return hash((__class__, item.sort_tuple))

    @staticmethod
    def orderitems(lhs: Lexical, rhs: Lexical, /) -> int:
        """orderitems(lhs: Lexical, rhs: Lexical, /) -> int
        Pairwise ordering comparison based on type rank and :attr:`sort_tuple`.
        This is the base method used to support equality and rich comparison
        operators between any Lexical instance, regardless of subclass.

        Args:
            lhs: The left-hand item.
            rhs: The right-hand item.

        Returns:
            The relative order of ``lhs`` and ``rhs``. The return value
            will be either:

                * Less than ``0`` if ``lhs`` precedes ``rhs`` in order.
                * Greater than ``0`` if ``rhs`` precedes ``lhs`` in order.
                * Equal to ``0`` if `lhs` is equal to ``rhs`` in order.

        Raises:
            TypeError: if an argument is not an instance of :class:`Lexical` with
                a valid :attr:`sort_tuple` attribute.
        """
        if lhs is rhs:
            return 0
        try:
            it = zip_longest(lhs.sort_tuple, rhs.sort_tuple, fillvalue=0)
        except AttributeError:
            check.inst(lhs, __class__)
            check.inst(rhs, __class__)
            raise # pragma: no cover
        for cmp in filter(None, starmap(opr.sub, it)):
            return cmp
        return 0

    @abcs.abcf.temp
    @membr.defer
    def wrapper(member: membr):
        @wraps(oper := getattr(opr, member.name))
        def wrapped(self, other, /):
            try:
                return oper(Lexical.orderitems(self, other), 0)
            except TypeError:
                if isinstance(other, Lexical): # pragma: no cover
                    raise
                return NotImplemented
        return wrapped

    __lt__ = __le__ = __gt__ = __ge__ = __eq__ = wrapper()

    def __hash__(self):
        return self.hash

    __delattr__ = Emsg.ReadOnly.razr

    __setattr__ = nosetattr(object, cls=LexicalAbcMeta)

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    def __bool__(self):
        'Always returns ``True``.'
        return True

    def for_json(self):
        "JSON Compatibility. Returns :attr:`ident` tuple."
        return self.ident

    def __init_subclass__(cls, /, *, lexcopy=False, **kw):
        """Subclass init hook.

        If `lexcopy` is ``True``, copy the class members to the next class,
        since our protection is limited without metaclass flexibility. Only
        applies to direct sub classes.
        """
        super().__init_subclass__(**kw)
        if not lexcopy or __class__ not in cls.__bases__:
            return
        src = dict(__class__.__dict__)
        del src['__init_subclass__']
        for _ in map(src.__delitem__, filter(src.__contains__, cls.__dict__)): pass
        cpnames = ('__copy__', '__deepcopy__')
        if not all(map(src.__contains__, cpnames)):
            for _ in map(src.__delitem__, cpnames): pass
        ftypes = (classmethod, staticmethod, FunctionType)
        for name, value in src.items():
            if isinstance(value, ftypes):
                setattr(cls, name, value)


class LexicalAbc(Lexical, metaclass=LexicalAbcMeta, lexcopy=True):
    'Base class for non-Enum lexical classes.'

    __slots__ = ('_ident', '_hash',)

    @lazy.prop
    def ident(self):
        return self.identitem(self)

    @lazy.prop
    def hash(self):
        return self.hashitem(self)

    @classmethod
    def first(cls) -> Self:
        if cls is __class__:
            return Lexical.first()
        raise TypeError(f'Abstract type {cls}')

    @abstractmethod
    def __init__(self): ...

    __delattr__ = Emsg.ReadOnly.razr

    def __setattr__(self, name, value, /):
        v = getattr(self, name, NOARG)
        if v is not NOARG:
            if getattr(LexicalAbc, '_readonly', False):
                if v == value:
                    errors.warn(
                        f'duplicate value for attribute {name}',
                        errors.RepeatValueWarning)
                else:
                    raise Emsg.ReadOnly(self, name)
        super().__setattr__(name, value)

    def __getnewargs__(self):
        return self.spec


class LexicalEnum(Lexical, LangCommonEnum, lexcopy=True):
    """Base class for Enum lexical classes. Subclassed by :class:`Quantifier`
    and :class:`Operator`.
    """

    __slots__ = (
        'hash',
        'ident',
        'index',
        'label',
        'order',
        'sort_tuple',
        'spec',
        'strings')

    order: int
    "A number to signify relative member order (need not be sequence index)."

    label: str
    "Label with spaces allowed."

    index: int
    "The member index in the members sequence."

    strings: frozenset[str]
    "Name, label, or other strings unique to a member."

    def __eq__(self, other):
        'Allow equality with the string name.'
        if self is other:
            return True
        if type(self) is type(other):
            # Non-identical members are assumed non-equal.
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

    @classmethod
    def first(cls) -> Self:
        if cls is __class__:
            return Quantifier._seq[0]
        return cls._seq[0]

    def next(self, /, *, loop: bool = False) -> Self:
        """
        Args:
            loop (bool): If ``True``, returns the first member after the last.
                Default is ``False``.
       
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

    def __init__(self, order: int, /):
        self.spec = self.name,
        self.order = order
        self.sort_tuple = _Ranks[type(self).__name__], order
        self.label = inflect.snakespace(self.name)
        self.strings = frozenset((self.name, self.label))
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
        for i, member in enumerate(subcls):
            member.index = i

class CoordsItem(LexicalAbc):
    """Common implementation for lexical types that are based on integer
    coordinates. For :class:`Constant`, :class:`Variable`, and :class:`Atomic`,
    the coordinates are `(index, subscript)`. For :class:`Predicate`, the
    coordinates are `(index, subscript, arity)`.
    """

    __slots__ = (
        'coords',
        'index',
        'sort_tuple',
        'spec',
        'subscript')

    Coords = BiCoords

    index: int
    "The `index` coordinate."

    subscript: int
    "The `subscript` coordinate."

    spec: BiCoords|TriCoords

    @classmethod
    def first(cls) -> Self:
        if cls is __class__:
            cls = Predicate
        return cls(cls.Coords.first)

    def next(self) -> Self:
        cls = type(self)
        idx, sub = self.spec[0:2]
        if idx < cls.TYPE.maxi:
            idx += 1
        else:
            idx = 0
            sub += 1
        return cls(self.spec._replace(index = idx, subscript = sub))

    def __new__(cls, *spec):
        self = object.__new__(cls)
        sa = object.__setattr__
        sa(self, 'spec', spec := self.Coords._make(
            spec[0] if len(spec) == 1 else spec))
        try:
            for field, value in zip(spec._fields, spec):
                sa(self, field, value.__index__())
        except:
            check.inst(value, int)
            raise # pragma: no cover
        try:
            if spec.index > self.TYPE.maxi:
                raise ValueError(f'{spec.index} > {self.TYPE.maxi}')
        except AttributeError:
            raise TypeError(f'Abstract type {cls}') from None
        if spec.subscript < 0:
            raise ValueError(f'subscript {spec.subscript} < 0')
        sa(self, 'sort_tuple', (self.TYPE.rank, *spec.sorting()))
        return self


class Parameter(CoordsItem):
    """Parameter base class for :class:`Constant` & :class:`Variable`."""

    spec: BiCoords

    @classmethod
    def first(cls):
        if cls is __class__:
            return Constant.first()
        return super().first()

#----------------------------------------------------------
#
#   Lexical Enum Classes
#
#----------------------------------------------------------


class Quantifier(LexicalEnum):
    """Quantifier enum class.

    Behaviors
    ---------

    * Calling a quantifier constructs a :class:`Quantified` sentence

      >>> x = Variable(0, 0)
      >>> s1 = Predicated.first()
      >>> s2 = Quantifier.Existential(x, s1)
      >>> s2 == Quantified(Quantifier.Existential, x, s1)
      True
    """

    Existential = 0
    "The :s:`X` Existential quantifier"

    Universal = 1
    "The :s:`L` Universal quantifier"

    other: Quantifier

    def __call__(self, *spec):
        'Quantify a variable over a sentence.'
        return Quantified(self, *spec)

    @classmethod
    def _after_init(cls):
        """``EbcMeta`` hook. Build :attr:`classes` list, and System Predicates."""
        super()._after_init()
        it = iter(cls)
        for a in it:
            b = next(it)
            a.other = b
            b.other = a

class Operator(LexicalEnum):
    """Operator enum class.

    Behaviors
    ---------

    * Calling an operator constructs an :class:`Operated` sentence

    >>> s1 = Atomic(0, 0)
    >>> s2 = Operator.Conditional(s1, s1)
    >>> s2 == Operated(Operator.Conditional, (s1, s1))
    True

    * Some operators map to Python operators, such as & or ~.
    
    >>> s = Atomic(0, 0)
    >>> Operator.Conjunction(s, s) == s & s
    True
    >>> s.negate() == ~s
    True

    See the :class:`Sentence` class for more.

    Members
    -------

    .. csv-table::
        :generator: member-table
        :generator-args: name arity
    """

    __slots__ = ('arity',)

    arity: int
    "The operator arity."
    other: Operator

    Assertion             = (10,  1)
    'The Assertion operator'
    Negation              = (20,  1)
    'The Negation (not) operator'
    Conjunction           = (30,  2)
    'The Conjunction (and) operator'
    Disjunction           = (40,  2)
    'The Disjunction (or) operator'
    MaterialConditional   = (50,  2)
    'The Material Conditional operator'
    MaterialBiconditional = (60,  2)
    'The Material Biconditional operator'
    Conditional           = (70,  2)
    'The Conditional operator'
    Biconditional         = (80,  2)
    'The Biconditional operator'
    Possibility           = (90,  1)
    'The Possibility operator'
    Necessity             = (100, 1)
    'The Necessity operator'

    def __call__(self, *args):
        'Apply the operator to make a new sentence.'
        return Operated(self, *args)

    def __init__(self, order, arity, /):
        super().__init__(order)
        self.arity = arity

    @classmethod
    def _after_init(cls):
        """``EbcMeta`` hook. Set :attr:`other` attribute."""
        super()._after_init()
        it = iter(cls)
        for a in it:
            b = next(it)
            a.other = b
            b.other = a

#----------------------------------------------------------
#
#   Abstract Sentence class.
#
#----------------------------------------------------------

class Sentence(LexicalAbc):
    """Sentence base class. This provides common attributes and methods for the
    concrete sentence classes :class:`Atomic`, :class:`Predicated`, :class:`Quantified`,
    and :class:`Operated`.

    Behaviors
    ---------

    * Sentences support the built-in operators ``~``, ``|``, and ``&``, for
      negation, disjunction, and conjunction, respectively.

      >>> a, b = Sentence.gen(2)
      >>> ~a == a.negate()
      True
      >>> a | b == a.disjoin(b)
      True
      >>> a & b == a.conjoin(b)
      True
    
      
    Subclasses
    ----------
    * :class:`Atomic`
    * :class:`Predicated`
    * :class:`Quantified`
    * :class:`Operated`
    """

    predicates: frozenset[Predicate]
    "Set of predicates, recursive."

    constants: frozenset[Constant]
    "Set of constants, recursive."

    variables: frozenset[Variable]
    "Set of variables, recursive."

    atomics: frozenset[Atomic]
    "Set of atomic sentences, recursive."

    quantifiers: tuple[Quantifier, ...]
    "Sequence of quantifiers, recursive."

    operators: tuple[Operator, ...]
    "Sequence of operators, recursive."

    def negate(self):
        """Negate this sentence, returning the new sentence. This can also be
        invoked using the ``~`` operator.

        Returns:
            The new sentence.
        """
        return Operator.Negation(self)

    def asserted(self):
        """Apply the :obj:`Assertion` operator. This can also be invoked using
        the ``+`` operator.
        
        Returns:
            The new sentence.
        """
        return Operator.Assertion(self)

    def disjoin(self, rhs: Sentence, /):
        """Apply the :obj:`Disjunction` operator to the right-hand sentence.
        This can also be invoked using the ``|`` operator.

        Args:
            rhs: The right-hand disjunct.
        
        Returns:
            The new sentence.
        """
        return Operator.Disjunction(self, rhs)

    def conjoin(self, rhs: Sentence, /):
        """Apply the :obj:`Conjunction` operator to the right-hand sentence.
        This can also be invoked using the ``&`` operator.

        Args:
            rhs: The right-hand conjunct.
        
        Returns:
            The new sentence.
        """
        return Operator.Conjunction(self, rhs)

    def negative(self) -> Sentence:
        """Either negate this sentence, or, if this is already a negated
        sentence return its negatum, i.e., "un-negate" the sentence. This can
        also be invoked using the ``-`` operator.

        >>> a = Atomic.first()
        >>> a.negate() == a.negative()
        True
        >>> a.negate().negative() == a
        True
        
        Returns:
            The new sentence.
        """
        if type(self) is Operated and self.operator is Operator.Negation:
            return self.lhs
        return Operator.Negation(self)

    def substitute(self, pnew: Parameter, pold: Parameter, /) -> Self:
        """Return the recursive substitution of ``pnew`` for all occurrences
        of ``pold``.

        Args:
            pnew: The new parameter.
            pold: The old parameter.
        
        Returns:
            The new sentence.
        """
        return self

    @classmethod
    def first(cls):
        if cls is __class__:
            return Atomic.first()
        raise TypeError(f'Abstract type {cls}')

    def __pos__(self):
        return Operator.Assertion(self)

    def __invert__(self):
        return Operator.Negation(self)

    def __and__(self, other):
        return Operator.Conjunction(self, other)

    def __or__(self, other):
        return Operator.Disjunction(self, other)

    def __neg__(self):
        return self.negative()


#----------------------------------------------------------
#
#   Concrete Classes
#
#----------------------------------------------------------

class Predicate(CoordsItem):
    """
    A predicate is specified by an integer 3-tuple of ``(index, subscript, arity)``.
    The index can range from 0-3, and the subscript and arity can be any
    positive integer.

    To create a predicate, the spec can be passed either as separate arguments,
    or as a single :obj:`tuple`:

    >>> p = Predicate(0, 0, 1)
    >>> p == Predicate((0, 0, 1))
    True

    System Predicates
    -----------------

    There are two built-in system predicates, :obj:`Identity` and :obj:`Existence`.
    These are specified internal by the special indexes -1 and -2, respectively.
    They are defined in an enum class :obj:`Predicate.System`, and can be accessed
    in several ways:

    >>> p = Predicate('Identity')
    >>> p is Predicate.Identity
    True
    >>> p is Predicate.System.Identity
    True

    System predicates are considered equal to their name.

    >>> Predicate.Identity == 'Identity'
    True

    Behaviors
    ---------

    * Calling a predicate will construct a :class:`Predicated` sentence:

      >>> p = Predicate(0, 0, 2)
      >>> a, b = Constant.gen(2)
      >>> p((a, b)) == Predicated(p, (a, b))
      True

    """

    def __init__(self, *spec):
        """
        Raises:
            ValueError: if an invalid coordinate value is passed, e.g.
                a negative number, or too large an `index` coordinate.
            TypeError: for the wrong number of arguments, or wrong type.
        """
        if len(spec) == 1:
            spec = spec[0]
        if self.arity <= 0:
            raise ValueError('`arity` must be > 0')
        self.bicoords = BiCoords(self.index, self.subscript)
        if self.index < 0:
            if self.System:
                raise ValueError('`index` must be >= 0')
            if len(spec) != 4: # pragma: no cover
                raise TypeError(f'need 4 elements, got {len(spec)}')
            self.name = spec[3]
            self._value_ = self
        else:
            if len(spec) != 3:
                raise TypeError(f'need 3 elements, got {len(spec)}')
            self.name = self.spec

    def __new__(cls, *spec):
        if len(spec) == 1:
            try:
                len(spec := spec[0])
            except:
                check.inst(spec, tuple)
                raise # pragma: no cover
        if spec:
            self = CoordsItem.__new__(cls, *spec[0:3])
        else:
            self = object.__new__(cls)
        return self

    @property
    def is_system(self) -> bool:
        "Whether this is a system predicate."
        return self.index < 0

    __slots__ = (
        '__objclass__',
        '_name_',
        '_refs',
        '_value_',
        '_sort_order_',
        'arity',
        'bicoords',
        'name',
        'value')

    Coords = TriCoords
    spec: TriCoords

    bicoords: BiCoords
    "The symbol coordinates `(index, subscript)`."

    arity: int
    "The predicate's arity."

    name: tuple[int, ...] | str
    """The name, for system predicates. For non-system predicates, this is the
    same as the :attr:`spec`.
    
    >>> Predicate.Identity.name
    'Identity'
    >>> Predicate(0, 0, 1).name # For compatibility only
    (0, 0, 1)
    """

    @lazy.prop
    def refs(self) -> Set[tuple|str]:
        """References used to create indexes for predicate stores.

        ================  =============================  ==========================================
        Attribute         Example                        Description
        ================  =============================  ==========================================
        :attr:`bicoords`  ``(1, 0)``                     symbol coordinates (`index`, `subscript`)

        :attr:`spec`      ``(1, 0, 2)``                  coordinates including `arity`

        :attr:`ident`     ``('Predicate', (1, 0, 2))``   full lexical identifier

        :attr:`name`      `"Identity"`                   (system predicates only)
        ================  =============================  ==========================================
        """
        return qsetf({self.spec, self.ident, self.bicoords, self.name})

    def __call__(self, *spec):
        'Apply the predicate to parameters to make a predicated sentence.'
        return Predicated(self, *spec)

    def next(self):
        if self.is_system:
            raise StopIteration
        return super().next()

    def __eq__(self, other):
        res = super().__eq__(other)
        if res is NotImplemented and self.is_system and isinstance(other, str):
            return self.name == other
        return res

    __hash__ = Lexical.__hash__

    if TYPE_CHECKING:
        class _SPT(type):
            def __iter__(self) -> Iterator[Predicate]: ...
            def __call__(self, _) -> Predicate: ...
        class System(LangCommonEnum, metaclass=_SPT):
            'System predicates enum.'
            Existence: Predicate
            "The Existence predicate :sc:`!`"
            Identity: Predicate
            "The Identity predicate :sc:`=`"
            @classmethod
            def first(cls) -> Predicate: ...
        Existence: Predicate
        Identity: Predicate
    else:
        System = MapProxy(dict(Existence=(-2, 0, 1), Identity=(-1, 0, 2)))


class Constant(Parameter):
    """
    A constant is specified by an integer 2-tuple of ``(index, subscript)``.
    The index can range from 0-3, and the subscript can be any positive integer.

    To create a constant, the spec can be passed either as separate arguments,
    or as a single :obj:`tuple`:

    >>> c = Constant(2, 9)
    >>> c == Constant((2, 9))
    True

    Behaviors
    ---------

    * A constant can be right-shifted ``>>`` into a :class:`Quantified` sentence
      as a convenience for the sentence's :attr:`unquantify()` method:

      >>> c = Constant(0, 0)
      >>> s1 = Quantified.first()
      >>> s2 = c >> s1
      >>> s2.constants == {c}
      True
    """

    def __init__(self, *spec):
        pass

    def __rshift__(self, other):
        'Same as ``other.unquantify(self)``.'
        if type(other) is Quantified:
            return other.unquantify(self)
        return NotImplemented

class Variable(Parameter):
    """
    A variable, just like a :class:`Constant`, is specified by an integer 2-tuple
    of ``(index, subscript)``. The index can range from 0-3, and the subscript
    can be any positive integer.

    >>> Variable(2, 10) == Variable((2, 10))
    True
    """

    def __init__(self, *spec):
        pass

class Atomic(CoordsItem, Sentence):
    """
    An atomic sentence sentence, like a :class:`Parameter`, is specified by an
    integer 2-tuple of ``(index, subscript)``. The index can range from 0-4, and the
    subscript can be any positive integer.

    >>> Atomic(4, 0) == Atomic((4, 0))
    True
    """

    predicates = EMPTY_SET
    constants = EMPTY_SET
    variables = EMPTY_SET
    quantifiers = EMPTY_SEQ
    operators = EMPTY_SEQ

    __slots__ = 'atomics'

    def __init__(self, *spec):
        self.atomics = frozenset((self,))

class Predicated(Sentence, Sequence[Parameter]):
    'Predicated sentence implementation.'

    operators = EMPTY_SEQ
    quantifiers = EMPTY_SEQ
    atomics = EMPTY_SET

    def __init__(self, pred, *params):
        """
        Args:
            pred (Predicate): The :class:`Predicate`, or :attr:`spec`, such as
                ``(1, 0, 2)``.
            params (Parameter): An iterable of :class:`Parameter`
        
        Raises:
            TypeError: if the number of params does not equal the predicate's arity.
        """
        if len(params) == 1:
            params, = params
        pred = Predicate(pred)
        if isinstance(params, Parameter):
            params = params,
        else:
            params = tuple(map(Parameter, params))
        if len(params) != pred.arity:
            raise TypeError(self, len(params), pred.arity)
        self.predicate = pred
        self.params = params
        self.predicates = frozenset((pred,))
        self.spec = (
            pred.spec,
            tuple(p.ident for p in params))
        self.sort_tuple = (
            self.TYPE.rank,
            *pred.sort_tuple,
            *(n for p in params for n in p.sort_tuple))

    __slots__ = (
        '_constants',
        '_variables',
        'params',
        'predicate',
        'predicates',
        'sort_tuple',
        'spec')

    predicate: Predicate
    "The predicate."

    params: tuple[Parameter, ...]
    "The parameters."

    @lazy.prop
    def constants(self):
        return frozenset(p for p in self if type(p) is Constant)

    @lazy.prop
    def variables(self):
        return frozenset(p for p in self if type(p) is Variable)

    def substitute(self, pnew: Parameter, pold: Parameter, /):
        if pnew == pold:
            return self
        return self.predicate(pnew if p == pold else p for p in self)

    @classmethod
    def first(cls, pred=None, /):
        """
        Args:
            pred (Predicate): The :class:`Predicate` or :attr:`spec`.
                Default is the :func:`Predicate.first`.
        """
        if pred is None:
            pred = Predicate.first()
        else:
            pred = Predicate(pred)
        return pred(repeat(Constant.first(), pred.arity))

    def next(self):
        return self.predicate.next()(self.params)

    def __len__(self):
        return len(self.params)

    def __contains__(self, p):
        return p in self.params

    def __getitem__(self, index: SupportsIndex|slice):
        return self.params[index]

class Quantified(Sentence, Sequence):
    'Quantified sentence implementation.'

    def __init__(self, q, v, s, /):
        """
        Args:
            q (Quantifier): The :class:`Quantifier` or name, such as ``"Existential"``.
            v (Variable): The :class:`Variable` to bind, or coords, such as ``(0, 0)``.
            s (Sentence): The inner :class:`Sentence`.
        """
        self.items = (
            q := Quantifier(q), v := Variable(v), s := Sentence(s))
        self.quantifier, self.variable, self.sentence = self.items
        self.spec = (*q.spec, v.spec, s.ident)
        self.sort_tuple = (
            self.TYPE.rank,
            *q.sort_tuple,
            *v.sort_tuple,
            *s.sort_tuple)

    __slots__ = (
        '_quantifiers',
        'items',
        'quantifier',
        'sentence',
        'sort_tuple',
        'spec',
        'variable')

    quantifier: Quantifier
    "The quantifier."

    variable: Variable
    "The bound variable."

    sentence: Sentence
    "The inner sentence."

    items: tuple[Quantifier, Variable, Sentence]
    "The items sequence: :class:`Quantifer`, :class:`Variable`, :class:`Sentence`."

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

    @lazy.prop
    def quantifiers(self):
        return tuple(chain((self.quantifier,), self.sentence.quantifiers))

    def unquantify(self, c: Constant, /):
        """Instantiate the variable with a constant.
        
        Args:
            c (Constant): The constant to substitute for the bound variable.

        Returns:
            Sentence: The unquantified sentence.
        """
        return self.sentence.substitute(Constant(c), self.variable)

    def substitute(self, pnew, pold, /):
        if pnew == pold:
            return self
        return self.quantifier(self.variable, self.sentence.substitute(pnew, pold))

    @classmethod
    def first(cls, q = Quantifier.first(), /):
        """
        Args:
            q (Quantifier): The quantifier, default is the first quantifier.
        """
        return cls(q, v := Variable.first(), Predicate.first()(v))

    def next(self, **sentkw):
        """
        Args:
            **sentkw: `Kwargs` for :func:`Sentence.next()` to create the inner sentence.
        
        Raises:
            TypeError: if :func:`Sentence.next()` returns a sentence for which the
                variable is no longer bound.
        """
        s = self.sentence.next(**sentkw)
        v = self.variable
        if v not in s.variables:
            raise TypeError(f'{v} no longer bound')
        return Quantified(self.quantifier, v, s)

    def __len__(self):
        return len(self.items)

    def __contains__(self, item):
        return item in self.items

    def count(self, item,/):
        return int(item in self.items)

    def __getitem__(self, index: SupportsIndex|slice):
        return self.items[index]


class Operated(Sentence, Sequence[Sentence]):
    'Operated sentence implementation.'

    def __init__(self, oper: Operator, *operands):
        """
        Args:
            oper: The operator.
            operands: The operands.
        """
        if len(operands) == 1:
            operands, = operands
        self.operator = oper = Operator(oper)
        if isinstance(operands, Sentence):
            self.operands = operands = operands,
        else:
            self.operands = operands = tuple(map(Sentence, operands))
        try:
            self.lhs = operands[0]
            self.rhs = operands[-1]
        except IndexError:
            raise Emsg.ArityMismatch(oper, oper.arity, operands)
        if len(operands) != oper.arity:
            raise Emsg.ArityMismatch(oper, oper.arity, operands)
        self.spec = (*oper.spec, tuple(s.ident for s in operands))
        self.sort_tuple = (
            self.TYPE.rank,
            *oper.sort_tuple,
            *(n for s in operands for n in s.sort_tuple))

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
        'spec')

    operator: Operator
    "The operator."

    operands: tuple[Sentence, ...]
    "The operands."

    lhs: Sentence
    "The first (left-most) operand."

    rhs: Sentence
    "The last (right-most) operand."

    @lazy.prop
    def predicates(self):
        return frozenset(chain.from_iterable(s.predicates for s in self))

    @lazy.prop
    def constants(self):
        return frozenset(chain.from_iterable(s.constants for s in self))

    @lazy.prop
    def variables(self):
        return frozenset(chain.from_iterable(s.variables for s in self))

    @lazy.prop
    def quantifiers(self):
        return *chain.from_iterable(s.quantifiers for s in self),

    @lazy.prop
    def operators(self):
        return tuple(
            (self.operator, *chain.from_iterable(
                s.operators for s in self)))

    @lazy.prop
    def atomics(self):
        return frozenset(chain.from_iterable(s.atomics for s in self))

    def substitute(self, pnew, pold, /):
        if pnew == pold:
            return self
        return self.operator(s.substitute(pnew, pold) for s in self)

    @classmethod
    def first(cls, oper=Operator.first(), /):
        oper = Operator(oper)
        return oper(Atomic.gen(oper.arity))

    def next(self, **kw):
        return self.operator(*self[0:-1], self[-1].next(**kw))

    def __len__(self):
        return self.operator.arity

    def __contains__(self, s: Any):
        return s in self.operands

    def __getitem__(self, index: SupportsIndex|slice):
        return self.operands[index]

#----------------------------------------------------------
#
#   LexType
#
#----------------------------------------------------------

class LexType(LangCommonEnum):
    """
    LexType metadata enum class for concrete types.

    .. csv-table::
        :generator: member-table
        :generator-args: name rank cls role maxi pcls
    
    """
    __slots__ = (
        'rank',
        'cls',
        'pcls',
        'role',
        'maxi',
        'hash')

    rank: int
    "A number to order items of different types."

    cls: type[Lexical]
    "The class reference."

    role: type[Lexical]
    "The category class, such as :class:`Sentence` for :class:`Atomic`."

    maxi: int | None
    "For coordinate classes, the maximum index, else ``None``."

    pcls: type[Lexical] | None
    """The "partner" class, if any. For example, :class:`Operated` and
    :class:`Operator` are partners.
    """

    hash: int
    "The member hash."

    classes: ClassVar[qsetf[type[Lexical]]]
    """Ordered set of all the classes.
    
    :meta hide-value:
    """

    #******  Members

    Predicate  = Predicate
    Constant   = Constant
    Variable   = Variable
    Quantifier = Quantifier
    Operator   = Operator
    Atomic     = Atomic
    Predicated = Predicated
    Quantified = Quantified
    Operated   = Operated

    #******  Call Behavior

    def __call__(self, *args, **kw) -> Lexical:
        return self.cls(*args, **kw)

    #******  Equality, Ordering, & Comparison

    @abcs.abcf.temp
    @membr.defer
    def wrapper(member: membr):
        @wraps(oper := getattr(opr, member.name))
        def wrapped(self: LexType, other):
            if type(other) is not LexType:
                return NotImplemented
            return oper(self.rank, other.rank)
        return wrapped

    __lt__ = __le__ = __gt__ = __ge__ = wrapper()

    def __eq__(self, other):
        return (
            self is other or
            self.cls is other or
            self is LexType.get(other, None))

    def __repr__(self):
        name = type(self).__name__
        try:
            return f'<{name}.{self.cls.__name__}>'
        except AttributeError: # pragma: no cover
            return f'<{name} ?ERR?>'

    def __hash__(self):
        return self.hash

    @closure
    def __init__():
        partners = dict((
            (Predicate, Predicated),
            (Quantifier, Quantified),
            (Operator, Operated)))
        partners.update(map(reversed, tuple(partners.items())))
        def init(self: LexType, cls: type[Lexical], /):
            self.cls = cls
            self.cls.TYPE = self
            self.rank = _Ranks[cls.__name__]
            self.hash = hash(type(self)) + self.rank
            self.pcls = partners.get(cls)
            self.maxi = 3 * issubclass(cls, CoordsItem) + (cls is Atomic) or None
            for role in filter(partial(issubclass, cls), (Parameter, Sentence, cls)):
                self.role = role
                break
        return init

    @classmethod
    def _member_keys(cls, member: LexType):
        """``EbcMeta`` hook. Add the class object to the member lookup keys."""
        return super()._member_keys(member) | {member.cls}

    @classmethod
    def _after_init(cls):
        """``EbcMeta`` hook. Build :attr:`classes` list, and System Predicates."""
        super()._after_init()

        cls.classes = qsetf(m.cls for m in cls)

        members = {
            name: (*value, name)
            for name, value in dict(Predicate.System).items()}

        Predicate.System = None

        class SystemPredicate(LangCommonEnum):

            def __new__(cls, *spec):
                return Predicate.__new__(Predicate, *spec)

            @classmethod
            def first(cls):
                return cls._seq[0]

            @classmethod
            def _member_keys(cls, pred: Predicate):
                return super()._member_keys(pred) | pred.refs | {pred}

            @abcs.abcf.before
            def prepare(ns: dict, bases):               
                ns.update(members)
                member_names = check.inst(ns._member_names, (dict, list))
                if isinstance(member_names, dict):
                    # In Python 3.11 _member_names is a dict
                    for key in members:
                        member_names[key] = None
                    return
                # In Python 3.10 _member_names is a list
                member_names += members.keys() # pragma: no cover

        Predicate.System = SystemPredicate
        Predicate.System.__name__ = 'System'
        Predicate.System.__qualname__ = 'Predicate.System'
        for pred in Predicate.System:
            setattr(Predicate, pred.name, pred)


#----------------------------------------------------------
#
#   Meta __call__ routine.
#
#----------------------------------------------------------

@closure
def metacall():

    import os
    from collections import deque

    class DequeCache:

        __slots__ = ('queue', 'idx', 'rev')

        queue: deque[Lexical]
        idx: dict[Any, Lexical]
        "Mapping of called args/specs to lexical, including the lexical itself"
        rev: dict[Lexical, set]
        "Mapping of leixcal to index keys, to enable removing"


        def __init__(self, maxlen=int(os.getenv('ITEM_CACHE_SIZE', 1000) or 0)):
            self.queue = deque(maxlen=maxlen)
            self.idx = {}
            self.rev = {}

        def __getitem__(self, key):
            return self.idx[key]

        def __setitem__(self, key, value):
            rev = self.rev
            idx = self.idx
            queue = self.queue
            if value in rev:
                value = idx[value]
            else:
                if len(rev) >= queue.maxlen:
                    old = queue.popleft()
                    for k in rev.pop(old):
                        del(idx[k])
                idx[value] = value
                rev[value] = {value}
                queue.append(value)
            idx[key] = value
            rev[value].add(key)

    cache = DequeCache()

    supercall = LangCommonMeta.__call__

    def call(cls, *spec):

        if len(spec) == 1:

            # Special cases.
            arg, = spec

            if isinstance(arg, cls):
                # Passthrough
                return arg

            if cls is Predicate and isinstance(arg, str):
                # System Predicate string
                return Predicate.System(arg)

        # Invoked class name.
        clsname = cls.__name__
        
        try:
            # Check cache
            return cache[clsname, spec]
        except KeyError:
            pass

        try:
            # Construct
            inst: LexicalAbc = supercall(cls, *spec)
        except TypeError:

            # Try to create from ident.

            if (
                # If a concrete LexType raised the error, or the class is
                # not abstract, propagate.
                cls in LexType or not abcs.isabstract(cls) or

                # Creating from spec supports only length 1.
                len(spec) != 1
            ):
                raise

            # Try arg as ident tuple (clsname, spec)
            clsname, spec = arg
            Class = LexType(clsname).cls

            # Check for appropriate class relationship.
            if not (cls is LexicalAbc or issubclass(Class, cls)):
                raise TypeError(Class, cls) from None

            try:
                # Check cache
                return cache[clsname, spec]
            except KeyError:
                pass

            # Construct
            inst: Lexical = Class(*spec)

        # Save to cache.
        cache[clsname, spec] = cache[inst.ident] = inst

        return inst

    call._cache = cache

    return call

LexicalAbcMeta.__call__ = metacall
