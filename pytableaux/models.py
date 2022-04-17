from __future__ import annotations

__all__ = 'BaseModel', 'Mval'

from pytableaux.errors import instcheck, Emsg
from pytableaux.tools import closure
from pytableaux.tools.abcs import Abc, AbcEnum
from pytableaux.tools.decorators import abstract
from pytableaux.tools.sets import setf
from pytableaux.lexicals import (
    Argument,
    Atomic,
    LexType,
    Operated,
    Operator,
    Predicated,
    Quantified,
    Quantifier,
    Sentence,
)
from pytableaux.proof.common import Branch

from dataclasses import dataclass
from itertools import (
    product,
    repeat,
    # starmap,
)
from typing import (
    Any,
    ClassVar,
    Mapping,
)

class Mval(AbcEnum):

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

MvalT = Mval | str | float

class BaseModel(Abc):

    Value: ClassVar[type[Mval]]

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
        def value_of(self: BaseModel, s: Sentence, /, **kw) -> Mval:
            if self.is_sentence_opaque(s):
                return self.value_of_opaque(s, **kw)
            try:
                return getattr(self, _methmap[s.TYPE])(s, **kw)
            except KeyError:
                pass
            instcheck(s, Sentence)
            raise NotImplementedError
        return value_of

    def value_of_quantified(self, s: Quantified, /, **kw) -> Mval:
        try:
            q = s.quantifier
        except AttributeError:
            raise TypeError
        if q is Quantifier.Existential:
            return self.value_of_existential(s, **kw)
        elif q is Quantifier.Universal:
            return self.value_of_universal(s, **kw)
        instcheck(s, Quantified)
        raise NotImplementedError

    def value_of_operated(self, s: Operated, /, **kw) -> Mval:
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
        instcheck(s, Operated)
        raise NotImplementedError

    def value_of_modal(self, s: Operated, /, **kw) -> Mval:
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

    def truth_table(self, oper: Operator, / , reverse = False) -> TruthTable:
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
    def truth_function(self, oper: Operator, *values: MvalT) -> Mval:
        if oper not in self.truth_functional_operators:
            raise ValueError(oper)
        if len(values) != oper.arity:
            raise Emsg.WrongLength(values, oper.arity)
        instcheck(oper, Operator)
        raise NotImplementedError

    @abstract
    def read_branch(self, branch: Branch, /):
        self.finish()

    @abstract
    def value_of_existential(self, s: Quantified, /, **kw) -> Mval:
        instcheck(s, Quantified)
        raise NotImplementedError

    @abstract
    def value_of_universal(self, s: Quantified, /, **kw) -> Mval:
        instcheck(s, Quantified)
        raise NotImplementedError

    @abstract
    def value_of_possibility(self, s: Operated, /, **kw) -> Mval:
        instcheck(s, Operated)
        raise NotImplementedError

    @abstract
    def value_of_necessity(self, s: Operated, /, **kw) -> Mval:
        instcheck(s, Operated)
        raise NotImplementedError

    @abstract
    def set_literal_value(self, s: Sentence, value: MvalT, /):
        instcheck(s, Sentence)
        raise NotImplementedError

    @abstract
    def set_opaque_value(self, s: Sentence, value: MvalT, /):
        instcheck(s, Sentence)
        raise NotImplementedError

    @abstract
    def set_atomic_value(self, s: Atomic, value: MvalT, /):
        instcheck(s, Atomic)
        raise NotImplementedError

    @abstract
    def set_predicated_value(self, s: Predicated, value: MvalT, /):
        instcheck(s, Predicated)
        raise NotImplementedError

    @abstract
    def value_of_opaque(self, s: Sentence, /) -> Mval:
        instcheck(s, Sentence)
        raise NotImplementedError

    @abstract
    def value_of_atomic(self, s: Atomic, /) -> Mval:
        instcheck(s, Atomic)
        raise NotImplementedError

    @abstract
    def value_of_predicated(self, s: Predicated, /) -> Mval:
        instcheck(s, Predicated)
        raise NotImplementedError

    @abstract
    def is_countermodel_to(self, a: Argument, /) -> bool:
        instcheck(a, Argument)
        raise NotImplementedError

    @abstract
    def get_data(self) -> Mapping[str, Any]:
        return {}


@dataclass(kw_only = True)
class TruthTable:
    'Truth table data class.'

    inputs: tuple[tuple[Mval], ...]
    outputs: tuple[Mval, ...]
    operator: Operator
    Value: type[Mval]
