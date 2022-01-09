from __future__ import annotations

__all__ = 'MapAttrView', 'DequeCache',

from tools.abcs import Abc, Copyable, abcm

class std:
    from collections import deque
    from collections.abc import Collection, Iterator, Mapping
    from types import MappingProxyType as MapProxy
    from typing import TypeVar

from typing import Any
KT = std.TypeVar('KT')
VT = std.TypeVar('VT')
NOARG = object()
EMPTY = tuple()


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

    @abcm.abstract
    def clear(self): ...

    @abcm.abstract
    def __len__(self): ...

    @abcm.abstract
    def __getitem__(self, key) -> VT: ...

    @abcm.abstract
    def __reversed__(self) -> std.Iterator[VT]: ...

    @abcm.abstract
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

del(abcm)