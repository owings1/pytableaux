from enum import Enum, unique
from past.builtins import basestring
from utils import LinkOrderSet, kwrepr, typecheck
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

class EventEmitter(object):

    @property
    def events(self):
        return self.__events

    def on(self, *args, **kw):
        self.events.on(*args, **kw)
        return self

    def once(self, *args, **kw):
        self.events.on(*args, **kw)
        return self

    def off(self, *args, **kw):
        self.events.on(*args, **kw)
        return self

    def emit(self, event, *args, **kw):
        return self.events.emit(event, *args, **kw)

    def __init__(self, *events):
        self.__events = EventsListeners(*events)

class Listeners(LinkOrderSet):

    class Listener(object):
        def __init__(self, cb, once = False, event = None):
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
            return kwrepr(
                event=self.event,
                listener=self.cb.__name__,
                callcount=self.callcount,
                once=self.once,
                callback=self.
                cb.__class__,
            )

    @property
    def name(self):
        return self.__name
    @property
    def emitcount(self):
        return self.__emitcount
    @property
    def callcount(self):
        return self.__callcount

    def _genitem_(self, cb, once = False):
        if isinstance(cb, __class__.Listener):
            cb = cb.cb
        if not callable(cb):
            raise TypeError(cb.__class__)
        return __class__.Listener(cb, once, self.name)

    def _genitems_(self, cbs, once = False):
        return (self._genitem_(cb, once = once) for cb in cbs)

    def emit(self, *args, **kw):
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
        return kwrepr(
            cls=self.__class__.__name__,
            event=self.name,
            listenercount=len(self),
            emitcount=self.emitcount,
            callcount=self.callcount,
        )

keytypes = (basestring, int, Enum,)

def checkkey(*keys):
    for key in keys:
        typecheck(key, keytypes, 'event')

def evargs(method):
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
                if not isinstance(cbs, (tuple, list)):
                    cbs = (cbs,)
                ret = method(self, event, *cbs)
            return ret
        raise TypeError()
    return normalize

class EventsListeners(object):
    @property
    def emitcount(self):
        return self.__emitcount
    def create(self, *events):
        checkkey(*events)
        for event in events:
            if event not in self:
                self[event] = Listeners(event)
        return self

    def delete(self, event):
        del(self[event])
        return self

    def clear(self):
        for event in self:
            self.remove(event)
        self.__base.clear()
        return self

    @evargs
    def on(self, event, *cbs):
        self[event].extend(cbs)
        return self

    @evargs
    def once(self, event, *cbs):
        self[event].extend(cbs, once = True)
        return self

    @evargs
    def off(self, event, *cbs):
        ev = self[event]
        for cb in cbs:
            ev.discard(cb)
        return self

    def emit(self, event, *args, **kw):
        return self[event].emit(*args, **kw)

    def __init__(self, *names):
        self.__base = {}
        self.create(*names)
        self.__emitcount = 0

    def __repr__(self):
        return kwrepr(
            cls=self.__class__.__name__,
            eventcount=len(self),
            emitcount=self.__emitcount,
        )

    # Delegate to base dict.
    def get(self, item, defval = None):
        return self.__base.get(item, defval)
    def keys(self):
        return self.__base.keys()
    def values(self):
        return self.__base.values()
    def items(self):
        return self.__base.items()
    def __len__(self):
        return len(self.__base)
    def __iter__(self):
        return iter(self.__base)
    def __contains__(self, key):
        return key in self.__base
    def __getitem__(self, key):
        return self.__base[key]
    def __setitem__(self, key, val):
        if not isinstance(key, keytypes):
            raise TypeError(key)
        if not isinstance(val, Listeners):
            raise TypeError(val)
        self.__base[key] = val
    def __delitem__(self, key):
        self[key].clear()
        del(self.__base[key])



