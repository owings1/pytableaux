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
pytableaux.models
^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product, repeat
from typing import Any, ClassVar, Generic, Mapping

from pytableaux.errors import Emsg, check
from pytableaux.lang.collect import Argument
from pytableaux.lang.lex import (Atomic, LexType, Operated, Operator,
                                 Predicated, Quantified, Quantifier, Sentence)
from pytableaux.proof.common import Branch
from pytableaux.tools import abstract, closure
from pytableaux.tools.abcs import Abc, Ebc
from pytableaux.tools.sets import setf
from pytableaux.tools.typing import VT

from typing import TypeVar, TYPE_CHECKING

__all__ = (
    'BaseModel',
    'Mval',
    'ValueFDE',
)

class Mval(Ebc):

    __slots__ = 'name', 'label', 'num',

    label: str
    num: float

    def __init__(self, label: str, num: float, /):
        self.label = label
        self.num = num

    def __eq__(self, other):
        if self is other:
            return True
        if isinstance(other, float):
            return other == self.num
        if isinstance(other, str):
            return other == self.name or other == self.label
        if isinstance(other, int):
            return float(other) == self.num
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

MvalId = Mval | str | float

MvalT = TypeVar('MvalT', bound = Mval)
MvalT_co = TypeVar('MvalT_co', bound = Mval, covariant = True)

class BaseModel(Generic[MvalT_co], Abc):

    # Value: ClassVar[type[Mval]]
    Value: ClassVar[type[MvalT_co]]

    truth_functional_operators: ClassVar[setf[Operator]] = setf({
        Operator.Assertion             ,
        Operator.Negation              ,
        Operator.Conjunction           ,
        Operator.Disjunction           ,
        Operator.MaterialConditional   ,
        Operator.Conditional           ,
        Operator.MaterialBiconditional ,
        Operator.Biconditional         ,
    })

    modal_operators: ClassVar[setf[Operator]] = setf({
        Operator.Necessity  ,
        Operator.Possibility,
    })

    @property
    def id(self) -> int:
        return id(self)

    @closure
    def value_of():
        _methmap = {
            LexType.Atomic     : 'value_of_atomic',
            LexType.Operated   : 'value_of_operated',
            LexType.Predicated : 'value_of_predicated',
            LexType.Quantified : 'value_of_quantified',
        }
        def value_of(self: BaseModel, s: Sentence, /, **kw) -> MvalT_co:
            if self.is_sentence_opaque(s):
                return self.value_of_opaque(s, **kw)
            try:
                return getattr(self, _methmap[s.TYPE])(s, **kw)
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
        elif q is Quantifier.Universal:
            return self.value_of_universal(s, **kw)
        check.inst(s, Quantified)
        raise NotImplementedError

    def value_of_operated(self, s: Operated, /, **kw) -> MvalT_co:
        if self.is_sentence_opaque(s):
            return self.value_of_opaque(s, **kw)
        if s.operator in self.truth_functional_operators:
            return self.truth_function(
                s.operator,
                *(
                    self.value_of(operand, **kw)
                    for operand in s.operands
                )
            )
        if s.operator in self.modal_operators:
            return self.value_of_modal(s, **kw)
        check.inst(s, Operated)
        raise NotImplementedError

    def value_of_modal(self, s: Operated, /, **kw) -> MvalT_co:
        oper = s.operator
        if oper is Operator.Possibility:
            return self.value_of_possibility(s, **kw)
        if oper is Operator.Necessity:
            return self.value_of_necessity(s, **kw)
        raise NotImplementedError

    def is_sentence_opaque(self, s: Sentence, /, **kw) -> bool:
        return False

    def is_sentence_literal(self, s: Sentence, /) -> bool:
        stype = type(s)
        return stype is Atomic or stype is Predicated or (
            stype is Operated and
            s.operator is Operator.Negation and
            (
                type(s.lhs) in (Atomic, Predicated) or
                self.is_sentence_opaque(s.lhs)
            )
        )

    def truth_table(self, oper: Operator, / , reverse = False) -> TruthTable[MvalT_co]:
        oper = Operator(oper)
        inputs = tuple(product(*repeat(self.Value, oper.arity)))
        if reverse:
            inputs = tuple(reversed(inputs))
        trfunc = self.truth_function
        return TruthTable(
            inputs = inputs,
            outputs = tuple(
                trfunc(oper, *values)
                for values in inputs
            ),
            operator = oper,
            Value = self.Value,
        )

    def finish(self):
        pass

    @abstract
    def truth_function(self, oper: Operator, a, b = None, /) -> MvalT_co:
        # if oper not in self.truth_functional_operators:
        #     raise ValueError(oper)
        # if len(values) != oper.arity:
        #     raise Emsg.WrongLength(values, oper.arity)
        # check.inst(oper, Operator)
        raise NotImplementedError

    @abstract
    def read_branch(self, branch: Branch, /):
        self.finish()

    @abstract
    def value_of_existential(self, s: Quantified, /, **kw) -> MvalT_co:
        check.inst(s, Quantified)
        raise NotImplementedError

    @abstract
    def value_of_universal(self, s: Quantified, /, **kw) -> MvalT_co:
        check.inst(s, Quantified)
        raise NotImplementedError

    @abstract
    def value_of_possibility(self, s: Operated, /, **kw) -> MvalT_co:
        check.inst(s, Operated)
        raise NotImplementedError

    @abstract
    def value_of_necessity(self, s: Operated, /, **kw) -> MvalT_co:
        check.inst(s, Operated)
        raise NotImplementedError

    @abstract
    def set_literal_value(self, s: Sentence, value: Any, /):
        check.inst(s, Sentence)
        raise NotImplementedError

    @abstract
    def set_opaque_value(self, s: Sentence, value: Any, /):
        check.inst(s, Sentence)
        raise NotImplementedError

    @abstract
    def set_atomic_value(self, s: Atomic, value: Any, /):
        check.inst(s, Atomic)
        raise NotImplementedError

    @abstract
    def set_predicated_value(self, s: Predicated, value: Any, /):
        check.inst(s, Predicated)
        raise NotImplementedError

    @abstract
    def value_of_opaque(self, s: Sentence, /) -> MvalT_co:
        check.inst(s, Sentence)
        raise NotImplementedError

    @abstract
    def value_of_atomic(self, s: Atomic, /) -> MvalT_co:
        check.inst(s, Atomic)
        raise NotImplementedError

    @abstract
    def value_of_predicated(self, s: Predicated, /) -> MvalT_co:
        check.inst(s, Predicated)
        raise NotImplementedError

    @abstract
    def is_countermodel_to(self, a: Argument, /) -> MvalT_co:
        check.inst(a, Argument)
        raise NotImplementedError

    @abstract
    def get_data(self) -> Mapping[str, Any]:
        return {}


@dataclass(kw_only = True)
class TruthTable(Generic[MvalT]):
    'Truth table data class.'

    inputs: tuple[tuple[MvalT], ...]
    outputs: tuple[MvalT, ...]
    operator: Operator
    Value: type[MvalT]
