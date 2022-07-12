from typing import (Any, Callable, ClassVar, Iterable, Iterator, Mapping,
                    NamedTuple, Set, overload)


from pytableaux.tools import abcs
from pytableaux.typing import _T, _RsetSectKT


class LangCommonMeta(abcs.AbcMeta):...
class LangCommonEnumMeta(abcs.EbcMeta):...
class LexicalAbcMeta(LangCommonMeta):...
class SysPredEnumMeta(LangCommonEnumMeta):
    __members__: Mapping[str, Predicate]
    @overload
    def __iter__(cls) -> Iterator[Predicate]: ...
    @overload
    def __reversed__(cls) -> Iterator[Predicate]: ...
    @overload
    def __getitem__(cls, key) -> Predicate: ...
    @overload
    def __call__(cls, value) -> Predicate: ...
    @overload
    def get(cls, key) -> Predicate: ...
    @overload
    def get(cls, key, default: _T) -> Predicate| _T: ...

class LangCommonEnum(abcs.Ebc, metaclass=LangCommonEnumMeta): ...


class __NotationMeta(LangCommonEnumMeta):
    default: Notation
class _NotationAttrs:
    charsets: set[str]
    default_charset: str
    writers: set[type[LexWriter]]
    DefaultWriter: type[LexWriter]
    rendersets: set[RenderSet]
    Parser: type[Parser]

class Notation(_NotationAttrs, LangCommonEnum, metaclass = __NotationMeta):
    polish: Notation
    standard: Notation
    @classmethod
    def get_common_charsets(cls) -> list[str]: ...

class Marking(LangCommonEnum):
    paren_open: str
    paren_close: str
    whitespace: str
    digit: str
    meta: str
    subscript: str
    tableau: str

class BiCoords(NamedTuple):
    index: int
    subscript: int
    class Sorting(NamedTuple):
        subscript: int
        index: int
    def sorting(self) -> BiCoords.Sorting: ...
    first: ClassVar[BiCoords]
    @staticmethod
    def min_unused(used: Set[BiCoords], maxi: int): ...

class TriCoords(NamedTuple):
    index: int
    subscript: int
    arity: int
    class Sorting(NamedTuple):
        subscript: int
        index: int
        arity: int
    def sorting(self) -> TriCoords.Sorting: ...
    first: ClassVar[TriCoords]

class TableStore(metaclass=LangCommonMeta):
    _instances: ClassVar[dict[Notation, dict[str, TableStore]]]
    default_fetch_key: ClassVar[str]
    @classmethod
    def load(cls: type[_T], notn: Notation, key: str, data: Mapping) -> _T: ...
    @classmethod
    def fetch(cls: type[_T], notn: Notation, key: str = ...) ->_T: ...
    @classmethod
    def available(cls, notn: Notation) -> list[str]: ...
    @classmethod
    def _initcache(cls, notns: Iterable[Notation], builtin: Mapping[Notation, Mapping[str, Mapping]]):...

class RenderSet(TableStore, Mapping[_RsetSectKT, Any]):
    notation: Notation
    renders: Mapping[_RsetSectKT, Callable[..., str]]
    strings: Mapping[_RsetSectKT, str]
    data: Mapping[str, Mapping[_RsetSectKT, Any]]
    keypair: tuple[Notation, str]
    @property
    def charset(self) -> str: ...
    @property
    def fetchkey(self) -> str: ...
    def __init__(self, data: Mapping[str, Any], keypair: tuple[Notation, str]) -> None: ...
    def string(self, ctype: Any, value: Any) -> str: ...

from pytableaux.lang.collect import Argument as Argument
from pytableaux.lang.collect import Predicates as Predicates
from pytableaux.lang.lex import Atomic as Atomic
from pytableaux.lang.lex import Constant as Constant
from pytableaux.lang.lex import Lexical as Lexical
from pytableaux.lang.lex import LexType as LexType
from pytableaux.lang.lex import Operated as Operated
from pytableaux.lang.lex import Operator as Operator
from pytableaux.lang.lex import Parameter as Parameter
from pytableaux.lang.lex import Predicate as Predicate
from pytableaux.lang.lex import Predicated as Predicated
from pytableaux.lang.lex import Quantified as Quantified
from pytableaux.lang.lex import Quantifier as Quantifier
from pytableaux.lang.lex import Sentence as Sentence
from pytableaux.lang.lex import Variable as Variable
from pytableaux.lang.lex import CoordsItem as CoordsItem
from pytableaux.lang.parsing import Parser as Parser
from pytableaux.lang.parsing import ParseTable as ParseTable
from pytableaux.lang.writing import LexWriter as LexWriter


# ParameterSpec = BiCoords
# PredicateSpec = TriCoords
# SpecType: Incomplete
# IdentType = tuple[str, tuple]
# ParameterIdent = tuple[str, BiCoords]
# QuantifierSpec = tuple[str]
# OperatorSpec = tuple[str]
# PredicateRef: Incomplete
# PredicatedSpec = tuple[TriCoords, tuple[ParameterIdent, ...]]
# QuantifiedSpec = tuple[str, BiCoords, IdentType]


#==================================================+
#  Type aliases -- used a runtime with isinstance  |
#==================================================+

# ParameterSpec = BiCoords
# "Parameter spec type (BiCoords)."

# PredicateSpec = TriCoords
# "Predicate spec type (TriCoords)."

# AtomicSpec = BiCoords
# "Atomic spec type (BiCoords)."

#====================+
#  Generic aliases   |
# #====================+

# SpecType = tuple[int|str|tuple, ...]
# "Tuple with integers, strings, or such nested tuples."
# # "tuple[int|str|tuple[int|str], ...]", ... etc.

# IdentType = tuple[str, tuple] #        tuple[str, SpecType]
# "Tuple of (classname, spec)."

# ParameterIdent = tuple[str, BiCoords]
# "Tuple of (classname, (index, subscript))."

# QuantifierSpec = tuple[str]
# "Singleton tuple of quantifier name."

# OperatorSpec = tuple[str]
# "Singleton tuple of operator name."

# PredicateRef = tuple[int, ...] | str
# "Predicate ref type, int tuple or string."

# PredicatedSpec = tuple[TriCoords, tuple[ParameterIdent, ...]]
# "Predicated sentence spec type."

# QuantifiedSpec = tuple[str, BiCoords, IdentType]
# "Quantified sentence spec type."

# OperandsSpec = tuple            #tuple[IdentType, ...]
# "Operands argument type."

# OperatedSpec =  tuple  #    tuple[str, OperandsSpec]
# "Operated sentence spec type."


# ParseTableValue = int|Lexical
# "ParseTable value type."


# PredsItemSpec = PredicateSpec | Predicate
# "Predicates store item spec."

# PredsItemRef  = PredicateRef  | Predicate
# "Predicates store item ref."
