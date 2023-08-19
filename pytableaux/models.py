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
from typing import Any, Generic, Mapping, TypeVar

from .errors import check
from .lang import (Argument, Atomic, Constant, Operated, Operator, Predicated, LexType,
                   Quantified, Quantifier, Sentence)
from .logics import LogicType
from .proof import Branch
from .tools import abcs

__all__ = (
    'BaseModel',
    'Mval',
    'ValueFDE',
    'ValueK3',
    'ValueLP',
    'ValueCPL')

class Mval(abcs.Ebc):

    __slots__ = 'name', 'label', 'num'

    label: str
    num: float

    def __init__(self, label: str, num: float, /):
        self.label = label
        self.num = num

    def __eq__(self, other):
        if self is other:
            return True
        if isinstance(other, (float, int)):
            return other == self.num
        if isinstance(other, str):
            return other == self.name# or other.lower() == self.label.lower()
        return NotImplemented

    def __hash__(self):
        return hash(self.num)

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

    def __float__(self):
        return self.num

    def __str__(self):
        return self.name

    @classmethod
    def _member_keys(cls, member: Mval):
        return super()._member_keys(member) | {member.label, member.num}


class ValueFDE(Mval):
    "Model values for gappy + glutty 4-valued logics, like FDE."

    F = 'False',   0.0
    N = 'Neither', 0.25
    B = 'Both',    0.75
    T = 'True',    1.0

class ValueK3(Mval):
    "Model values for gappy 3-valued logics, like K3 and others."

    F = 'False',   0.0
    N = 'Neither', 0.5
    T = 'True',    1.0

class ValueLP(Mval):
    "Model values for glutty 3-valued logics, like LP and others."

    F = 'False', 0.0
    B = 'Both', 0.5
    T = 'True', 1.0

class ValueCPL(Mval):
    'Model values for 2-valued "classical" logics.'

    F = 'False', 0.0
    T = 'True' , 1.0

# MvalId = Mval | str | float
MvalT = TypeVar('MvalT', bound = Mval)
MvalT_co = TypeVar('MvalT_co', bound = Mval, covariant = True)

class BaseModel(Generic[MvalT_co], abcs.Abc):
    Meta: type[LogicType.Meta]

    values: type[MvalT_co]
    "The values of the model"
    designated_values: Set[MvalT_co]
    "The set of designated values"
    unassigned_value: MvalT_co
    "The default 'unassigned' value"
    truth_functional_operators: Set[Operator]
    "The truth-functional operators"
    modal_operators: Set[Operator] 
    "The modal operators"
    truth_function: BaseModel.TruthFunction[MvalT_co]

    @property
    def id(self) -> int:
        return id(self)

    def is_sentence_opaque(self, s: Sentence, /) -> bool:
        return False

    def is_sentence_literal(self, s: Sentence, /) -> bool:
        return type(s) in (Atomic, Predicated) or (
            type(s) is Operated and
            s.operator is Operator.Negation and (
                type(s.lhs) in (Atomic, Predicated) or
                self.is_sentence_opaque(s.lhs)))

    _methmap = {}

    _methmap.update(
        (('value_of', member.cls), f'value_of_{member.name.lower()}')
        for member in LexType if member.role is Sentence)

    def value_of(self, s: Sentence, /, **kw) -> MvalT_co:
        if self.is_sentence_opaque(s):
            return self.value_of_opaque(s, **kw)
        try:
            name = self._methmap['value_of', type(s)]
            func = getattr(self, name)
        except (AttributeError, KeyError):
            pass
        else:
            return func(s, **kw)
        check.inst(s, Sentence)
        raise NotImplementedError

    @abstractmethod
    def value_of_opaque(self, s: Sentence, /) -> MvalT_co:
        raise NotImplementedError

    @abstractmethod
    def value_of_atomic(self, s: Atomic, /) -> MvalT_co:
        raise NotImplementedError

    @abstractmethod
    def value_of_predicated(self, s: Predicated, /) -> MvalT_co:
        raise NotImplementedError

    @abstractmethod
    def value_of_quantified(self, s: Quantified, /, **kw) -> MvalT_co:
        raise NotImplementedError

    def value_of_operated(self, s: Operated, /, **kw) -> MvalT_co:
        if s.operator in self.truth_functional_operators:
            return self.truth_function(s.operator,
                *map(lambda s: self.value_of(s, **kw), s))
        check.inst(s, Operated)
        raise NotImplementedError

    # @abstractmethod
    # def truth_function(self, oper: Operator, a, b = None, /) -> MvalT_co:
    #     raise NotImplementedError

    @abstractmethod
    def set_literal_value(self, s: Sentence, value: MvalT_co, /):
        raise NotImplementedError

    @abstractmethod
    def set_opaque_value(self, s: Sentence, value: MvalT_co, /):
        raise NotImplementedError

    @abstractmethod
    def set_atomic_value(self, s: Atomic, value: MvalT_co, /):
        raise NotImplementedError

    @abstractmethod
    def set_predicated_value(self, s: Predicated, value: MvalT_co, /):
        raise NotImplementedError

    @abstractmethod
    def is_countermodel_to(self, a: Argument, /) -> bool:
        raise NotImplementedError

    @abstractmethod
    def read_branch(self, branch: Branch, /):
        self.finish()

    def finish(self):
        pass

    @abstractmethod
    def get_data(self) -> Mapping[str, Any]:
        return {}

    def truth_table(self, oper: Operator, / , *, reverse=False) -> TruthTable[MvalT_co]:
        oper = Operator(oper)
        inputs = tuple(product(*repeat(self.values, oper.arity)))
        if reverse:
            inputs = tuple(reversed(inputs))
        outputs = tuple(
            self.truth_function(oper, *values)
            for values in inputs)
        return TruthTable(
            inputs = inputs,
            outputs = outputs,
            operator = oper,
            Value = self.values,
            mapping = MapProxy(dict(zip(inputs, outputs))))

    class TruthFunction(Generic[MvalT], abcs.Abc):

        values: type[MvalT]

        def __init__(self, values: type[MvalT]) -> None:
            self.values = values

        def __call__(self, oper: Operator, *args: MvalT) -> MvalT:
            try:
                func = getattr(self, oper.name)
            except AttributeError:
                raise ValueError(oper) from None
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

    _methmap = MapProxy(_methmap)

    @classmethod
    def __init_subclass__(cls):
        super().__init_subclass__()
        abcs.merge_attr(cls, '_methmap', supcls=__class__, transform=MapProxy)
        Meta = cls.__dict__.get('Meta', LogicType.meta_for_module(cls.__module__))
        if Meta:
            cls.Meta = Meta
            # cls.Value = Meta.values
            cls.values = Meta.values
            cls.designated_values = Meta.designated_values
            cls.unassigned_value = Meta.unassigned_value
            cls.modal_operators = frozenset(Meta.modal_operators)
            cls.truth_functional_operators = frozenset(Meta.truth_functional_operators)
            cls.truth_function = cls.TruthFunction(cls.values)

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

