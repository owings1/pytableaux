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
from builtins import ModuleNotFoundError
from collections import deque
from collections.abc import Callable, Collection, ItemsView, Iterable, Iterator, \
    KeysView, Mapping, MutableSet, Sequence, ValuesView
from copy import copy
# from functools import partial
from importlib import import_module
from inspect import isclass
from itertools import chain, islice
# from operator import is_not
from past.builtins import basestring
from time import time
from types import MappingProxyType, ModuleType
from typing import Any, NamedTuple, TypeVar, Union, abstractmethod, cast

from errors import DuplicateKeyError, IllegalStateError
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
    '__contains__': 'in',
})

# Types
strtype = basestring
LogicRef = Union[ModuleType, str]
IndexTypes = (int, slice)
IndexType = Union[int, slice]

T = TypeVar('T')
RetType = TypeVar('RetType')

def get_module(ref, package: str = None) -> ModuleType:

    cache = _myattr(get_module, dict)
    keys = set()
    ret = {'mod': None}

    def _checkref(ref):
        key = (package, ref)
        if key in cache:
            return bool(_setcache(cache[key]))
        keys.add(key)
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
        if package != None and package != getattr(ref, '__package__', None):
            raise ModuleNotFoundError(
                "Module '{0}' not in package '{1}'".format(ref.__name__, package)
            )
        return _setcache(ref)

    if not isstr(ref):
        raise TypeError("ref must be string or module, or have __module__ attribute")

    ref = ref.lower()
    if _checkref(ref):
        return ret['mod']
    if package == None:
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

def islogic(obj) -> bool:
    return isinstance(obj, ModuleType) and obj.__name__.startswith('logics.')

def instcheck(obj, classinfo):
    if not isinstance(obj, classinfo):
        raise TypeError(obj, type(obj), classinfo)
    return obj

def subclscheck(cls, typeinfo):
    if not issubclass(cls, typeinfo):
        raise TypeError(cls, typeinfo)
    return cls

def nowms() -> int:
    return int(round(time() * 1000))

def cat(*args: str) -> str:
    return ''.join(args)

def wrparens(*args: str) -> str:
    return cat('(', *args, ')')

# notnone = partial(is_not, None)

