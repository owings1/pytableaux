from __future__ import annotations

__all__ = (
    'LinkSequence',
    'linkseq',
    'linqset',
)

from errors import (
    Emsg,
    instcheck,
)
from tools import abstract
from tools.abcs import (
    abcm,
    Abc, Copyable, IntEnum,
    static
)
from tools.hybrids import MutableSequenceSet
from tools.sequences  import (
    absindex,
    slicerange,
    SequenceApi,
    MutableSequenceApi,
)
from tools.sets import EMPTY_SET
from tools.typing import VT

from itertools import filterfalse
from typing import (
    final, overload,
    Collection,
    Generic,
    Iterable,
    Iterator,
    Literal,
    SupportsIndex,
    TypeVar,
)

NOARG = object()


#====================================
#  Helper Classes
#====================================

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

@static
class linkiter:

    def links(origin: Link[VT], step: int = 1, count: int = -1, /) -> Iterator[Link[VT]]:
        stepabs = abs(int(step))
        try:
            rel = LinkRel(step / stepabs)
        except ZeroDivisionError:
            raise ValueError('step cannot be zero') from None
        cur = origin
        while count and cur:
            yield cur
            count -= 1
            if count:
                i = 0
                while i < stepabs and cur is not None:
                    i += 1
                    cur = cur[rel]

    def links_sliced(seq: LinkSequence[VT], slice_: slice) -> Iterator[Link[VT]]:
        start, stop, step = slice_.indices(len(seq))
        count = (stop - start) / step
        count = int(count + 1 if count % 1 else count)
        if count < 1:
            origin = None
        else:
            origin = seq._link_at(start)
        yield from linkiter.links(origin, step, count)

    def values(origin: Link[VT], step: int = 1, count: int = -1, /) -> Iterator[VT]:
        for link in linkiter.links(origin, step, count):
            yield link.value

    def values_sliced(seq: LinkSequence[VT], slice_: slice) -> Iterator[VT]:
        for link in linkiter.links_sliced(seq, slice_):
            yield link.value

#====================================
#  Sequence Classes
#====================================

class LinkSequence(SequenceApi[VT]):
    'Linked sequence read interface.'

    __slots__ = '__link_first__', '__link_last__',
    __link_first__ : Link[VT]
    __link_last__  : Link[VT]

    @abstract
    def __new__(cls, *args, **kw):
        inst = super().__new__(cls)
        inst.__link_first__ = None
        inst.__link_last__ = None
        return inst

    def __iter__(self) -> Iterator[VT]:
        return linkiter.values(self.__link_first__, 1)

    def __reversed__(self) -> Iterator[VT]:
        return linkiter.values(self.__link_last__, -1)

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
            return self._from_iterable(linkiter.values_sliced(self, i))

        raise Emsg.InstCheck(i, (SupportsIndex, slice))

    def _link_at(self, index: SupportsIndex) -> Link[VT]:
        'Get a Link entry by index. Supports negative value. Raises ``IndexError``.'

        length = len(self)
        index = absindex(length, index)

        # Direct access for first/last.
        if index == 0:
            return self.__link_first__
        if index == length - 1:
            return self.__link_last__

        # TODO: Raise performance warning.

        # Choose best iteration direction.
        if index > length / 2:
            # Scan reversed from end.
            it = linkiter.links(self.__link_last__, index - length + 1, 2)
        else:
            # Scan forward from beginning.
            it = linkiter.links(self.__link_first__, index, 2)

        # Advance iterator.
        # it.advance()
        next(it)
        return next(it)

    def _link_of(self, value: VT) -> Link[VT]:
        'Get a link entry by value. Should raise ``MissingValueError``.'
        for link in linkiter.links(self.__link_first__):
            if link.value == value:
                return link
        raise Emsg.MissingValue(value)
        
    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, list(self).__repr__())

