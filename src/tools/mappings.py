from __future__ import annotations

__all__ = (
    'MappingApi', 'MutableMappingApi', 'MapAttrView', 'DequeCache',
    'dmap', 'mapf', 'miter',
)

from tools.abcs import Abc, Copyable, abcf, F, T
from decorators import abstract, static, final, overload, fixed, wraps
from errors import instcheck

from typing import (
    Callable, Iterable, Iterator, Mapping, MutableMapping,
    Any, TypeVar,
)

@static
class std:
    from collections import deque
    from collections.abc import Collection
    from types import MappingProxyType as MapProxy

KT = TypeVar('KT')
VT = TypeVar('VT')
MT = TypeVar('MT', bound = Mapping)
KV = TypeVar('KV', bound = tuple[Any, Any])
Itemable = TypeVar('Itemable', Mapping, Iterable)
# MMT = TypeVar('MMT', bound = MutableMapping)
# FT = TypeVar('FT', bound = Callable[..., Any])
_NOARG = object()
EMPTY = tuple()

from itertools import (
    chain as _chain,
)
import operator as opr
from operator import (
    not_,
    truth
)


def _true(_): return True

class miter(Iterator[tuple[KT, VT]]):

    __slots__ = '_gen_', '__next__'

    @overload
    def __init__(self, keys: Iterable[KT], /, vget: Callable[[KT], VT], **kw): ...
    @overload
    def __init__(self, mapping: Mapping[KT, VT], /, **kw):...
    @overload
    def __init__(self, items: Iterable[tuple[KT, VT]], /, **kw): ...
    def __init__(self, obj, /, *, 
        vget: Callable[[KT], VT] = None,
        kpred: Callable[[Any], Any] = _true,
        vpred: Callable[[Any], Any] = _true,
        koper: Callable[[Any], Any] = truth,
        voper: Callable[[Any], Any] = truth,
    ):
        if vget is None:
            if hasattr(obj, 'keys'):
                it = self._gen1(obj.keys, obj.__getitem__, kpred, vpred, koper, voper)
            else:
                it = self._gen2(obj, kpred, vpred, koper, voper)
        else:
            it = self._gen1(obj.__iter__, vget, kpred, vpred, koper, voper)
        self.__next__ = it.__next__

    def __iter__(self):
        return self

    @overload
    def __next__(self) -> tuple[KT, VT]:...
    del(__next__)

    @static
    def _gen1(getkeys, vget, kpred, vpred, koper, voper):
        for k in getkeys():
            if koper(kpred(k)):
                v = vget(k)
                if voper(vpred(v)):
                    yield k, v

    @static
    def _gen2(items, kpred, vpred, koper, voper):
        for k, v in items:
            if koper(kpred(k)) and voper(vpred(v)):
                yield k, v

class MappingApi(Mapping[KT, VT], Copyable):

    __slots__ = EMPTY

    @abcf.temp
    def oper(getiter: Callable[..., Iterable]) -> Callable[[MT, Mapping], MT]:
        if getiter.__name__.startswith('__r'):
            fromiter = '_rfrom_iterable'
        else:
            fromiter = '_from_iterable'
        @wraps(getiter)
        def f(self, other):
            if not isinstance(other, Mapping):
                return NotImplemented
            return getattr(self, fromiter)(getiter(self, other))
        return f

    @oper
    def __or__(self, other):
        return _chain(miter(self), miter(other))

    @oper
    def __ror__(self, other):
        return _chain(miter(other), miter(self))

    @oper
    def __and__(self, other):
        return miter(self, kpred = other.__contains__)

    @oper
    def __rand__(self, other):
        return miter(other, kpred = self.__contains__)

    @oper
    def __sub__(self, other):
        return miter(self, kpred = other.__contains__, koper = not_)

    @oper
    def __rsub__(self, other):
        return miter(other, kpred = self.__contains__, koper = not_)

    @oper
    def __xor__(self, other):
        return _chain(
            miter(self, kpred = other.__contains__, koper = not_),
            miter(other, self.__contains__, koper = not_),
        )

    @oper
    def __rxor__(self, other):
        return _chain(
            miter(other, kpred = self.__contains__, koper = not_),
            miter(self, kpred = other.__contains__, koper = not_),
        )

    def copy(self):
        return self._from_iterable(miter(self))

    @classmethod
    def _from_iterable(cls: type[MT], it: Iterable) -> MT:
        return cls(it)

    _rfrom_iterable = _from_iterable