testlw = None
def dictrepr(d: dict, limit = 10, j: str = ', ', vj = '=', paren = True) -> str:
    pairs = (
        cat(str(k), vj, v.__name__
        if isclass(v) else (
            v if isstr(v) else (
                testlw.write(v) if testlw and testlw.canwrite(v)
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

def kwrepr(**kw) -> str: return dictrepr(kw)

def orepr(obj, _d = None, **kw):
    try:
        oname = obj if isstr(obj) else obj.__class__.__name__
        istr = dictrepr(_d if _d != None else kw, j= ' ', vj=':',paren = False)
        return '<%s %s>' % (oname, istr)
    except:
        return '<%s ?ERR?>' % obj.__class__.__name__

def isstr(obj) -> bool:
    return isinstance(obj, strtype)

def isint(obj) -> bool:
    return isinstance(obj, int)

def sortedbyval(map: dict) -> list:
    return list(it[1] for it in sorted((v, k) for k, v in map.items()))

def _myattr(func, cls = set, name = '_cache'):
    if not hasattr(func, name):
        setattr(func, name, cls())
    return getattr(func, name)

def mroattr(cls: type, attr: str, **adds) -> filter:
    return filter (bool, chain(
        * (
            c.__dict__.get(attr, EmptySet)
            for c in reversed(cls.mro())
        ),
        (
            (name, value)
            for name, value in adds.items()
        )
    ))

def dedupitems(items):
    track = {}
    dedup = []
    for k, v in items:
        if k in track and v is None:
            # A value of None clears the item.
            item = (k, track.pop(k))
            idx = dedup.index(item)
            dedup.pop(idx)
        elif k not in track:
            if v is not None:
                track[k] = v
                dedup.append((k, v))
        elif track[k] != v:
            raise ValueError('Conflict %s: %s (was: %s)' % (k, v, track[k]))
    return dedup

class Decorators(object):

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
        def fcheckwrap(method: Callable) -> Callable:
            def fcheckstate(self, *args, **kw):
                for attr, val in attrs.items():
                    if getattr(self, attr) != val:
                        raise IllegalStateError(attr)
                return method(self, *args, **kw)
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
        def fcmpwrap(fcmp: Callable) -> Callable:
            fname = fcmp.__name__
            opsym = CmpFnOper.get(fname, fname)
            def fcmpsafe(a, b):
                try:
                    return fcmp(a, b)
                except excepts: # type: ignore
                    eargs = (opsym, type(a), type(b),)
                    raise TypeError("'%s' not supported for %s and %s" % eargs)
            return fcmpsafe
        return fcmpwrap

    cmperr = cmperrors(AttributeError, TypeError)

    def cmptypes(*types: type) -> Callable:
        def fcmpwrap(fcmp: Callable) -> Callable:
            fname = fcmp.__name__
            opsym = CmpFnOper.get(fname, fname)
            def fcmpcheck(a, b):
                if not isinstance(b, types or a.__class__):
                    eargs = (opsym, type(a), type(b),)
                    raise TypeError("'%s' not supported for %s and %s" % eargs)
                return fcmp(a, b)
            return fcmpcheck
        return fcmpwrap

    cmptype = cmptypes()

    @staticmethod
    def _privkey(method) -> tuple[str]:
        name = method.__name__
        key = cat('_', __name__, '__lazy_', name)
        return (name, key)

    @staticmethod
    def _isreadonly(obj, *args, cls: bool = None, check: Callable = None, **kw) -> bool:
        if check is None:
            return True
        if cls is not None and cls is not False:
            if cls == True:
                obj = obj.__class__
            else:
                obj = cls
        return bool(check(obj))

class SortBiCoords(NamedTuple):
    subscript : int
    index     : int

class BiCoords(NamedTuple):
    index     : int
    subscript : int
    first   = (0, 0)
    Sorting = SortBiCoords
    def sorting(self) -> tuple[int, ...]:
        return self.Sorting(self.subscript, self.index, *self[2:])

class SortTriCoords(NamedTuple):
    subscript : int
    index     : int
    arity     : int

class TriCoords(NamedTuple):
    index     : int
    subscript : int
    arity     : int
    first   = (0, 0, 1)
    Sorting = SortTriCoords
    sorting = BiCoords.sorting

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

    def elapsed(self):
        if self._is_running:
            return self._elapsed + (nowms() - self._start_time)
        return self._elapsed

    def elapsed_avg(self):
        return self.elapsed() / max(1, self.times_started())

    def is_running(self):
        return self._is_running

    def times_started(self):
        return self._times_started

    def __repr__(self):
        return self.elapsed().__repr__()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        if self.is_running():
            self.stop()

class DictAttrView(Mapping):

    def get(self, key, default = None):
        return self.__base.get(key, default)

    def items(self) -> ItemsView:
        return self.__base.items()

    def keys(self) -> KeysView:
        return self.__base.keys()

    def values(self) -> ValuesView:
        return self.__base.values()

    def __copy__(self):
        return self.__class__(self.__base)

    copy = __copy__

    def __init__(self, base: Mapping):
        self.__base = base

    def __getattr__(self, name):
        try:
            return self.__base[name]
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, key):
        return self.__base[key]

    def __contains__(self, key):
        return key in self.__base

    def __len__(self):
        return len(self.__base)

    def __iter__(self):
        return iter(self.__base)

    def __dir__(self):
        return list(self)

    def __repr__(self):
        return cat(
            self.__class__.__name__,
            wrparens(self.__base.__repr__()),
        )

class UniqueList(Sequence, MutableSet):

    def add(self, item):
        if item not in self:
            self.__set.add(item)
            self.__list.append(item)

    append = add

    def update(self, items: Iterable):
        for item in items:
            self.add(item)

    extend = update

    def clear(self):
        self.__set.clear()
        self.__list.clear()

    def count(self, item):
        return int(item in self)

    def index(self, item):
        return self.__list.index(item)

    def pop(self, *i: int):
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

    def __iter__(self):
        return iter(self.__list)

    def __contains__(self, item):
        return item in self.__set

    def __getitem__(self, key: IndexType):
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

    def __add__(self, value: Iterable):
        inst = copy(self)
        if value is not self:
            inst.update(value)
        return inst

    def __iadd__(self, value: Iterable):
        if value is not self:
            self.update(value)
        return self

    def __sub__(self, value: Iterable):
        return self.difference(value)

    def __isub__(self, value: Iterable):
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

    class LinkEntry(object):

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
                raise DuplicateKeyError(item)
            entry = self.__idx[item] = LinkOrderSet.LinkEntry(item)
            if self.__first == None:
                self.__first = self.__last = entry
                return
            if self.__first == self.__last:
                self.__first.next = entry
            link_entry_method(self, entry)
        return prep

    def _genitem_(self, item):
        return item

class LinkOrderSet(LinkOrderSet):

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

    def __init__(self, items: Iterable = None):
        self.__first = self.__last = None
        self.__idx: dict[Any, LinkOrderSet.LinkEntry] = {}
        if items != None:
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