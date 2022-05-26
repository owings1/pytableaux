import abc as _abc
import enum as _enum
from typing import (Any, Callable, Collection, Iterable, Iterator, Reversible,
                    Mapping, Sequence, Set, SupportsIndex, overload)

from pytableaux.tools.hooks import _ProviderInfo as _HookProviderInfo
from pytableaux.tools.hooks import _UserInfo as _HookUserInfo
from pytableaux.typing import _F, _KT, _RT, _T, _TT, _EnumDictType, _EnumT
from enum import auto as eauto

class AbcMeta(_abc.ABCMeta):
    def __new__(cls, clsname: str, bases: tuple[type, ...], ns: dict, *, hooks: _HookUserInfo = ..., skiphooks: bool = ..., skipflags: bool = ..., hookinfo: _HookProviderInfo = ..., **kw): ...
    def hook(cls, *hooks: str, attr: str = ...) -> Callable[[_F], _F]: ...
class Abc(metaclass=AbcMeta): ...
class Copyable(metaclass=AbcMeta):
    def copy(self:_T) -> _T: ...
    def __copy__(self:_T) -> _T: ...

def annotated_attrs(obj) -> dict[str, tuple]:...
def check_mrodict(mro: Sequence[type], *names: str):...
def clsafter(Class: _TT, ns: Mapping = ..., /, skipflags: bool = ..., deleter: Callable[[type, str], None] = ...) -> _TT:...
def em_mixins(Class: type[_enum.Enum]) -> tuple[type, ...]:...
def hookable(*hooks: str, attr:str = ...) -> Callable[[_F], _F]:...
def is_enumcls(obj: Any) -> bool:...
def isabstract(obj) -> bool:...
def merge_attr(obj, name: str, it:Iterable = ..., /, *, setter: Callable[[type, str, Any], Any] = ..., **kw):...
def merged_attr(name: str, it: Iterable = None, /, *, oper: Callable[[Any, Any], _RT] = ..., initial:_RT|Any = ..., default:_RT|Any = ..., transform: Callable[[Any], _RT] = ..., getitem: bool = ..., **iteropts) -> _RT:...
def mroiter(cls: type, *, supcls: type[_T]|tuple[type, ...] = ..., mcls: type|tuple[type, ...] = ..., reverse: bool = ..., start: SupportsIndex = ..., stop: SupportsIndex = ...) -> Iterator[type[_T]]:...
def nsinit(ns: dict, bases: tuple[type, ...], /, skipflags: bool = ...) -> None:...

def _em_rebase(oldcls: type[_EnumT], *bases: type, ns: Mapping = ..., metaclass: type = ..., **kw) -> type[_EnumT]:...

class EnumLookup(Mapping[_KT, _EnumT], Reversible[_KT]):
    def __init__(self, Owner: type[_EnumT], build: bool = ...) -> None: ...
    def build(self) -> None: ...
    def pseudo(self, member: _EnumT) -> _EnumT: ...
    def _asdict(self) -> dict[_KT, _EnumT]: ...
    @classmethod
    def _makemap(cls, Owner: type[_EnumT], keyfuncs: Collection[Callable], /) -> dict[_KT, _EnumT]:...
    @classmethod
    def _seqmap(cls, members: Sequence[_EnumT], keyfuncs: Collection[Callable], /) -> dict[_KT, _EnumT]:...
    @classmethod
    def _pseudomap(cls, pseudos: Collection[_EnumT], /) -> dict[_KT, _EnumT]:...
    @classmethod
    def _check_pseudo(cls, pseudo: _enum.Enum, Owner: type[_enum.Enum], /) -> set[_KT]:...
    @classmethod
    def _get_keyfuncs(cls, Owner: type[_enum.Enum], /) -> set[Callable]:...
    @staticmethod
    def _pseudo_keys(pseudo: _enum.Enum, /) -> set[_KT]:...
    @staticmethod
    def _default_keys(member: _enum.Enum, /) -> set[_KT]:...

class EbcMeta(_enum.EnumMeta):
    _mixin_bases_: tuple[type, ...]
    _lookup: EnumLookup
    _seq: Sequence
    _member_names_: Sequence[str]
    __members__: Mapping[str, _EnumT]

    def __new__(cls, clsname: str, bases: tuple[type, ...], ns: _EnumDictType, *, skipflags: bool = ..., idxbuild: bool = ..., skipabcm: bool = ..., **kw): ...
    @overload
    def __call__(cls: EbcMeta|type[_EnumT], value: Any) -> _EnumT: ...
    @overload
    def __call__(cls: EbcMeta|type[_EnumT], value: str, names: Iterable, **kw) -> type[_EnumT]: ...
    def __getitem__(cls: EbcMeta|type[_EnumT], key: Any) -> _EnumT: ...
    @overload
    def get(cls: EbcMeta|type[_EnumT], key: Any) -> _EnumT: ...
    @overload
    def get(cls: EbcMeta|type[_EnumT], key: Any, default: _T) -> _EnumT|_T: ...
    def __iter__(cls: EbcMeta|type[_EnumT]) -> Iterator[_EnumT]: ...
    def __reversed__(cls: EbcMeta|type[_EnumT]) -> Iterator[_EnumT]: ...
    @property
    @overload
    def _seq(cls: EbcMeta|type[_EnumT]) -> Sequence[_EnumT]: ...
    @property
    @overload
    def _lookup(cls: EbcMeta|type[_EnumT]) -> EnumLookup[_EnumT]: ...
    @property
    @overload
    def _member_map_(cls: EbcMeta|type[_EnumT]) -> Mapping[str, _EnumT]: ...
    @property
    @overload
    def __members__(cls: EbcMeta|type[_EnumT]) -> Mapping[str, _EnumT]: ...

class Ebc(_enum.Enum, metaclass=EbcMeta):
    name: str
    value: Any
    def __copy__(self:_T) -> _T: ...
    def __deepcopy__(self:_T, memo:Any) ->_T: ...
    @classmethod
    def _on_init(cls:type[_EnumT], subcls:type[_EnumT]) -> None:...
    @classmethod
    def _member_keys(cls:type[_EnumT], member: _EnumT) -> Set[Any]: ...
    @classmethod
    def _after_init(cls) -> None:...

class Eset(frozenset, _enum.Enum):
    Empty: frozenset
    member_key_methods: frozenset
    reserve_names: frozenset
    hook_methods: frozenset
    clean_methods: frozenset

class Astr(str, Ebc):
    flag: str
    hookuser: str
    hookinfo: str

class FlagEnum(_enum.Flag, Ebc):
    name: str|None
    value: int
    def __invert__(self:_EnumT) -> _EnumT: ...

class abcf(FlagEnum):
    blank: int
    before: int
    temp: int
    after: int
    static: int
    inherit: int
    def __call__(self, obj: _F) -> _F: ...
    @classmethod
    def read(cls, obj:Any, default: abcf|SupportsIndex = ..., *, attr: str = ...) -> abcf: ...
    @classmethod
    def save(cls, obj: _F, value: abcf|SupportsIndex, *, attr: str = ...) -> _F: ...

class IntEnum(int, Ebc): ...
class IntFlag(int, FlagEnum): ...
