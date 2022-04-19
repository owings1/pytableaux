# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
pytableaux.tools
----------------

"""
from __future__ import annotations

__docformat__ = 'google'
__all__ = (
    'abstract',
    'closure',
    'MapProxy',
    'static',
)

import keyword
from abc import abstractmethod as abstract
from types import FunctionType, MappingProxyType as _MapProxy
from typing import Any, Callable, Literal, Mapping, overload

from pytableaux.tools.typing import KT, TT, VT, T

def closure(func: Callable[..., T]) -> T:
    'Closure decorator calls the argument and returns its return value.'
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

def thru(obj: T) -> T:
    'Return the argument.'
    return obj

def true(obj: Any) -> Literal[True]:
    'Always returns ``True``.'
    return True

def false(obj: Any) -> Literal[False]:
    'Always returns ``False``.'
    return False

def key0(obj: Any) -> Any:
    'Get key/subscript ``0``.'
    return obj[0]

def isdund(name: str) -> bool:
    'Whether the string is a dunder name string.'
    return (
        len(name) > 4 and name[:2] == name[-2:] == '__' and
        name[2] != '_' and name[-3] != '_'
    )

def isint(obj: Any) -> bool:
    'Whether the argument is an ``int`` instance'
    return isinstance(obj, int)

def isattrstr(obj: Any) -> bool:
    "Whether ``obj`` is a non-keyword identifier string."
    return (
        isinstance(obj, str) and
        obj.isidentifier() and
        not keyword.iskeyword(obj)
    )