class linkseq(LinkSequence[VT], MutableSequenceApi[VT]):
    'Linked sequence mutable base implementation.'
    _link_type_: type[Link[VT]] = Link

    __slots__ = '__len',
    __len: int

    def __new__(cls, *args, **kw):
        inst = object.__new__(cls)
        inst.__link_first__ = None
        inst.__link_last__ = None
        inst.__len = 0
        return inst

    def __init__(self, values: Iterable[VT] = None, /):
        if values is not None:
            self.extend(values)

    def clear(self):
        self.__link_first__ = None
        self.__link_last__ = None
        self.__len = 0

    def copy(self):
        cls = type(self)
        inst = cls.__new__(cls)
        prev = None
        for link in map(self._link_type_, self):
            link.prev = prev
            if prev:
                prev.next = link
            else:
                inst.__link_first__ = link
            prev = link
        inst.__link_last__ = prev
        inst.__len = len(self)
        return inst

    def __len__(self):
        return self.__len

    @abcm.hookable('cast', 'check')
    def insert(self, index: SupportsIndex, value: VT, /, *,
        cast = None, check = None
    ):
        'Insert a value before an index. Raises ``MissingValueError``.'
        length = len(self)
        index = absindex(length, index, False)
        if cast is not None:
            value = cast(value)
        if check is not None:
            check(self, (value,), EMPTY_SET)
        newlink = self._link_type_(value)
        if length == 0:
            # Seed.
            self._seed(newlink)
        elif index >= length:
            # Append.
            self._spot(1, self.__link_last__, newlink)
        elif index <= 0:
            # Prepend.
            self._spot(-1, self.__link_first__, newlink)
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
            # _unlink() will not modify the prev/next attributes of the Link.
            for _ in map(self._unlink, linkiter.links_sliced(self, i)):
                pass
            return

        raise Emsg.InstCheck(i, (SupportsIndex, slice))

    @abcm.hookable('cast', 'check')
    def __setitem__(self, i: SupportsIndex|slice, value: VT|Collection[VT],
        /, *, cast = None, check = None):
        'Set value(s) by index/slice. Raises ``IndexError.'

        if isinstance(i, SupportsIndex):
            index = i
            arrival = value
            if cast is not None:
                arrival = cast(arrival)
            departure = self._link_at(index)
            if check is not None:
                check(self, (arrival,), (departure.value,))
            departure.value = arrival
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
            if check is not None:
                # TODO: optimize -- get first link only once, so we don't have
                # to find it twice.
                departures = self[slice_]
                check(self, arrivals, departures)
            link_it = linkiter.links_sliced(self, slice_)
            for link, arrival in zip(link_it, arrivals):
                link.value = arrival
            return

        raise Emsg.InstCheck(i, (SupportsIndex, slice))

    def sort(self, /, *, key = None, reverse = False):
        'Sort in place.'
        for link, value in zip(
            linkiter.links(self.__link_first__),
            sorted(self, key = key, reverse = reverse),
        ):
            link.value = value

    def reverse(self):
        'Reverse in place.'
        link = self.__link_last__
        while link is not None:
            link.invert()
            link = link.next
        self.__link_first__, self.__link_last__ = (
             self.__link_last__, self.__link_first__
        )

    #******  Link update methods

    def _seed(self, link: Link[VT], /):
        '''Add the Link as the intial (only) member. This is called by __setitem__,
        insert, append, etc., when the collection is empty.'''
        if len(self) != 0:
            raise IndexError('cannot seed a non-empty collection')
        self.__link_first__ = self.__link_last__ = link
        self.__len += 1

    def _spot(self, rel: Literal[LinkRel.prev]|Literal[LinkRel.next],
        neighbor: Link[VT], link: Link[VT], /):
        'Insert a Link before or after another Link already in the collection.'
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
                self.__link_first__ = link
            # But if rel were instead 1, it would be opposite, and our
            # new {link} would be the last element.
            else:
                self.__link_last__ = link
        self.__len += 1

    def _unlink(self, link: Link[VT]):
        'Remove a Link entry. Implementations must not alter the link attributes.'
        if link.prev is None:
            # Removing the first element.
            if link.next is None:
                # And only element.
                # Unset both first and last (empty)
                self.__link_first__ = None
                self.__link_last__ = None
            else:
                # Promote new first element.
                link.next.prev = None
                self.__link_first__ = link.next
        elif link.next is None:
            # Removing the last element (but not the only element).
            # Promote new last element.
            link.prev.next = None
            self.__link_last__ = link.prev
        else:
            # Removing a link the middle.
            # Sew up the gap.
            link.prev.next = link.next
            link.next.prev = link.prev
        self.__len -= 1

