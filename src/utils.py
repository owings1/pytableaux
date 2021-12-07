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

from errors import DuplicateKeyError, IllegalStateError

from builtins import ModuleNotFoundError
from collections import deque #, namedtuple
from collections.abc import Callable, Collection, Hashable, ItemsView, Iterable,\
    Iterator, KeysView, Mapping, MutableSet, Sequence, ValuesView
from copy import copy
import enum
from importlib import import_module
from inspect import isclass
from itertools import chain, islice
from time import time
from types import MappingProxyType, ModuleType
import typing
from typing import Any, Annotated, NamedTuple, TypeVar, Union, abstractmethod, cast

# from functools import partial
# from operator import is_not
# from pprint import pp

# Constants
EmptySet = frozenset()
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

# Types
strtype = str
LogicRef = Union[ModuleType, str]
IndexTypes = (int, slice)
IndexType = Union[int, slice]

T = TypeVar('T')
T2 = TypeVar('T2')
RetType = TypeVar('RetType')


class Annotate(enum.Enum):
    MroMerge = enum.auto()
    SubclsMerge = enum.auto()

class AttrNote(NamedTuple):

    cls: type
    attr: str
    otype: type
    meta: set
    endtype: type
    args: list

    @classmethod
    def forclass(cls, Class: type, metaset: set = EmptySet) -> Iterator[tuple[str, ...]]:
        annot = Class.__annotations__
        notes = (
            cls(Class, attr, *vals[0:2], vals[ - (len(vals) > 2)], vals)
            for attr, vals in (
                (k, typing.get_args(v))
                for k, v in annot.items()
                if typing.get_origin(v) is Annotated
            )
        )
        filt = (n for n in notes if metaset.issubset(n.meta))
        return ((n.attr,n) for n in filt)


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

    if not isinstance(ref, strtype):
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


def instcheck(obj, classinfo, exp = True):
    if isinstance(obj, classinfo) != exp:
        raise TypeError(obj, type(obj), classinfo)
    return obj

def isstr(obj) -> bool:
    return isinstance(obj, strtype)

def subclscheck(cls, typeinfo, exp = True):
    if issubclass(cls, typeinfo) != exp:
        raise TypeError(cls, typeinfo)
    return cls

def nowms() -> int:
    """Current time in milliseconds"""
    return int(round(time() * 1000))

def cat(*args: str) -> str:
    """Concat all argument strings"""
    return ''.join(args)

def errstr(err):
    if isinstance(err, Exception):
        return '%s: %s' % (err.__class__.__name__, err)
    return str(err)

def wrparens(*args: str) -> str:
    """Concat all argument strings and wrap in parentheses"""
    return cat('(', *args, ')')

def drepr(d: dict, limit = 10, j: str = ', ', vj = '=', paren = True) -> str:
    lw = drepr.lw
    islogic = drepr.islogic
    pairs = (
        cat(str(k), vj, v.__name__
        if isclass(v) else (
            v if isinstance(v, strtype) else (
                lw.write(v) if lw is not None and lw.canwrite(v)
                else (
                    v.name if islogic(v)
                    else v.__repr__()
                )
            )
        ))
        for k,v in islice(d.items(), limit)
    )
    istr = j.join(pairs)
    if paren:
        return wrparens(istr)
    return istr
drepr.islogic = lambda obj: (
    isinstance(obj, ModuleType) and
    obj.__name__.startswith('logics.')
)
# For testing, set this to a LexWriter instance.
drepr.lw = None

def orepr(obj, _d: dict = None, **kw) -> str:
    d = _d if _d is not None else kw
    if isinstance(obj, strtype):
        oname = obj
    else:
        try: oname = obj.__class__.__qualname__
        except AttributeError: oname = obj.__class__.__name__
    try:
        if callable(d): d = d()
        dstr = drepr(d, j = ' ', vj = ':', paren = False)
        return '<%s %s>' % (oname, dstr)
    except Exception as e:
        return '<%s !ERR: %s !>' % (oname, errstr(e))

def fixedreturn(val: Hashable) -> Callable:
    """Returns a function that returns the argument."""
    try: return fixedreturn.__dict__[val]
    except KeyError: pass
    def fnfixed(*_, **_k): return val
    return fixedreturn.__dict__.setdefault(val, fnfixed)

def fixedprop(val: Hashable) -> property:
    """Returns a property that returns the argument."""
    try: return fixedprop.__dict__[val]
    except KeyError: pass
    prop = property(fixedreturn(val))
    return fixedprop.__dict__.setdefault(val, prop)

