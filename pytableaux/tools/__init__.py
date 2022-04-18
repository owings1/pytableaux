from __future__ import annotations

__all__ = (
    'abstract',
    'closure',
    'MapProxy',
    'static',
)

import keyword
from types import FunctionType, MappingProxyType as _MapProxy
from typing import Any, Callable, Literal, Mapping, overload
from pytableaux.tools.typing import KT, T, TT, VT

from abc import abstractmethod as abstract

def thru(obj: T) -> T:
    'Return the argument.'
    return obj

def true(obj: Any) -> Literal[True]:
    'Always returns ``True``.'
    return True

def false(obj: Any) -> Literal[False]:
    'Always returns ``False``.'
    return False

def closure(func: Callable[..., T]) -> T:
    return func()

@overload
def static(cls: TT, /) -> TT: ...

@overload
def static(meth: Callable[..., T], /) -> staticmethod[T]: ...

def static(cls, /):
    'Static class decorator, and wrapper around staticmethod'

    if not isinstance(cls, type):
        if isinstance(cls, (classmethod, staticmethod)):
            return cls
        return staticmethod(cls)

    ns = cls.__dict__

    for name, member in ns.items():
        if isdund(name) or not isinstance(member, FunctionType):
            continue
        setattr(cls, name, staticmethod(member))

    if '__new__' not in ns:
        cls.__new__ = thru # type: ignore

    if '__init__' not in ns:
        def finit(self): raise TypeError
        cls.__init__ = finit

    return cls

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

def isdund(name: str) -> bool:
    return (
        len(name) > 4 and name[:2] == name[-2:] == '__' and
        name[2] != '_' and name[-3] != '_'
    )

def isattrstr(obj: Any) -> bool:
    "Whether ``obj`` is a non-keyworkd identifier string."
    return (
        isinstance(obj, str) and
        obj.isidentifier() and
        not keyword.iskeyword(obj)
    )