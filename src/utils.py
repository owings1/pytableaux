# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
#
# ------------------
#
# pytableaux - utils module
from __future__ import annotations

# from errors import DuplicateKeyError# , IllegalStateError

from builtins import ModuleNotFoundError
# from collections.abc import Mapping#, Sequence
from importlib import import_module
import itertools
from types import ModuleType
# import typing
# from typing import TypeAlias

# import abc
# from collections import deque #, namedtuple
    #  Collection, Hashable, ItemsView, ,\
    # , KeysView, , MutableSet, Sequence, ValuesView
# from copy import copy
# import enum
# from functools import reduce
# from functools import partial
# from pprint import pp
# from time import time
# from inspect import isclass

# Constants
# NOARG = object()
# EmptySet = frozenset()
# from types import MappingProxyType
# CmpFnOper = MappingProxyType({
#     '__lt__': '<',
#     '__le__': '<=',
#     '__gt__': '>',
#     '__ge__': '>=',
#     '__eq__': '==',
#     '__ne__': '!=',
#     '__or__': '|',
#     '__ror__': '|',
#     '__contains__': 'in',
# })


# strtype = str
# LogicRef = ModuleType | str
# IndexType: TypeAlias = int | slice
# IntTuple: TypeAlias = tuple[int, ...]
# enumerated field (0, 'name') etc.
# FieldSeqItem: TypeAlias = tuple[int, str]
# FieldItemSequence: TypeAlias = Sequence[FieldSeqItem]

# T = TypeVar('T')

# P = ParamSpec('P')
# RetType = TypeVar('RetType')


def get_module(ref, package: str = None) -> ModuleType:

    cache = get_module.__dict__
    keys = set()
    ret = {'mod': None}

    def _checkref(ref):
        if ref is None: return
        key = (package, ref)
        try: return bool(_setcache(cache[key]))
        except KeyError: keys.add(key)
        return False

    def _setcache(val):
        for key in keys:
            cache[key] = val
        ret['mod'] = val
        return val

    if hasattr(ref, '__module__'):
        if _checkref(ref.__module__):
            return ret['mod']
        ref = import_module(ref.__module__)

    if isinstance(ref, ModuleType):
        if _checkref(ref.__name__):
            return ret['mod']
        if package is not None and package != getattr(ref, '__package__', None):
            raise ModuleNotFoundError(
                "Module '{0}' not in package '{1}'".format(ref.__name__, package)
            )
        return _setcache(ref)

    if not isinstance(ref, str):
        raise TypeError("ref must be string or module, or have __module__ attribute")

    ref: str = ref.lower()
    if _checkref(ref):
        return ret['mod']
    if package is None:
        return _setcache(import_module(ref))
    pfx = cat(package, '.')
    try:
        return _setcache(import_module(cat(pfx, ref)))
    except ModuleNotFoundError:
        if not ref.startswith(pfx):
            raise
        ref = ref[len(pfx):]
        if _checkref(ref):
            return ret['mod']
        return _setcache(import_module(cat(pfx, ref)))

def get_logic(ref) -> ModuleType:
    """
    Get the logic module from the specified reference.

    Each of following examples returns the :ref:`FDE <FDE>` logic module::

        get_logic('fde')
        get_logic('FDE')
        get_logic('logics.fde')
        get_logic(get_logic('FDE'))


    :param any ref: The logic reference.
    :return: The logic module.
    :rtype: module
    :raises ModuleNotFoundError: if the logic is not found.
    :raises TypeError: if no module name can be determined from ``ref``.
    """
    return get_module(ref, package = 'logics')


def it_drain(it):
    try:
        while True: next(it)
    except StopIteration: pass

def isstr(obj) -> bool:
    return isinstance(obj, str)

def ispow2(n):
    return n != 0 and n & (n-1) == 0

def cat(*args: str) -> str:
    'Concat all argument strings'
    return ''.join(args)

def errstr(err) -> str:
    if isinstance(err, Exception):
        return '%s: %s' % (err.__class__.__name__, err)
    return str(err)

def wrparens(*args: str, parens='()') -> str:
    'Concat all argument strings and wrap in parentheses'
    return cat(parens[0], ''.join(args), parens[-1])

def drepr(d: dict, limit = 10, j: str = ', ', vj = '=', paren = True) -> str:
    lw = drepr.lw
    pairs = (
        cat(str(k), vj, valrepr(v, lw = lw))
        for k,v in itertools.islice(d.items(), limit)
    )
    istr = j.join(pairs)
    if paren:
        return wrparens(istr)
    return istr
# For testing, set this to a LexWriter instance.
drepr.lw = None

def valrepr(v, lw = drepr.lw, **opts) -> str:
    if isinstance(v, str): return v
    if isinstance(v, type): return v.__name__
    if isinstance(v, ModuleType):
        if v.__name__.startswith('logics.'):
            return getattr(v, 'name', v.__name__)
    try: return lw(v)
    except TypeError: pass
    return v.__repr__()

