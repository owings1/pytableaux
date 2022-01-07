from __future__ import annotations
from callables import calls
from decorators import operd
from tools.abcs import Copyable

import collections.abc as bases
import operator as opr
import typing

__all__ = 'SetApi', 'MutableSetApi', 'setf', 'setm'

T = typing.TypeVar('T')
V = typing.TypeVar('V')

class SetApi(bases.Set[V], Copyable):
    'Fusion interface of collections.abc.Set and built-in frozenset.'

    __slots__ = ()

    _opts = dict(freturn = calls.method('_from_iterable'))

    issubset   = operd.apply(opr.le, info = set.issubset)
    issuperset = operd.apply(opr.ge, info = set.issuperset)

    union        = operd.reduce(opr.or_,  info = set.union,        **_opts)
    intersection = operd.reduce(opr.and_, info = set.intersection, **_opts)
    difference   = operd.reduce(opr.sub,  info = set.difference,   **_opts)

    symmetric_difference = operd.apply(opr.xor,
        info = set.symmetric_difference
    )

    del(_opts)

    def __or__(self :T|SetApi, other) -> T: ...
    def __and__(self :T|SetApi, other) -> T: ...
    def __sub__(self :T|SetApi, other) -> T: ...
    def __xor__(self :T|SetApi, other) -> T: ...
    __or__  = bases.Set.__or__
    __and__ = bases.Set.__and__
    __sub__ = bases.Set.__sub__
    __xor__ = bases.Set.__xor__

    def copy(self):
        return self._from_iterable(self)

    @classmethod
    def _from_iterable(cls: type[T], it: bases.Iterable) -> T:
        return cls(it)

class setf(SetApi[V], frozenset[V]):
    'SetApi wrapper around built-in frozenset.'
    __slots__ = ()
    __len__      = frozenset.__len__
    __contains__ = frozenset.__contains__
    __iter__     = frozenset[V].__iter__

EMPTY_SET = setf()

class MutableSetApi(bases.MutableSet[V], SetApi[V]):
    'Fusion interface of collections.abc.MutableSet and built-in set.'

    __slots__ = EMPTY_SET

    update              = operd.iterself(opr.ior,  info = set.update)
    intersection_update = operd.iterself(opr.iand, info = set.intersection_update)
    difference_update   = operd.iterself(opr.isub, info = set.difference_update)

    symmetric_difference_update = operd.apply(opr.ixor,
        info = set.symmetric_difference_update
    )

class setm(MutableSetApi[V], set[V]):
    'MutableSetApi wrapper around built-in set.'
    __slots__ = EMPTY_SET
    __len__      = set.__len__
    __contains__ = set.__contains__
    __iter__     = set[V].__iter__
    clear   = set.clear
    add     = set.add
    discard = set.discard