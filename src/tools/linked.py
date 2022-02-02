from __future__ import annotations

__all__ = (
    'LinkSequenceApi',
    'MutableLinkSequenceApi',
    'MutableLinkSequenceSetApi',
    'linqset',
)

from errors import (
    Emsg,
    DuplicateValueError,
    MissingValueError,
    instcheck,
)
from tools.abcs import T, VT
from tools.decorators import abstract, final, overload
from tools.sequences  import absindex, slicerange

class bases:
    from tools.abcs import Abc, Copyable
    from tools.sequences import SequenceApi, MutableSequenceApi
    from tools.hybrids import MutableSequenceSetApi

from collections.abc import Collection, Iterable, Iterator
from itertools import filterfalse
from typing import Generic, SupportsIndex, TypeVar

NOARG = object()
EMPTY = ()

import enum
class LinkRel(enum.IntEnum):
    'Link directional/subscript enum.'
    prev, self, next = -1, 0, 1

del(enum)

class Link(Generic[VT], bases.Copyable):
    'Link value container.'

    value: VT
    prev: Link[VT]
    next: Link[VT]

    __slots__ = 'prev', 'next', 'value'

    @property
    def self(self: LinkT) -> LinkT:
        return self
    # def __new__(cls, *a):
    #     inst = object.__new__(cls)
    #     inst.prev = inst.next = None
    #     return inst
    def __init__(self, value: VT, /, ):#prev: Link = None, nxt: Link = None, /):
        self.value = value
        self.prev = self.next = None
        # self.prev = prev
        # self.next = nxt

    def __getitem__(self, rel: int) -> Link[VT] | None:
        'Get previous, self, or next with -1, 0, 1, or ``LinkRel`` enum.'
        return getattr(self, LinkRel(rel)._name_)

    def __setitem__(self, rel: int, link: Link):
        'Set previous or next with -1, 1, or ``LinkRel`` enum.'
        setattr(self, LinkRel(rel)._name_, link)

    def invert(self):
        'Invert prev and next attributes in place.'
        self.prev, self.next = self.next, self.prev

    # def copy(self, value = NOARG):
    def copy(self):
        inst = type(self)(self.value)
        inst.prev = self.prev
        inst.next = self.next
        return inst
        # cls = type(self)
        # inst = cls.__new__(cls)
        # if value is NOARG:
        #     inst.value = self.value
        # else:
        #     inst.value = value
        # inst.prev = self.prev
        # inst.next = self.next
        # return inst

    def __repr__(self):
        from tools.misc import wraprepr
        return wraprepr(self, self.value)

class HashLink(Link[VT]):

    __slots__ = EMPTY

    def __eq__(self, other):
        if self is other:
            return True
        if isinstance(other, type(self)):
            return self.value == other.value
        return self.value == other

    def __hash__(self):
        return hash(self.value)

class LinkIter(Iterator[Link[VT]], bases.Abc):
    'Linked sequence iterator.'

    _start : Link
    _step  : int
    _rel   : LinkRel
    _count : int
    _cur   : Link

    __slots__ = '_start', '_step', '_count', '_cur', '_rel'

    def __init__(self, start: Link, step: int = 1, count: int = -1, /):
        self._start = start if count else None
        self._step  = abs(int(step))
        self._count = count
        try:
            self._rel = LinkRel(step / self._step)
        except ZeroDivisionError:
            raise ValueError('step cannot be zero') from None
        self._cur = None

    @classmethod
    def from_slice(cls: type[LinkIterT],
        seq: LinkSequenceApi[VT],
        slc: slice,
    /) -> LinkIterT:
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

    def __next__(self) -> Link[VT]:
        self.advance()
        return self._cur

class LinkValueIter(LinkIter[VT]):
    'Linked sequence iterator over values.'

    __slots__ = EMPTY

    @classmethod
    def from_slice(
        cls: type[LinkValueIter[VT]],
        seq: LinkSequenceApi[VT],
        slc: slice,
    /) -> LinkValueIter[VT]: ...
    from_slice = LinkIter.from_slice

    def __next__(self) -> VT:
        self.advance()
        return self._cur.value

