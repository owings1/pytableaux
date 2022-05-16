# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
pytableaux.tools.linked
-----------------------
"""
from __future__ import annotations

from itertools import filterfalse
from typing import (TYPE_CHECKING, Collection, Generic, Iterable, Iterator,
                    Literal, SupportsIndex, TypeVar)

from pytableaux import __docformat__, tools
from pytableaux.errors import Emsg
from pytableaux.errors import check as echeck
from pytableaux.tools import abcs
from pytableaux.tools.hooks import HookProvider
from pytableaux.tools.hybrids import MutableSequenceSet
from pytableaux.tools.sequences import (MutableSequenceApi, SequenceApi,
                                        absindex, slicerange)
from pytableaux.tools.sets import EMPTY_SET
VT = TypeVar('VT')
if TYPE_CHECKING:
    from typing import overload

__all__ = (
    'HashLink',
    'Link',
    'linkiter',
    'LinkRel',
    'linkseq',
    'LinkSequence',
    'linqset',
)

class LinkRel(abcs.IntEnum):
    'Link directional/subscript enum.'

    prev = -1
    "Indicates `prev` attribute, or `before` position."

    self = 0
    "Indicates `self`."

    next = 1
    "Indicates `next` attribute, or `after` position."

class Link(Generic[VT], abcs.Copyable):
    'Link value container.'

    value: VT
    "The value."

    prev: Link[VT]|None
    "The previous link."

    next: Link[VT]|None
    "The next link."

    __slots__ = 'prev', 'next', 'value'
    __iter__ = None

    @property
    def self(self):
        return self

    def __init__(self, value: VT, /, ):
        self.value = value
        self.prev = self.next = None

    def copy(self):
        inst = type(self)(self.value)
        inst.prev = self.prev
        inst.next = self.next
        return inst

    def __getitem__(self, rel: int):
        'Get previous, self, or next with -1, 0, 1, or ``LinkRel`` enum.'
        return getattr(self, LinkRel(rel)._name_)

    def __setitem__(self, rel: int, link: Link):
        'Set previous or next with -1, 1, or ``LinkRel`` enum.'
        setattr(self, LinkRel(rel)._name_, link)

    def invert(self) -> None:
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

class linkiter:
    "Link iterator methods."

    __new__ = NotImplemented

    @staticmethod
    def links(origin: Link[VT]|None, step: int = 1, count: int = -1, /) -> Iterator[Link[VT]]:
        """Create an iterator over ``Link`` objects.

        Args:
            origin: The origin link. A value of ``None`` returns an empty iterator.
            step (int): The step increment. A negative value will iterate in reverse.
            count (int): The limit, or ``-1`` for no limit.
        
        Returns:
            The link iterator.
        """
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

    @staticmethod
    def links_sliced(seq: LinkSequence[VT], slice_: slice, /) -> Iterator[Link[VT]]:
        """Create an iterator over ``Link`` objects for a sequence slice.

        Args:
            seq: The sequence.
            slice_ (slice): The slice object.
        
        Returns:
            The link iterator.
        """
        start, stop, step = slice_.indices(len(seq))
        count = (stop - start) / step
        count = int(count + 1 if count % 1 else count)
        if count < 1:
            origin = None
        else:
            origin = seq._link_at(start)
        yield from linkiter.links(origin, step, count)

    @staticmethod
    def values(origin: Link[VT]|None, step: int = 1, count: int = -1, /) -> Iterator[VT]:
        """Create an iterator over link values.

        Args:
            origin: The origin link. A value of ``None`` returns an empty iterator.
            step (int): The step increment. A negative value will iterate in reverse.
            count (int): The limit, or ``-1`` for no limit.
        
        Returns:
            The value iterator.
        """
        for link in linkiter.links(origin, step, count):
            yield link.value

    @staticmethod
    def values_sliced(seq: LinkSequence[VT], slice_: slice, /) -> Iterator[VT]:
        """Create an iterator over link values for a sequence slice.

        Args:
            seq: The sequence.
            slice_ (slice): The slice object.
        
        Returns:
            The value iterator.
        """
        for link in linkiter.links_sliced(seq, slice_):
            yield link.value

#====================================
#  Sequence Classes
#====================================

class LinkSequence(SequenceApi[VT]):
    'Linked sequence read interface.'

    __link_first__ : Link[VT]|None
    "The first link."

    __link_last__  : Link[VT]|None
    "The last link."

    __slots__ = '__link_first__', '__link_last__',

    @tools.abstract
    def __new__(cls, *args, **kw):
        inst = super().__new__(cls)
        inst.__link_first__ = None
        inst.__link_last__ = None
        return inst

    def __iter__(self) -> Iterator[VT]:
        return linkiter.values(self.__link_first__, 1)

    def __reversed__(self) -> Iterator[VT]:
        return linkiter.values(self.__link_last__, -1)

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

    def _link_at(self, index: SupportsIndex, /) -> Link[VT]:
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
        next(it)

        return next(it)

    def _link_of(self, value: VT, /) -> Link[VT]:
        'Get a link entry by value. Should raise ``MissingValueError``.'
        for link in linkiter.links(self.__link_first__):
            if link.value == value:
                return link
        raise Emsg.MissingValue(value)

    def __repr__(self):
        return f'{type(self).__name__}({list(self)})'

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

    @abcs.hookable('cast', 'check')
    def insert(self, index: SupportsIndex, value: VT, /, *,
        cast = None, check = None
    ):
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

    def remove(self, value: VT, /):
        self._unlink(self._link_of(value))

    def __delitem__(self, i):
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

    @abcs.hookable('cast', 'check')
    def __setitem__(self, i, value,
        /, *, cast = None, check = None):
        "Set value(s) by index/slice."

        if isinstance(i, SupportsIndex):
            index = i
            arrival: VT = value
            if cast is not None:
                arrival = cast(arrival)
            departure = self._link_at(index)
            if check is not None:
                check(self, (arrival,), (departure.value,))
            departure.value = arrival
            return

        if isinstance(i, slice):
            slice_ = i
            arrivals: Collection[VT] = value
            if cast is not None:
                arrivals = tuple(map(cast, arrivals))
            else:
                echeck.inst(arrivals, Collection)
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

    def sort(self, /, *, key = None, reverse: bool = False) -> None:
        for link, value in zip(
            linkiter.links(self.__link_first__),
            sorted(self, key = key, reverse = reverse),
        ):
            link.value = value

    def reverse(self) -> None:
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
        """Add the link as the intial (only) member. This is called by ``__setitem__``,
        ``insert``, ``append``, etc., when the collection is empty.
        """
        if len(self) != 0:
            raise IndexError('cannot seed a non-empty collection')
        self.__link_first__ = self.__link_last__ = link
        self.__len += 1

    def _spot(self, rel: Literal[-1]|Literal[1], neighbor: Link[VT], link: Link[VT], /):
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

    def _unlink(self, link: Link[VT], /):
        """Remove a Link entry.
        
        NB: Implementations must not alter the direct `prev` or `next` attributes
        of ``link``, but may alter the attributes of `link.prev` or `link.next`.
        """
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
    hookinfo = HookProvider(linkseq) - {'check'}
):
    """Mutable ``linqseq`` implementation for hashable values, based on
    a dict index. Inserting and removing is fast (O(1)) no matter where
    in the list, *so long as positions are referenced by value*. Accessing
    by numeric index requires iterating from the front or back.
    """

    _link_type_: type[HashLink[VT]] = HashLink

    __link_first__ : HashLink[VT]
    __link_last__  : HashLink[VT]

    __table : dict[VT, HashLink[VT]]
    "The link hash table."

    __slots__ = '__table',

    def __new__(cls, *args, **kw):
        inst: linqset[VT] = super().__new__(cls)
        inst.__table = dict()
        return inst

    def __init__(self, values: Iterable[VT] = None, /):
        if values is not None:
            self.update(values)

    #******  New public methods

    @abcs.hookable('cast')
    def wedge(self, value: VT, neighbor: VT, rel: Literal[-1]|Literal[1], /, *,
        cast = None
    ) -> None:
        """Place a new value next to (before or after) another value.
        
        This is the most performant way to insert a new value anywhere in the
        collection, with speed O(1).  Methods that add by index (__setitem__,
        insert, etc.) will first iterate to find the index, then call this method.

        Args:
            value: The new value to add.
            neighbor: The existing element next to which to place the value.
            rel (int): ``-1`` to place before, or ``1`` to place after neighbor.

        Raises:
            DuplicateValueError: on duplicate ``value``.
            MissingValueError: on missing ``neighbor``.
        """
        rel = LinkRel(rel)
        if rel is LinkRel.self:
            raise ValueError(rel)
        neighbor: HashLink[VT] = self._link_of(neighbor)
        if cast is not None:
            value = cast(value)
        if value in self:
            raise Emsg.DuplicateValue(value)
        newlink = self._link_type_(value)
        self._spot(rel, neighbor, newlink)

    def iter_from_value(self, value: VT, /, *, reverse: bool = False, step: int = 1) -> Iterator[VT]:
        """Return an iterator starting from ``value``.

        Args:
            value: The origin value.
            reverse (bool): Whether to iterate in reverse.
            step (int): The step increment.

        Returns:
            An iterator of values.
        """
        return linkiter.values(self._link_of(value), -step if reverse else step)

    #******  Index Reads

    def __contains__(self, value: VT):
        return value in self.__table

    def _link_of(self, value: VT, /) -> HashLink[VT]:
        try:
            return self.__table[value]
        except KeyError:
            raise Emsg.MissingValue(value) from None

    #******  Index Updates

    def _seed(self, link: HashLink[VT], /) -> None:
        super()._seed(link)
        self.__table[link.value] = link

    def _spot(self, rel: LinkRel, neighbor: HashLink[VT], link: HashLink[VT], /) -> None:
        super()._spot(rel, neighbor, link)
        self.__table[link.value] = link

    def _unlink(self, link: HashLink[VT], /) -> None:
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

    @abcs.hookable('check')
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
