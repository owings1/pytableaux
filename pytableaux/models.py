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
"""
pytableaux.models
^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from abc import abstractmethod
from collections.abc import Set
from dataclasses import dataclass
from itertools import product, repeat
from types import MappingProxyType as MapProxy
from typing import Any, Generic, Iterable, Literal, Mapping, Self, TypeVar

from .errors import check, Emsg
from .lang import (Argument, Atomic, Constant, Operated, Operator, Predicated,
                   Quantified, Sentence)
from .logics import LogicType
from .proof import Branch
from .tools import EMPTY_MAP, abcs, maxceil, minfloor

__all__ = (
    'BaseModel',
    'Mval',
    'ValueFDE',
    'ValueK3',
    'ValueLP',
    'ValueCPL')

class Mval(abcs.Ebc):

    __slots__ = 'name', 'num'

    def __init__(self, num: float, /):
        self.num: float = num

    def __eq__(self, other):
        if self is other:
            return True
        if isinstance(other, (float, int)):
            return other == self.num
        if isinstance(other, str):
            return other == self.name
        return NotImplemented

    def __hash__(self):
        # Since equal names can have unequal nums, we hash the name, so
        # equal values have equal hashes.
        return hash(self.name)

    def __le__(self, other):
        return self.num <= other
    def __lt__(self, other):
        return self.num < other
    def __ge__(self, other):
        return self.num >= other
    def __gt__(self, other):
        return self.num > other
    def __sub__(self, other):
        return type(self)(self.num - other)
    def __rsub__(self, other):
        return other - self.num
    def __add__(self, other):
        return type(self)(self.num + other)
    def __radd__(self, other):
        return other + self.num
    def __truediv__(self, other):
        return type(self)(self.num / other)
    def __rtruediv__(self, other):
        return other / self.num
    def __floordiv__(self, other):
        return type(self)(self.num // other)
    def __rfloordiv__(self, other):
        return other // self.num

    def __float__(self):
        return self.num

    def __str__(self):
        return self.name

    @classmethod
    def _member_keys(cls, member: Mval):
        return super()._member_keys(member) | {member.num}


class ValueFDE(Mval):
    "Model values for gappy + glutty 4-valued logics, like FDE."

    F = 0.0
    N = 0.25
    B = 0.75
    T = 1.0

class ValueK3(Mval):
    "Model values for gappy 3-valued logics, like K3 and others."

    F = 0.0
    N = 0.5
    T = 1.0

class ValueLP(Mval):
    "Model values for glutty 3-valued logics, like LP and others."

    F = 0.0
    B = 0.5
    T = 1.0

class ValueCPL(Mval):
    'Model values for 2-valued "classical" logics.'

    F = 0.0
    T = 1.0

MvalT = TypeVar('MvalT', bound = Mval)
MvalT_co = TypeVar('MvalT_co', bound = Mval, covariant = True)

class BaseModel(Generic[MvalT_co], abcs.Abc):
    Meta: type[LogicType.Meta]

    values: type[MvalT_co]
    "The values of the model"

    truth_function: BaseModel.TruthFunction[MvalT_co]

    __slots__ = ('_finished',)

    @property
    def id(self) -> int:
        return id(self)

    @property
    def finished(self) -> bool:
        try:
            return self._finished
        except AttributeError:
            self._finished = False
            return False

    def is_sentence_opaque(self, s: Sentence, /) -> bool:
        if not self.Meta.quantified and type(s) is Quantified:
            return True
        if not self.Meta.modal and type(s) is Operated and s.operator in self.Meta.modal_operators:
            return True
        return False

    def is_sentence_literal(self, s: Sentence, /) -> bool:
        return type(s) in (Atomic, Predicated) or (
            type(s) is Operated and
            s.operator is Operator.Negation and (
                type(s.lhs) in (Atomic, Predicated) or
                self.is_sentence_opaque(s.lhs)))

    def value_of(self, s: Sentence, /, **kw) -> MvalT_co:
        self._check_finished()
        if self.is_sentence_opaque(s):
            return self.value_of_opaque(s, **kw)
        try:
            name = f'value_of_{type(s).__name__.lower()}'
            func = getattr(self, name)
        except AttributeError:
            check.inst(s, Sentence)
            raise NotImplementedError from ValueError(s)
        return func(s, **kw)

    @abstractmethod
    def value_of_opaque(self, s: Sentence, /) -> MvalT_co:
        self._check_finished()

    @abstractmethod
    def value_of_atomic(self, s: Atomic, /) -> MvalT_co:
        self._check_finished()

    @abstractmethod
    def value_of_predicated(self, s: Predicated, /) -> MvalT_co:
        self._check_finished()

    @abstractmethod
    def value_of_quantified(self, s: Quantified, /) -> MvalT_co:
        self._check_finished()

    def value_of_operated(self, s: Operated, /, **kw) -> MvalT_co:
        self._check_finished()
        if s.operator in self.Meta.truth_functional_operators:
            return self.truth_function(s.operator,
                *map(lambda s: self.value_of(s, **kw), s))
        check.inst(s, Operated)
        raise NotImplementedError from ValueError(s.operator)

    @abstractmethod
    def set_literal_value(self, s: Sentence, value: MvalT_co, /):
        self._check_not_finished()

    @abstractmethod
    def set_opaque_value(self, s: Sentence, value: MvalT_co, /):
        self._check_not_finished()

    @abstractmethod
    def set_atomic_value(self, s: Atomic, value: MvalT_co, /):
        self._check_not_finished()

    @abstractmethod
    def set_predicated_value(self, s: Predicated, value: MvalT_co, /):
        self._check_not_finished()

    def is_countermodel_to(self, a: Argument, /) -> bool:
        return (
            all(map(self.Meta.designated_values.__contains__, map(self.value_of, a.premises))) and
            self.value_of(a.conclusion) not in self.Meta.designated_values)

    @abstractmethod
    def read_branch(self, branch: Branch, /) -> Self:
        self._check_not_finished()
        self.finish()
        return self

    def _check_finished(self):
        if not self.finished:
            raise Emsg.IllegalState('Model not yet finished')

    def _check_not_finished(self):
        if self.finished:
            raise Emsg.IllegalState('Model already finished')

    def finish(self) -> Self:
        self._check_not_finished()
        self._finished = True
        return self

    @abstractmethod
    def get_data(self) -> Mapping[str, Any]:
        return {}

    @classmethod
    def truth_table(cls, oper: Operator, / , *, reverse=False) -> TruthTable[MvalT_co]:
        oper = Operator(oper)
        if reverse:
            values = tuple(reversed(cls.values))
        else:
            values = cls.values
        inputs = tuple(product(*repeat(values, oper.arity)))
        outputs = tuple(
            cls.truth_function(oper, *values)
            for values in inputs)
        return TruthTable(
            inputs = inputs,
            outputs = outputs,
            operator = oper,
            Value = cls.values,
            mapping = MapProxy(dict(zip(inputs, outputs))))

    def __enter__(self) -> Self:
        self._check_not_finished()
        return self

    def __exit__(self, type, value, traceback):
        if not self.finished:
            self.finish()

    class TruthFunction(Generic[MvalT], abcs.Abc):

        values: type[MvalT]
        maxval: MvalT
        minval: MvalT
        values_sequence: tuple[MvalT, ...]
        values_indexes: Mapping[MvalT, int]

        generalizing_operators: Mapping[Operator, Literal['min', 'max']] = EMPTY_MAP
        generalized_orderings: Mapping[Literal['min', 'max'], tuple[MvalT, ...]] = EMPTY_MAP
        generalized_indexes: Mapping[Literal['min', 'max'], Mapping[MvalT, int]]

        def __init__(self, values: type[MvalT]) -> None:
            self.values = values
            self.maxval = max(values)
            self.minval = min(values)
            self.values_sequence = tuple(self.values)
            self.values_indexes = MapProxy({
                value: i
                for i, value in enumerate(self.values_sequence)})
            self.generalized_indexes = MapProxy({
                key: MapProxy(dict(map(reversed, enumerate(value))))
                for key, value in self.generalized_orderings.items()})

        def __call__(self, oper: Operator, *args: MvalT) -> MvalT:
            try:
                name = oper.name
            except AttributeError:
                name = Operator(oper).name
            try:
                func = getattr(self, name)
            except AttributeError:
                raise NotImplementedError from ValueError(oper)
            return func(*args)

        @abstractmethod
        def Assertion(self, a: MvalT, /) -> MvalT:
            raise NotImplementedError

        @abstractmethod
        def Negation(self, a: MvalT, /) -> MvalT:
            raise NotImplementedError

        @abstractmethod
        def Conjunction(self, a: MvalT, b: MvalT, /) -> MvalT:
            raise NotImplementedError

        @abstractmethod
        def Disjunction(self, a: MvalT, b: MvalT, /) -> MvalT:
            raise NotImplementedError

        @abstractmethod
        def Conditional(self, a: MvalT, b: MvalT, /) -> MvalT:
            raise NotImplementedError

        @abstractmethod
        def Biconditional(self, a: MvalT, b: MvalT, /) -> MvalT:
            raise NotImplementedError

        @abstractmethod
        def MaterialConditional(self, a: MvalT, b: MvalT, /) -> MvalT:
            raise NotImplementedError

        @abstractmethod
        def MaterialBiconditional(self, a: MvalT, b: MvalT, /) -> MvalT:
            raise NotImplementedError

        def generalize(self, oper: Operator, it: Iterable[MvalT], /) -> MvalT:
            mode = self.generalizing_operators[oper]
            try:
                ordering = self.generalized_orderings[mode]
            except KeyError:
                if mode == 'max':
                    return maxceil(self.maxval, it, self.minval)
                if mode == 'min':
                    return minfloor(self.minval, it, self.maxval)
                raise NotImplementedError from ValueError(mode)
            indexes = self.generalized_indexes[mode]
            it = map(indexes.__getitem__, it)
            if mode == 'max':
                return ordering[maxceil(len(ordering) - 1, it, 0)]
            if mode == 'min':
                return ordering[minfloor(0, it, len(ordering) - 1)]
            raise NotImplementedError from ValueError(mode)

    @classmethod
    def __init_subclass__(cls):
        super().__init_subclass__()
        Meta = cls.__dict__.get('Meta', LogicType.meta_for_module(cls.__module__))
        if not Meta:
            return
        cls.Meta = Meta
        cls.values = Meta.values
        cls.minval = min(Meta.values)
        cls.maxval = max(Meta.values)
        cls.truth_function = cls.TruthFunction(Meta.values)

@dataclass(kw_only = True)
class TruthTable(Mapping[tuple[MvalT, ...], MvalT]):
    'Truth table data class.'

    inputs: tuple[tuple[MvalT, ...], ...]
    outputs: tuple[MvalT, ...]
    operator: Operator
    Value: type[MvalT]
    mapping: Mapping[tuple[MvalT, ...], MvalT]

    def __getitem__(self, key):
        return self.mapping[key]
    def __iter__(self):
        return iter(self.mapping)
    def __reversed__(self):
        return reversed(self.mapping)
    def __len__(self):
        return len(self.mapping)

class PredicateInterpretation:
    pos: set[tuple[Constant, ...]]
    neg: set[tuple[Constant, ...]]
    constants: set[Constant]
    def __init__(self) -> None:
        self.pos = set()
        self.neg = set()
        self.constants = set()
    def addpos(self, item: tuple[Constant,...]):
        self.constants.update(item)
        self.pos.add(item)
    def addneg(self, item: tuple[Constant,...]):
        self.constants.update(item)
        self.neg.add(item)
    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, __class__):
            return NotImplemented
        return self.pos == other.pos and self.neg == other.neg