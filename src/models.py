from __future__ import annotations

__all__ = 'BaseModel', 

from errors import instcheck, Emsg
from tools.abcs import Abc
from tools.decorators import abstract
from tools.hybrids import qsetf
from tools.sets import setf
from lexicals import (
    Operator,
    Sentence, Atomic, Predicated, Operated, Quantified,
    Argument
)

from itertools import (
    product,
    repeat,
    # starmap,
)
from typing import (
    Any, Mapping
)

ModelValue = Any

class BaseModel(Abc):

    truth_values = qsetf()
    # Default set
    truth_functional_operators = setf({
        Operator.Assertion             ,
        Operator.Negation              ,
        Operator.Conjunction           ,
        Operator.Disjunction           ,
        Operator.MaterialConditional   ,
        Operator.Conditional           ,
        Operator.MaterialBiconditional ,
        Operator.Biconditional         ,
    })
    # Default set
    modal_operators = setf({
        Operator.Necessity  ,
        Operator.Possibility,
    })

    # flag set by tableau
    is_countermodel = None

    @property
    def id(self):
        return id(self)

    @abstract
    def read_branch(self, branch): ...

    def value_of(self, s: Sentence, /, **kw) -> ModelValue:
        if self.is_sentence_opaque(s):
            return self.value_of_opaque(s, **kw)
        stype = type(s)
        if stype is Operated:
            return self.value_of_operated(s, **kw)
        elif stype is Predicated:
            return self.value_of_predicated(s, **kw)
        elif stype is Atomic:
            return self.value_of_atomic(s, **kw)
        elif stype is Quantified:
            return self.value_of_quantified(s, **kw)
        instcheck(s, Sentence)
        raise NotImplementedError

    @abstract
    def truth_function(self, oper: Operator, *values) -> ModelValue:
        # TODO: accept single iterable
        if oper not in self.truth_functional_operators:
            raise TypeError(oper)
        if len(values) != oper.arity:
            raise Emsg.WrongLength(values, oper.arity)
        raise NotImplementedError

    def truth_table_inputs(self, arity: int):
        return tuple(product(
            *repeat(self.truth_values, arity)
        ))

    def is_sentence_opaque(self, s: Sentence, /, **kw):
        return False

    def is_sentence_literal(self, s: Sentence) -> bool:
        return isinstance(s, (Atomic, Predicated)) or (
            isinstance(s, Operated) and
            s.operator is Operator.Negation and
            (
                isinstance(s.lhs, (Atomic, Predicated)) or
                self.is_sentence_opaque(s.lhs)
            )
        )

    @abstract
    def value_of_opaque(self, s: Sentence, /, **kw) -> ModelValue:
        instcheck(s, Sentence)
        raise NotImplementedError

    @abstract
    def value_of_atomic(self, s: Atomic, /, **kw) -> ModelValue:
        instcheck(s, Atomic)
        raise NotImplementedError

    @abstract
    def value_of_predicated(self, s: Predicated, /, **kw) -> ModelValue:
        instcheck(s, Predicated)
        raise NotImplementedError

    @abstract
    def value_of_quantified(self, s: Quantified, /, **kw) -> ModelValue:
        instcheck(s, Quantified)
        raise NotImplementedError

    def value_of_operated(self, s: Operated, /, **kw) -> ModelValue:
        return self.truth_function(
            s.operator,
            *(
                self.value_of(operand, **kw)
                for operand in s.operands
            )
        )

    @abstract
    def is_countermodel_to(self, a: Argument, /) -> bool:
        instcheck(a, Argument)
        raise NotImplementedError

    @abstract
    def get_data(self) -> Mapping:
        return {}

    def truth_table(self, oper: Operator, / , reverse=False):
        oper = Operator(oper)
        inputs = self.truth_table_inputs(oper.arity)
        if reverse:
            inputs = tuple(reversed(inputs))
        outputs = [
            self.truth_function(oper, *values)
            for values in inputs
        ]
        return {'inputs': inputs, 'outputs': outputs}

    def truth_tables(self, **kw):
        return {
            oper: self.truth_table(oper, **kw)
            for oper in self.truth_functional_operators
        }
