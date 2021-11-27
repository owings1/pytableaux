from enum import Enum, unique
from past.builtins import basestring
from utils import LinkOrderSet, orepr, typecheck
from typing import Callable, Iterator, Sequence, Union

@unique
class Events(Enum):
    AFTER_APPLY        = 10
    AFTER_BRANCH_ADD   = 20
    AFTER_BRANCH_CLOSE = 30
    AFTER_NODE_ADD     = 40
    AFTER_NODE_TICK    = 50
    AFTER_RULE_APPLY   = 60
    AFTER_TRUNK_BUILD  = 70
    BEFORE_APPLY       = 80
    BEFORE_TRUNK_BUILD = 100

keytypes = (basestring, int, Enum,)
EventId = Union[basestring, int, Enum]

class Listeners(LinkOrderSet):

    class Listener(Callable):

        def __init__(self, cb: Callable, once: bool = False, event: EventId = None):
            self.cb = cb
            self.once = once
            self.event = event
            self.callcount = 0

        def __call__(self, *args, **kw):
            self.callcount += 1
            return self.cb(*args, **kw)

        def __eq__(self, other):
            return self.cb == other or (
                isinstance(other, __class__) and
                self.cb == other.cb
            )

        def __hash__(self):
            return hash(self.cb)

        def __repr__(self):
            return orepr(self,
                event = self.event,
                listener = self.cb.__name__,
                callcount = self.callcount,
                once = self.once,
                cb = self.cb.__class__,
            )

    @property
    def name(self) -> EventId:
        return self.__name

    @property
    def emitcount(self) -> int:
        return self.__emitcount

    @property
    def callcount(self) -> int:
        return self.__callcount

    def _genitem_(self, cb: Callable, once = False):
        if cb in self:
            return cb
        if isinstance(cb, __class__.Listener):
            cb = cb.cb
        if not callable(cb):
            raise TypeError(cb.__class__)
        return __class__.Listener(cb, once, self.name)

    def emit(self, *args, **kw) -> int:
        self.__emitcount += 1
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
            self.__callcount += count
        return count

    def __init__(self, name):
        super().__init__()
        self.__name = name
        self.__callcount = 0
        self.__emitcount = 0

    def __repr__(self):
        return orepr(self,
            event = self.name,
            listenercount = len(self),
            emitcount = self.emitcount,
            callcount = self.callcount,
        )

def checkkey(*keys):
    for key in keys:
        typecheck(key, keytypes, 'event')

def evargs(method: Callable) -> Callable:
    def normalize(self, *args, **kw):
        if kw:
            if args: raise TypeError()
            return normalize(self, kw)
        if not args: raise TypeError()
        arg = args[0]
        if isinstance(arg, keytypes):
            event, *cbs = args
            return method(self, event, *cbs)
        if len(args) > 1: raise TypeError()
        if isinstance(arg, dict):
            ret = None
            for event, cbs in arg.items():
                if not isinstance(cbs, Sequence):
                    cbs = (cbs,)
                ret = method(self, event, *cbs)
            return ret
        raise TypeError()
    return normalize

class EventsListeners(object):

    @property
    def emitcount(self) -> int:
        return self.__emitcount

    def create(self, *events: EventId):
        checkkey(*events)
        for event in events:
            if event not in self:
                self[event] = Listeners(event)

    def delete(self, event: EventId):
        del(self[event])

    def clear(self):
        for event in self:
            self.remove(event)
        self.__base.clear()

    @evargs
    def on(self, event: EventId, *cbs: Callable):
        self[event].extend(cbs)

    @evargs
    def once(self, event: EventId, *cbs: Callable):
        self[event].extend(cbs, once = True)

    @evargs
    def off(self, event: EventId, *cbs: Callable):
        ev = self[event]
        for cb in cbs:
            ev.discard(cb)

    def emit(self, event: EventId, *args, **kw) -> int:
        return self[event].emit(*args, **kw)

    def __init__(self, *names: EventId):
        self.__base: dict[EventId, Listeners] = {}
        self.create(*names)
        self.__emitcount = 0

    def __repr__(self):
        return orepr(self,
            eventcount = len(self),
            emitcount = self.__emitcount,
        )

    # Delegate to base dict.

    def get(self, item, defval = None) -> Listeners:
        return self.__base.get(item, defval)

    def keys(self):
        return self.__base.keys()

    def values(self):
        return self.__base.values()

    def items(self):
        return self.__base.items()

    def __len__(self):
        return len(self.__base)

    def __iter__(self) -> Iterator[EventId]:
        return iter(self.__base)

    def __contains__(self, key: EventId):
        return key in self.__base

    def __getitem__(self, key: EventId) ->  Listeners:
        return self.__base[key]

    def __setitem__(self, key: EventId, val: Listeners):
        if not isinstance(key, keytypes):
            raise TypeError(key, type(key), keytypes)
        if not isinstance(val, Listeners):
            raise TypeError(val, type(val), Listeners)
        self.__base[key] = val

    def __delitem__(self, key: EventId):
        del(self.__base[key])

class EventEmitter(object):

    @property
    def events(self) -> EventsListeners:
        return self.__events

    def on(self, *args, **kw):
        self.events.on(*args, **kw)

    def once(self, *args, **kw):
        self.events.once(*args, **kw)

    def off(self, *args, **kw):
        self.events.off(*args, **kw)

    def emit(self, event, *args, **kw) -> int:
        return self.events.emit(event, *args, **kw)

    def __init__(self, *events):
        self.__events = EventsListeners(*events)