
from typing import (Any, ClassVar, Generic, Hashable, Iterable, Iterator,
                    Literal, Mapping, Sequence, SupportsIndex,
                    overload)

from pytableaux.lang import (BiCoords, LangCommonEnum, LexicalAbcMeta, LangCommonEnumMeta,
                             SysPredEnumMeta, TriCoords)
from pytableaux.tools import abcs
from pytableaux.tools.hybrids import qsetf
from pytableaux.tools.sequences import seqf
from pytableaux.tools.sets import setf
from pytableaux.typing import _T, _LexT, _SenT
from _typeshed import SupportsRichComparison as _SupportsRichCompare

_ParameterSpec = BiCoords
_PredicateSpec = TriCoords
_SpecType: tuple[int|str|tuple, ...]
_IdentType = tuple[str, tuple]
_ParameterIdent = tuple[str, BiCoords]
_QuantifierSpec = tuple[str]
_OperatorSpec = tuple[str]
_PredicateRef: tuple[int, ...] | str
_PredicatedSpec = tuple[TriCoords, tuple[_ParameterIdent, ...]]
_QuantifiedSpec = tuple[str, BiCoords, _IdentType]
_QuantifierEnumValue = tuple[int, str]
_OperatorEnumValue = tuple[int, str, int, str|None]
_LexTypeEnumValue = tuple[int, type[Lexical], type[Lexical], int|None, type[Lexical]|None]

class __LexTypeMeta(LangCommonEnumMeta):
    classes: qsetf[type[Lexical]]
class _LexTypeAttrs:
    rank:int
    role: type[Lexical]
    cls: type[Lexical]
    pcls: type[Lexical]
    maxi: int|None
    hash: int
class _LexicalEnumAttrs:
    spec: tuple[str]
    ident: tuple[str, tuple[str]]
    order: int
    label: str
    index: int
    strings: setf[str]
class __OperatorMeta(LangCommonEnumMeta):
    lib_opmap: Mapping[str, Operator]
class _OperatorAttrs:
    arity: int
    libname: str|None

class Lexical(abcs.Copyable, _SupportsRichCompare, Hashable):
    TYPE: ClassVar[LexType]
    spec: _SpecType
    ident: tuple
    sort_tuple: tuple[int, ...]
    hash: int
    @classmethod
    def first(cls: type[_LexT]) -> _LexT: ...
    def next(self:_LexT, **kw) -> _LexT: ...
    @classmethod
    def gen(cls:type[_LexT], stop: int|None, first: _LexT|None = ..., **nextkw) -> Iterator[_LexT]: ...
    @staticmethod
    def identitem(item: Lexical) -> tuple[str, tuple]: ...
    @staticmethod
    def hashitem(item: Lexical) -> int: ...
    @staticmethod
    def orderitems(a: Lexical, b:Lexical) -> int: ...
    def __bool__(self) -> Literal[True]: ...
    def for_json(self) -> tuple: ...

class LexicalAbc(Lexical, metaclass=LexicalAbcMeta):...

class LexicalEnum(_LexicalEnumAttrs, Lexical, LangCommonEnum):...

class CoordsItem(LexicalAbc, Generic[_T]):
    Coords: ClassVar[type[_T]]
    spec: _T
    index: int
    subscript: int
    @overload
    def __init__(self, *spec: int) -> None: ...
    @overload
    def __init__(self, spec: Iterable[int]) -> None: ...

class Parameter(CoordsItem[BiCoords]):
    spec: _ParameterSpec
    ident: _ParameterIdent
    is_constant: bool
    is_variable: bool
    @overload
    def __init__(self, spec: tuple[int, int]) -> None: ...
    @overload
    def __init__(self, index: int, subscript: int) -> None: ...

class Constant(Parameter):
    def __rshift__(self, other:Quantified) -> Sentence: ...
class Variable(Parameter):...

class Quantifier(LexicalEnum):
    Existential: _QuantifierEnumValue
    Universal: _QuantifierEnumValue
    @overload
    def __call__(self,  v: Variable, s: Sentence, /) -> Quantified: ...
    @overload
    def __call__(self, items: tuple[Variable, Sentence], /) -> Quantified: ...


class Operator(_OperatorAttrs, LexicalEnum, metaclass = __OperatorMeta):

    Assertion: _OperatorEnumValue
    Negation: _OperatorEnumValue
    Conjunction: _OperatorEnumValue
    Disjunction: _OperatorEnumValue
    MaterialConditional: _OperatorEnumValue
    MaterialBiconditional: _OperatorEnumValue
    Conditional: _OperatorEnumValue
    Biconditional: _OperatorEnumValue
    Possibility: _OperatorEnumValue
    Necessity: _OperatorEnumValue

    @overload
    def __call__(self, operand: Sentence) -> Operated: ...
    @overload
    def __call__(self, operands: Iterable[Sentence]) -> Operated: ...
    @overload
    def __call__(self, *operands: Sentence) -> Operated: ...

