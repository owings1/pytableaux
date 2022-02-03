from __future__ import annotations

__all__ = (
    'LinkSequence',
    'MutableLinkSequence',
    'MutableLinkSequenceSet',
    'linqset',
)

from errors import (
    Emsg,
    DuplicateValueError,
    MissingValueError,
    instcheck,
)
from tools.abcs import (
    abcm, abcf, Abc, Copyable, IntEnum,
    VT,
    #T, VT_co
)
from tools.decorators import abstract, final, overload
from tools.hybrids import MutableSequenceSetApi
from tools.sequences  import (
    absindex,
    slicerange,
    SequenceApi,
    MutableSequenceApi,
)
from tools.sets import EMPTY_SET

from collections.abc import (
    Collection,
    Iterable,
    Iterator,
)
from itertools import filterfalse
from typing import (
    Generic,
    Literal,
    SupportsIndex,
    TypeVar,
)

NOARG = object()


# - - -- - - -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
#
#  Helper Classes
#
# - - -- - - -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

class LinkRel(IntEnum):
    'Link directional/subscript enum.'
    prev = -1
    self = 0
    next = 1

class Link(Generic[VT], Copyable):
    'Link value container.'

    value: VT
    prev: Link[VT]
    next: Link[VT]

    __slots__ = 'prev', 'next', 'value'
    __iter__ = None

    @property
    def self(self: LinkT) -> LinkT:
        return self

    def __init__(self, value: VT, /, ):
        self.value = value
        self.prev = self.next = None

    def copy(self):
        inst = type(self)(self.value)
        inst.prev = self.prev
        inst.next = self.next
        return inst

    # def __getitem__(self, rel: int) -> Link[VT] | None:
    def __getitem__(self: LinkT, rel: int) -> LinkT | None:
        'Get previous, self, or next with -1, 0, 1, or ``LinkRel`` enum.'
        return getattr(self, LinkRel(rel)._name_)

    def __setitem__(self, rel: int, link: Link):
        'Set previous or next with -1, 1, or ``LinkRel`` enum.'
        setattr(self, LinkRel(rel)._name_, link)

    def invert(self):
        'Invert prev and next attributes in place.'
        self.prev, self.next = self.next, self.prev

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, self.value.__repr__())

class HashLink(Link[VT]):
    'Link container for a hashable value.'

    __slots__ = EMPTY_SET

    prev: HashLink[VT]
    next: HashLink[VT]

    def __eq__(self, other):
        if self is other:
            return True
        if isinstance(other, type(self)):
            return self.value == other.value
        return self.value == other

    def __hash__(self):
        return hash(self.value)

LinkT     = TypeVar('LinkT',    bound = Link)
LinkT_co  = TypeVar('LinkT_co', bound = Link, covariant = True)

class LinkIter(Iterator[LinkT_co], Abc):
    'Linked sequence iterator.'

    _start : LinkT_co
    _step  : int
    _rel   : LinkRel
    _count : int
    _cur   : LinkT_co

    __slots__ = '_start', '_step', '_count', '_cur', '_rel'

    def __init__(self, start: LinkT_co, step: int = 1, count: int = -1, /):
        self._start = start if count else None
        self._step  = abs(int(step))
        self._count = count
        try:
            self._rel = LinkRel(step / self._step)
        except ZeroDivisionError:
            raise ValueError('step cannot be zero') from None
        self._cur = None

    @classmethod
    def from_slice(cls: type[LinkIter[Link[VT]]], seq: LinkSequence[VT], slice_: slice,
    /) -> LinkIter[Link[VT]]:
        # TODO: lazy search for the start?
        istart, stop, step = slice_.indices(len(seq))
        count = _ceil((stop - istart) / step)
        if count < 1:
            start = None
        else:
            start = seq._link_at(istart)
        inst = cls(start, step, count)
        return inst

    def __iter__(self):
        return self

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

    # def __next__(self) -> LinkT_co:
    def __next__(self):
        self.advance()
        return self._cur

class LinkValueIter(LinkIter[Link[VT]]):
    'Linked sequence iterator over values.'

    __slots__ = EMPTY_SET

    @classmethod
    @overload
    def from_slice(cls: type[LinkValueIter[VT]], seq: LinkSequence[VT], slice_: slice,
    /) -> LinkValueIter[VT]: ...
    from_slice = LinkIter.from_slice

    def __next__(self) -> VT:
        self.advance()
        return self._cur.value

