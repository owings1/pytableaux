from __future__ import annotations

__all__ = 'SetApi', 'MutableSetApi', 'setf', 'setm', 'EMPTY_SET'

from tools.abcs import Copyable, T, VT
from tools.decorators import abstract, final, overload, operd

from collections.abc import Set, MutableSet
import operator as opr
from typing import Iterable

EMPTY = ()

class SetApi(Set[VT], Copyable):
    'Fusion interface of collections.abc.Set and built-in frozenset.'

    __slots__ = EMPTY

    @overload
    def __or__(self:T, other) -> T: ...
    @overload
    def __and__(self:T, other) -> T: ...
    @overload
    def __sub__(self:T, other) -> T: ...
    @overload
    def __xor__(self:T, other) -> T: ...

    __or__  = Set.__or__
    __and__ = Set.__and__
    __sub__ = Set.__sub__
    __xor__ = Set.__xor__

    red = operd.reduce.template(freturn = '_from_iterable')
    app = operd.apply

    @overload
    def issubset(self, other: Iterable) -> bool: ...
    @overload
    def issuperset(self, other: Iterable) -> bool: ...
    @overload
    def union(self:T, *others: Iterable) -> T: ...
    @overload
    def intersection(self:T, *others: Iterable) -> T: ...
    @overload
    def difference(self:T, *others: Iterable) -> T: ...
    @overload
    def symmetric_difference(self:T, other: Iterable) -> T: ...

    issubset = app(opr.le, set.issubset)
    issuperset = app(opr.ge, set.issuperset)
    union = red(opr.or_, set.union)
    intersection = red(opr.and_, set.intersection)
    difference = red(opr.sub, set.difference)
    symmetric_difference = app(opr.xor, set.symmetric_difference)

    del(red, app)

    def copy(self):
        return self._from_iterable(self)

    @classmethod
    def _from_iterable(cls: type[T], it: Iterable) -> T:
        return cls(it)

class MutableSetApi(MutableSet[VT], SetApi[VT]):
    'Fusion interface of collections.abc.MutableSet and built-in set.'

    __slots__ = EMPTY

    rep = operd.repeat

    @overload
    def update(self, *others: Iterable): ...
    @overload
    def intersection_update(self, *others: Iterable): ...
    @overload
    def difference_update(self, *others: Iterable): ...
    @overload
    def symmetric_difference_update(self, other: Iterable): ...

    update = rep(opr.ior, set.update)
    intersection_update = rep(opr.iand, set.intersection_update)
    difference_update = rep(opr.isub, set.difference_update)
    symmetric_difference_update = operd.apply(opr.ixor,
        set.symmetric_difference_update
    )

    del(rep)

class setf(SetApi[VT], frozenset[VT]):
    'SetApi wrapper around built-in frozenset.'
    __slots__ = EMPTY
    __len__      = frozenset.__len__
    __contains__ = frozenset.__contains__
    __iter__     = frozenset[VT].__iter__

class setm(MutableSetApi[VT], set[VT]):
    'MutableSetApi wrapper around built-in set.'
    __slots__ = EMPTY
    __len__      = set.__len__
    __contains__ = set.__contains__
    __iter__     = set[VT].__iter__
    clear   = set.clear
    add     = set.add
    discard = set.discard

EMPTY_SET = setf()

del(opr, operd, Copyable, Set, MutableSet, EMPTY)

del(abstract, final, overload)