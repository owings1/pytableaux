from collections.abc import Set
from types import MappingProxyType as MapProxy
from typing import Any, Generic, Iterable, Mapping, overload

from pytableaux.tools import abcs
from pytableaux.typing import _KT, _T, _VT, _MapT, _Self, _SetT

class MapCover(Mapping[_KT, _VT], abcs.Copyable):
    def __init__(self, mapping: Mapping, /) -> None:...

class KeySetAttr:
    def update(self, it: Iterable = ..., /, **kw) -> None: ...
    @classmethod
    def _keyattr_ok(cls, name: str) -> bool:...

class dictattr(KeySetAttr, dict[_KT, _VT]):...

class dictns(dictattr[_KT, _VT]):...



class DequeCache(Generic[_VT]):
    @property
    def maxlen(self) -> int:...
    def __init__(self, maxlen:int|None = ...) -> None: ...