# ----------- LinkSequence ------------------ #

class LinkSequenceApi(bases.SequenceApi[VT]):
    'Linked sequence read interface.'

    __slots__ = EMPTY

    @property
    @abstract
    def _link_first_(self) -> Link[VT]:
        return None

    @property
    @abstract
    def _link_last_(self) -> Link[VT]:
        return None

    def __iter__(self) -> Iterator[VT]:
        return LinkValueIter(self._link_first_, 1)

    def __reversed__(self) -> Iterator[VT]:
        return LinkValueIter(self._link_last_, -1)

    @overload
    def __getitem__(self, index: SupportsIndex, /) -> VT:...

    @overload
    def __getitem__(self: LinkSeqT, slice_: slice, /) -> LinkSeqT: ...

    def __getitem__(self, i):
        '''Get element(s) by index/slice.

        Retrieves links using _link_at(index) method. Subclasses should
        avoid overriding this method, and instead override _link_at() for
        any performance enhancements.'''

         # ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ Index Implementation ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ #

        if isinstance(i, SupportsIndex): return self._link_at(i).value

         # ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ Slice Implementation ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ #

        return self._from_iterable(
            LinkValueIter.from_slice(self, instcheck(i, (slice, int)))
        )

    def _link_at(self, index: SupportsIndex) -> Link[VT]:
        'Get a Link entry by index. Supports negative value. Raises ``IndexError``.'

        index = absindex(len(self), index)

        # Direct access for first/last.
        if index == 0:
            return self._link_first_
        if index == len(self) - 1:
            return self._link_last_

        # TODO: Raise performance warning.

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
        from tools.misc import wraprepr
        return wraprepr(self, list(self))


LinkT     = TypeVar('LinkT',     bound = Link)
LinkIterT = TypeVar('LinkIterT', bound = LinkIter)
LinkSeqT  = TypeVar('LinkSeqT',  bound = LinkSequenceApi)


class MutableLinkSequenceApi(LinkSequenceApi[VT], bases.MutableSequenceApi[VT]):
    'Linked sequence write interface.'
    __slots__  = EMPTY

    _new_link = Link
    # @abstract
    # def __setitem__(self, index: int|slice, value):
    #     ...

class linkseq(MutableLinkSequenceApi[VT]):
    pass
    # TODO
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

