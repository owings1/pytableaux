from typing import Any, ClassVar, Generic, Mapping, Sequence, TypeVar, overload

from pytableaux.lang import (Argument, Atomic, Operated, Operator, Predicated,
                             Quantified, Sentence)
from pytableaux.proof import Branch
from pytableaux.tools import abcs, sets


class Mval(abcs.Ebc):
    label: str
    num: float
    def __init__(self, label: str, num: float) -> None: ...
    def __eq__(self, other:Mval|str|float) -> bool: ...
    def __hash__(self) -> int: ...
    def __le__(self, other:Mval|str|float) -> bool: ...
    def __lt__(self, other:Mval|str|float) -> bool: ...
    def __ge__(self, other:Mval|str|float) -> bool: ...
    def __gt__(self, other:Mval|str|float) -> bool: ...
    def __float__(self) -> float: ...

class ValueFDE(Mval):
    F: ValueFDE
    N: ValueFDE
    B: ValueFDE
    T: ValueFDE

class ValueK3(Mval):
    F: ValueK3
    N: ValueK3
    T: ValueK3

class ValueLP(Mval):
    F: ValueLP
    B: ValueLP
    T: ValueLP

class ValueCPL(Mval):
    F: ValueCPL
    T: ValueCPL

MvalT = TypeVar('MvalT', bound=Mval)
MvalT_co = TypeVar('MvalT_co', bound=Mval, covariant=True)

class BaseModel(abcs.Abc, Generic[MvalT_co], metaclass=abcs.AbcMeta):
    Value: ClassVar[type[MvalT_co]]
    truth_functional_operators: ClassVar[sets.setf[Operator]]
    modal_operators: ClassVar[sets.setf[Operator]]
    unassigned_value: ClassVar[MvalT_co]
    @property
    def id(self) -> int: ...
    def finish(self) -> None: ...
    def get_data(self) -> Mapping[str, Any]: ...
    def read_branch(self, branch: Branch) -> None: ...
    def is_countermodel_to(self, a: Argument) -> bool: ...
    def is_sentence_literal(self, s: Sentence) -> bool: ...
    def is_sentence_opaque(self, s: Sentence, **kw) -> bool: ...
    def set_atomic_value(self, s: Atomic, value: MvalT_co)-> None: ...
    def set_literal_value(self, s: Sentence, value: MvalT_co)-> None: ...
    def set_opaque_value(self, s: Sentence, value: MvalT_co)-> None: ...
    def set_predicated_value(self, s: Predicated, value: MvalT_co)-> None: ...
    def value_of(self, s:Sentence) -> MvalT_co: ...
    def value_of_atomic(self, s: Atomic) -> MvalT_co: ...
    def value_of_existential(self, s: Quantified, **kw) -> MvalT_co: ...
    def value_of_modal(self, s: Operated, **kw) -> MvalT_co: ...
    def value_of_necessity(self, s: Operated, **kw) -> MvalT_co: ...
    def value_of_opaque(self, s: Sentence) -> MvalT_co: ...
    def value_of_operated(self, s: Operated, **kw) -> MvalT_co: ...
    def value_of_possibility(self, s: Operated, **kw) -> MvalT_co: ...
    def value_of_predicated(self, s: Predicated) -> MvalT_co: ...
    def value_of_quantified(self, s: Quantified, **kw) -> MvalT_co: ...
    def value_of_universal(self, s: Quantified, **kw) -> MvalT_co: ...
    @overload
    def truth_function(self, oper: Operator, a,/) -> MvalT_co: ...
    @overload
    def truth_function(self, oper: Operator, a, b,/) -> MvalT_co: ...
    def truth_table(self, oper: Operator, /,reverse: bool = ...) -> TruthTable[MvalT_co]: ...

class TruthTable(Generic[MvalT]):
    inputs: tuple[tuple[MvalT], ...]
    outputs: tuple[MvalT, ...]
    operator: Operator
    Value: type[MvalT]
    @overload
    def __init__(self, *, inputs:tuple[tuple[MvalT], ...], outputs:tuple[MvalT, ...], operator: Operator, Value: Sequence[MvalT]) -> None: ...
    @overload
    def __init__(self, *, inputs:tuple[MvalT], outputs:tuple[MvalT, ...], operator: Operator, Value: Sequence[MvalT]) -> None: ...
