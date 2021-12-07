from __future__ import annotations

from callables import fpreds
from utils import cat, instcheck, wrparens

import abc
from collections.abc import Callable, Collection, Hashable, ItemsView, Iterable,\
    Iterator, KeysView, Mapping, MappingView, MutableSet, Sequence, ValuesView
import typing
from typing import Any, Annotated, NamedTuple, TypeVar, Union, abstractmethod, cast


T = TypeVar('T')

class ABCMeta(abc.ABCMeta):
    pass

class DictAttrView(MappingView, Mapping[str, T]):
    """A Mapping view with attribute access."""

    # MappingView uses the '_mapping' slot.
    __slots__ = ('_mapping',)

    def __init__(self, base: Mapping[str, T]):
        self._mapping = base

    def __getattr__(self, name: str):
        try: return self._mapping[name]
        except KeyError: raise AttributeError(name)

    def _s_dir__(self):
        # return list(filterself)
        pass


    def __copy__(self) -> DictAttrView[T]:
        inst = object.__new__(self.__class__)
        inst._mapping = self._mapping
        return inst

    # def __contains__(self, key):
    #     return key in self._mapping

    def __getitem__(self, key) -> T:
        return self._mapping[key]

    def __iter__(self) -> Iterator[str]:
        yield from self._mapping

    def __reversed__(self):
        try: return reversed(self._mapping)
        except TypeError: return NotImplemented



# d: DictAttrView[str] = 2
# d['asdf'].startswith('asdf')

# d.get('foo').startswith
# for k, v in d.items():
#     k.startswith('f')
#     v.startswith('t')