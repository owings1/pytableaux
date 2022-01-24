from __future__ import annotations

from typing import TypeVar
T = TypeVar('T')
V = TypeVar('V')
del(TypeVar)

NOARG = object()
EMPTY = ()

from tools.decorators import abstract, final, overload
from errors import (
    Emsg,
    DuplicateValueError,
    MissingValueError,
    instcheck as _instcheck,
)

class bases:
    from tools.abcs import Abc, Copyable
    from tools.sequences import SequenceApi, MutableSequenceApi
    from tools.hybrids import MutableSequenceSetApi

from collections.abc import Iterable, Iterator
from typing import Generic, SupportsIndex


import enum
class LinkRel(enum.IntEnum):
    'Link directional/subscript enum.'
    prev, self, next = -1, 0, 1

del(enum)

def _absindex(seqlen, index: SupportsIndex, strict = True, /) -> int:
    'Normalize to positive/absolute index.'
    if not isinstance(index, int):
        index = int(_instcheck(index, SupportsIndex))
    if index < 0:
        index = seqlen + index
    if strict and (index >= seqlen or index < 0):
        raise Emsg.IndexOutOfRange(index)
    return index

class Link(Generic[V], bases.Copyable):
    'Link value container.'

    value: V
    prev: Link[V]
    next: Link[V]

    __slots__ = 'prev', 'next', 'value'

    @property
    def self(self: T) -> T:
        return self

    def __init__(self, value, prev: Link = None, nxt: Link = None, /):
        self.value = value
        self.prev = prev
        self.next = nxt

    def __getitem__(self, rel: int) -> Link[V] | None:
        'Get previous, self, or next with -1, 0, 1, or ``LinkRel`` enum.'
        return getattr(self, LinkRel(rel).name)

    def __setitem__(self, rel: int, link: Link):
        'Set previous or next with -1, 1, or ``LinkRel`` enum.'
        setattr(self, LinkRel(rel).name, link)

    def invert(self):
        'Invert prev and next attributes in place.'
        self.prev, self.next = self.next, self.prev

    def copy(self, value = NOARG):
        inst: Link = object.__new__(type(self))
        inst.value = self.value if value is NOARG else value
        inst.prev = self.prev
        inst.next = self.next
        return inst

    def __repr__(self):
        import tools.misc as misc
        return misc.wraprepr(self, self.value)

class HashLink(Link[V]):

    __slots__ = EMPTY

    def __eq__(self, other):
        if self is other:
            return True
        if isinstance(other, self.__class__):
            return self.value == other.value
        return self.value == other

    def __hash__(self):
        return hash(self.value)

class LinkIter(Iterator[Link[V]], bases.Abc):
    'Linked sequence iterator.'

    _start: Link
    _step: int
    _rel: LinkRel
    _count: int
    _cur: Link

    __slots__ = '_start', '_step', '_count', '_cur', '_rel'

    def __init__(self, start: Link, step: int = 1, count: int = -1, /):
        self._start = start if count else None
        self._step = abs(int(step))
        self._count = count
        try:
            self._rel = LinkRel(step / self._step)
        except ZeroDivisionError:
            raise ValueError('step cannot be zero') from None
        self._cur = None

    @classmethod
    def from_slice(
        cls: type[LinkIter[V]],
        seq: LinkSequenceApi[V],
        slc: slice,
    /) -> LinkIter[V]:
        istart, stop, step = slc.indices(len(seq))
        count = (stop - istart) / step
        if count % 1: count += 1 # ceil
        start = None if count < 1 else seq._link_at(istart)
        return cls(start, step, int(count))

    def __iter__(self):
        return self

    @final
    def advance(self):
        if not self._count:
            self._cur = None
        elif self._cur is None:
            self._cur = self._start
        else:
            i = 0
            while i < self._step and self._cur is not None:
                i += 1
                self._cur = self._cur[self._rel]
        if self._cur is None:
            del self._start
            self._count = None
            raise StopIteration
        self._count -= 1

    def __next__(self) -> Link[V]:
        self.advance()
        return self._cur

