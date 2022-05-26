import builtins
import enum as _enum
from types import FunctionType, MethodType, ModuleType
from typing import (Any, Callable, Generic, Iterable, Iterator, Mapping, MutableSequence, Sequence, Set, TypeVar, ParamSpec,
                    overload)

from _typeshed import SupportsRichComparison as _SupportsRichCompare

from pytableaux.logics import LogicType
from pytableaux.lang import Lexical, Sentence
from pytableaux.proof import filters, Branch, Node, Target, Rule
from pytableaux.tools.linked import LinkSequence, Link
_P = ParamSpec('_P')

_Self = TypeVar('_Self')
_T = TypeVar('_T')
_T1 = TypeVar('_T1')
_KT = TypeVar('_KT')
_VT = TypeVar('_VT')
_RT = TypeVar('_RT')
_LHS = TypeVar('_LHS')
_RHS = TypeVar('_RHS')
_F = TypeVar('_F', bound=Callable)
_TT = TypeVar('_TT', bound=type)
_MapT = TypeVar('_MapT', bound=Mapping)
_EnumT = TypeVar('_EnumT', bound=_enum.Enum)
_SysRulesT = TypeVar('_SysRulesT', bound = LogicType.TabRules)
_RsetSectKT = _enum.Enum|tuple[_enum.Enum, bool]
_RuleT = TypeVar('_RuleT', bound = Rule)
_LnkSeqT = TypeVar('_LnkSeqT', bound = LinkSequence)
_LnkT = TypeVar('_LnkT', bound = Link)
_LexT = TypeVar('_LexT', bound = Lexical)
_SenT = TypeVar('_SenT', bound = Sentence)
_DictT = TypeVar('_DictT', bound = dict)
_SeqT = TypeVar('_SeqT', bound = Sequence)
_MSeqT = TypeVar('_MSeqT', bound = MutableSequence)
_SetT = TypeVar('_SetT', bound = Set)



_LogicModule = LogicType | ModuleType
_LogicLookupKey = ModuleType | str
_HasModuleAttr = MethodType | FunctionType | type
_LogicLocatorRef = _LogicLookupKey | _HasModuleAttr
_NodeTargetsFn = Callable[[Rule, Iterable[Node], Branch], Any]
_NodeTargetsGen = Callable[[Rule, Iterable[Node], Branch], Iterator[Target]]
_NodePredFunc = Callable[[Node], bool]

class _EnumDictType(_enum._EnumDict):
    _member_names: list[str]
    _last_values : list[object]
    _ignore      : list[str]
    _auto_called : bool
    _cls_name    : str

@overload
def iter(__etype: type[_EnumT]) -> Iterator[_EnumT]: ...
@overload
def iter(__it: Iterable[_T]) -> Iterator[_T]: ...
@overload
def iter(__function: Callable[[], _T], __sentinel: Any) -> Iterator[_T]: ...

class _TypeInstDict(dict[type[_VT], _VT]):
    @overload
    def __getitem__(self, key: type[_T]) -> _T: ...
    @overload
    def get(self, key: type[_T]) -> _T: ...
    @overload
    def get(self, key: Any, default: type[_T1]) -> _T1: ...
    @overload
    def copy(self:_T) -> _T: ...
    @overload
    def setdefault(self, key: type[_T], value: Any) -> _T: ...
    @overload
    def pop(self, key: type[_T]) -> _T: ...

class _FiltersDict(_TypeInstDict[filters.NodeCompare]):pass

class property(builtins.property, Generic[_Self, _T]):
    fget: Callable[[_Self], Any] | None
    fset: Callable[[_Self, Any], None] | None
    fdel: Callable[[_Self], None] | None
    @overload
    def __init__(
        self,
        fget: Callable[[_Self], _T] | None = ...,
        fset: Callable[[_Self, Any], None] | None = ...,
        fdel: Callable[[_Self], None] | None = ...,
        doc: str | None = ...,
    ) -> None: ...
    def getter(self, __fget: Callable[[_Self], _T]) -> property[_Self, _T]: ...
    def setter(self, __fset: Callable[[_Self, Any], None]) -> property[_Self, _T]: ...
    def deleter(self, __fdel: Callable[[_Self], None]) -> property[_Self, _T]: ...
    def __get__(self, __obj: _Self, __type: type | None = ...) -> _T: ...
    def __set__(self, __obj: _Self, __value: Any) -> None: ...
    def __delete__(self, __obj: _Self) -> None: ...


