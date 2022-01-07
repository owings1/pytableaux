from __future__ import annotations

__all__ = 'KeyCacheFactory', 'MapAttrView', 'DequeCache',

from tools.abcs import Abc, Copyable
import decorators as d

import typing

from typing import Any
KT = typing.TypeVar('KT')
VT = typing.TypeVar('VT')
NOARG = object()
EMPTY = tuple()

class std:
    from collections import deque
    from collections.abc import Callable, Collection, Iterator, Mapping
    from types import MappingProxyType as MapProxy
    __new__ = None

class KeyCacheFactory(dict[KT, VT], Abc):

    __fncreate__: std.Callable[[KT], VT]

    __slots__ = '__fncreate__',

    def __init__(self, fncreate: std.Callable[[KT], VT]):
        super().__init__()
        self.__fncreate__ = fncreate

    def __getitem__(self, key: KT) -> VT:
        try: return super().__getitem__(key)
        except KeyError:
            val = self[key] = self.__fncreate__(key)
            return val

    def __call__(self, key: KT) -> VT:
        return self[key]

class MapAttrView(std.Mapping[str, VT], Copyable):
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

    @d.abstract
    def clear(self): ...

    @d.abstract
    def __len__(self): ...

    @d.abstract
    def __getitem__(self, key) -> VT: ...

    @d.abstract
    def __reversed__(self) -> std.Iterator[VT]: ...

    @d.abstract
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

del(d)