class LinkValueIter(LinkIter[V]):
    'Linked sequence iterator over values.'

    __slots__ = EMPTY

    @classmethod
    def from_slice(
        cls: type[LinkValueIter[V]],
        seq: LinkSequenceApi[V],
        slc: slice,
    /) -> LinkValueIter[V]: ...
    from_slice = LinkIter.from_slice

    def __next__(self) -> V:
        self.advance()
        return self._cur.value

# ----------- LinkSequence ------------------ #

class LinkSequenceApi(bases.SequenceApi[V]):
    'Linked sequence read interface.'

    __slots__ = EMPTY

    @property
    @abstract
    def _link_first_(self) -> Link[V]:
        return None

    @property
    @abstract
    def _link_last_(self) -> Link[V]:
        return None

    def __iter__(self):
        return LinkValueIter(self._link_first_, 1)

    def __reversed__(self):
        return LinkValueIter(self._link_last_, -1)

    @overload
    def __getitem__(self, index: SupportsIndex) -> V:...
    @overload
    def __getitem__(self:T, index: slice) -> T: ...

    def __getitem__(self, index):
        '''Get element(s) by index/slice.

        Retrieves links using _link_at(index) method. Subclasses should
        avoid overriding this method, and instead override _link_at() for
        any performance enhancements.'''
        if isinstance(index, slice):
            return self._from_iterable(
                LinkValueIter.from_slice(self, index)
            )
        return self._link_at(index).value

    def _link_at(self, index: SupportsIndex) -> Link:
        'Get a Link entry by index. Supports negative value. Raises ``IndexError``.'

        index = _absindex(len(self), index)

        # Direct access for first/last.
        if index == 0:
            return self._link_first_
        if index == len(self) - 1:
            return self._link_last_

        # TODO: warn performance

        # Choose best iteration direction.
        if index > len(self) / 2:
            # Scan reversed from end.
            it = LinkIter(self._link_last_, index - len(self) + 1, 2)
        else:
            # Scan forward from beginning.
            it = LinkIter(self._link_first_, index, 2)

        # Advance iterator.
        it.advance()
        return next(it)

    def __repr__(self):
        import tools.misc as misc
        return misc.wraprepr(self, list(self))

class MutableLinkSequenceApi(LinkSequenceApi[V], bases.MutableSequenceApi[V]):
    'Linked sequence write interface.'
    __slots__  = EMPTY

    _new_link = Link
    # @abstract
    # def __setitem__(self, index: int|slice, value):
    #     ...

class linkseq(MutableLinkSequenceApi[V]):
    # __first : Link
    # __last  : Link

    # def __init__(self, values: Iterable = None, /):
    #     self.__first = None
    #     self.__last = None
    #     if values is not None:
    #         self.extend(values)
    # @property
    # def _link_first_(self) -> Link:
    #     return self.__first

    # @property
    # def _link_last_(self) -> Link:
    #     return self.__last

    ...

# ----------- LinkSequenceSet ------------------ #