class Decorators(object):

    __new__ = None

    def abstract(method: Callable[..., RetType]) -> Callable[..., RetType]:
        @abstractmethod
        def notimplemented(*args, **kw):
            raise NotImplementedError('abstractmethod', method)
        return notimplemented

    def lazyget(method: Callable[..., RetType]) -> Callable[..., RetType]:
        name, key = __class__._privkey(method)
        def fget(self) -> RetType:
            if not hasattr(self, key):
                setattr(self, key, method(self))
            return getattr(self, key)
        return fget

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
            fcheckstate.__qualname__ = method.__name__
            return fcheckstate
        return fcheckwrap

    def nosetattr(*args, **kw) -> Callable:
        if args and callable(args[0]):
            origin = args[0]
        else:
            origin = None
        changeonly = kw.pop('changeonly', False)
        def fsetwrap(origin: Callable):
            def fset(self, attr, val):
                # print('check', self.__class__.__name__)
                if __class__._isreadonly(self, **kw):
                    if not changeonly:
                        raise AttributeError('%s is readonly' % self)
                    if hasattr(self, attr):
                        if getattr(self, attr) is val:
                            return
                        raise AttributeError('%s.%s is immutable' % (self, attr))
                # print('not readonly', self.__class__.__name__)
                return origin(self, attr, val)
            return fset
        return fsetwrap(origin) if origin is not None else fsetwrap

    def nochangeattr(*args, **kw) -> Callable:
        kw['changeonly'] = True
        return __class__.nosetattr(*args, **kw)

    def cmperrors(*excepts: type) -> Callable:
        def fcmpwrap(fcmp: Callable[..., RetType]) -> Callable[..., RetType]:
            fname = fcmp.__name__
            opsym = CmpFnOper.get(fname, fname)
            def fcmperrs(a, b):
                try:
                    return fcmp(a, b)
                except excepts: # type: ignore
                    eargs = (opsym, type(a), type(b),)
                    raise TypeError("'%s' not supported for %s and %s" % eargs)
            fcmperrs.__qualname__ = fname
            return fcmperrs
        return fcmpwrap

    cmperr = cmperrors(AttributeError, TypeError)

    def cmptypes(*types: type) -> Callable:
        def fcmpwrap(fcmp: Callable[..., RetType]) -> Callable[..., RetType]:
            fname = fcmp.__name__
            opsym = CmpFnOper.get(fname, fname)
            eflag = TypeError()
            def fcmptypecheck(a, b):
                try:
                    if not isinstance(b, types or a.__class__):
                        raise eflag
                    return fcmp(a, b)
                except TypeError as err:
                    if err is eflag: err = None
                    eargs = (opsym, type(a), type(b),)
                    raise TypeError("'%s' not supported for %s and %s" % eargs) \
                        from err
            fcmptypecheck.__qualname__ = fname
            return fcmptypecheck
        return fcmpwrap

    cmptype = cmptypes()

    def argslice(*spec) -> Callable:
        slc = spec[0] if isinstance(spec[0], slice) else slice(*spec)
        def fslicewrap(func: Callable) -> Callable:
            def fslice(*args): return func(*args[slc])
            return fslice
        return fslicewrap

    @staticmethod
    def _privkey(method) -> tuple[str]:
        name = method.__name__
        key = cat('_', __name__, '__lazy_', name)
        return (name, key)

    @staticmethod
    def _isreadonly(obj, *args, cls: bool = None, check: Callable = None, **kw) -> bool:
        if check is None:
            return True
        if cls:
            if cls == True: obj = obj.__class__
            else: obj = cls
        return bool(check(obj))

def px(self): return self.index
def py(self): return self.subscript
def pz(self): return self.arity
px = property(px)
py = property(py)
pz = property(pz)

class SortBiCoords(NamedTuple):

    # y : int
    # x : int
    # subscript = py
    # index     = px

    subscript : int
    index     : int
    x = px
    y = py

class BiCoords(NamedTuple):

    # x : int
    # y : int
    # index     = px
    # subscript = py

    index     : int
    subscript : int
    x = px
    y = py
 
    Sorting = SortBiCoords

    def sorting(self) -> tuple[int, ...]:
        # return self.Sorting(self.y, self.x, *self[2:])
        return self.Sorting(self.subscript, self.index, *self[2:])

    first   = (0, 0)

