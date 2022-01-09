from __future__ import annotations

__all__ = 'EventEmitter', 'EventsListeners',

from decorators import raisr
from errors import instcheck
from tools.abcs import Abc, abcf
from tools.linked import linqset
from utils import orepr

from collections.abc import Callable, ItemsView, Iterator, KeysView, Mapping, \
    MutableMapping, Sequence, ValuesView
from enum import Enum
from typing import TypeAlias


EventId: TypeAlias = str | int | Enum
class Listener(Callable, Abc):

    cb        : Callable
    once      : bool
    event     : EventId
    callcount : int

    __slots__ = 'cb', 'once', 'event', 'callcount'

    def __call__(self, *args, **kw):
        self.callcount += 1
        return self.cb(*args, **kw)

    def __eq__(self, other: Callable):
        return self is other or self.cb == other or (
            isinstance(other, self.__class__) and
            self.cb == other.cb
        )

    def __hash__(self):
        return hash(self.cb)

    def __init__(self, cb: Callable, once: bool = False, event: EventId = None):
        if not callable(cb):
            raise TypeError(cb)
        self.cb = cb
        self.once = once
        self.event = event
        self.callcount = 0

    def __repr__(self):
        return orepr(self,
            event = self.event,
            once = self.once,
            cb = self.cb,
            callcount = self.callcount,
        )

    def __setattr__(self, attr, val):
        if attr == 'callcount':
            instcheck(val, int)
        elif hasattr(self, 'event'):
            # Immutable
            raise AttributeError('cannot set %s' % attr)
        super().__setattr__(attr, val)

    __delattr__ = raisr(AttributeError)

class Listeners(linqset[Listener]):

    emitcount: int
    callcount: int

    __slots__ = 'emitcount', 'callcount', '__event'

    @property
    def event(self) -> EventId:
        return self.__event

    def _before_add(self, value):
        instcheck(value, Listener)

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
                        self.remove(listener)
        finally:
            self.callcount += count
        return count

    def __init__(self, event: EventId):
        super().__init__()
        self.__event = event
        self.callcount = 0
        self.emitcount = 0

    def __repr__(self):
        return orepr(self,
            event = self.event,
            listeners = len(self),
            emitcount = self.emitcount,
            callcount = self.callcount,
        )

class EventsListeners(MutableMapping[EventId, Listeners], Abc):

    emitcount: int
    callcount: int

    __base: dict[EventId, Listeners]

    __slots__ = 'emitcount', 'callcount', '__base'

    def create(self, *events: EventId):
        for event in events:
            if event not in self:
                self[event] = Listeners(event)

    def delete(self, event: EventId):
        del(self[event])

    @abcf.temp
    def normargs(feventmod: Callable) -> Callable:
        def normalize(self, *args, **kw):
            if not (args or kw) or (args and kw):
                raise TypeError
            arg, *cbs = (kw,) if kw else args
            if isinstance(arg, EventId):
                feventmod(self, arg, *cbs)
                return
            if isinstance(arg, Mapping) and not len(cbs):
                for event, cbs in arg.items():
                    if not isinstance(cbs, Sequence):
                        cbs = (cbs,)
                    feventmod(self, event, *cbs)
                return
            raise TypeError
        return normalize

    @normargs
    def on(self, event: EventId, *cbs: Callable):
        self[event].extend(Listener(cb, False, event) for cb in cbs)

    @normargs
    def once(self, event: EventId, *cbs: Callable):
        self[event].extend(Listener(cb, True, event) for cb in cbs)

    @normargs
    def off(self, event: EventId, *cbs: Callable):
        ev = self[event]
        for cb in cbs:
            ev.discard(cb)

    def emit(self, event: EventId, *args, **kw) -> int:
        self.emitcount += 1
        callcount = self[event].emit(*args, **kw)
        self.callcount += callcount
        return callcount

    # Delegate to base dict.

    def clear(self):
        self.__base.clear()

    def get(self, key: EventId, default = None) -> Listeners:
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self) -> KeysView[EventId]:
        return self.__base.keys()

    def values(self) -> ValuesView[Listeners]:
        return self.__base.values()

    def items(self) -> ItemsView[EventId, Listeners]:
        return self.__base.items()

    def pop(self, key: EventId, *default) -> Listeners:
        try:
            return self.__base.pop(key)
        except KeyError:
            if default:
                return default[0]
            raise

    def popitem(self) -> tuple[EventId, Listeners]:
        return self.__base.popitem()

    def setdefault(self, key, value = None):
        try:
            return self[key]
        except KeyError:
            pass
        self[key] = value
        return value

    def copy(self):
        cls = self.__class__
        inst = cls.__new__(cls)
        inst.__dict__.update(self.__dict__ | {
            '__base': self.__base.copy()
        })
        return inst

    def barecopy(self):
        # Only copy event keys, not listeners
        cls = self.__class__
        inst = cls.__new__(cls)
        __class__.__init__(inst, *self)
        return inst

    def __len__(self):
        return len(self.__base)

    def __iter__(self) -> Iterator[EventId]:
        return iter(self.__base)

    def __contains__(self, key: EventId):
        return isinstance(key, EventId) and key in self.__base

    def __getitem__(self, key: EventId) -> Listeners:
        return self.__base[key]

    def __setitem__(self, key: EventId, val: Listeners):
        self.__base[instcheck(key, EventId)] = instcheck(val, Listeners)

    def __delitem__(self, key: EventId):
        del(self.__base[key])

    def __eq__(self, other):
        return self is other or (
            isinstance(other, self.__class__) and
            self.__base == other.__base
        )

    def __copy__(self):
        return self.copy()

    def __init__(self, *names: EventId):
        self.__base = {}
        self.emitcount = self.callcount = 0
        self.create(*names)

    def __repr__(self):
        return orepr(self,
            events = len(self),
            listeners = sum(len(v) for v in self.values()),
            emitcount = self.emitcount,
            callcount = self.callcount,
        )

    def __setattr__(self, attr, val):
        # Protect __base
        if attr == '__base' and getattr(self, attr, None) != None:
            raise AttributeError('cannot set %s' % attr)
        if attr in ('callcount', 'emitcount'):
            instcheck(val, int)
        super().__setattr__(attr, val)

class EventEmitter:

    __slots__ = '__events',

    @property
    def events(self) -> EventsListeners:
        return self.__events

    @events.setter
    def events(self, value: EventsListeners):
        self.__events = instcheck(value, EventsListeners)

    def on(self, *args, **kw):
        self.events.on(*args, **kw)

    def once(self, *args, **kw):
        self.events.once(*args, **kw)

    def off(self, *args, **kw):
        self.events.off(*args, **kw)

    def emit(self, event: EventId, *args, **kw) -> int:
        return self.events.emit(event, *args, **kw)

    def copy(self):
        cls = self.__class__
        inst = cls.__new__(cls)
        inst.events = inst.events.copy()
        return inst

    __copy__ = copy

    def __init__(self, *events):
        self.events = EventsListeners(*events)