class MutableLinkSequenceSetApi(MutableLinkSequenceApi[V], bases.MutableSequenceSetApi[V]):
    'Linked sequence set read/write interface.'

    __slots__ = EMPTY

    _new_link = HashLink

    @abstract
    def _link_of(self, value) -> Link:
        'Get a link entry by value. Implementations must raise ``MissingValueError``.'
        raise NotImplementedError

    @abstract
    def _seed(self, link: Link, /):
        'Add the link as the intial (only) member.'
        raise NotImplementedError

    @abstract
    def _wedge(self, rel: LinkRel, neighbor: Link, link: Link, /):
        'Add the new link and wedge it next to neighbor.'
        raise NotImplementedError

    @abstract
    def _unlink(self, link: Link):
        'Remove a link entry. Implementations must not alter the link attributes.'
        raise NotImplementedError

    def insert(self, index: int, value):
        '''Insert a value before an index. Raises ``DuplicateValueError`` and
        ``MissingValueError``.'''
        index = _absindex(len(self), index, False)
        if len(self) == 0:
            # Seed.
            self.seed(value)
        elif index >= len(self):
            # Append.
            self.wedge(1, self._link_last_.value, value)
        elif index <= 0:
            # Prepend.
            self.wedge(-1, self._link_first_.value, value)
        else:
            # In-between.
            self.wedge(-1, self._link_at(index).value, value)

    def __setitem__(self, index: SupportsIndex|slice, value):
        '''Set value by index/slice. Raises ``DuplicateValueError``.

        Retrieves the existing link at index using _link_at(), then calls
        remove() with the value. If the set is empty, seed() is called.
        Otherwise, wedge() is used to place the value after the old link's
        previous link, or, if setting the first value, before the old link's
        next link.
        
        Note that the old value is removed before the attempt to set the new value.
        This is to avoid double-calling the _new_value hook to check for membership.
        If a DuplicateValueError is raised, an attempt is made to re-add the old
        value using the old link attributes, skipping _new_value, _before_add, and
        _after_add hooks, by calling the _wedge method.'''
        if isinstance(index, slice):
            olds, values = self._setslice_prep(index, value)
            if len(olds) != len(values):
                raise Emsg.MismatchSliceSize(value, olds)
            it = LinkIter.from_slice(self, index)
            for link, v in zip(it, values):
                if v in self:
                    # Skip hooks since we are just re-ordering the value.
                    link.value = v
                    continue
                self.remove(link.value)
                if len(self) == 0:
                    self.seed(v)
                elif link.prev is not None:
                    self.wedge(1, link.prev.value, v)
                else:
                    self.wedge(-1, link.next.value, v)
            return

        link = self._link_at(index)
        self.remove(link.value)
        if len(self) == 0:
            self.seed(value)
            return
        try:
            if link.prev is not None:
                self.wedge(1, link.prev.value, value)
            else:
                self.wedge(-1, link.next.value, value)
        except DuplicateValueError:
            if link.prev is not None:
                self._wedge(1, link.prev, link)
            else:
                self._wedge(-1, link.next, link)
            raise

    def __delitem__(self, index: SupportsIndex|slice):
        '''Remove element(s) by index/slice.
        
        Retrieves the link with _link_at() and calls remove() with the value.
        
        For slices, an iterator is created from LinkIter.from_slice(), which
        uses _link_at() to retrieve the first link. Each value is deleted by
        calling remove() as it is yielded from the iterator. This avoids loading
        all values into memory, but assumes neither remove() nor _unlink() will
        modify the prev/next attributes of the Link object.'''
        if isinstance(index, slice):
            for value in LinkValueIter.from_slice(self, index):
                self.remove(value)
            return
        self.remove(self._link_at(index).value)

    def remove(self, value):
        '''Remove element by value. Raises ``MissingValueError``.
        
        Retrieves the link using _link_of and delegates to the subclass _unlink
        implementation. This handles the _after_remove hook.'''
        self._unlink(self._link_of(value))
        self._after_remove(value)

    def seed(self, value):
        '''Add the initial element. Raises ``IndexError`` if non-empty.

        This is called by __setitem__ and insert when the set is empty.
        This calls the _new_value hook and handles the _before_add and
        _after_add hooks, then delegates to the subclass _seed implementation.'''
        if len(self) > 0: raise IndexError
        value = self._new_value(value)
        self._before_add(value)
        self._seed(self._new_link(value))
        self._after_add(value)

    def wedge(self, rel: int, neighbor, value, /):
        '''Place a new value next to another value. Raises ``DuplicateValueError``
        and ``MissingValueError``.
        
        This is called by __setitem__ and insert when the set is non-empty.
        This calls the _new_value hook and handles the _before_add and
        _after_add hooks. The neighbor link is retrieved using _link_of.
        This handles missing/duplicate errors, and delegates to the subclass
        _wedge implementation.'''
        rel = LinkRel(rel)
        if rel is LinkRel.self:
            raise NotImplementedError
        neighbor = self._link_of(neighbor)
        value = self._new_value(value)
        if value in self:
            raise DuplicateValueError(value)
        self._before_add(value)
        self._wedge(rel, neighbor, self._new_link(value))
        self._after_add(value)

    def iter_from_value(self, value, /, reverse = False) -> Iterator[V]:
        'Return an iterator starting from ``value``.'
        return LinkValueIter(self._link_of(value), -1 if reverse else 1)

