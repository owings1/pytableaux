from __future__ import annotations

from enum import Enum
from itertools import filterfalse
from typing import TYPE_CHECKING, Callable, Mapping

from pytableaux.errors import check, Emsg
from pytableaux.tools.abcs import Abc, Copyable, abcf
from pytableaux.tools.decorators import wraps
from pytableaux.tools.linked import linqset
from pytableaux.tools.mappings import dmap
from pytableaux.tools.misc import orepr
from pytableaux.tools.typing import F

if TYPE_CHECKING:
    from typing import Iterable, overload

__all__ = (
    'EventEmitter',
    'EventsListeners',
    'Listener',
    'Listeners',
)

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

    def copy(self, *, listeners:bool = False):
        """Copy event emitter.
        
        Args:
            listeners (bool): Copy listeners.
        """
        cls = type(self)
        inst = cls.__new__(cls)
        inst.events = inst.events.copy(listeners = listeners)
        return inst

class Listener(Callable, Abc):

    cb        : Callable
    once      : bool
    callcount : int

    __slots__ = (
        'cb',
        'once',
        'callcount',
    )

    def __init__(self, cb: Callable, once: bool = False):
        self.cb = cb
        self.once = once
        self.callcount = 0

    def __call__(self, *args, **kw):
        self.callcount += 1
        return self.cb(*args, **kw)

    def __eq__(self, other):
        # if self is other:
        #     return True
        # if not isinstance(other, type(self)):
        #     # return self.cb is other
        #     if callable(other):
        #         return self.cb is other
        #     return NotImplemented
        # return False

        return self is other or self.cb == other or (
            isinstance(other, type(self)) and
            self.cb == other.cb
        )

    def __hash__(self):
        return hash(self.cb)

    def __repr__(self):
        return orepr(self,
            once = self.once,
            cb = self.cb,
            callcount = self.callcount,
        )

    __delattr__ = Emsg.ReadOnly.razr

class Listeners(linqset[Listener]):


    emitcount: int
    callcount: int

    __slots__ = 'emitcount', 'callcount'

    def __init__(self, values: Iterable[Listener] = None):
        super().__init__(values)
        self.callcount = 0
        self.emitcount = 0

    @abcf.temp
    @linqset.hook('cast')
    def cast(value):
        return check.inst(value, Listener)

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
        return orepr(self,
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
        """Create events.
        
        Args:
            *events: The event IDs. Existing events are ignored.
        """
        for event in filterfalse(self.__contains__, events):
            self[event] = Listeners()
            # self[event] = Listeners(event)

    def delete(self, event: EventId):
        """Delete an event and all listeners.
        
        Args:
            event: The event ID.
        """
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
                    # if not isinstance(cbs, Sequence):
                    if callable(cbs):
                        cbs = cbs,
                    method(self, event, *cbs)
            else:
                raise TypeError
        return f

    @normargs
    def on(self, event: EventId, *cbs: Callable):
        """Attach listeners."""
        self[event].extend(Listener(cb, False) for cb in cbs)

    @normargs
    def once(self, event: EventId, *cbs: Callable):
        """Attach single-call listeners."""
        self[event].extend(Listener(cb, True) for cb in cbs)

    @normargs
    def off(self, event: EventId, *cbs: Callable):
        """Detach listeners."""
        for _ in map(self[event].discard, cbs): pass

    def emit(self, event: EventId, *args, **kw) -> int:
        """Emit an event.
        
        Args:
            event: The event ID.
            *args: Listener arguments.
            **kw: Listener kwargs.
        
        Returns:
            The number of listeners called.
        """
        listeners = self[event]
        self.emitcount += 1
        callcount = listeners.emit(*args, **kw)
        self.callcount += callcount
        return callcount

    def copy(self, *, listeners:bool = False):
        """Copy events.
        
        Args:
            listeners (bool): Copy listeners.
        """
        if listeners:
            return super().copy()
        cls = type(self)
        inst = cls.__new__(cls)
        inst.emitcount = inst.callcount = 0
        inst.create(*self)
        return inst

    def __setitem__(self, key, value):
        # Override for type check
        super().__setitem__(key, check.inst(value, Listeners))

    if TYPE_CHECKING:
        @overload
        def update(self, it: Iterable = None, /, **kw):...

    # Alternate update impl uses setitem.
    update = dmap._setitem_update

    def __repr__(self):
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

