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

import functools
import keyword
import re
from abc import abstractmethod as abstract
from types import MappingProxyType, FunctionType
from typing import TYPE_CHECKING, Any, Callable, Iterator, Literal, Mapping

from pytableaux import __docformat__
from pytableaux.tools.typing import T

__all__ = (
    'abstract',
    'classalias',
    'classns',
    'closure',
    'dxopy',
    'dxopy',
    'EMPTY_MAP',
    'MapProxy',
    'NameTuple',
)

def closure(func: Callable[..., T]) -> T:
    """Closure decorator calls the argument and returns its return value.
    If the return value is a function, updates its wrapper.
    """
    ret = func()
    if type(ret) is FunctionType:
        functools.update_wrapper(ret, func)
    return ret

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

    @classalias(MappingProxyType)
    class MapProxy: pass

    class classns: pass

MapProxy = MappingProxyType
EMPTY_MAP = MapProxy({})
NOARG = object
@closure
def classns():

    if TYPE_CHECKING:

        class classns:
            """A base class that produces a dict of the class body.

            Usage::

                class ns(classns):
                    def spam(): ...
            
            The value of ``ns`` will be::

                {'spam': <function ns.spam>}

            The raw mapping, including `'__module__'` and `'__qualname__'`
            are stored in ``ns._raw``.

            Additional keyword arguments are added to the dict.
            """

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
        def __new__(cls, clsname, bases, ns: dict, **kw):
            return nsdict(ns, **kw)

    classns = type.__new__(meta, 'classns', (), {})

    return classns

@closure
def NameTuple():

    if TYPE_CHECKING:
        class NameTuple:
            """A NamedTuple that accepts Generic aliases for type checking.

            Usage::

                class spam(NameTuple, Generic[T]):
                    eggs: T
                    bacon: str
            
            Allows the following::

                class MyList(list[spam[int]]): ...

            At runtime the additional bases are ignored, so it is roughly
            equivalent to::

                class spam(NamedTuple):
                    eggs: T
                    bacon: str
            
            with the addition of `__orig_bases__`, and `__parameters__`
            attributes::

                >>> spam.__orig_bases__
                (<class 'pytableaux.tools.NameTuple'>, typing.Generic[~T])
                >>> spam.__parameters__
                (~T,)
            """

    from types import new_class
    import typing

    class meta(type):

        __call__ = staticmethod(typing.NamedTuple)

        @staticmethod
        def __prepare__(clsname, bases):
            return dict(__orig_bases__ = bases)

        def __new__(cls, clsname: str, bases, ns, **kw):
            assert bases[0] is NameTuple
            if (origs := ns['__orig_bases__'][1:]):
                for a, b in zip(origs, bases[1:]):
                    if b is typing.Generic:
                        ns['__parameters__'] = a.__parameters__
                        break
                new_class(clsname, origs, kw)
            return typing.NamedTupleMeta(clsname, (typing._NamedTuple,), ns)

    NameTuple = type.__new__(meta, 'NameTuple', (), {})

    return NameTuple

@classalias(NameTuple)
class NameTuple: pass


def thru(obj: T) -> T:
    'Return the argument.'
    return obj

def true(_: Any) -> Literal[True]:
    'Always returns ``True``.'
    return True

def false(_: Any) -> Literal[False]:
    'Always returns ``False``.'
    return False

def key0(obj: Any) -> Any:
    'Get key/subscript ``0``.'
    return obj[0]

def key1(obj: Any) -> Any:
    'Get key/subscript ``1``.'
    return obj[1]

def noinit(slf: Any = None):
    'Raise `TypeError`.'
    raise TypeError

def dund(name:str) -> str:
    "Convert name to dunder format."
    return name if isdund(name) else f'__{name}__'

def isdund(name: str) -> bool:
    'Whether the string is a dunder name string.'
    return (
        len(name) > 4 and
        name[:2] == name[-2:] == '__' and
        name[2] != '_' and
        name[-3] != '_'
    )

def undund(name:str) -> str:
    if isdund(name):
        return name[2:-2]
    return name

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

def getitem(obj, key, default = NOARG, /):
    try:
        return obj[key]
    except (KeyError, IndexError):
        if default is NOARG:
            raise
        return default

@closure
def dxopy():

    def api(a: Mapping, proxy = False, /, ) -> Mapping:
        """Deep map copy, recursive for mapping values.
        Safe for circular reference. Second arg supports
        deep proxy.
        """
        if proxy:
            wrap = MapProxy
        else:
            wrap = thru
        return runner(a, {}, wrap, runner)

    def runner(a: Mapping, memo: dict, wrap, recur):
        if (i := id(a)) in memo:
            return a
        memo[i] = True
        m = wrap({
            key: recur(value, memo, wrap, recur)
                if isinstance(value, Mapping)
                else value
            for key, value in a.items()
        })
        memo[id(m)] = True
        return m

    return api