class mapf(MappingApi[KT, VT]):
    'Fixed mapping.'
    __slots__ = '_'
    _: Mapping[KT, VT]
    _mapping_basecls = std.MapProxy

    @classmethod
    def ref(cls: type[MT], mapping: Mapping) -> MT:
        'Create a reference-only object to a mapping.'
        instcheck(mapping, Mapping)
        inst = cls.__new__(cls)
        inst._ = mapping
        return inst

    @overload
    def __init__(self, mapping: Mapping): ...
    @overload
    def __init__(self, items: Iterable): ...
    @overload
    def __init__(self, **kwargs): ...

    def __init__(self, obj = None, /, **kw):
        if obj is not None:
            kw.update(obj)
        self._ = self._mapping_basecls(kw)

    def __len__(self):
        return len(self._)

    def __iter__(self):
        return iter(self._)

    def __reversed__(self) -> reversed[KT]:
        return reversed(self._)

    def __getitem__(self, key):
        return self._[key]

    def __repr__(self):
        return repr(dict(self))

    # .... protect _

    def __setattr__(self, name, value):
        if name == '_' and hasattr(self, name):
            raise AttributeError(name)
        super().__setattr__(name, value)

    def __delattr__(self, name):
        if name == '_':
            raise AttributeError(name)
        super().__delattr__(name)

    def __dir__(self):
        return [n for n in super().__dir__() if n != '_']

class MutableMappingApi(MappingApi[KT, VT], MutableMapping[KT, VT], Copyable):

    __slots__ = EMPTY

    @abcf.temp
    def ioper(apply: Callable[[T], Any]) -> Callable[[T, Mapping], T]:
        @wraps(apply)
        def f(self, other):
            if not isinstance(other, Mapping):
                return NotImplemented
            apply(self, other)
            return self
        return f

    @ioper
    def __ior__(self, other):
        for k in other:
            self[k] = other[k]

    @ioper
    def __iand__(self, other):
        for k in other:
            if k not in self:
                del(self[k])
    @ioper
    def __isub__(self, other):
        for k in other:
            if k in self:
                del(self[k])
    @ioper
    def __ixor__(self, other):
        for k in other:
            if k in self:
                del(self[k])
        for k in self:
            if k in other:
                del(self[k])

class dmap(dict, MutableMappingApi[KT, VT]):
    pass
    __slots__ = EMPTY
    copy = MutableMappingApi.copy
    __or__ = MutableMappingApi.__or__
    __ror__ = MutableMappingApi.__ror__

class MapAttrView(MappingApi[str, VT], Copyable):
    'A Mapping with attribute access.'

    __slots__ = '_mapping',

    def __init__(self, base: Mapping[str, VT]):
        self._mapping = base

    def __getattr__(self, name: str) -> VT:
        try:
            return self._mapping[name]
        except KeyError:
            raise AttributeError(name)

    def __dir__(self):
        from callables import preds
        return list(filter(preds.isidentifier, self))

    def copy(self):
        inst = object.__new__(self.__class__)
        inst._mapping = self._mapping
        return inst

    def __len__(self):
        return len(self._mapping)

    def __getitem__(self, key: str) -> VT:
        return self._mapping[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._mapping)

    def __reversed__(self) -> Iterator[str]:
        return reversed(self._mapping)

class DequeCache(std.Collection[VT], Abc):

    __slots__ = EMPTY

    maxlen: int
    idx: int
    rev: Mapping[Any, VT]

    @abstract
    def clear(self): ...

    @abstract
    def __len__(self): ...

    @abstract
    def __getitem__(self, key) -> VT: ...

    @abstract
    def __reversed__(self) -> Iterator[VT]: ...

    @abstract
    def __setitem__(self, key, item: VT): ...

    def __new__(cls, Vtype: type, maxlen = 10):

        from errors import notsubclscheck
        notsubclscheck(Vtype, (int, slice))
        instcheck(Vtype, type)

        idx      : dict[Any, VT] = {}
        idxproxy : Mapping[Any, VT] = std.MapProxy(idx)

        rev      : dict[VT, set] = {}
        revproxy : Mapping[VT, set] = std.MapProxy(rev)

        deck     : std.deque[VT] = std.deque(maxlen = maxlen)

        class Api(DequeCache[VT]):

            __slots__ = EMPTY

            maxlen = property(lambda _: deck.maxlen)
            idx = property(lambda _: idxproxy)
            rev = property(lambda _: revproxy)

            def clear(self):
                for d in (idx, rev, deck): d.clear()

            def __len__(self):
                return len(deck)

            def __iter__(self) -> Iterator[VT]:
                return iter(deck)

            def __reversed__(self) -> Iterator[VT]:
                return reversed(deck)

            def __contains__(self, item: VT):
                return item in rev

            def __getitem__(self, key) -> VT:
                return idx[key]

            def __setitem__(self, key, item: VT):
                instcheck(item, Vtype)
                if item in self:
                    item = self[item]
                else:
                    if len(deck) == deck.maxlen:
                        old = deck.popleft()
                        for k in rev.pop(old): del(idx[k])
                    idx[item] = item
                    rev[item] = {item}
                    deck.append(item)
                idx[key] = item
                rev[item].add(key)

            __new__  = object.__new__

        Api.__qualname__ = 'DequeCache.Api'
        return Api()

del(abstract, static, final, overload, wraps)


def _gen(n = 5, *a):
    # testing...
    r = n  if isinstance(n, range) else range(n, *a)
    return zip(r, map('valueOf(%s)'.__mod__, r))