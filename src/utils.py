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

from errors import instcheck, DuplicateKeyError, IllegalStateError

import abc
from builtins import ModuleNotFoundError
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
import enum
from functools import reduce
from importlib import import_module
from inspect import isclass
from itertools import islice, repeat, starmap
import operator as opr
from types import MappingProxyType, ModuleType
import typing
from typing import Any, Annotated, DefaultDict, \
    Generic, NamedTuple, \
    ParamSpec, TypeAlias, TypeVar, \
    abstractmethod

# from collections import deque #, namedtuple
    #  Collection, Hashable, ItemsView, ,\
    # , KeysView, , MutableSet, Sequence, ValuesView
# from copy import copy
# from functools import partial
# from pprint import pp
# from time import time

# Constants
NOARG = object()
# EmptySet = frozenset()
CmpFnOper = MappingProxyType({
    '__lt__': '<',
    '__le__': '<=',
    '__gt__': '>',
    '__ge__': '>=',
    '__eq__': '==',
    '__ne__': '!=',
    '__or__': '|',
    '__ror__': '|',
    '__contains__': 'in',
})


strtype = str
LogicRef = ModuleType | str
IndexType: TypeAlias = int | slice
IntTuple: TypeAlias = tuple[int, ...]
# enumerated field (0, 'name') etc.
FieldSeqItem: TypeAlias = tuple[int, str]
FieldItemSequence: TypeAlias = Sequence[FieldSeqItem]

T = TypeVar('T')
KT = TypeVar('KT')
VT = TypeVar('VT')
P = ParamSpec('P')
RetType = TypeVar('RetType')


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


def it_drain(it: Iterable):
    try:
        while True: next(it)
    except StopIteration: pass

def items_from_keys(keys: Iterable[KT], d: dict[KT, VT]) -> Iterator[tuple[KT, VT]]:
    'Return an iterator of items in ``d`` of keys from ``keys``'
    return zip(
        keys,
        starmap(
            opr.getitem,
            zip(repeat(d), keys)
        )
    )

# def instcheck(obj, classinfo: type[T]) -> T:
#     if not isinstance(obj, classinfo):
#         raise TypeError(obj)
#     return obj

def isstr(obj) -> bool:
    return isinstance(obj, strtype)

def ispow2(n):
    return n != 0 and n & (n-1) == 0

def subclscheck(cls: type, typeinfo: T) -> T:
    if not issubclass(cls, typeinfo):
        raise TypeError(cls, typeinfo)
    return cls

def notsubclscheck(cls: type, typeinfo):
    if issubclass(cls, typeinfo):
        raise TypeError(cls, typeinfo)
    return cls

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
        for k,v in islice(d.items(), limit)
    )
    istr = j.join(pairs)
    if paren:
        return wrparens(istr)
    return istr
# For testing, set this to a LexWriter instance.
drepr.lw = None

def valrepr(v, lw = drepr.lw, **opts) -> str:
    if isinstance(v, str): return v
    if isclass(v): return v.__name__
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


class MetaFlag(enum.Flag):
    blank  = 0
    nsinit = 4
    temp   = 8
    nsclean = nsinit | temp
    

class AttrNote(NamedTuple):

    cls: type
    attr: str

    otype: type
    flag: MetaFlag
    merger: Any = None
    endtype: type = None
    extra: list = []

    @classmethod
    def forclass(cls, Class: type) -> dict[str, AttrNote]:
        annot = typing.get_type_hints(Class, include_extras = True)
        notes = (
            cls(Class, attr, *vals[0:4], vals[4:])
            for attr, vals in (
                (k, typing.get_args(v))
                for k, v in annot.items()
                if typing.get_origin(v) is Annotated
            )
        )
        return dict((n.attr,n) for n in notes)

class ABCMeta(abc.ABCMeta):

    _metaflag_attr = '_metaflag'

    def __new__(cls, clsname, bases, ns: dict, **kw):
        cls.nsinit(ns, bases, **kw)
        Class = super().__new__(cls, clsname, bases, ns, **kw)
        cls.nsclean(Class, ns, bases, **kw)
        return Class

    @staticmethod
    def nsinit(ns: dict, bases, /, **kw):
        mfattr = __class__._metaflag_attr
        # kit = list(attrs)
        # for v in (attrs[k] for k in kit):
        for v in tuple(ns.values()):
            # mf = getattr(v, attrname, MetaFlag.blank)
            if MetaFlag.nsinit in getattr(v, mfattr, MetaFlag.blank):
                instcheck(v, Callable)(ns, bases, **kw)

    @staticmethod
    def nsclean(Class, ns: dict, bases, deleter = delattr, **kw):
        attrname = __class__._metaflag_attr
        kit = ns.keys()
        for k, v in ((k,ns[k]) for k in kit):
            mf = getattr(v, attrname, MetaFlag.blank)
            if mf is not mf.blank and mf in MetaFlag.nsclean:
                deleter(Class, k)
    
    @staticmethod
    def basesmap(bases):
        bmap = DefaultDict(list)
        for b in bases: bmap[b.__name__].append(b)
        return bmap

    @staticmethod
    def annotated_attrs(obj):
        annot = typing.get_type_hints(obj, include_extras = True)
        return {
            k: typing.get_args(v)
            for k,v in annot.items()
            if typing.get_origin(v) is Annotated
        }

    @staticmethod
    def merge_mroattr(
        subcls: type,
        attr: str,
        supcls: type = None,
        oper: Callable = opr.or_
    ) -> dict:
        return reduce(oper, (
            getattr(c, attr)
            for c in reversed(subcls.mro())
            if issubclass(c, supcls or subcls)
        ))

    @staticmethod
    def check_mrodict(mro: Sequence[type], names: Sequence[str]):
        if len(names) and not len(mro):
            return NotImplemented
        for name in names:
            for base in mro:
                if name in base.__dict__:
                    if base.__dict__[name] is None:
                        return NotImplemented
                    break
        return True


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

