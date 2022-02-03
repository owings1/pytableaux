from __future__ import annotations

__all__ = 'EventEmitter', 'EventsListeners',

from errors import instcheck
from tools.abcs import Abc, Copyable, abcf, F
from tools.decorators import raisr, wraps
from tools.linked import linqset, MutableLinkSequenceSet as MutLinkSeqSet
from tools.mappings import (
    dmap, ItemsIterator, MutableMappingApi
)

from enum import Enum
from itertools import chain, filterfalse, starmap
from typing import Callable, Mapping, Sequence

EventId = str | int | Enum

class EventEmitter(Copyable):

    __slots__ = 'events',

    def __init__(self, *events):
        self.events = EventsListeners(*events)

    def on(self, *args, **kw):
        self.events.on(*args, **kw)

    def once(self, *args, **kw):
        self.events.once(*args, **kw)

    def off(self, *args, **kw):
        self.events.off(*args, **kw)

    def emit(self, event: EventId, *args, **kw) -> int:
        return self.events.emit(event, *args, **kw)

    def copy(self):
        cls = type(self)
        inst = cls.__new__(cls)
        inst.events = inst.events.copy()
        return inst

class Listener(Callable, Abc):

    cb        : Callable
    once      : bool
    event     : EventId
    callcount : int

    __slots__ = 'cb', 'once', 'event', 'callcount'

    def __init__(self, cb: Callable, once: bool = False, event: EventId|None = None):
        # instcheck(cb, Callable)
        self.cb = cb
        self.once = once
        self.event = event
        self.callcount = 0

    def __call__(self, *args, **kw):
        self.callcount += 1
        return self.cb(*args, **kw)

    def __eq__(self, other):
        return self is other or self.cb == other or (
            isinstance(other, type(self)) and
            self.cb == other.cb
        )

    def __hash__(self):
        return hash(self.cb)

    def __repr__(self):
        from tools.misc import orepr
        return orepr(self,
            event = self.event,
            once = self.once,
            cb = self.cb,
            callcount = self.callcount,
        )

    __delattr__ = raisr(AttributeError)

class Listeners(linqset[Listener]):

    emitcount: int
    callcount: int

    __slots__ = 'emitcount', 'callcount', 'event'

    def __init__(self, event: EventId):
        super().__init__()
        self.event = event
        self.callcount = 0
        self.emitcount = 0

    @abcf.temp
    @MutLinkSeqSet.hook('cast')
    def cast(value):
        return instcheck(value, Listener)

    def emit(self, *args, **kw) -> int:
        self.emitcount += 1
        count = 0
        try:
            for listener in self:
                try:
                    listener(*args, **kw)
                    count += 1
                finally:
                    if listener.once:
                        # Discard instead of remove, since a consumer might
                        # manually remove the listener when it is called.
                        self.discard(listener)
        finally:
            self.callcount += count
        return count

    def __repr__(self):
        from tools.misc import orepr
        return orepr(self,
            event = self.event,
            listeners = len(self),
            emitcount = self.emitcount,
            callcount = self.callcount,
        )

class EventsListeners(dmap[EventId, Listeners]):

    emitcount: int
    callcount: int

    __slots__ = 'emitcount', 'callcount',

    def __init__(self, *names: EventId):
        self.emitcount = self.callcount = 0
        self.create(*names)

    def create(self, *events: EventId):
        for event in filterfalse(self.__contains__, events):
            self[event] = Listeners(event)

    def delete(self, event: EventId):
        del(self[event])

    @abcf.temp
    def normargs(method: F) -> F:
        '''
        Possible ways to call on/once/off ...

        .on(event_id, func1, func2, ...)
        
        .on(dict(
            event1 = func1,
            event2 = (func2, func3, ...),
        ))

        .on(event1 = (func1, func2), event2 = func3, ...)
        '''
        @wraps(method)
        def f(self, *args, **kw):
            if not (args or kw) or (args and kw):
                raise TypeError
            arg, *cbs = (kw,) if kw else args
            if isinstance(arg, EventId):
                method(self, arg, *cbs)
            elif isinstance(arg, Mapping) and not len(cbs):
                for event, cbs in arg.items():
                    if not isinstance(cbs, Sequence):
                        cbs = cbs,
                    method(self, event, *cbs)
            else:
                raise TypeError
        return f

    @normargs
    def on(self, event, *cbs: Callable):
        self[event].extend(Listener(cb, False, event) for cb in cbs)

    @normargs
    def once(self, event: EventId, *cbs: Callable):
        self[event].extend(Listener(cb, True, event) for cb in cbs)

    @normargs
    def off(self, event: EventId, *cbs: Callable):
        for _ in map(self[event].discard, cbs): pass

    def emit(self, event: EventId, *args, **kw) -> int:
        ev = self[event]
        self.emitcount += 1
        callcount = ev.emit(*args, **kw)
        self.callcount += callcount
        return callcount

    def barecopy(self):
        # Only copy event keys, not listeners
        cls = type(self)
        inst = cls.__new__(cls)
        __class__.__init__(inst, *self)
        return inst

    def __setitem__(self, key, value):
        # Override for type check
        super().__setitem__(key, instcheck(value, Listeners))

    # Alternate update impl uses setitem.
    update = dmap._setitem_update

    def __repr__(self):
        from tools.misc import orepr
        return orepr(self,
            events = len(self),
            listeners = sum(map(len, self.values())),
            emitcount = self.emitcount,
            callcount = self.callcount,
        )

    @classmethod
    def _from_mapping(cls, mapping):
        inst = cls()
        inst.update(mapping)
        return inst

    @classmethod
    def _from_iterable(cls, it):
        inst = cls()
        inst.update(it)
        return inst

del(Abc, Copyable, dmap, linqset, abcf, raisr, wraps)