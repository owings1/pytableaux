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
from .lang import (Argument, Atomic, Operated, Operator, Predicated,
                   Quantified, Quantifier, Sentence)
from .logics import LogicType
from .proof import Branch
from .tools import closure
from .tools.abcs import Abc, Ebc

__all__ = (
    'BaseModel',
    'Mval',
    'ValueFDE',
    'ValueK3',
    'ValueLP',
    'ValueCPL')

class Mval(Ebc):

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
            return other == self.name or other == self.label
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

class BaseModel(Generic[MvalT_co], Abc):
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

    @property
    def id(self) -> int:
        return id(self)

    @closure
    def value_of():
        _methmap = {
            Atomic     : 'value_of_atomic',
            Operated   : 'value_of_operated',
            Predicated : 'value_of_predicated',
            Quantified : 'value_of_quantified'}
        def value_of(self: BaseModel, s: Sentence, /, **kw) -> MvalT_co:
            if self.is_sentence_opaque(s):
                return self.value_of_opaque(s, **kw)
            try:
                return getattr(self, _methmap[type(s)])(s, **kw)
            except KeyError:
                pass
            check.inst(s, Sentence)
            raise NotImplementedError
        return value_of

    def value_of_quantified(self, s: Quantified, /, **kw) -> MvalT_co:
        try:
            q = s.quantifier
        except AttributeError:
            raise TypeError
        if q is Quantifier.Existential:
            return self.value_of_existential(s, **kw)
        if q is Quantifier.Universal:
            return self.value_of_universal(s, **kw)
        check.inst(s, Quantified)
        raise NotImplementedError

    def value_of_operated(self, s: Operated, /, **kw) -> MvalT_co:
        if self.is_sentence_opaque(s):
            return self.value_of_opaque(s, **kw)
        if s.operator in self.truth_functional_operators:
            return self.truth_function(
                s.operator,
                *(self.value_of(operand, **kw)
                    for operand in s.operands))
        if s.operator in self.modal_operators:
            return self.value_of_modal(s, **kw)
        check.inst(s, Operated)
        raise NotImplementedError

    def value_of_modal(self, s: Operated, /, **kw) -> MvalT_co:
        if s.operator is Operator.Possibility:
            return self.value_of_possibility(s, **kw)
        if s.operator is Operator.Necessity:
            return self.value_of_necessity(s, **kw)
        raise NotImplementedError

    def is_sentence_opaque(self, s: Sentence, /, **kw) -> bool:
        return False

    def is_sentence_literal(self, s: Sentence, /) -> bool:
        stype = type(s)
        return stype is Atomic or stype is Predicated or (
            stype is Operated and
            s.operator is Operator.Negation and (
                type(s.lhs) in (Atomic, Predicated) or
                self.is_sentence_opaque(s.lhs)))

    def truth_table(self, oper: Operator, / , reverse = False) -> TruthTable[MvalT_co]:
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

    def finish(self):
        pass

    @abstractmethod
    def truth_function(self, oper: Operator, a, b = None, /) -> MvalT_co:
        raise NotImplementedError

    @abstractmethod
    def read_branch(self, branch: Branch, /):
        self.finish()

    @abstractmethod
    def value_of_existential(self, s: Quantified, /, **kw) -> MvalT_co:
        check.inst(s, Quantified)
        raise NotImplementedError

    @abstractmethod
    def value_of_universal(self, s: Quantified, /, **kw) -> MvalT_co:
        check.inst(s, Quantified)
        raise NotImplementedError

    @abstractmethod
    def value_of_possibility(self, s: Operated, /, **kw) -> MvalT_co:
        check.inst(s, Operated)
        raise NotImplementedError

    @abstractmethod
    def value_of_necessity(self, s: Operated, /, **kw) -> MvalT_co:
        check.inst(s, Operated)
        raise NotImplementedError

    @abstractmethod
    def set_literal_value(self, s: Sentence, value: Any, /):
        check.inst(s, Sentence)
        raise NotImplementedError

    @abstractmethod
    def set_opaque_value(self, s: Sentence, value: Any, /):
        check.inst(s, Sentence)
        raise NotImplementedError

    @abstractmethod
    def set_atomic_value(self, s: Atomic, value: Any, /):
        check.inst(s, Atomic)
        raise NotImplementedError

    @abstractmethod
    def set_predicated_value(self, s: Predicated, value: Any, /):
        check.inst(s, Predicated)
        raise NotImplementedError

    @abstractmethod
    def value_of_opaque(self, s: Sentence, /) -> MvalT_co:
        check.inst(s, Sentence)
        raise NotImplementedError

    @abstractmethod
    def value_of_atomic(self, s: Atomic, /) -> MvalT_co:
        check.inst(s, Atomic)
        raise NotImplementedError

    @abstractmethod
    def value_of_predicated(self, s: Predicated, /) -> MvalT_co:
        check.inst(s, Predicated)
        raise NotImplementedError

    @abstractmethod
    def is_countermodel_to(self, a: Argument, /) -> bool:
        check.inst(a, Argument)
        raise NotImplementedError

    @abstractmethod
    def get_data(self) -> Mapping[str, Any]:
        return {}

    def __init_subclass__(cls):
        super().__init_subclass__()
        Meta = cls.__dict__.get('Meta', LogicType.meta_for_module(cls.__module__))
        if Meta:
            cls.Meta = Meta
            # cls.Value = Meta.values
            cls.values = Meta.values
            cls.designated_values = Meta.designated_values
            cls.unassigned_value = Meta.unassigned_value
            cls.modal_operators = frozenset(Meta.modal_operators)
            cls.truth_functional_operators = frozenset(Meta.truth_functional_operators)

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