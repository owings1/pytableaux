from _typeshed import Incomplete
from enum import Enum
from pytableaux.tools import abcs
from pytableaux.tools.linked import linqset
from pytableaux.tools.mappings import dmap
from pytableaux.typing import _F, _RT, _T
from typing import Callable, Iterable, overload
EventId = str | int | Enum

class EventEmitter(abcs.Copyable):
    events: EventsListeners
    def __init__(self, *events) -> None: ...
    def on(self, *args, **kw) -> None: ...
    def once(self, *args, **kw) -> None: ...
    def off(self, *args, **kw) -> None: ...
    def emit(self, event: EventId, *args, **kw) -> int: ...
    def copy(self, *, listeners: bool = ...): ...

class Listener(Callable[..., _RT], abcs.Abc):
    cb: Callable[..., _RT]
    once: bool
    callcount: int
    def __init__(self, cb: Callable[..., _RT], once: bool = ...) -> None: ...
    def __call__(self, *args, **kw) -> _RT: ...
    def __eq__(self, other): ...
    def __hash__(self): ...
    __delattr__: Incomplete

class Listeners(linqset[Listener]):
    emitcount: int
    callcount: int
    def __init__(self, values: Iterable[Listener] = ...) -> None: ...
    def emit(self, *args, **kw) -> int: ...

class EventsListeners(dmap[EventId, Listeners]):
    emitcount: int
    callcount: int
    def __init__(self, *names: EventId) -> None: ...
    def create(self, *events: EventId): ...
    def delete(self, event: EventId): ...
    def on(self, event: EventId, *cbs: Callable): ...
    def once(self, event: EventId, *cbs: Callable): ...
    def off(self, event: EventId, *cbs: Callable): ...
    def emit(self, event: EventId, *args, **kw) -> int: ...
    def copy(self:_T, *, listeners: bool = ...)->_T: ...
    def update(self, it: Iterable = ..., **kw): ...