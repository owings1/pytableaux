from __future__ import annotations

__all__ = (
    'MappingApi', 'MutableMappingApi', 'MapAttrView', 'DequeCache',
    'dmap',
)

from tools.abcs import Abc, Copyable, abcf
from decorators import abstract, static, final, overload, wraps


@static
class std:
    from collections import deque
    from collections.abc import Collection, Iterator, Mapping, MutableMapping
    from types import MappingProxyType as MapProxy
    from typing import Callable, TypeVar

from typing import Any
KT = std.TypeVar('KT')
VT = std.TypeVar('VT')
MT = std.TypeVar('MT', bound = std.Mapping)
MMT = std.TypeVar('MMT', bound = std.MutableMapping)
FT = std.TypeVar('FT', bound = std.Callable[..., Any])
NOARG = object()
EMPTY = tuple()

import itertools
import operator as opr

from typing import Iterable

class MappingApi(std.Mapping[KT, VT], Copyable):
    __slots__ = EMPTY

    @abcf.temp
    def oper(getiter: FT) -> FT:
        if getiter.__name__.startswith('__r'):
            method = '_rfrom_itemiterable'
        else:
            method = '_from_itemiterable'
        @wraps(getiter)
        def f(self, other: std.Mapping) -> MappingApi[KT, VT]:
            if not isinstance(other, std.Mapping):
                return NotImplemented
            return getattr(self, method)(getiter(self, other))
        return f

    @oper
    def __or__(self, other: std.Mapping) -> MappingApi[KT, VT]:
        return itertools.chain(
            ((k, self[k]) for k in self),
            ((k, other[k]) for k in other),
        )

    @oper
    def __ror__(self, other: std.Mapping) -> MappingApi[KT, VT]:
        return itertools.chain(
            ((k, other[k]) for k in other),
            ((k, self[k]) for k in self),
        )

    @oper
    def __and__(self, other):
        return ((k, self[k]) for k in self if k in other)

    @oper
    def __rand__(self, other):
        return ((k, other[k]) for k in other if k in self)

    @oper
    def __sub__(self, other):
        return ((k, self[k]) for k in self if k not in other)

    @oper
    def __rsub__(self, other):
        return ((k, other[k]) for k in other if k not in self)

    @oper
    def __xor__(self, other):
        return itertools.chain(
            ((k, self[k]) for k in self if k not in other),
            ((k, other[k]) for k in other if k not in self)
        )

    @oper
    def __rxor__(self, other):
        return itertools.chain(
            ((k, other[k]) for k in other if k not in self),
            ((k, self[k]) for k in self if k not in other),
        )

    def copy(self):
        return self._from_itemiterable(self.items())

    @classmethod
    def _from_itemiterable(cls, it: Iterable[tuple[KT, VT]]) -> MappingApi[KT, VT]:
        return cls(it)

    @classmethod
    def _rfrom_itemiterable(cls, it: Iterable[tuple[KT, VT]]) -> MappingApi[KT, VT]:
        return cls(it)


class MutableMappingApi(MappingApi[KT, VT], std.MutableMapping[KT, VT], Copyable):
    __slots__ = EMPTY

    @abcf.temp
    def ioper(apply: FT) -> FT:
        @wraps(apply)
        def f(self: MMT, other: std.Mapping) -> MMT:
            if not isinstance(other, std.Mapping):
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
    # copy = MutableMappingApi.copy
    __or__ = MutableMappingApi.__or__
    __ror__ = MutableMappingApi.__ror__

class MapAttrView(MappingApi[str, VT], Copyable):
    'A Mapping with attribute access.'

    __slots__ = '_mapping',

    def __init__(self, base: std.Mapping[str, VT]):
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

    def __iter__(self) -> std.Iterator[str]:
        return iter(self._mapping)

    def __reversed__(self) -> std.Iterator[str]:
        return reversed(self._mapping)

class DequeCache(std.Collection[VT], Abc):

    __slots__ = EMPTY

    maxlen: int
    idx: int
    rev: std.Mapping[Any, VT]

    @abstract
    def clear(self): ...

    @abstract
    def __len__(self): ...

    @abstract
    def __getitem__(self, key) -> VT: ...

    @abstract
    def __reversed__(self) -> std.Iterator[VT]: ...

    @abstract
    def __setitem__(self, key, item: VT): ...

    def __new__(cls, Vtype: type, maxlen = 10):

        from errors import instcheck, notsubclscheck
        notsubclscheck(Vtype, (int, slice))
        instcheck(Vtype, type)

        idx      : dict[Any, VT] = {}
        idxproxy : std.Mapping[Any, VT] = std.MapProxy(idx)

        rev      : dict[VT, set] = {}
        revproxy : std.Mapping[VT, set] = std.MapProxy(rev)

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

            def __iter__(self) -> std.Iterator[VT]:
                return iter(deck)

            def __reversed__(self) -> std.Iterator[VT]:
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