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
from itertools import chain, repeat
from types import FunctionType
from types import MappingProxyType as MapProxy
from typing import Any, ClassVar, Mapping, Sequence

from .. import _ENV, __docformat__, errors, tools
from ..errors import Emsg, check
from ..tools import EMPTY_SEQ, EMPTY_SET, abcs, lazy, membr, qsetf, wraps
from . import (BiCoords, LangCommonEnum, LangCommonMeta, LexicalAbcMeta,
               SysPredEnumMeta, TriCoords, nosetattr)

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
    """Base Lexical interface.
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

    ident: tuple
    """Equality identifier able to compare across types. Equivalent to
    ``(classname, spec)``.
    """

    sort_tuple: tuple
    """Sorting identifier, to order tokens of the same type. Numbers only
    (no strings). This is also used in hashing, so equal objects should
    have equal sort_tuples.

    **NB**: The first value must be the lexical rank of the type as specified
    in the :class:`LexType` enum class.
    """

    hash: int
    "The integer hash."

    #******  Item Generation

    @classmethod
    def first(cls):
        "Get the canonically first item of the type."
        if cls is __class__:
            return Predicate.first()
        raise TypeError(f'Abstract type {cls}')

    @tools.abstract
    def next(self, **kw):
        "Get the canonically next item of the type."
        raise NotImplementedError

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

    #******  Equality, Ordering, & Comparison

    @staticmethod
    def identitem(item: Lexical, /) -> tuple:# -> IdentType:
        'Build an :attr:`ident` tuple for the item from the class name and :attr:`spec`.'
        return type(item).__name__, item.spec

    @staticmethod
    def hashitem(item: Lexical, /) -> int:
        'Compute a hash for the item based on class name and :attr:`sort_tuple`.'
        return hash((type(item).__name__, item.sort_tuple))

    @staticmethod
    @tools.closure
    def orderitems():

        def cmpgen(a: Lexical, b: Lexical, /):
            yield a.TYPE.rank - b.TYPE.rank
            it = zip(ast := a.sort_tuple, bst := b.sort_tuple)
            yield from (ai - bi for ai, bi in it)
            yield len(ast) - len(bst)

        def orderitems(lhs, rhs, /) -> int:
            """Pairwise ordering comparison based on type rank and :attr:`sort_tuple`.

            Args:
                lhs (Lexical): The left-hand item.
                rhs (Lexical): The right-hand item.

            Returns:
                int: The relative order of ``lhs`` and ``rhs``. The return value
                will be either:

                   * Less than ``0`` if ``lhs`` precedes ``rhs`` in order.
                   * Greater than ``0`` if ``rhs`` precedes ``lhs`` in order.
                   * Equal to ``0`` if `lhs` is equal to ``rhs`` in order.

            Raises:
                TypeError: if an argument is not an instance of :class:`Lexical` with
                    a valid :attr:`TYPE` attribute.
            """
            if lhs is rhs:
                return 0
            try:
                for cmp in cmpgen(lhs, rhs):
                    if cmp:
                        return cmp
                return 0
            except AttributeError:
                raise TypeError

        return orderitems

    @abcs.abcf.temp
    @membr.defer
    def ordr(member: membr):
        cmpoper = getattr(opr, member.name)
        def f(self, other, /):
            try:
                return cmpoper(Lexical.orderitems(self, other), 0)
            except TypeError:
                if isinstance(other, Lexical):
                    raise
                return NotImplemented
        return wraps(cmpoper)(f)

    __lt__ = __le__ = __gt__ = __ge__ = __eq__ = ordr()

    def __hash__(self):
        return self.hash

    #******   Behaviors

    __delattr__ = Emsg.ReadOnly.razr

    __setattr__ = nosetattr(object, cls = LexicalAbcMeta)

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

    def __init_subclass__(subcls: type[Lexical], /, *,
        lexcopy = False,
        skipnames = {tools.dund('init_subclass')},
        _cpnames = frozenset(map(tools.dund, ('copy', 'deepcopy'))),
        _ftypes = (classmethod, staticmethod, FunctionType),
        **kw):
        """Subclass init hook.

        If `lexcopy` is ``True``, copy the class members to the next class,
        since our protection is limited without metaclass flexibility. Only
        applies to direct sub classes.
        """
        super().__init_subclass__(**kw)
        if not lexcopy or __class__ not in subcls.__bases__:
            return
        src = dict(__class__.__dict__)
        for key in chain(subcls.__dict__, skipnames):
            src.pop(key, None)
        for name in _cpnames:
            if name not in src:
                for name in _cpnames:
                    src.pop(name, None)
                break
        for name, value in src.items():
            if isinstance(value, _ftypes):
                setattr(subcls, name, value)


class LexicalAbc(Lexical, metaclass = LexicalAbcMeta, lexcopy = True):
    'Base class for non-Enum lexical classes.'

    __slots__ = ('_ident', '_hash',)

    @lazy.prop
    def ident(self):
        return self.identitem(self)

    @lazy.prop
    def hash(self):
        return self.hashitem(self)

    @classmethod
    def first(cls):
        if cls is __class__:
            return Lexical.first()
        raise TypeError(f'Abstract type {cls}')

    @tools.abstract
    def __init__(self): ...

    __delattr__ = Emsg.ReadOnly.razr

    def __setattr__(self, name, value, /):
        if (v := getattr(self, name, NOARG)) is not NOARG:
            if getattr(LexicalAbc, '_readonly', False):
                if v == value:#isinstance(v, tuple) and v == value:
                    errors.warn(f'duplicate value for attribute {name}',
                        errors.RepeatValueWarning)
                    # return
                else:
                    raise Emsg.ReadOnly(self, name)
        super().__setattr__(name, value)

    def __getnewargs__(self):
        return self.spec


class LexicalEnum(Lexical, LangCommonEnum, lexcopy = True):
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
    """Name, label, or other strings unique to a member.
    """

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

    @classmethod
    def first(cls):
        if cls is __class__:
            return Quantifier._seq[0]
        return cls._seq[0]

    def next(self, /, *, loop: bool = False):
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

    def __init__(self, order: int, label: str, /):
        self.spec = self.name,
        self.order = order
        self.sort_tuple = _Ranks[type(self).__name__], order
        self.label = label
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
        for i, member in enumerate(subcls._seq):
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

    @classmethod
    def first(cls):
        if cls is __class__:
            return Predicate.first()
        return cls(cls.Coords.first)

    def next(self):
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
            raise
        try:
            if spec.index > self.TYPE.maxi:
                raise ValueError(f'{spec.index} > {self.TYPE.maxi}')
        except AttributeError:
            raise TypeError(f'Abstract: {type(self)}') from None
        if spec.subscript < 0:
            raise ValueError(f'subscript {spec.subscript} < 0')
        sa(self, 'sort_tuple', (self.TYPE.rank, *spec.sorting()))
        return self


class Parameter(CoordsItem):
    """Parameter base class for :class:`Constant` & :class:`Variable`."""

    __slots__ = EMPTY_SET

    is_constant: bool
    "Whether the parameter is a :class:`Constant`."

    is_variable: bool
    "Whether the parameter is a :class:`Variable`."

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
    'Quantifier lexical enum class.'

    Existential = (0, 'Existential')
    "The :s:`X` Existential quantifier"

    Universal = (1, 'Universal')
    "The :s:`L` Universal quantifier"

    def __call__(self, *spec) -> Quantified:
        'Quantify a variable over a sentence.'
        return Quantified(self, *spec)

class Operator(LexicalEnum):
    """Operator lexical enum class. Member definitions correspond to
    (`order`, `label`, `arity`, `libname`).

    """
    
    # .. member-table:: pytableaux.lang.lex.Operator
    #     :columns: order, label, arity, libname

    __slots__ = ('arity', 'libname',)

    arity: int
    "The operator arity."

    libname: str|None
    """If the operator implements a Python arithmetic operator, this
    will be the special `"dunder"` name corresponding to Python's
    built-in :obj:`operator` module. For example, for :attr:`Conjunction`,
    which implements ``&``, the value is ``'__and__'``.
    """

    Assertion             = (10,  'Assertion',              1, None)
    Negation              = (20,  'Negation',               1, '__invert__')
    Conjunction           = (30,  'Conjunction',            2, '__and__')
    Disjunction           = (40,  'Disjunction',            2, '__or__')
    MaterialConditional   = (50,  'Material Conditional',   2, None)
    MaterialBiconditional = (60,  'Material Biconditional', 2, None)
    Conditional           = (70,  'Conditional',            2, None)
    Biconditional         = (80,  'Biconditional',          2, None)
    Possibility           = (90,  'Possibility',            1, None)
    Necessity             = (100, 'Necessity',              1, None)

    lib_opmap: ClassVar[Mapping[str, Operator]]

    def __call__(self, *args):
        'Apply the operator to make a new sentence.'
        if len(args) > 1:
            return Operated(self, args)
        return Operated(self, *args)

    def __init__(self, order, label, arity, libname, /):
        super().__init__(order, label)
        self.arity = arity
        self.libname = libname
        if libname is not None:
            self.strings |= {libname}

    @classmethod
    def _after_init(cls):
        "Class init hook. Build the :attr:`lib_opmap`."
        super()._after_init()
        cls.lib_opmap = MapProxy({
            o.libname: o for o in cls if o.libname is not None})

#----------------------------------------------------------
#
#   Abstract Sentence class.
#
#----------------------------------------------------------

class Sentence(LexicalAbc):
    'Sentence base class.'

    __slots__ = EMPTY_SET

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
        'Negate this sentence, returning the new sentence.'
        return Operated(Operator.Negation, (self,))

    def asserted(self):
        """Apply the :obj:`Assertion` operator.
        
        Returns:
            The new sentence.
        """
        return Operated(Operator.Assertion, (self,))

    def disjoin(self, rhs, /):
        """Apply the :obj:`Disjunction` operator to the right-hand sentence.

        Args:
            rhs (Sentence): The right-hand disjunct.
        
        Returns:
            The new sentence.
        """
        return Operated(Operator.Disjunction, (self, rhs))

    def conjoin(self, rhs, /):
        """Apply the :obj:`Conjunction` operator to the right-hand sentence.

        Args:
            rhs (Sentence): The right-hand conjunct.
        
        Returns:
            The new sentence.
        """
        return Operated(Operator.Conjunction, (self, rhs))

    def negative(self):
        """Either negate this sentence, or, if this is already a negated
        sentence return its negatum, i.e., "un-negate" the sentence.
        """
        return Operated(Operator.Negation, (self,))

    def substitute(self, pnew, pold, /):
        """Return the recursive substitution of ``pnew`` for all occurrences
        of ``pold``.
        """
        return self

    @classmethod
    def first(cls):
        if cls is __class__:
            return Atomic.first()
        raise TypeError(f'Abstract type {cls}')

    @abcs.abcf.temp
    @membr.defer
    def libopers_1(member: membr):
        oper = Operator.lib_opmap[member.name]
        def f(self: Sentence) -> Operated:
            return Operated(oper, self)
        return wraps(oper)(f)

    @abcs.abcf.temp
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

#----------------------------------------------------------
#
#   Concrete Classes
#
#----------------------------------------------------------

class Predicate(CoordsItem):
    """Predicate implementation."""

    def __init__(self, *spec):
        """Create a predicate, or get a system predicate.

        Args:
            index (int): The `index` coordinate.
            subscript (int): The `subscript` coordinate.
            arity (int): The predicate's arity.

        The parameters can be passed either expanded, or as a single
        :obj:`tuple`, for example::

            Predicate(0, 0, 1)
            Predicate((0, 0, 1))
        
        To get a system predicate instance, use the name, for example::

            Predicate('Identity')
        
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
            if len(self.System):
                raise ValueError('`index` must be >= 0')
            if len(spec) != 4:
                raise TypeError(f'need 4 elements, got {len(spec)}')
            self.is_system = True
            self.name = spec[3]
        else:
            if len(spec) != 3:
                raise TypeError(f'need 3 elements, got {len(spec)}')
            self.is_system = False
            self.name = self.spec
            self.__objclass__ = __class__
        self._name_ = self.name
        self._value_ = self

    def __new__(cls, *spec):
        if len(spec) == 1:
            try:
                len(spec := spec[0])
            except:
                check.inst(spec, tuple)
                raise
        if spec:
            self = CoordsItem.__new__(cls, *spec[0:3])
        else:
            self = object.__new__(cls)
        return self

    __slots__ = (
        '__objclass__',
        '_name_',
        '_refs',
        '_value_',
        '_sort_order_',
        'arity',
        'bicoords',
        'is_system',
        'name',
        'value')

    Coords = TriCoords

    bicoords: BiCoords
    "The symbol coordinates `(index, subscript)`."

    arity: int
    "The predicate's arity."

    is_system: bool
    "Whether this is a system predicate."

    name: tuple[int, ...] | str
    "The name, for system predicates. Same as :attr:`spec` for user predicates."

    @lazy.prop
    def refs(self):
        """References used to create indexes for predicate stores.

        ================  =============================  ==========================================
        Attribute         Example                        Description
        ================  =============================  ==========================================
        :attr:`bicoords`  ``(1, 0)``                     symbol coordinates (`index`, `subscript`)

        :attr:`spec`      ``(1, 0, 2)``                  including `arity`

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
            arity = self.arity
            for pred in self.System:
                if pred is not self and pred.arity == arity and pred > self:
                    return pred
        return super().next()

    class System(LangCommonEnum):
        'System predicates enum.'

        Existence = (-2, 0, 1, 'Existence')
        "The Existence predicate :sc:`!`"
        Identity  = (-1, 0, 2, 'Identity')
        "The Identity predicate :sc:`=`"

class Constant(Parameter):
    """Constant parameter implementation."""

    def __init__(self, *spec):
        """
        Args:
            index (int): The index coordinate.
            subscript (int): The subscript coordinate.
        """

    def __new__(cls, *spec):
        self = CoordsItem.__new__(cls, *spec)
        sa = object.__setattr__
        sa(self, 'is_constant', True)
        sa(self, 'is_variable', False)
        return self

    __slots__ = (
        'is_constant',
        'is_variable')

    def __rshift__(self, other):
        'Same as ``other.unquantify(self)``.'
        if not isinstance(other, Quantified):
            return NotImplemented
        return other.unquantify(self)


class Variable(Parameter):
    """Variable parameter implementation."""

    def __init__(self, *spec):
        """
        Args:
            index (int): The index coordinate.
            subscript (int): The subscript coordinate.
        """

    def __new__(cls, *spec):
        self = CoordsItem.__new__(cls, *spec)
        sa = object.__setattr__
        sa(self, 'is_constant', False)
        sa(self, 'is_variable', True)
        return self

    __slots__ = Constant.__slots__


class Atomic(CoordsItem, Sentence):
    'Atomic sentence implementation.'

    def __init__(self, *spec):
        """
        Args:
            index (int): The index coordinate.
            subscript (int): The subscript coordinate.
        """
        self.predicates = self.constants = self.variables = EMPTY_SET
        self.quantifiers = self.operators = EMPTY_SEQ
        self.atomics = frozenset((self,))

    def __new__(cls, *spec):
        return CoordsItem.__new__(cls, *spec)

    __slots__ = (
        'atomics',
        'constants',
        'operators',
        'predicates',
        'quantifiers',
        'variables')

class Predicated(Sentence, Sequence[Parameter]):
    'Predicated sentence implementation.'

    def __init__(self, pred, params, /):
        """
        Args:
            pred (Predicate): The :class:`Predicate`, or :attr:`spec`, such as
                ``(1, 0, 2)``.
            params (Parameter): An iterable of :class:`Parameter`, or
                :obj:`ParameterSpec`, such as ``(1, 0)``. For a unary predicate,
                a single parameter/spec is accepted.
        
        Raises:
            TypeError: if the number of params does not equal the predicate's arity.
        """
        self.predicate = Predicate(pred)
        pred = self.predicate
        if isinstance(params, Parameter):
            self.params = params,
        else:
            self.params = tuple(map(Parameter, params))
        params = self.params
        if len(params) != pred.arity:
            raise TypeError(self.predicate, len(params), pred.arity)
        self.predicates = frozenset((pred,))
        self.paramset = frozenset(params)
        self.operators = EMPTY_SEQ
        self.quantifiers = EMPTY_SEQ
        self.atomics = EMPTY_SET
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
        'atomics',
        'operators',
        'params',
        'paramset',
        'predicate',
        'predicates',
        'quantifiers',
        'sort_tuple',
        'spec')

    predicate: Predicate
    "The predicate."

    params: tuple
    "The parameters."

    paramset: frozenset[Parameter]
    "A set view of parameters."

    @lazy.prop
    def constants(self):
        return frozenset(p for p in self.paramset if p.is_constant)

    @lazy.prop
    def variables(self):
        return frozenset(p for p in self.paramset if p.is_variable)

    def substitute(self, pnew, pold, /):
        if pnew == pold or pold not in self.paramset:
            return self
        return Predicated(self.predicate, tuple(
            (pnew if p == pold else p for p in self.params)))

    @classmethod
    def first(cls, pred = None, /):
        """
        Args:
            pred (Predicate): The :class:`Predicate` or :attr:`spec`.
                Default is the :func:`Predicate.first`.
        """
        if pred is None:
            pred = Predicate.first()
        return cls(pred, tuple(repeat(Constant.first(), pred.arity)))

    def next(self):
        return Predicated(self.predicate.next(), self.params)

    #******  Sequence Behavior

    def __len__(self):
        return len(self.params)

    def __contains__(self, p):
        return p in self.paramset

    def __getitem__(self, index):
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

    items: tuple
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

    def unquantify(self, c, /):
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
        return Quantified(
            self.quantifier, self.variable, self.sentence.substitute(pnew, pold))

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

    def __contains__(self, item: Any, /):
        return item in self.items

    def count(self, item,/):
        return int(item in self.items)

    def __getitem__(self, index, /):
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
        self.lhs = operands[0]
        self.rhs = operands[-1]
        if len(operands) != oper.arity:
            raise Emsg.WrongLength(operands, oper.arity)
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

    spec: tuple   #OperatedSpec

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
        return Operated(self.operator, tuple(
            s.substitute(pnew, pold) for s in self))

    def negative(self) -> Sentence:
        if self.operator is Operator.Negation:
            return self.lhs
        return Operated(Operator.Negation, self)

    @classmethod
    def first(cls, oper = Operator.first(), /):
        return cls(oper, Atomic.gen(Operator(oper).arity))

    def next(self, **kw):
        return Operated(self.operator,
            (*self.operands[0:-1], self.operands[-1].next(**kw)))

    def __len__(self):
        return len(self.operands)

    def __contains__(self, s: Any, /):
        return s in self.operands

    def __getitem__(self, index, /):
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
        :generator-args: name rank cls role maxi
    
    """
    __slots__ = (
        'rank',
        'cls',
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

    Predicate  = (_Ranks['Predicate'],  Predicate,  Predicate,     3, Predicated)
    Constant   = (_Ranks['Constant'],   Constant,   Parameter,     3, None)
    Variable   = (_Ranks['Variable'],   Variable,   Parameter,     3, None)
    Quantifier = (_Ranks['Quantifier'], Quantifier, Quantifier, None, Quantified)
    Operator   = (_Ranks['Operator'],   Operator,   Operator,   None, Operated)
    Atomic     = (_Ranks['Atomic'],     Atomic,     Sentence,      4, None)
    Predicated = (_Ranks['Predicated'], Predicated, Sentence,   None, Predicate[1])
    Quantified = (_Ranks['Quantified'], Quantified, Sentence,   None, Quantifier[1])
    Operated   = (_Ranks['Operated'],   Operated,   Sentence,   None, Operator[1])

    #******  Call Behavior

    def __call__(self, *args, **kw) -> Lexical:
        return self.cls(*args, **kw)

    #******  Equality, Ordering, & Comparison

    @abcs.abcf.temp
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
            self is LexType.get(other, None))

    def __repr__(self, /):
        name = type(self).__name__
        try:
            return f'<{name}.{self.cls.__name__}>'
        except AttributeError:
            return f'<{name} ?ERR?>'

    def __hash__(self):
        return self.hash

    def __init__(self, rank, cls: type[Lexical], role, maxi, pcls, /):
        self.rank = rank
        self.cls = cls
        self.role = role
        self.maxi = maxi
        self.pcls = pcls
        self.hash = hash(type(self)) + self.rank
        self.cls.TYPE = self

    @classmethod
    def _member_keys(cls, member: LexType):
        """``EbcMeta`` hook. Add the class object to the member lookup keys."""
        return super()._member_keys(member)# | {member.cls}

    @classmethod
    def _after_init(cls):
        """``EbcMeta`` hook. Build :attr:`classes` list, and System Predicates."""
        super()._after_init()
        cls.classes = qsetf(m.cls for m in cls)
        class _(LangCommonEnum, metaclass = SysPredEnumMeta):
            def __new__(cls, *spec):
                return Predicate.__new__(Predicate, *spec)
            @classmethod
            def _member_keys(cls, pred: Predicate):
                return super()._member_keys(pred) | pred.refs | {pred}
            @abcs.abcf.before
            def expand(ns:dict, bases):
                members = {name: m.value for name, m in Predicate.System._member_map_.items()}
                ns.update(members)
                if isinstance(ns._member_names, list):
                    # In Python 3.10 _member_names is a list
                    ns._member_names += members.keys()
                elif isinstance(ns._member_names, dict):
                    # In Python 3.11 _member_names is a dict
                    for key in members:
                        ns._member_names[key] = None
                else:
                    raise TypeError(f"Unhandled _member_names type: {type(ns._member_names)}")
                Predicate.System = EMPTY_SET
            @classmethod
            def _after_init(cls):
                cls.__name__ = 'Predicate'
                cls.__qualname__ = 'Predicate.System'
                for pred in cls:
                    setattr(Predicate, pred.name, pred)
                Predicate.System = cls

#----------------------------------------------------------
#
#   Meta __call__ routine.
#
#----------------------------------------------------------

@tools.closure
def metacall():

    from collections import deque
    class DequeCache:

        __slots__ = ('__getitem__', '__len__', 'queue', 'idx', 'rev')

        @property
        def maxlen(self) -> int:
            return self.queue.maxlen

        def __init__(self, maxlen = 100):

            self.idx = {}
            self.rev: dict[object, set] = {}
            self.queue = deque(maxlen = maxlen)

            self.__getitem__ = self.idx.__getitem__
            self.__len__ = self.rev.__len__

        def __setitem__(self, key, item, /):
            if item in self.rev:
                item = self.idx[item]
            else:
                if len(self) >= self.queue.maxlen:
                    old = self.queue.popleft()
                    for k in self.rev.pop(old):
                        del(self.idx[k])
                self.idx[item] = item
                self.rev[item] = {item}
                self.queue.append(item)
            self.idx[key] = item
            self.rev[item].add(key)

    cache = DequeCache(maxlen = _ENV.ITEM_CACHE_SIZE)
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
                # abstract, propagate.
                cls in LexType or abcs.isabstract(cls) or

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
