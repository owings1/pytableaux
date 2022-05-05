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

import keyword
import re
from abc import abstractmethod as abstract
from types import FunctionType, MappingProxyType
from typing import TYPE_CHECKING, Any, Callable, Iterator, Literal, Mapping

from pytableaux import __docformat__
from pytableaux.tools.typing import KT, TT, VT, T

__all__ = (
    'abstract',
    'closure',
    'MapProxy',
    'static',
    'classns',
    'classalias',
)
def closure(func: Callable[..., T]) -> T:
    'Closure decorator calls the argument and returns its return value.'
    return func()

def classalias(orig: type[T]) -> Callable[[type], type[T]]:
    """Decorator factory for class alias for type hinting.

    Usage::

        @classalias(int)
        class integer: pass

    Args:
        orig (type): The reference class.
    
    Returns:
        A decorator that ignores its argument and returns `orig`.
    """
    def d(_: type) -> type[T]:
        return orig
    return d

if TYPE_CHECKING:
    class classns: pass

@closure
def classns():

    ignore = {'__module__', '__qualname__'}

    class nsdict(dict):
        __slots__ = '_raw',
        _raw: Mapping[str, Any]
        def __init__(self, ns: dict, **kw):
            self._raw = MapProxy(ns)
            self.update(ns)
            for key in ignore:
                self.pop(key, None)
            if len(kw):
                self.update(kw)

    class meta(type):
        def _new(cls, clsname: str, bases: tuple[type, ...], ns: dict, **kw):
            # if setup:
            #     return super().__new__(cls, clsname, bases, ns)
            return nsdict(ns, **kw)

    setup = True

    class classns(metaclass = meta):
        """A base class that produces a dict of the class body.

        Usage::

            class ns(clasns):
                def spam(): ...
        
        The value of ``ns`` will be::

            {'spam': <function ns.spam>}

        The raw mapping, including `'__module__'` and `'__qualname__'`
        are stored in ``ns._raw``.

        Additional keyword arguments are added to the dict.
        """
        __slots__ = ()

    meta.__new__ = meta._new
    del(meta._new)

    setup = False

    return classns

class MapProxy(Mapping[KT, VT]):
    'Cast to a proxy if not already.'
    EMPTY_MAP = MappingProxyType({})

    def __new__(cls, mapping: Mapping[KT, VT] = None,/, **kw) -> MapProxy[KT, VT]:

        if mapping is None:
            if len(kw):
                mapping = kw
            else:
                return cls.EMPTY_MAP # type: ignore
        elif not isinstance(mapping, Mapping):
            mapping = dict(mapping, **kw)
        elif len(kw):
            raise TypeError("Cannot specify kwargs and mapping")
        if isinstance(mapping, MappingProxyType):
            return mapping # type: ignore
        return MappingProxyType(mapping) # type: ignore

def static(cls: TT, /) -> TT:
    'Static class decorator, and wrapper around staticmethod'

    if not isinstance(cls, type):
        raise TypeError(cls)

    ns = cls.__dict__

    for name, member in ns.items():
        if isdund(name) or not isinstance(member, FunctionType):
            continue
        setattr(cls, name, staticmethod(member))

    if '__new__' not in ns:
        cls.__new__ = thru # type: ignore

    if '__init__' not in ns:
        cls.__init__ = noinit

    return cls

def thru(obj: T) -> T:
    'Return the argument.'
    return obj

def true(_: Any) -> Literal[True]:
    'Always returns ``True``.'
    return True

def false(_: Any) -> Literal[False]:
    'Always returns ``False``.'
    return False

# def notnone(obj: Any) -> bool:
#     'Wether `obj` is not `None`.'
#     return obj is not None

def key0(obj: Any) -> Any:
    'Get key/subscript ``0``.'
    return obj[0]

def noinit(slf: Any = None):
    'Raise `TypeError`.'
    raise TypeError

def dund(*names:str) -> Iterator[str]:
    "Convert names to dunder format."
    return map('__{}__'.format, names)

def isdund(name: str) -> bool:
    'Whether the string is a dunder name string.'
    return (
        len(name) > 4 and
        name[:2] == name[-2:] == '__' and
        name[2] != '_' and
        name[-3] != '_'
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

def isstr(obj: Any) -> bool:
    'Whether the argument is an ``str`` instance'
    return isinstance(obj, str)

re_boolyes = re.compile(r'^(true|yes|1)$', re.I)
'Regex for string boolean `yes`.'

def sbool(arg: str, /) -> bool:
    "Cast string to boolean, leans toward ``False``."
    return bool(re_boolyes.match(arg))