class SortTriCoords(NamedTuple):

    # y: int
    # x: int
    # z: int
    # subscript = py
    # index     = px
    # arity     = pz

    subscript : int
    index     : int
    arity     : int
    x = px
    y = py
    z = pz

class TriCoords(NamedTuple):

    # x: int
    # y: int
    # z: int
    # index     = px
    # subscript = py
    # arity     = pz

    index     : int
    subscript : int
    arity     : int
    x = px
    y = py
    z = pz

    Sorting = SortTriCoords
    sorting = BiCoords.sorting

    first   = (0, 0, 1)

def ftmp():
    for cls in (BiCoords, TriCoords):
        cls.first = cls(*cls.first)
ftmp()
del(ftmp)

class CacheNotationData(object):

    default_fetch_name = 'default'

    @classmethod
    def load(cls, notn, name: str, data: Mapping):
        idx = cls.__getidx(notn)
        if not isinstance(name, strtype):
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

class StopWatch(object):

    __slots__ = ('_start_time', '_elapsed', '_is_running', '_times_started')

    def __init__(self, started=False):
        self._start_time = None
        self._elapsed = 0
        self._is_running = False
        self._times_started = 0
        if started:
            self.start()

    def start(self):
        if self._is_running:
            raise IllegalStateError('StopWatch already started.')
        self._start_time = nowms()
        self._is_running = True
        self._times_started += 1
        return self

    def stop(self):
        if not self._is_running:
            raise IllegalStateError('StopWatch already stopped.')
        self._is_running = False
        self._elapsed += nowms() - self._start_time
        return self

    def reset(self):
        self._elapsed = 0
        if self._is_running:
            self._start_time = nowms()
        return self

    def elapsed(self) -> float:
        if self._is_running:
            return self._elapsed + (nowms() - self._start_time)
        return self._elapsed

    def elapsed_avg(self) -> float:
        return self.elapsed() / max(1, self.times_started())

    def is_running(self) -> bool:
        return self._is_running

    def times_started(self) -> int:
        return self._times_started

    def __repr__(self):
        return self.elapsed().__repr__()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        if self.is_running():
            self.stop()



class UniqueList(Sequence[T], MutableSet[T]):

    __slots__ = ('__set', '__list')

    def add(self, item):
        if item not in self:
            self.__set.add(item)
            self.__list.append(item)

    append = add

    def update(self, items: Iterable[T]):
        for item in items:
            self.add(item)

    extend = update

    def clear(self):
        self.__set.clear()
        self.__list.clear()

    def count(self, item) -> int:
        return int(item in self)

    def index(self, item) -> int:
        return self.__list.index(item)

    def pop(self, *i: int) -> T:
        item = self.__list.pop(*i)
        self.__set.remove(item)
        return item

    def remove(self, item):
        self.__set.remove(item)
        self.__list.remove(item)

    def discard(self, item):
        if item in self:
            self.remove(item)

    def reverse(self):
        self.__list.reverse()

    def sort(self, *args, **kw):
        self.__list.sort(*args, **kw)

    def union(self, other: Iterable):
        inst = copy(self)
        if other is not self:
            inst.update(other)
        return inst

    def difference(self, other: Iterable):
        if not isinstance(other, (set, dict, self.__class__)):
            other = set(other)
        return self.__class__((x for x in self if x not in other))

    def difference_update(self, other: Iterable):
        for item in other:
            self.discard(item)

    def symmetric_difference(self, other: Iterable):
        inst = self.difference(other)
        inst.update((x for x in other if x not in self))
        return inst

    def symmetric_difference_update(self, other: Iterable):
        inst = self.symmetric_difference(other)
        self.clear()
        self.update(inst)

    def intersection(self, other: Iterable):
        if not isinstance(other, (set, dict, self.__class__)):
            other = set(other)
        return self.__class__((x for x in self if x in other))

    def intersection_update(self, other: Iterable):
        if not isinstance(other, (set, dict, self.__class__)):
            other = set(other)
        for item in self.__set.difference(other):
            self.remove(item)

    def isdisjoint(self, other) -> bool:
        if isinstance(other, self.__class__):
            other = other.__set
        return self.__set.isdisjoint(other)

    def issubset(self, other) -> bool:
        if isinstance(other, self.__class__):
            other = other.__set
        return self.__set.issubset(other)

    def issuperset(self, other) -> bool:
        if isinstance(other, self.__class__):
            other = other.__set
        return self.__set.issuperset(other)

    def copy(self):
        return self.__class__(self)

    def __len__(self):
        return len(self.__set)

    def __iter__(self) -> Iterator[T]:
        return iter(self.__list)

    def __contains__(self, item):
        return item in self.__set

    def __getitem__(self, key: IndexType) -> T:
        return self.__list[key]

    def __delitem__(self, key: IndexType):
        if isinstance(key, slice):
            for item in self.__list[key]:
                self.__set.remove(item)
            del self.__list[key]
        elif isinstance(key, int):
            self.pop(key)
        else:
            raise TypeError(key, type(key), IndexTypes)

    def __add__(self, value: Iterable[T]):
        inst = copy(self)
        if value is not self:
            inst.update(value)
        return inst

    def __iadd__(self, value: Iterable[T]):
        if value is not self:
            self.update(value)
        return self

    def __sub__(self, value: Iterable[T]):
        return self.difference(value)

    def __isub__(self, value: Iterable[T]):
        self.difference_update(value)
        return self

    __copy__ = copy

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            other = other.__list
        return self.__list == other

    def __init__(self, items: Iterable = None):
        self.__set = set()
        self.__list = []
        if items:
            self.update(items)

    def __repr__(self):
        return cat(self.__class__.__name__, wrparens(self.__list.__repr__()))

