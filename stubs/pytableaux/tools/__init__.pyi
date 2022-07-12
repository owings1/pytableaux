from abc import abstractmethod as abstract
from types import MappingProxyType as MapProxy
from typing import (Any, Callable, Concatenate, Generator, Generic, Iterable,
                    Iterator, Mapping, Optional, Pattern, overload)

from pytableaux.typing import _F, _KT, _P, _RT, _T, _VT, _MapT, _Self, property

pass
from pytableaux.tools.abcs import AbcMeta
from pytableaux.tools.hybrids import EMPTY_QSET as EMPTY_QSET
from pytableaux.tools.hybrids import qset as qset
from pytableaux.tools.hybrids import qsetf as qsetf
from pytableaux.tools.mappings import DequeCache as DequeCache
from pytableaux.tools.mappings import dmap as dmap
from pytableaux.tools.mappings import dmapattr as dmapattr
from pytableaux.tools.mappings import dmapns as dmapns
from pytableaux.tools.sequences import EMPTY_SEQ as EMPTY_SEQ
from pytableaux.tools.sets import EMPTY_SET as EMPTY_SET
from pytableaux.tools.sets import SetView as SetView
from pytableaux.tools.sets import setf as setf

EMPTY_MAP: Mapping
re_boolyes: Pattern

def closure(func: Callable[..., _T]) -> _T: ...
def dund(name:str) -> str:...
def dxopy(a: Mapping[_KT, _VT], proxy = ..., /, ) -> dict[_KT, _VT]:...
def getitem(obj, key, default = ..., /):...
def isattrstr(obj: Any) -> bool: ...
def for_defaults(defaults: Mapping[_KT, _VT], override: Optional[Mapping], /) -> dict[_KT, _VT]: ...
def isdund(name: str) -> bool:...
def isint(obj: Any) -> bool:...
def isstr(obj: Any) -> bool:...
def itemsiter(obj, /, **kw) -> Iterator[tuple]:...
def key0(obj: Any) -> Any: ...
def maxceil(ceil:_T, it: Iterable) -> _T:...
def minfloor(floor:_T, it: Iterable) -> _T:...
def sbool(arg: str, /) -> bool: ...
def thru(obj: _T) -> _T:...
def true(_: Any) ->bool:...
def undund(name: str) -> str:...
def select_fget(obj: Any) -> Callable[[Any, Any, Optional[Any]], Any]:...
def substitute(coll:_T, old_value:Any, new_value:Any) -> _T:...


class BaseMember(Generic[_T], metaclass = AbcMeta):
    def __set_name__(self, owner: _T, name): str: ...
    def sethook(self, owner: type, name: str) -> None: ...
    @property
    def owner(self) -> _T: ...
    @property
    def name(self) -> str: ...

class membr(BaseMember[_T], Generic[_T, _RT]):
    owner: _T
    cbak: tuple[Callable[..., _RT], tuple, dict]
    def __init__(self, cb: Callable[..., _RT], *args, **kw) -> None: ...
    def __call__(self) -> _RT: ...
    @classmethod
    def defer(cls, fdefer: Callable[Concatenate[membr[_T, _RT], _P], _RT]) -> Callable[_P, _RT]: ...

class operd:
    def __new__(cls, *args, **kw): ...
    class Base(BaseMember, Callable):
        oper: Callable
        wrap: wraps
        def __init__(self, oper: Callable, info: Any = ...) -> None: ...
    class apply(Base):
        def __call__(self, info: Any = ...): ...
    class reduce(Base):
        inout: tuple[Callable, Callable]
        def __init__(self, oper: Callable, info: Any = ..., freturn: Callable|str = ..., finit: Callable|str = ...) -> None: ...
        def __call__(self, info: Callable|Mapping = ...): ...
    @overload
    @staticmethod
    def repeat(oper: Callable, info: _F) -> _F: ...
    @overload
    @staticmethod
    def repeat(oper: _F) -> _F: ...

class wraps(dict[str, str]):
    original: Callable|Mapping
    only: set[str]
    def __init__(self, original: Callable|Mapping = ..., only=..., exclude=..., **kw) -> None: ...
    def __call__(self, fout: _F) -> _F: ...
    def read(self, obj) -> Generator[tuple[str, Any], None, None]: ...
    def write(self, obj: _F) -> _F: ...
    def update(self, obj: object = ..., **kw): ...
    def setdefault(self, key, value): ...
    def __setitem__(self, key, value) -> None: ...

class raisr(BaseMember):
    Error: type[Exception]
    wrap: wraps
    def __init__(self, Error: type[Exception]) -> None: ...
    def __call__(self, original: Callable|Mapping | None = ...): ...

class lazy:
    def __new__(cls, *args, **kw) -> lazy.get: ...
    class get(BaseMember, Generic[_F], metaclass=AbcMeta):
        key: str
        format: Callable[[str], str]
        @overload
        def __new__(cls, method: _F) -> _F: ...
        @overload
        def __new__(cls, key: str|None, method: _F) -> _F: ...
        @overload
        def __new__(cls, key: str|None) -> lazy.get: ...
        @overload
        def __new__(cls) -> lazy.get: ...
        def __call__(self, method: _F) -> _F: ...
    class prop(get[type[_Self]]):
        @property
        def propclass(self) -> type[property]: ...
        @overload
        def __new__(cls, func: Callable[[_Self], _T]) -> property[_Self, _T]: ...
        def __call__(self, method: Callable[[_Self], _T]) -> property[_Self, _T]: ...
    class dynca(prop):
        @property
        def propclass(self) -> type[property]: ...

class NoSetAttr(BaseMember):
    enabled: bool
    defaults: dict[str, Any]
    cache: dict[Any, dict]
    def __init__(self, *, enabled: bool = ..., **defaults) -> None: ...
    def __call__(self, base: type, **opts): ...
    def cached(func: _F) -> _F: ...