class MutableLinkSequenceSetApi(MutableLinkSequenceApi[VT], bases.MutableSequenceSetApi[VT]):
    'Linked sequence set read/write interface.'

    #: Class or method for creating Link objects.
    _new_link: type[Link] = HashLink
    __slots__ = EMPTY

    # - - -- - - -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    # ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ Subclass Implementation Methods ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ 
    # - - -- - - -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    @abstract
    def _link_of(self, value: VT) -> Link[VT]:
        'Get a link entry by value. Should raise ``MissingValueError``.'
        raise MissingValueError

    @abstract
    def _seed(self, link: Link, /):
        'Add the link as the intial (only) member.'
        raise TypeError

    @abstract
    def _wedge(self, rel: LinkRel, neighbor: Link, link: Link, /):
        'Add the new link and wedge it next to neighbor.'
        raise NotImplementedError

    @abstract
    def _unlink(self, link: Link):
        'Remove a link entry. Implementations must not alter the link attributes.'
        raise NotImplementedError
    # - - -- - - -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    # - - -- - - -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 


    def insert(self, index: SupportsIndex, value: VT):
        '''Insert a value before an index. Raises ``DuplicateValueError`` and
        ``MissingValueError``.'''
        index = absindex(len(self), index, False)
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

    def __setitem__(self, index: SupportsIndex|slice, value: VT|Collection[VT]):
        '''Set value(s) by index/slice. Raises ``DuplicateValueError``.

        Retrieves the existing link at index using _link_at(), then calls
        remove() with the value. If the set is empty, seed() is called.
        Otherwise, wedge() is used to place the value after the old link's
        previous link, or, if setting the first value, before the old link's
        next link.

        .. following notes N/A since these hooks are being removed ...

        Note that the old value is removed before the attempt to set the new value.
        This is to avoid double-calling the _new_value hook to check for membership.
        If a DuplicateValueError is raised, an attempt is made to re-add the old
        value using the old link attributes, skipping _new_value and _before_add hooks,
        by calling the _wedge method.'''

        # ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ Index Implementation ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ #

        if isinstance(index, SupportsIndex):

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
            return

        # ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ Slice Implementation ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ ◀︎▶︎ #

        slice_ = instcheck(index, slice)
        # check for set? convert to seqset first?
        values = instcheck(value, Collection)
        del(index, value)

        range_ = slicerange(len(self), slice_, values)

        # This should fail if subclass does not suppor slice.
        olds = self[slice_]

        # Any value that is already in our set, and is not in the old values to
        # remove is a duplicate.

        for v in filterfalse(olds.__contains__, filter(self.__contains__, values)):
            raise DuplicateValueError(v)

        it = LinkIter.from_slice(self, slice_)
        for link, v in zip(it, values):
            if v in self:
                # Re-ordering the value. This is assuming the
                # duplicate checks performed above.
                link.value = v
                continue
                        
            self.remove(link.value)

            if len(self) == 0:
                self.seed(v)
            elif link.prev is not None:
                self.wedge(1, link.prev.value, v)
            else:
                self.wedge(-1, link.next.value, v)


    def __delitem__(self, index: SupportsIndex|slice):
        '''Remove element(s) by index/slice.
        
        Retrieves the link with _link_at() and calls remove() with the value.
        
        For slices, an iterator is created from LinkIter.from_slice(), which
        uses _link_at() to retrieve the first link. Each value is deleted by
        calling remove() as it is yielded from the iterator. This avoids loading
        all values into memory, but assumes neither remove() nor _unlink() will
        modify the prev/next attributes of the Link object.'''
        # ◀︎▶︎ Index Implementation ◀︎▶︎ 
        if isinstance(index, SupportsIndex):
            self.remove(self._link_at(index).value)
            return

        # ◀︎▶︎ Slice Implementation ◀︎▶︎ 
        slice_ = instcheck(index, slice)
        for _ in map(self.remove, LinkValueIter.from_slice(self, slice_)):
            pass

    def remove(self, value: VT):
        '''Remove element by value. Raises ``MissingValueError``.
        
        Retrieves the link using _link_of and delegates to the subclass _unlink
        implementation.'''
        self._unlink(self._link_of(value))

    def seed(self, value):
        '''Add the initial element. Raises ``IndexError`` if non-empty.
        This is called by __setitem__ and insert when the set is empty.

        .. old notes ...

        This calls the _new_value hook and handles the _before_add hook,
        then delegates to the subclass _seed implementation.'''
        if len(self) > 0: raise IndexError
        self._seed(self._new_link(value))


    def wedge(self, rel: int, neighbor, value, /):
        '''Place a new value next to another value. Raises ``DuplicateValueError``
        and ``MissingValueError``.
        
        This is called by __setitem__ and insert when the set is non-empty.
        The neighbor link is retrieved using _link_of. This handles missing/duplicate
        errors, and delegates to the subclass _wedge implementation.'''
        rel = LinkRel(rel)
        if rel is LinkRel.self:
            raise NotImplementedError
        neighbor = self._link_of(neighbor)
        if value in self:
            raise DuplicateValueError(value)
        self._wedge(rel, neighbor, self._new_link(value))

    def iter_from_value(self, value, /, reverse = False) -> Iterator[VT]:
        'Return an iterator starting from ``value``.'
        return LinkValueIter(self._link_of(value), -1 if reverse else 1)


