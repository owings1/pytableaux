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
from types import FunctionType, MappingProxyType, new_class
from typing import TYPE_CHECKING, Any, Callable, Literal, Mapping

from pytableaux import __docformat__

__all__ = (
    'abstract',
    'clsns',
    'closure',
    'dxopy',
    'dxopy',
    'EMPTY_MAP',
    'MapProxy',
    'NameTuple',
)

if TYPE_CHECKING:

    from pytableaux.tools.typing import _T

    def classalias(orig: type[_T]) -> Callable[[type], type[_T]]:
        """Decorator factory for class alias for type hinting.

        Usage::

            @classalias(int)
            class integer: pass

        Args:
            orig (type): The reference class.
        
        Returns:
            A decorator that ignores its argument and returns `orig`.
        """
        def d(_: type) -> type[_T]:
            return orig
        return d

MapProxy = MappingProxyType
EMPTY_MAP = MapProxy({})
NOARG = object

def closure(func: Callable[..., _T]) -> _T:
    """Closure decorator calls the argument and returns its return value.
    If the return value is a function, updates its wrapper.
    """
    ret = func()
    if type(ret) is FunctionType:
        functools.update_wrapper(ret, func)
    return ret

def thru(obj: _T) -> _T:
    'Return the argument.'
    return obj

def true(_: Any) -> Literal[True]:
    'Always returns ``True``.'
    return True

def key0(obj: Any) -> Any:
    'Get key/subscript ``0``.'
    return obj[0]

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

def undund(name: str) -> str:
    "Remove dunder from the name."
    if isdund(name):
        return name[2:-2]
    return name

def isint(obj: Any) -> bool:
    'Whether the argument is an :obj:`int` instance'
    return isinstance(obj, int)

def isattrstr(obj: Any) -> bool:
    "Whether the argument is a non-keyword identifier string"
    return (
        isinstance(obj, str) and
        obj.isidentifier() and
        not keyword.iskeyword(obj)
    )

def isstr(obj: Any) -> bool:
    'Whether the argument is an :obj:`str` instance'
    return isinstance(obj, str)

re_boolyes = re.compile(r'^(true|yes|1)$', re.I)
'Regex for string boolean `yes`.'

def sbool(arg: str, /) -> bool:
    "Cast string to boolean, leans toward ``False``."
    return bool(re_boolyes.match(arg))

def getitem(obj, key, default = NOARG, /):
    "Get by subscript similar to :func:`getattr`."
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


@closure
def NameTuple():
    class NameTuple:
        pass
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
    if TYPE_CHECKING:
        class NameTuple: ...

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

    NameTuple = type.__new__(meta, 'NameTuple', (), {dund('doc'): NameTuple.__doc__})

    return NameTuple


@closure
def clsns():
    class clsns:
        pass
        """A base class that produces a useful dict of a class body.

        Decorator usage::

            @clsns
            class ns:
                def spam(): ...
                eggs = 1

            >>> ns
            ... {'spam': <function ns.spam>, 'eggs': 1}

        The original class is stored in `.cls`. The raw mapping is
        copied to `.raw`.

            >>> ns.cls
            ... <class '__main__.ns'>

            >>> ns.raw.keys()
            ... dict_keys(['__module__', 'spam', 'eggs', '__dict__', '__weakref__', '__doc__'])

        Base class usage. A new class is created by removing the first base,
        which must be ``clsns``.:

            class ns(clsns, int):
                eggs = 3

            >>> ns
            ... {'eggs': 3}

            >>> ns.cls.__bases__
            ... (<class 'int'>,)    

        Additional keyword arguments are added to the dict.

            class ns(clsns, bacon = 4):
                eggs = 5

            >>> ns
            ... {'eggs': 5, 'bacon': 4}
        """

    ignore = set(map(dund, ('module', 'qualname', 'doc', 'dict', 'weakref')))

    class Ns(dict):

        __slots__ = 'raw', 'cls'

        raw: Mapping[str, Any]

        def __init__(self, ns: dict, cls = None, /, **kw):
            if isinstance(ns, type):
                if cls: raise TypeError
                cls, ns = ns, ns.__dict__
            self.raw = MapProxy(dict(ns))
            self.cls = cls
            self.update(ns)
            for key in ignore:
                self.pop(key, None)
            if len(kw):
                self.update(kw)
  
    class meta(type):

        def __new__(cls, name, bases, ns: dict, typecls = False, **kw):
            assert bases[0] is clsns
            if typecls:
                c = type(name, bases[1:], dict(ns))
            else:
                c = new_class(name, bases[1:], None, lambda n: n.update(ns))
            return Ns(ns, c, **kw)

        def __call__(self, *args, **kw):
            return Ns(*args, **kw)

    clsns = type.__new__(meta, 'clsns', (), {dund('doc'): clsns.__doc__})

    return clsns

if TYPE_CHECKING:

    @classalias(clsns)
    class clsns: pass

    @classalias(NameTuple)
    class NameTuple: pass

    @classalias(MappingProxyType)
    class MapProxy: pass