class Sentence(LexicalAbc):
    predicates: setf[Predicate]
    constants: setf[Constant]
    variables: setf[Variable]
    atomics: setf[Atomic]
    quantifiers: seqf[Quantifier]
    operators: seqf[Operator]
    def negate(self) -> Operated: ...
    def asserted(self) -> Operated: ...
    def disjoin(self, rhs: Sentence) -> Operated: ...
    def conjoin(self, rhs: Sentence) -> Operated: ...
    def negative(self) -> Sentence: ...
    def substitute(self:type[_SenT], pnew: Parameter, pold: Parameter) -> _SenT: ...
    def __invert__(self) -> Operated: ...
    def __and__(self, other: Sentence) -> Operated: ...
    def __or__(self, other: Sentence) -> Operated: ...

class Predicate(CoordsItem[TriCoords]):
    spec: _PredicateSpec
    arity: int
    bicoords: BiCoords
    is_system: bool
    name: str|TriCoords
    @property
    def refs(self) -> qsetf[_PredicateRef]: ...
    @overload
    def __init__(self, spec: tuple[int, int, int]) -> None: ...
    @overload
    def __init__(self, index: int, subscript: int, arity: int) -> None: ...
    @overload
    def __init__(self, name: str) -> None: ...
    def __call__(self, *spec: _PredicatedSpec) -> Predicated: ...
    class System(LangCommonEnum, metaclass=SysPredEnumMeta):
        Existence: Predicate
        Identity: Predicate
class Atomic(CoordsItem[BiCoords], Sentence):
    @overload
    def __init__(self, spec: tuple[int, int]) -> None: ...
    @overload
    def __init__(self, index: int, subscript: int) -> None: ...

class Predicated(Sentence, Sequence[Parameter]):
    spec: _PredicatedSpec
    predicate: Predicate
    params: tuple[Parameter, ...]
    paramset: setf[Parameter]
    @overload
    def __init__(self, pred: Predicate, param: Parameter, /) -> None: ...
    @overload
    def __init__(self, pred: Predicate, params: Iterable[Parameter], /) -> None: ...
    @overload
    def __init__(self, pred: Predicate, *params: Parameter) -> None: ...
    @overload
    def __getitem__(self, i: SupportsIndex, /) -> Parameter:...
    @overload
    def __getitem__(self, s: slice, /) -> tuple[Parameter, ...]:...
    @classmethod
    def first(cls, pred: Predicate = ..., /) -> Predicated:...

class Quantified(Sentence, Sequence):
    @overload
    def __init__(self, q: Quantifier, v: Variable, s: Sentence, /) -> None: ...
    @overload
    def __init__(self, spec: tuple[Quantifier, Variable, Sentence], /) -> None: ...
    spec: _QuantifiedSpec
    quantifier: Quantifier
    variable: Variable
    sentence: Sentence
    items: tuple[Quantifier, Variable, Sentence]
    @classmethod
    def first(cls, q: Quantifier = ..., /) -> Quantified:...
    def unquantify(self, c: Constant) -> Sentence: ...
    @overload
    def __getitem__(self, i: Literal[0,-3]) -> Quantifier: ...
    @overload
    def __getitem__(self, i: Literal[1,-2]) -> Variable: ...
    @overload
    def __getitem__(self, i: Literal[2,-1]) -> Sentence: ...
    @overload
    def __getitem__(self, i: SupportsIndex) -> Quantifier|Variable|Sentence: ...

class Operated(Sentence, Sequence[Sentence]):
    operator: Operator
    operands: tuple[Sentence, ...]
    lhs: Sentence
    rhs: Sentence
    @classmethod
    def first(cls, oper: Operator = ..., /) -> Operated:...
    @overload
    def __init__(self, oper: Operator, operand: Sentence) -> None: ...
    @overload
    def __init__(self, oper: Operator, operands: Iterable[Sentence]) -> None: ...
    @overload
    def __init__(self, oper: Operator, *operands: Sentence) -> None: ...

class LexType(_LexTypeAttrs, LangCommonEnum, metaclass = __LexTypeMeta):

    Predicate: _LexTypeEnumValue
    Constant: _LexTypeEnumValue
    Variable: _LexTypeEnumValue
    Quantifier: _LexTypeEnumValue
    Operator: _LexTypeEnumValue
    Atomic: _LexTypeEnumValue
    Predicated: _LexTypeEnumValue
    Quantified: _LexTypeEnumValue
    Operated: _LexTypeEnumValue

    def __call__(self, *args, **kw) -> Lexical: ...