def orepr(obj, _d: dict = None, _ = None, **kw) -> str:
    d = _d if _d is not None else kw
    if isinstance(obj, str):
        oname = obj
    else:
        try: oname = obj.__class__.__qualname__
        except AttributeError: oname = obj.__class__.__name__
    if _ is not None: oname = cat(oname, '.', valrepr(_))
    try:
        if callable(d): d = d()
        dstr = drepr(d, j = ' ', vj = ':', paren = False)
        if dstr:
            return '<%s %s>' % (oname, dstr)
        return '<%s>' % oname
    except Exception as e:
        return '<%s !ERR: %s !>' % (oname, errstr(e))

def wraprepr(obj, inner, **kw) -> str:
    if not isinstance(obj, str):
        obj = obj.__class__.__name__
    return cat(obj, wrparens(inner.__repr__(), **kw))


def renamefn(fnew: T, forig) -> T:
    fnew.__qualname__ = forig.__qualname__
    fnew.__name__ = forig.__name__
    return fnew

from collections.abc import Callable
import typing
KT = typing.TypeVar('KT')
VT = typing.TypeVar('VT')
class KeyCacheFactory(dict[KT, VT]):

    def __getitem__(self, key: KT) -> VT:
        try: return super().__getitem__(key)
        except KeyError:
            val = self[key] = self.__fncreate__(key)
            return val

    def __call__(self, key: KT) -> VT:
        return self[key]

    __slots__ = '__fncreate__',
    __fncreate__: Callable[[KT], VT]

    def __init__(self, fncreate: Callable[[KT], VT]):
        super().__init__()
        self.__fncreate__ = fncreate

# import operator as opr

# def items_from_keys(keys: Iterable[KT], d: dict[KT, VT]) -> Iterator[tuple[KT, VT]]:
#     'Return an iterator of items in ``d`` of keys from ``keys``'
#     return zip(
#         keys,
#         itertools.starmap(
#             opr.getitem,
#             zip(itertools.repeat(d), keys)
#         )
#     )

# methodproxy: AttrCacheFactory[Callable[[str], calls.method]] = \
#     AttrCacheFactory(partial(calls.func, calls.method))

# _ga = object.__getattribute__

# class AttrCacheFactory(Generic[T]):

#     def __getattribute__(self, name: str) -> T:
#         if name.startswith('__'): return _ga(self, name)
#         cache: dict = _ga(self, '__cache__')
#         return cache[name]

#     __slots__ = '__cache__',
#     __cache__: KeyCacheFactory[str, T]

#     def __init__(self, fncreate: Callable[[str], T]):
#         self.__cache__ = KeyCacheFactory(fncreate)

#     def __dir__(self):
#         return list(self.__cache__.keys())

# class Decorators(object):

#     __new__ = None


#     # def setonce(method: Callable[..., RetType]) -> Callable[..., RetType]:
#     #     name, key = __class__._privkey(method)
#     #     def fset(self, val):
#     #         if hasattr(self, key): raise AttributeError(name)
#     #         setattr(self, key, method(self, val))
#     #     return fset

#     def checkstate(**attrs: dict) -> Callable:
#         def fcheckwrap(method: Callable[..., RetType]) -> Callable[..., RetType]:
#             def fcheckstate(self, *args, **kw):
#                 for attr, val in attrs.items():
#                     if getattr(self, attr) != val:
#                         raise IllegalStateError(attr)
#                 return method(self, *args, **kw)
#             return renamefn(fcheckstate, method)
#         return fcheckwrap

#     @staticmethod
#     def _privkey(method) -> tuple[str]:
#         name = method.__name__
#         key = cat('_', __name__, '__lazy_', name)
#         return (name, key)

from collections.abc import Mapping
class CacheNotationData:

    default_fetch_name = 'default'

    @classmethod
    def load(cls, notn, name: str, data: Mapping):
        idx = cls.__getidx(notn)
        if not isinstance(name, str):
            raise TypeError(name, type(name), str)
        if not isinstance(data, Mapping):
            raise TypeError(name, type(data), Mapping)
        if name in idx:
            from errors import DuplicateKeyError
            raise DuplicateKeyError(notn, name, cls)
        idx[name] = cls(data)
        return idx[name]

    @classmethod
    def fetch(cls, notn, name = None):
        if name == None:
            name = cls.default_fetch_name
        idx = cls.__getidx(notn)
        builtin = cls.__builtin[notn]
        return idx.get(name) or cls.load(notn, name, builtin[name])

    @classmethod
    def available(cls, notn):
        return sorted(set(cls.__getidx(notn)).union(cls.__builtin[notn]))

    @classmethod
    def __getidx(cls, notn):
        try:
            return cls.__instances[notn]
        except KeyError:
            raise ValueError("Invalid notation '%s'" % notn)

    @classmethod
    def _initcache(cls, notns, builtin):
        a_ = '_initcache'
        if cls == __class__:
            raise TypeError("Cannot invoke '%s' on %s" % (cls, a_))
        if hasattr(cls, '__builtin'):
            raise AttributeError("%s has no attribute '%s'" % (cls, a_))
        builtin = cls.__builtin = dict(builtin)
        notns = set(notns).union(builtin)
        cls.__instances = {notn: {} for notn in notns}