# - - -- - - -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
#
#  Sequence Classes
#
# - - -- - - -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 

class LinkSequence(SequenceApi[VT]):
    'Linked sequence read interface.'

    __slots__ = EMPTY_SET

    @abstract
    def _link_first(self) -> Link[VT]:
        'Return the first Link object, or None.'
        return None

    @abstract
    def _link_last(self) -> Link[VT]:
        'Return the last Link object, or None.'
        return None

    def __iter__(self) -> Iterator[VT]:
        return LinkValueIter(self._link_first(), 1)

    def __reversed__(self) -> Iterator[VT]:
        return LinkValueIter(self._link_last(), -1)

    @overload
    def __getitem__(self, index: SupportsIndex, /) -> VT:...

    @overload
    def __getitem__(self: LinkSeqT, slice_: slice, /) -> LinkSeqT: ...

    def __getitem__(self, i):
        'Get element(s) by index/slice.'
        # Retrieves link(s) using _link_at(index) method. Subclasses should
        # avoid overriding this method, and instead override _link_at() for
        # any performance enhancements.

        if isinstance(i, SupportsIndex):
            # Index Implementation
            return self._link_at(i).value

        if isinstance(i, slice):
            # Slice Implementation
            return self._from_iterable(
                LinkValueIter.from_slice(self, i)
            )

        raise Emsg.InstCheck(i, (SupportsIndex, slice))

    def _link_at(self, index: SupportsIndex) -> Link[VT]:
        'Get a Link entry by index. Supports negative value. Raises ``IndexError``.'

        length = len(self)
        index = absindex(length, index)

        # Direct access for first/last.
        if index == 0:
            return self._link_first()
        if index == length - 1:
            return self._link_last()

        # TODO: Raise performance warning.

        # Choose best iteration direction.
        if index > length / 2:
            # Scan reversed from end.
            it = LinkIter(self._link_last(), index - length + 1, 2)
        else:
            # Scan forward from beginning.
            it = LinkIter(self._link_first(), index, 2)

        # Advance iterator.
        it.advance()
        return next(it)

    def _link_of(self, value: VT) -> Link[VT]:
        'Get a link entry by value. Should raise ``MissingValueError``.'
        for link in LinkIter(self._link_first()):
            if link.value == value:
                return link
        raise MissingValueError(value)
        
    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, list(self).__repr__())