class linqset(MutableLinkSequenceSetApi[V]):
    'MutableLinkSequenceSetApi implementation.'

    __first : HashLink[V]
    __last  : HashLink[V]
    __links : dict[V, HashLink[V]]

    __slots__ = '__first', '__last', '__links'

    def __init__(self, values: Iterable = None, /):
        self.__links = {}
        self.__first = None
        self.__last = None
        if values is not None:
            self.update(values)

    @property
    def _link_first_(self) -> HashLink[V]:
        return self.__first

    @property
    def _link_last_(self) -> HashLink[V]:
        return self.__last

    def __len__(self):
        return len(self.__links)

    def __contains__(self, value: V):
        return value in self.__links

    def _link_of(self, value: V) -> HashLink[V]:
        if value in self.__links:
            return self.__links[value]
        raise MissingValueError(value)

    def _seed(self, link: Link, /):
        self.__first = \
        self.__last = \
        self.__links[link.value] = link

    def _wedge(self, rel: int, neighbor: Link, link: Link, /):
        link[rel] = neighbor[rel]
        link[-rel] = neighbor
        if neighbor[rel] is not None:
            # Point neighbor's old neighbor to new link.
            neighbor[rel][-rel] = link
        # Point neighbor to new link.
        neighbor[rel] = link
        if link[rel] is None:
            # Promote new first/last element.
            if rel == -1:
                self.__first = link
            else:
                self.__last = link
        self.__links[link.value] = link

    def _unlink(self, link: Link):
        if link.prev is None:
            if link.next is None:
                # No more elements.
                self.__first = None
                self.__last = None
            else:
                # Promote new first element.
                link.next.prev = None
                self.__first = link.next
        else:
            if link.next is None:
                # Promote new last element.
                link.prev.next = None
                self.__last = link.prev
            else:
                # Patch the gap.
                link.prev.next = link.next
                link.next.prev = link.prev
        del self.__links[link.value]

    def reverse(self):
        'Reverse in place.'
        link = self.__last
        while link is not None:
            link.invert()
            link = link.next
        self.__first, self.__last = self.__last, self.__first

    def sort(self, /, *, key = None, reverse = False):
        'Sort in place.'
        if len(self) < 2:
            return
        values = sorted(self, key = key, reverse = reverse)
        it = iter(values)
        link = None
        try:
            while True:
                link_prev = link
                link = self._link_of(next(it))
                link.prev = link_prev
                if link_prev is not None:
                    link_prev.next = link
        except StopIteration:
            link.next = None
        self.__first = self._link_of(values[0])
        self.__last = self._link_of(values[-1])

    def clear(self):
        'Clear the collection.'
        self.__links.clear()
        self.__first = None
        self.__last = None

    def copy(self):
        inst = object.__new__(type(self))
        inst.__links = links = type(self.__links)()
        it = LinkIter(self.__first)
        try:
            link = next(it)
        except StopIteration:
            inst.__first = inst.__last = None
        else:
            inst.__first = links[link.value] = link.copy()
            for link in it:
                links[link.value] = link.copy()
            inst.__last = link
        return inst

del(abstract, final, overload)