class linqset(MutableLinkSequenceSetApi[VT]):
    '''MutableLinkSequenceSetApi implementation for hashable values, based on
    a dict index. Inserting and removing is fast (constant) no matter where
    in the list, *so long as positions are referenced by value*. Accessing
    by numeric index requires iterating from the front or back.'''

    __first : HashLink[VT]
    __last  : HashLink[VT]
    __links : dict[VT, HashLink[VT]]

    __slots__ = '__first', '__last', '__links'

    def __init__(self, values: Iterable[VT] = None, /):
        self.__links = {}
        self.__first = None
        self.__last = None
        if values is not None:
            self.update(values)

    @property
    def _link_first_(self) -> HashLink[VT]:
        return self.__first

    @property
    def _link_last_(self) -> HashLink[VT]:
        return self.__last

    def __len__(self):
        return len(self.__links)

    def __contains__(self, value: VT):
        return value in self.__links

    def _link_of(self, value: VT) -> HashLink[VT]:
        'Get a Link by its value.'
        try: return self.__links[value]
        except KeyError: pass
        raise MissingValueError(value)

    def _seed(self, link: Link, /):
        'Store the initial link. Collection is guaranteed to be empty.'
        self.__first = \
        self.__last = \
        self.__links[link.value] = link

    def _wedge(self, rel: int, neighbor: Link, link: Link, /):
        'Insert a Link before or after another Link already in the sequence.'
        # Example:
        #  
        #   Let rel == -1 (prev), meaning we must insert {link}
        #   before {neighbor}. Thus -rel == 1 (next)
        #
        # So now {link.next} is {neigbor}
        link[-rel] = neighbor
        # We need to be after whoever neighbor was after (if anyone).
        # So now {link.prev} is {neigbor.prev}, (which might be null).
        link[rel] = neighbor[rel]

        if neighbor[rel] is not None:
            # If it is non-null, then {neighbor} has a link behind it.
            # We point that link's `.next` attribute to our new {link}.
            neighbor[rel][-rel] = link

        # Now {neighbor.prev} should point to the new {link}.
        neighbor[rel] = link

        if link[rel] is None:
            # However, if {neighbor} did not have a link behind, then
            # our {link} is now the first element (in our case).
            if rel == -1:
                self.__first = link
            # But if rel were instead 1, it would be opposite, and our
            # new {link} would be the last element.
            else:
                self.__last = link
        # Add to index.
        self.__links[link.value] = link

    def _unlink(self, link: Link):
        'Remove the Link from the sequence.'
        if link.prev is None:
            # Removing the first element.
            if link.next is None:
                # And only element.
                self.__first = None
                self.__last = None
            else:
                # Promote new first element.
                link.next.prev = None
                self.__first = link.next
        elif link.next is None:
            # Removing the last element (but not the only element).
            # Promote new last element.
            link.prev.next = None
            self.__last = link.prev
        else:
            # Removing a link the middle.
            # Sew up the gap.
            link.prev.next = link.next
            link.next.prev = link.prev
        # Remove from index.
        del self.__links[link.value]

    def reverse(self):
        'Reverse in place.'
        link = self.__last
        while link is not None:
            link.invert()
            link = link.next
        self.__first, self.__last = self.__last, self.__first

    def sort(self, /, *, key = None, reverse = False):
        '''Sort in place. Creates list of the values in memory using ``sorted()``.
        Then iterates over those sorted values, retrieving the internal link
        objects via the value -> link dict index, updating the prev/next
        attributes.'''
        if len(self) < 2: return
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
        'Copy the collection. Copies the index and the internal Link objects.'
        # ------ build the objects and index
        index =  type(self.__links)()
        prev = None
        for link in map(self._new_link, self):
            index[link.value] = link
            link.prev = prev
            if prev: prev.next = link
            prev = link
        # ---- create the instance
        cls = type(self)
        inst = cls.__new__(cls)
        if index:
            inst.__first = index[next(iter(index))]
            inst.__last  = index[next(reversed(index))]
        else:
            inst.__first = None
            inst.__last = None
        inst.__links = index
        return inst


del(abstract, final, overload, bases)