class MutableLinkSequence(LinkSequence[VT], MutableSequenceApi[VT]):
    'Linked sequence mutable base methods.'

    __slots__  = EMPTY_SET

    _link_type_: type[Link[VT]] = Link

    # - - -- - - -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    #                 Abstract Methods
    # - - -- - - -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 

    # _link_first, _link_last, __len__, sort

    @abstract
    def _seed(self, link: Link[VT], /):
        '''Add the Link as the intial (only) member. This is called by __setitem__,
        insert, append, etc., when the collection is empty.'''
        raise IndexError

    @abstract
    def _spot(self, rel: Literal[LinkRel.prev]|Literal[LinkRel.next],
        neighbor: Link[VT], link: Link[VT], /):
        'Insert a Link before or after another Link already in the collection.'
        # --------------------------------------------------------------
        # This provides a partial implementation that adjusts the prev/next
        # attributes of the links, but does not implement adjusting the
        # first/last properties of the sequence.
        #
        # Instead, the return value can be used to determine if first or
        # last should be set.
        #
        #   - A return value of ``-1`` (LinkRel.prev) means the link
        #     should be set as the first link.
        #
        #   - A return value of ``1`` (LinkRel.next) means the link
        #     should be set as the last link.
        #
        #   - A return value of ``None`` means neither should be set.
        # --------------------------------------------------------------

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
            #
            # if rel == -1:
            #   set first := link
            #
            # But if rel were instead 1, it would be opposite, and our
            # new {link} would be the last element.
            #
            # else:
            #   set last := link
            #
            return rel
        return None

    @abstract
    def _unlink(self, link: Link[VT]):
        'Remove a Link entry. Implementations must not alter the link attributes.'
        # --------------------------------------------------------------
        # This provides a partial implementation that adjusts the prev/next
        # attributes of the links, but does not implement adjusting the
        # first/last properties of the sequence.
        #
        # Instead, the return value can be used to determine if first or
        # last should be set.
        #
        #   - A return value of ``None``  means no adjustment to first or last
        #     should be made.
        #
        #   - Otherwise the return value is a tuple (first, last). Either
        #     or both values could be ``None``, meaning they should be set
        #     to ``None``, or unset. If only value should change, the other
        #     is retrieved by _link_first() or _link_last() and returned.
        if link.prev is None:
            # Removing the first element.
            if link.next is None:
                # And only element.
                # Unset both first and last (empty)
                return None, None
            else:
                # Promote new first element.
                link.next.prev = None
                # Update the first, keep the last
                return link.next, self._link_last()
        elif link.next is None:
            # Removing the last element (but not the only element).
            # Promote new last element.
            link.prev.next = None
            # Keep the first, update the last
            return self._link_first(), link.prev
        else:
            # Removing a link the middle.
            # Sew up the gap.
            link.prev.next = link.next
            link.next.prev = link.prev
        # No change to first or last
        return None

    # - - -- - - -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 

    @abcm.hookable('cast')
    def insert(self, index: SupportsIndex, value: VT, /, *,
        cast = None
    ):
        '''Insert a value before an index. Raises ``MissingValueError``.'''
        length = len(self)
        index = absindex(length, index, False)
        if cast is not None:
            value = cast(value)
        newlink = self._link_type_(value)
        if length == 0:
            # Seed.
            self._seed(newlink)
            # self.seed(value)
        elif index >= length:
            # Append.
            self._spot(1, self._link_last(), newlink)
        elif index <= 0:
            # Prepend.
            self._spot(-1, self._link_first(), newlink)
        else:
            # In-between.
            self._spot(-1, self._link_at(index), newlink)

    def remove(self, value: VT):
        'Remove element by value. Raises ``MissingValueError``.'        
        self._unlink(self._link_of(value))

    def __delitem__(self, i: SupportsIndex|slice):
        'Remove element(s) by index/slice.'

        if isinstance(i, SupportsIndex):
            # Index Implementation
            self._unlink(self._link_at(i))
            return

        if isinstance(i, slice):
            # Slice Implementation
            #
            # Values are removed lazily, as they are yielded from the iterator.
            # This avoids reloading all values into memory, but assumes
            # _unlink() will modify the prev/next attributes of the Link object.
            for _ in map(self._unlink, LinkIter.from_slice(self, i)):
                pass
            return

        raise Emsg.InstCheck(i, (SupportsIndex, slice))

    @abcm.hookable('cast')
    def __setitem__(self, i: SupportsIndex|slice, value: VT|Collection[VT],
        /, *, cast = None):
        'Set value(s) by index/slice. Raises ``IndexError.'

        if isinstance(i, SupportsIndex):
            index = i
            arrival = value
            if cast is not None:
                arrival = cast(arrival)
            departure = self._link_at(index)

            self.__setitem_index__(index, arrival, departure)
            return

        if isinstance(i, slice):
            slice_ = i
            arrivals = value
            if cast is not None:
                arrivals = tuple(map(cast, arrivals))
            else:
                instcheck(arrivals, Collection)
            range_ = slicerange(len(self), slice_, arrivals)
            if not len(range_):
                return
            self.__setitem_slice__(slice_, arrivals, range_)
            return

        raise Emsg.InstCheck(i, (SupportsIndex, slice))

    @abcm.hookable('check')
    def __setitem_index__(self, index: SupportsIndex, arrival: VT, departure: Link[VT],
        /, *, check = None):
        'Index setitem Implementation'
        if check is not None:
            check(self, (arrival,), (departure.value,))
        departure.value = arrival

    @abcm.hookable('check')
    def __setitem_slice__(self: MutLinkSeqT, slice_: slice, arrivals: Collection[VT], 
        range_: range,/,*, check = None):
        'Slice setitem Implementation'
        if check is not None:
            # TODO: optimize -- get first link only once, so we don't have
            # to find it twice.
            departures = self[slice_]
            check(self, arrivals, departures)
        link_it = LinkIter.from_slice(self, slice_)
        for link, arrival in zip(link_it, arrivals):
            link.value = arrival

