from __future__ import annotations
from errors import instcheck as _instcheck
import utils

import enum
import itertools
import typing

class ErrMsg(enum.Enum):
    ExtendedSliceSize = 'attempt to assign sequence of size %d to extended slice of size %d'
    IndexRange = 'sequence index out of range'

class bases:
    from collections import deque
    from collections.abc import (
        Iterable, MutableSequence, Sequence
    )
    from tools.abcs import Copyable

class d:
    from decorators import (
        abstract, metad, namedf, overload, wraps
    )


T = typing.TypeVar('T')
V = typing.TypeVar('V')
NOARG = object()

__all__ = (
    'SequenceApi', 'MutableSequenceApi', 'SequenceProxy', 'seqf',
)

class SequenceApi(bases.Sequence[V], bases.Copyable):
    "Extension of collections.abc.Sequence and built-in sequence (tuple)."

    __slots__ = ()

    @d.overload
    def __getitem__(self: T, s: slice) -> T: ...

    @d.overload
    def __getitem__(self, i: int) -> V: ...

    @d.abstract.impl
    def __getitem__(self, index):
        raise IndexError

    @d.overload
    def __add__(self:T, other: bases.Iterable) -> T: ...
    def __add__(self, other):
        if not isinstance(other, bases.Iterable):
            return NotImplemented
        return self._from_iterable(itertools.chain(self, other))

    __radd__ = __add__

    @d.overload
    def __mul__(self:T, other: int) -> T: ...
    def __mul__(self, other):
        if not isinstance(other, int):
            return NotImplemented
        return self._from_iterable(
            itertools.chain.from_iterable(
                itertools.repeat(self, other)
            )
        )

    __rmul__ = __mul__

    def _absindex(self, index: int, strict = True, /) -> int:
        'Normalize to positive/absolute index.'
        _instcheck(index, int)
        if index < 0:
            index = len(self) + index
        if strict and (index >= len(self) or index < 0):
            raise IndexError(ErrMsg.IndexRange.value)
        return index

    def copy(self):
        return self._from_iterable(self)

    @classmethod
    def _from_iterable(cls: type[T], it: bases.Iterable) -> T:
        return cls(it)

SequenceApi.register(tuple)

class MutableSequenceApi(SequenceApi[V], bases.MutableSequence[V]):
    'Fusion interface of collections.abc.MutableSequence and built-in list.'

    __slots__ = ()

    @d.abstract
    def sort(self, /, *, key = None, reverse = False):
        raise NotImplementedError

    def _new_value(self, value):
        '''Hook to return the new value before it is attempted to be added.
        Must be idempotent. Does not affect deletions.'''
        return value

    @d.overload
    def _setslice_prep(self:T, slc: slice, values: bases.Iterable, /) -> tuple[T, T]: ...
    def _setslice_prep(self, slc: slice, values: bases.Iterable, /):
        olds = self[slc]
        values = self._from_iterable(map(self._new_value, values))
        if abs(slc.step or 1) != 1 and len(olds) != len(values):
            raise ValueError(
                ErrMsg.ExtendedSliceSize.value % (len(values), len(olds))
            )
        return olds, values

    @d.overload
    def __imul__(self:T, other: int) -> T: ...
    def __imul__(self, other):
        if not isinstance(other, int):
            return NotImplemented
        self.extend(itertools.chain.from_iterable(
            itertools.repeat(self, other - 1)
        ))
        return self

MutableSequenceApi.register(list)
MutableSequenceApi.register(bases.deque)

class SequenceProxy(SequenceApi[V]):
    'Sequence view proxy.'

    __slots__ = ()

    _proxy_names_ = set()

    @d.metad.after
    def _after(cls):
        cls._proxy_names_ = frozenset(cls._proxy_names_)

    @d.metad.temp
    def proxyfn(default = NOARG, *args):
        def defer(member: d.namedf[SequenceProxy], default = NOARG):
            owner: type[SequenceProxy]
            owner, name = member._owner_name
            owner._proxy_names_.add(name)
            if default is NOARG:
                method = getattr(SequenceApi, name, None)
                if callable(method) and not d.abstract.isabstract(method):
                    default = method
            def f(cls: type[SequenceProxy], *args):
                proxy_method = cls._get_base_attr(name, default)
                setattr(cls, name, proxy_method)
                return proxy_method(*args)
            return classmethod(d.wraps(member)(f))
        return d.namedf(defer, *args)

    __len__      = proxyfn()
    __getitem__  = proxyfn()
    __contains__ = proxyfn()
    __iter__     = proxyfn()
    __reversed__ = proxyfn()
    count        = proxyfn()
    index        = proxyfn()
    _from_iterable = proxyfn()

    def copy(self):
        return self

    def __repr__(self):
        return utils.wraprepr(self, list(self))

    @classmethod
    @d.abstract
    def _get_base_attr(cls, name): ...

    def __new__(cls, base: SequenceApi):

        _instcheck(base, SequenceApi)
        names = cls._proxy_names_

        class SeqProxy(SequenceProxy):

            __slots__ = ()
            __new__ = object.__new__

            @classmethod
            def _get_base_attr(cls, name, default = NOARG,/):
                if name in names:
                    value = getattr(base, name, default)
                    if value is not NOARG: return value
                raise AttributeError(name)

        SeqProxy.__qualname__ = '%s.%s' % (
            type(base).__qualname__, SeqProxy.__name__
        )
        return SeqProxy()

class seqf(tuple[V], SequenceApi[V]):
    'Frozen sequence, fusion of tuple and SequenceApi.'
    # __eq__  = tuple.__eq__
    # __ne__  = tuple.__ne__
    # __gt__  = tuple.__gt__
    # __ge__  = tuple.__ge__
    # __lt__  = tuple.__lt__
    # __le__  = tuple.__le__

    # __hash__ = tuple.__hash__

    __add__  = SequenceApi.__add__

    @d.overload
    def __radd__(self, other: seqf[V]) -> seqf[V]: ...
    @d.overload
    def __radd__(self, other: tuple[V, ...]) -> tuple[V, ...]: ...
    @d.overload
    def __radd__(self, other: list[V]) -> list[V]: ...
    @d.overload
    def __radd__(self, other: bases.deque[V]) -> bases.deque[V]: ...

    def __radd__(self, other):
        if not isinstance(other, bases.Iterable):
            return NotImplemented
        # Check concrete type, not subclass.
        otype = type(other)
        it = itertools.chain(other, self)
        # Since we inherit from tuple, Python will prefer our __radd__
        # to tuple's __add__, which we don't want to override.
        if otype is tuple or otype is list:
            return otype(it)
        if otype is bases.deque:
            maxlen = other.maxlen
            if maxlen is not None and len(other) + len(self) > maxlen:
                # Making a new deque that exceeds maxlen of lhs is not supported.
                raise TypeError(
                    "deque maxlen (%d) would be exceeded by "
                    "new instance (%s)" % (maxlen, len(other) + len(self))
                )
            return otype(it, maxlen)
        return self._from_iterable(it)

    __mul__  = SequenceApi.__mul__
    __rmul__ = SequenceApi.__rmul__

    def __repr__(self):
        return type(self).__name__ + super().__repr__()

EMPTY_SEQ = seqf()

del(enum, typing)