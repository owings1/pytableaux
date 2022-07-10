from typing import (Any, Callable, Collection, Iterable, Iterator,
                    SupportsIndex, TypeVar, overload)

from pytableaux.tools.sequences import MutableSequenceApi, SequenceApi
from pytableaux.tools.sets import MutableSetApi, SetApi

_T = TypeVar('_T')
_T_co = TypeVar('_T_co', covariant=True)
__QsetT = TypeVar('__QsetT', bound = SequenceSet)
_self = TypeVar('_self')

EMPTY_QSET: qsetf

class SequenceSet(SequenceApi[_T_co], SetApi[_T_co]):
    def __mul__(self: _self, other:SupportsIndex) -> _self: ...
    def __rmul__(self: _self, other:SupportsIndex) -> _self: ...
    @classmethod
    def _from_iterable(cls:type[__QsetT], it:Iterable) -> __QsetT:...

class qsetf(SequenceSet[_T_co]):
    def __init__(self, values: Iterable = ...) -> None: ...
    def copy(self:_T) -> _T: ...
    @overload
    def __getitem__(self:__QsetT, index: slice) -> __QsetT: ...
    @overload
    def __getitem__(self, index: SupportsIndex) -> _T_co: ...
    def __iter__(self) -> Iterator[_T_co]: ...
    def __reversed__(self) -> Iterator[_T_co]: ...
    @classmethod
    def _from_iterable(cls:type[__QsetT], it:Iterable) -> __QsetT:...

class QsetView(SequenceSet[_T_co]):
    def copy(self:_T) -> _T: ...

class MutableSequenceSet(SequenceSet[_T_co], MutableSequenceApi[_T_co], MutableSetApi[_T_co]):
    def add(self, value:_T_co) -> None: ...
    def discard(self, value:_T_co) -> None: ...
    def reverse(self) -> None: ...

class qset(MutableSequenceSet[_T_co]):
    def __init__(self, values: Iterable = ...) -> None: ...
    def copy(self:_T) -> _T: ...
    @overload
    def __getitem__(self:__QsetT, index: slice) -> __QsetT: ...
    @overload
    def __getitem__(self, index: SupportsIndex) -> _T_co: ...
    def insert(self, index: SupportsIndex, value:_T_co) -> None: ...
    def __delitem__(self, key: SupportsIndex|slice,) -> None: ...
    @overload
    def __setitem__(self, key: SupportsIndex, value: _T_co) -> None: ...
    @overload
    def __setitem__(self, key: slice, value: Collection[_T_co]) -> None: ...