_ga = object.__getattribute__

class AttrCacheFactory(Generic[T]):

    def __getattribute__(self, name: str) -> T:
        if name.startswith('__'): return _ga(self, name)
        cache: dict = _ga(self, '__cache__')
        return cache[name]

    __slots__ = '__cache__',
    __cache__: KeyCacheFactory[str, T]

    def __init__(self, fncreate: Callable[[str], T]):
        self.__cache__ = KeyCacheFactory(fncreate)

    def __dir__(self):
        return list(self.__cache__.keys())

class Decorators(object):

    __new__ = None


    def setonce(method: Callable[..., RetType]) -> Callable[..., RetType]:
        name, key = __class__._privkey(method)
        def fset(self, val):
            if hasattr(self, key): raise AttributeError(name)
            setattr(self, key, method(self, val))
        return fset

    def checkstate(**attrs: dict) -> Callable:
        def fcheckwrap(method: Callable[..., RetType]) -> Callable[..., RetType]:
            def fcheckstate(self, *args, **kw):
                for attr, val in attrs.items():
                    if getattr(self, attr) != val:
                        raise IllegalStateError(attr)
                return method(self, *args, **kw)
            return renamefn(fcheckstate, method)
        return fcheckwrap

    @staticmethod
    def _privkey(method) -> tuple[str]:
        name = method.__name__
        key = cat('_', __name__, '__lazy_', name)
        return (name, key)

class BiCoords(NamedTuple):
    index     : int
    subscript : int
 
    class Sorting(NamedTuple):
        subscript : int
        index     : int

    def sorting(self) -> BiCoords.Sorting:
        return self.Sorting(self.subscript, self.index)

    first = (0, 0)

BiCoords.first = BiCoords._make(BiCoords.first)

class TriCoords(NamedTuple):
    index     : int
    subscript : int
    arity     : int

    class Sorting(NamedTuple):
        subscript : int
        index     : int
        arity     : int

    def sorting(self) -> TriCoords.Sorting:
        return self.Sorting(self.subscript, self.index, self.arity)

    first = (0, 0, 1)

TriCoords.first = TriCoords._make(TriCoords.first)


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

class StopWatch:
    'Millisecond stopwatch.'

    __slots__ = '_start_time', '_accum', '_running', 'count'

    def __init__(self, started = False):
        self._start_time = None
        self._accum = 0
        self.count = 0
        self._running = False
        if started:
            self.start()

    def start(self):
        'Start the StopWatch. Raises IllegalStateError if already started.'
        if self._running:
            raise IllegalStateError('StopWatch already started.')
        self.count += 1
        self._running = True
        self._start_time = self._nowms()

    def stop(self):
        'Stop the StopWatch. Raises IllegalStateError if already stopped.'
        if not self._running:
            raise IllegalStateError('StopWatch already stopped.')
        self._running = False
        self._accum += self._nowms() - self._start_time

    def reset(self):
        'Reset elapsed to 0.'
        self._accum = 0
        if self._running:
            self._start_time = self._nowms()

    @property
    def elapsed(self) -> int:
        'Elapsed milliseconds.'
        if self._running:
            return self._accum + (self._nowms() - self._start_time)
        return self._accum

    @property
    def elapsed_avg(self) -> float:
        'Elapsed milliseconds / count.'
        try:
            return self.elapsed / self.count
        except ZeroDivisionError:
            return 0

    @property
    def running(self) -> bool:
        'Whether the StopWatch is running.'
        return self._running

    def __repr__(self):
        return wraprepr(self, self.elapsed)

    def __float__(self):
        return float(self.elapsed)

    def __int__(self):
        return self.elapsed

    def __str__(self):
        return str(self.elapsed)

    def __enter__(self) -> StopWatch:
        'Start/stop context entry.'
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        if self._running:
            self.stop()

    from time import time as _time
    @staticmethod
    def _nowms(time = _time) -> int:
        'Current time in milliseconds'
        return int(round(time() * 1000))
    del(_time)