class linqset(linkseq[VT], MutableSequenceSet[VT],
    hookinfo = abcm.hookinfo(linkseq) - {'check'}
):
    '''Mutable LinkSequenceSet implementation for hashable values, based on
    a dict index. Inserting and removing is fast (constant) no matter where
    in the list, *so long as positions are referenced by value*. Accessing
    by numeric index requires iterating from the front or back.'''

    _link_type_: type[HashLink[VT]] = HashLink

    __link_first__ : HashLink[VT]
    __link_last__  : HashLink[VT]
    __table : dict[VT, HashLink[VT]]

    __slots__ = '__table',

    def __new__(cls, *args, **kw):
        inst = super().__new__(cls)
        inst.__table = dict()
        return inst

    def __init__(self, values: Iterable[VT] = None, /):
        if values is not None:
            self.update(values)

    #******  New public methods

    @abcm.hookable('cast')
    def wedge(self, value: VT, neighbor: VT, rel: Literal[-1]|Literal[1], /, *,
        cast = None
    ):
        '''Place a new value next to (before or after) another value.
        
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
            raise ValueError(rel)
        neighbor: Link[VT] = self._link_of(neighbor)
        if cast is not None:
            value = cast(value)
        if value in self:
            raise Emsg.DuplicateValue(value)
        newlink = self._link_type_(value)
        self._spot(rel, neighbor, newlink)

    def iter_from_value(self, value: VT, /, *,
        reverse = False, step: int = 1
    ) -> Iterator[VT]:
        'Return an iterator starting from ``value``.'
        return linkiter.values(self._link_of(value), -step if reverse else step)

    #******  Index Reads

    def __contains__(self, value: VT):
        return value in self.__table

    def _link_of(self, value: VT) -> HashLink[VT]:
        try: return self.__table[value]
        except KeyError: pass
        raise Emsg.MissingValue(value) from None

    #******  Index Updates

    def _seed(self, link: HashLink[VT], /):
        super()._seed(link)
        self.__table[link.value] = link

    def _spot(self, rel: LinkRel, neighbor: HashLink[VT], link: HashLink[VT], /):
        super()._spot(rel, neighbor, link)
        self.__table[link.value] = link

    def _unlink(self, link: Link):
        super()._unlink(link)
        del self.__table[link.value]

    def clear(self):
        super().clear()
        self.__table.clear()

    def copy(self):
        inst = super().copy()
        table = inst.__table
        for link in linkiter.links(inst.__link_first__):
            table[link.value] = link
        return inst

    #******  Duplicate check hook

    @abcm.hookable('check')
    @linkseq.hook('check')
    def __check(self, arrivals: Collection[VT], departures: Collection[VT], 
        /, *, check = None):

        for v in filterfalse(
            departures.__contains__,
            filter(self.__contains__, arrivals)
        ):
            raise Emsg.DuplicateValue(v)
        if check is not None:
            check(self, arrivals, departures)


LinkSeqT     = TypeVar('LinkSeqT',    bound = LinkSequence)
MutLinkSeqT  = TypeVar('MutLinkSeqT', bound = linkseq)
LinkT     = TypeVar('LinkT',    bound = Link)
LinkT_co  = TypeVar('LinkT_co', bound = Link, covariant = True)


del(
    abstract, final, overload, static,
    abcm, Abc, Copyable, IntEnum,
    TypeVar,
)