class LinkOrderSet(Collection):

    class LinkEntry:

        __slots__ = ('prev', 'next', 'item')

        def __init__(self, item):
            self.prev: LinkOrderSet.LinkEntry = None
            self.next: LinkOrderSet.LinkEntry = None
            self.item = item

        def __eq__(self, other):
            return self.item == other or (
                isinstance(other, self.__class__) and
                self.item == other.item
            )

        def __hash__(self):
            return hash(self.item)

        def __repr__(self):
            return self.item.__repr__()

    def View(obj):
        obj = cast(LinkOrderSet, obj)
        class LinkOrderSetView(Collection):
            __slots__ = ()
            def __len__(self):
                return len(obj)
            def __iter__(self):
                return iter(obj)
            def __reversed__(self):
                return reversed(obj)
            def __contains__(self, item):
                return item in obj
            def __getitem__(self, key):
                return obj[key]
            def first(self):
                return obj.first()
            def last(self):
                return obj.last()
            def __repr__(self):
                return obj.__class__.__repr__(self)
            def __copy__(self):
                return self.__class__()
        return LinkOrderSetView()

    def item(item_method: Callable) -> Callable:
        def wrap(self: LinkOrderSet, item, *args, **kw):
            item = self._genitem_(item, *args, **kw)
            return item_method(self, item)
        return wrap

    def iter_items(iter_item_method: Callable) -> Callable:
        def wrap(self: LinkOrderSet, items, *args, **kw):
            for item in items:
                iter_item_method(self, item, *args, **kw)
            return 
        return wrap

    def entry(link_entry_method: Callable) -> Callable:
        def prep(self: LinkOrderSet, item):
            if item in self:
                if self.strict:
                    raise DuplicateKeyError(item)
                return
            entry = self.__idx[item] = LinkOrderSet.LinkEntry(item)
            if self.__first is None:
                self.__first = self.__last = entry
                return
            if self.__first == self.__last:
                self.__first.next = entry
            link_entry_method(self, entry)
        return prep

    def _genitem_(self, item):
        return item