class linkseq(MutableLinkSequence[VT]):
    _link_type_: type[Link[VT]] = Link

    __first : Link[VT]
    __last  : Link[VT]
    __len   : int

    __slots__ = '__first', '__last', '__len'

    def __new__(cls, *args, **kw):
        inst = super().__new__(cls)
        inst.__len = 0
        inst.__first = None
        inst.__last = None
        return inst

    def __init__(self, values: Iterable[VT] = None, /):
        if values is not None:
            self.extend(values)

    def _link_first(self) -> Link[VT]:
        return self.__first

    def _link_last(self) -> Link[VT]:
        return self.__last

    def __len__(self):
        return self.__len

    def _seed(self, link: Link[VT], /):
        if self.__len != 0:
            raise IndexError
        self.__first = self.__last = link
        self.__len += 1

    def _spot(self, rel: LinkRel, neighbor: Link[VT], link: Link[VT], /):
        ret = super()._spot(rel, neighbor, link)
        if ret is not None:
            if ret == -1:
                self.__first = link
            else:
                self.__last = link
        self.__len += 1

    def _unlink(self, link: Link[VT]):
        ret = super()._unlink(link)
        if ret is not None:
            self.__first, self.__last = ret
        self.__len -= 1

    # TODO:

    @abstract
    def sort(self, /, *, key = None, reverse = False):
        raise NotImplementedError

# ----------- LinkSequenceSet ------------------ #

class MutableLinkSequenceSet(MutableLinkSequence[VT], MutableSequenceSetApi[VT]):
    'Linked sequence set read/write interface.'

    #: Link object class.
    _link_type_: type[HashLink[VT]] = HashLink
    __slots__ = EMPTY_SET

    # - - -- - - -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    #                 Abstract Methods
    # - - -- - - -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 

    @abstract
    def _link_of(self, value: VT) -> Link[VT]:
        'Get a link entry by value. Should raise ``MissingValueError``.'
        # Re-declared abstract for set-based implementation.
        raise MissingValueError

    # - - -- - - -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 

    @abcm.hookable('cast')
    def wedge(self, value: VT, neighbor: VT, rel: Literal[-1]|Literal[1], /, *,
        cast = None
    ):
        '''Place a new value next to (before or after) another value. Raises
        ``DuplicateValueError`` and ``MissingValueError``.
        
        This is the most performant way to insert a new value anywhere in the
        collection, with speed O(1).  Methods that add by index (__setitem__,
        insert, etc.) will first iterate to find the index, then call this method.

        :param value: The new value to add.
        :param neighbor: The existing element next to which to place the value.
        :param int rel: ``-1`` to place before, or ``1`` to place after neighbor.

        :raises errors.DuplicateValueError:
        :raises errors.MissingValueError:
        '''
        rel = LinkRel(rel)
        if rel is LinkRel.self:
            raise TypeError
        neighbor: Link[VT] = self._link_of(neighbor)
        if cast is not None:
            value = cast(value)
        if value in self:
            raise DuplicateValueError(value)
        newlink = self._link_type_(value)
        self._spot(rel, neighbor, newlink)


    @abcf.temp
    @abcm.hookable('check')
    @MutableLinkSequence.hook('check')
    def dupecheck(self, arrivals: Collection[VT], departures: Collection[VT], 
        /, *, check = None):

        for v in filterfalse(departures.__contains__, filter(self.__contains__, arrivals)):
            raise DuplicateValueError(v)
        if check is not None:
            check(self, arrivals, departures)
    # def __setitem_index__(self, index: SupportsIndex, arriving, /):
    #     'Index setitem Implementation'

    #     link = self._link_at(index)
    #     leaving = link.value

    #     #  Check for duplicates
    #     if arriving in self and arriving != leaving:
    #         raise DuplicateValueError(arriving)

    #     link.value = arriving

    # def __setitem_slice__(self, slice_: slice, arriving: Collection[VT], range_: range,/,):
    #     'Slice setitem Implementation'

    #     # Any value that is already in our set, and is not in the old values to
    #     # remove is a duplicate.
    #     leaving = self[slice_]


    #     for v in filterfalse(leaving.__contains__, filter(self.__contains__, arriving)):
    #         raise DuplicateValueError(v)

    #     link_it = LinkIter.from_slice(self, slice_)
    #     for link, v in zip(link_it, arriving):
    #         link.value = v

    def iter_from_value(self, value: VT, /, *,
        reverse = False, step: int = 1
    ) -> Iterator[VT]:
        'Return an iterator starting from ``value``.'
        return LinkValueIter(self._link_of(value), -step if reverse else step)

    __setitem__ = MutableLinkSequence.__setitem__
    @abcf.before
    def copyhooks(ns: dict, bases):
        src = abcm.hookinfo(MutableLinkSequence)
        # print('src', src)
        # print(src.attrs())
        from tools.abcs import HookInfo

        return
        src = abcm.hookinfo(MutableLinkSequence)
        for hook, hookmap in src.items():
            for name, member in hookmap.items():
                if name not in ns:
                    ns[name] = member
                    ...
        res = {} #..
        ahooks = set(src.keys())
        bhooks = set(res.keys())
        ahooks - bhooks

        return
        (item for items in (
            (zip(repeat(hook), hmap.keys()) for hook, hmap in res.items())
        ) for item in items)
        (zip(repeat(hook), hmap.keys()) for hook, hmap in src.items())
        anames = (name for hmap in src.values() for name in hmap.keys())
        bnames = (name for hmap in res.values() for name in hmap.keys())

        (name for hmap in res.values() for name in hmap.keys())
        set(chain.from_iterable(hmap.keys() for hmap in src.values())).difference(
            set(chain.from_iterable(hmap.keys() for hmap in res.values()))
        )
