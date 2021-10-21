class Events(object):
    AFTER_APPLY        = 10
    AFTER_BRANCH_ADD   = 20
    AFTER_BRANCH_CLOSE = 30
    AFTER_NODE_ADD     = 40
    AFTER_NODE_TICK    = 50
    AFTER_RULE_APPLY   = 60
    AFTER_TRUNK_BUILD  = 70
    BEFORE_TRUNK_BUILD = 100

class EventEmitter(object):

    def __init__(self):
        self.__listeners = dict()

    def add_listener(self, event, callback):
        if not callable(callback):
            raise TypeError('callback argument must be callable')
        self.__listeners[event].append(callback)
        return self

    def add_listeners(self, *args, **kw):
        for arg in args:
            for event, callback in arg.items():
                self.add_listener(event, callback)
        for event, callback in kw.items():
            self.add_listener(event, callback)
        return self

    def deregister_all_events(self):
        return self.deregister_event(*self.__listeners)

    def deregister_event(self, *events):
        for event in events:
            del(self.__listeners[event])
        return self

    def emit(self, event, *args, **kw):
        for callback in self.__listeners[event]:
            callback(*args, **kw)
        return self

    def register_event(self, *events):
        for event in events:
            if event not in self.__listeners:
                self.__listeners[event] = list()
        return self

    def remove_listener(self, event, callback):
        idx = self.__listeners[event].index(callback)
        self.__listeners[event].pop(idx)
        return self

    def remove_listeners(self, *events):
        for event in events:
            self.__listeners[event].clear()
        return self

    def remove_all_listeners(self):
        for event in self.__listeners:
            self.__listeners[event].clear()
        return self