class LinkOrderSet(LinkOrderSet):

    slots = ('__first', '__last', '__idx', 'strict', '_utils__lazy_view')

    @LinkOrderSet.item
    @LinkOrderSet.entry
    def append(self, entry: LinkOrderSet.LinkEntry):
        if self.__first == self.__last:
            self.__first.next = entry
        entry.prev = self.__last
        entry.prev.next = entry
        self.__last = entry

    add = append

    update = extend = LinkOrderSet.iter_items(append)

    @LinkOrderSet.item
    @LinkOrderSet.entry
    def prepend(self, entry: LinkOrderSet.LinkEntry):
        if self.__first == self.__last:
            self.__last.prev = entry
        entry.next = self.__first
        entry.next.prev = entry
        self.__first = entry

    unshift = prepend

    prextend = LinkOrderSet.iter_items(prepend)

    @LinkOrderSet.item
    def remove(self, item):
        entry = self.__idx.pop(item)
        if entry.prev == None:
            if entry.next == None:
                # Empty
                self.__first = self.__last = None
            else:
                # Remove first
                entry.next.prev = None
                self.__first = entry.next
        else:
            if entry.next == None:
                # Remove last
                entry.prev.next = None
                self.__last = entry.prev
            else:
                # Remove in-between
                entry.prev.next = entry.next
                entry.next.prev = entry.prev

    def pop(self):
        if not len(self):
            raise IndexError('pop from empty collection')
        item = self.last()
        self.remove(item)
        return item

    def shift(self):
        if not len(self):
            raise IndexError('shift from empty collection')
        item = self.first()
        self.remove(item)
        return item

    @LinkOrderSet.item
    def discard(self, item):
        if item in self:
            self.remove(item)
    
    def clear(self):
        self.__idx.clear()
        self.__first = self.__last = None

    def first(self):
        return self.__first.item if self.__first else None

    def last(self):
        return self.__last.item if self.__last else None

    @property
    @Decorators.lazyget
    def view(self):
        return LinkOrderSet.View(self)

    def __init__(self, items: Iterable = None, strict = True):
        self.strict = strict
        self.__first = self.__last = None
        self.__idx: dict[Any, LinkOrderSet.LinkEntry] = {}
        if items is not None:
            self.extend(items)

    def __len__(self):
        return len(self.__idx)

    def __contains__(self, item):
        return item in self.__idx

    def __getitem__(self, key):
        return self.__idx[key].item

    def __delitem__(self, key):
        self.remove(key)

    def __iter__(self):
        cur = self.__first
        while cur:
            item = cur.item
            yield item
            cur = cur.next
                
    def __reversed__(self):
        cur = self.__last
        while cur:
            item = cur.item
            yield item
            cur = cur.prev

    def __copy__(self):
        return self.__class__((x for x in self))

    def __repr__(self):
        return orepr(self,
            len = len(self),
            first = self.first(),
            last = self.last(),
        )


class DequeCache(Collection[T]):

    __slots__ = ()
    abstract = Decorators.abstract

    ItemType = T

    maxlen: int
    idx: int
    rev: Mapping[Any, ItemType]

    @abstract
    def clear(self): ...

    @abstract
    def add(self, item: ItemType, keys = None): ...

    @abstract
    def update(self, d: dict): ...

    @abstract
    def get(self, key, default = None): ...

    @abstract
    def __len__(self): ...

    @abstract
    def __iter__(self) -> Iterator[ItemType]: ...

    @abstract
    def __reversed__(self) -> Iterator[ItemType]: ...

    @abstract
    def __contains__(self, item: ItemType): ...

    @abstract
    def __getitem__(self, key) -> ItemType: ...

    @abstract
    def __setitem__(self, key, item: ItemType): ...

    del(abstract)

    def __new__(cls, ItemType: type, maxlen = 10):

        if issubclass(ItemType, IndexTypes):
            raise TypeError()
        instcheck(ItemType, type)

        idx      : dict[Any, ItemType] = {}
        idxproxy : Mapping[Any, ItemType] = MappingProxyType(idx)

        rev      : dict[ItemType, set] = {}
        revproxy : Mapping[ItemType, set] = MappingProxyType(rev)

        deck     : deque[ItemType] = deque(maxlen = maxlen)

        class Api(DequeCache, Collection[ItemType]):

            __slots__ = ()

            maxlen: int = property(lambda _: deck.maxlen)
            idx: int = property(lambda _: idxproxy)
            rev: Mapping[Any, ItemType] = property(lambda _: revproxy)

            def clear(self):
                for d in (idx, rev, deck): d.clear()

            def add(self, item: ItemType, keys = None):
                self[item] = item
                if keys is not None:
                    for k in keys: self[k] = item

            def update(self, d: dict):
                for k, v in d.items(): self[k] = v

            def get(self, key, default = None):
                try: return self[key]
                except KeyError: return default

            def __len__(self):
                return len(deck)

            def __iter__(self) -> Iterator[ItemType]:
                return iter(deck)

            def __reversed__(self) -> Iterator[ItemType]:
                return reversed(deck)

            def __contains__(self, item: ItemType):
                return item in rev

            def __getitem__(self, key) -> ItemType:
                if isinstance(key, IndexTypes): return deck[key]
                return idx[key]

            def __setitem__(self, key, item: ItemType):
                instcheck(item, ItemType)
                if item in self: item = self[item]
                else:
                    if len(deck) == deck.maxlen:
                        old = deck.popleft()
                        for k in rev.pop(old): del(idx[k])
                    idx[item] = item
                    rev[item] = {item}
                    deck.append(item)
                idx[key] = item
                rev[item].add(key)

        Api.__qualname__ = 'DequeCache.Api'
        return object.__new__(Api)