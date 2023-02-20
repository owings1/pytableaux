# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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
pytableaux.tools.events
^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from enum import Enum
from itertools import filterfalse
from typing import Any, Callable, Mapping

from ..errors import Emsg
from . import abcs, wraps
from .linked import linqset

__all__ = (
    'EventEmitter',
    'EventsListeners',
    'Listener',
    'Listeners')

class EventEmitter(abcs.Copyable):

    __slots__ = 'events',

    def __init__(self, *events):
        self.events = EventsListeners(*events)

    def on(self, *args, **kw):
        self.events.on(*args, **kw)

    def once(self, *args, **kw):
        self.events.once(*args, **kw)

    def off(self, *args, **kw):
        self.events.off(*args, **kw)

    def emit(self, event, *args, **kw) -> int:
        return self.events.emit(event, *args, **kw)

    def copy(self, *, listeners = False):
        """Copy event emitter.
        
        Args:
            listeners (bool): Copy listeners.
        """
        cls = type(self)
        inst = cls.__new__(cls)
        inst.events = inst.events.copy(listeners = listeners)
        return inst

class Listener(Callable, abcs.Abc):

    cb        : Callable
    once      : bool
    callcount : int

    __slots__ = ('cb', 'once', 'callcount')

    def __init__(self, cb: Callable, once: bool = False):
        self.cb = cb
        self.once = once
        self.callcount = 0

    def __call__(self, *args, **kw):
        self.callcount += 1
        return self.cb(*args, **kw)

    def __eq__(self, other):
        return self is other or self.cb == other or (
            isinstance(other, type(self)) and
            self.cb == other.cb)

    def __hash__(self):
        return hash(self.cb)

    def __repr__(self):
        return (
            f'<{type(self).__name__} once:{self.once} cb:{self.cb} '
            f'callcount:{self.callcount}>')

    __delattr__ = Emsg.ReadOnly.razr

class Listeners(linqset[Listener]):

    emitcount: int
    callcount: int

    __slots__ = ('emitcount', 'callcount')

    def __init__(self, values = None):
        super().__init__(values)
        self.callcount = 0
        self.emitcount = 0

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
        return (
            f'<{type(self).__name__} listeners:{len(self)} '
            f'emitcount:{self.emitcount} callcount:{self.callcount}>')

class EventsListeners(dict[Any, Listeners]):

    emitcount: int
    callcount: int

    __slots__ = ('emitcount', 'callcount')

    def __init__(self, *events):
        self.emitcount = 0
        self.callcount = 0
        if events:
            self.create(*events)

    def create(self, *events):
        """Create events.
        
        Args:
            *events: The event IDs. Existing events are ignored.
        """
        for event in filterfalse(self.__contains__, events):
            self[event] = Listeners()

    def delete(self, event):
        """Delete an event and all listeners.
        
        Args:
            event: The event ID.
        """
        del(self[event])

    @abcs.abcf.temp
    def normargs(method):
        '''
        Possible ways to call on/once/off ...

        .on(event_id, func1, func2, ...)
        
        .on(dict(
            event1 = func1,
            event2 = (func2, func3, ...),
        ))

        .on(event1 = (func1, func2), event2 = func3, ...)
        '''
        idtypes = (str, int, Enum)
        @wraps(method)
        def f(self, *args, **kw):
            if not (args or kw) or (args and kw):
                raise TypeError
            arg, *cbs = (kw,) if kw else args
            if isinstance(arg, idtypes):
                method(self, arg, *cbs)
            elif isinstance(arg, Mapping) and not len(cbs):
                for event, cbs in arg.items():
                    if callable(cbs):
                        cbs = cbs,
                    method(self, event, *cbs)
            else:
                raise TypeError
        return f

    @normargs
    def on(self, event, *cbs):
        """Attach listeners."""
        self[event].extend(Listener(cb, False) for cb in cbs)

    @normargs
    def once(self, event, *cbs):
        """Attach single-call listeners."""
        self[event].extend(Listener(cb, True) for cb in cbs)

    @normargs
    def off(self, event, *cbs):
        """Detach listeners."""
        for _ in map(self[event].discard, cbs): pass

    def emit(self, event, *args, **kw) -> int:
        """Emit an event.
        
        Args:
            event: The event ID.
            *args: Listener arguments.
            **kw: Listener kwargs.
        
        Returns:
            int: The number of listeners called.
        """
        listeners = self[event]
        self.emitcount += 1
        callcount = listeners.emit(*args, **kw)
        self.callcount += callcount
        return callcount

    def copy(self, *, listeners = False):
        """Copy events.
        
        Args:
            listeners (bool): Copy listeners.
        """
        if listeners:
            return super().copy()
        cls = type(self)
        inst = cls.__new__(cls)
        inst.emitcount = 0
        inst.callcount = 0
        inst.create(*self)
        return inst

    def __repr__(self):
        return (f'<{type(self).__name__} events:{len(self)} '
            f'listeners:{sum(map(len, self.values()))} '
            f'emitcount:{self.emitcount} callcount:{self.callcount}>')

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