class linqset(MutableLinkSequenceSet[VT]):
    '''MutableLinkSequenceSet implementation for hashable values, based on
    a dict index. Inserting and removing is fast (constant) no matter where
    in the list, *so long as positions are referenced by value*. Accessing
    by numeric index requires iterating from the front or back.'''

    __first : HashLink[VT]
    __last  : HashLink[VT]
    __table : dict[VT, HashLink[VT]]

    __slots__ = '__first', '__last', '__table'

    def __new__(cls, *args, **kw):
        inst = super().__new__(cls)
        inst.__table = {}
        inst.__first = None
        inst.__last = None
        return inst

    def __init__(self, values: Iterable[VT] = None, /):
        if values is not None:
            self.update(values)

    def copy(self):
        'Copy the collection. Copies the index and the internal Link objects.'
        # ------ build the objects and index
        index =  type(self.__table)()
        prev = None
        for link in map(self._link_type_, self):
            index[link.value] = link
            link.prev = prev
            if prev:
                prev.next = link
            prev = link
        # ---- create the instance
        cls = type(self)
        inst = super().__new__(cls)
        if index:
            inst.__first = index[next(iter(index))]
            inst.__last  = index[next(reversed(index))]
        else:
            inst.__first = None
            inst.__last = None
        inst.__table = index
        return inst

    def _link_first(self) -> HashLink[VT]:
        return self.__first

    def _link_last(self) -> HashLink[VT]:
        return self.__last

    def __len__(self):
        return len(self.__table)

    def __contains__(self, value: VT):
        return value in self.__table

    def _link_of(self, value: VT) -> HashLink[VT]:
        try: return self.__table[value]
        except KeyError: pass
        raise MissingValueError(value) from None

    def _seed(self, link: HashLink[VT], /):
        self.__first = \
        self.__last = \
        self.__table[link.value] = link

    def _spot(self, rel: LinkRel, neighbor: HashLink[VT], link: HashLink[VT], /):
        ret = super()._spot(rel, neighbor, link)
        if ret is not None:
            if ret == -1:
                self.__first = link
            else:
                self.__last = link
        # Add to index.
        self.__table[link.value] = link

    def _unlink(self, link: Link):
        ret = super()._unlink(link)
        if ret is not None:
            self.__first, self.__last = ret
        # Remove from index.
        del self.__table[link.value]
        # return
        # if link.prev is None:
        #     # Removing the first element.
        #     if link.next is None:
        #         # And only element.
        #         self.__first = None
        #         self.__last = None
        #     else:
        #         # Promote new first element.
        #         link.next.prev = None
        #         self.__first = link.next
        # elif link.next is None:
        #     # Removing the last element (but not the only element).
        #     # Promote new last element.
        #     link.prev.next = None
        #     self.__last = link.prev
        # else:
        #     # Removing a link the middle.
        #     # Sew up the gap.
        #     link.prev.next = link.next
        #     link.next.prev = link.prev
        # # Remove from index.
        # del self.__table[link.value]

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
        self.__table.clear()
        self.__first = None
        self.__last = None


LinkIterT    = TypeVar('LinkIterT', bound = LinkIter)
LinkSeqT     = TypeVar('LinkSeqT',  bound = LinkSequence)
MutLinkSeqT  = TypeVar('MutLinkSeqT', bound = MutableLinkSequence)

def _ceil(n):
    if n % 1: n += 1
    return int(n)

del(
    abstract, final, overload,
    abcm, Abc, Copyable, IntEnum,
    TypeVar,
)