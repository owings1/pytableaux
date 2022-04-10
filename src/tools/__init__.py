from __future__ import annotations

from types import MappingProxyType as _MapProxy
from typing import Any, Callable, Mapping
from tools.typing import KT, T, VT

from abc import abstractmethod as abstract

def closure(func: Callable[..., T]) -> T:
    return func()

class MapProxy(Mapping[KT, VT]):
    'Cast to a proxy if not already.'
    EMPTY_MAP = _MapProxy({})

    def __new__(cls, mapping: Mapping[KT, VT] = None) -> MapProxy[KT, VT]:

        if mapping is None:
            return cls.EMPTY_MAP # type: ignore
        if isinstance(mapping, _MapProxy):
            return mapping # type: ignore
        if not isinstance(mapping, Mapping):
            mapping = dict(mapping)
        return _MapProxy(mapping) # type: ignore



