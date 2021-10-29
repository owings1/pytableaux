
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
#
# ------------------
#
# pytableaux - utils module
from builtins import ModuleNotFoundError
from errors import IllegalStateError
from importlib import import_module
from time import time
from types import ModuleType
from past.builtins import basestring

def get_module(ref, package = None):

    cache = _myattr(get_module, dict)
    keys = set()
    ret = {'mod': None}

    def _checkref(ref):
        key = (package, ref)
        if key in cache:
            return bool(_setcache(cache[key]))
        keys.add(key)
        return False

    def _setcache(val):
        for key in keys:
            cache[key] = val
        ret['mod'] = val
        return val

    if hasattr(ref, '__module__'):
        if _checkref(ref.__module__):
            return ret['mod']
        ref = import_module(ref.__module__)

    if ismodule(ref):
        if _checkref(ref.__name__):
            return ret['mod']
        if package != None and package != getattr(ref, '__package__', None):
            raise ModuleNotFoundError(
                "Module '{0}' not in package '{1}'".format(ref.__name__, package)
            )
        return _setcache(ref)

    if not isstr(ref):
        raise TypeError("ref must be string or module, or have __module__ attribute")

    ref = ref.lower()
    if _checkref(ref):
        return ret['mod']
    if package == None:
        return _setcache(import_module(ref))
    pfx = cat(package, '.')
    try:
        return _setcache(import_module(cat(pfx, ref)))
    except ModuleNotFoundError:
        if not ref.startswith(pfx):
            raise
        ref = ref[len(pfx):]
        if _checkref(ref):
            return ret['mod']
        return _setcache(import_module(cat(pfx, ref)))

def get_logic(ref):
    """
    Get the logic module from the specified reference.

    Each of following examples returns the :ref:`FDE <FDE>` logic module::

        get_logic('fde')
        get_logic('FDE')
        get_logic('logics.fde')
        get_logic(get_logic('FDE'))


    :param any ref: The logic reference.
    :return: The logic module.
    :rtype: module
    :raises ModuleNotFoundError: if the logic is not found.
    :raises TypeError: if no module name can be determined from ``ref``.
    """
    return get_module(ref, package = 'logics')

def nowms():
    return int(round(time() * 1000))

def cat(*args):
    return ''.join(args)

def isstr(obj):
    return isinstance(obj, basestring)

def isint(obj):
    return isinstance(obj, int)

def ismodule(obj):
    return isinstance(obj, ModuleType)

def istableau(obj):
    """
    Check if an object is a tableau.
    """
    cache = _myattr(istableau)
    cls = obj.__class__
    if cls in cache:
        return True
    d = obj.__dict__
    if not (
        callable(getattr(obj, 'branch', None)) and
        #: TODO: move the Tableau impl to Rule class, then we don't need this check
        callable(getattr(obj, 'branching_complexity', None)) and
        isinstance(d.get('history'), list) and
        True
    ):
        return False
    cache.add(cls)
    return True

def isrule(obj):
    """
    Checks if an object is a rule instance.
    """
    cache = _myattr(isrule)
    cls = obj.__class__
    if cls in cache:
        return True
    d = obj.__dict__
    if not (
        callable(getattr(obj, 'get_target', None)) and
        callable(getattr(obj, 'apply', None)) and
        isstr(d.get('name')) and
        istableau(d.get('tableau')) and
        isinstance(d.get('apply_count'), int) and
        isinstance(d.get('timers'), dict) and
        isinstance(d.get('apply_timer'), StopWatch) and
        isinstance(d.get('search_timer'), StopWatch) and
        True
    ):
        return False
    cache.add(cls)
    return True

def sortedbyval(map):
    return list(it[1] for it in sorted((v, k) for k, v in map.items()))

def _myattr(func, cls = set, name = '_cache'):
    if not hasattr(func, name):
        setattr(func, name, cls())
    return getattr(func, name)

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

class StopWatch(object):

    def __init__(self, started=False):
        self._start_time = None
        self._elapsed = 0
        self._is_running = False
        self._times_started = 0
        if started:
            self.start()

    def start(self):
        if self._is_running:
            raise IllegalStateError('StopWatch already started.')
        self._start_time = nowms()
        self._is_running = True
        self._times_started += 1
        return self

    def stop(self):
        if not self._is_running:
            raise IllegalStateError('StopWatch already stopped.')
        self._is_running = False
        self._elapsed += nowms() - self._start_time
        return self

    def reset(self):
        self._elapsed = 0
        if self._is_running:
            self._start_time = nowms()
        return self

    def elapsed(self):
        if self._is_running:
            return self._elapsed + (nowms() - self._start_time)
        return self._elapsed

    def elapsed_avg(self):
        return self.elapsed() / max(1, self.times_started())

    def is_running(self):
        return self._is_running

    def times_started(self):
        return self._times_started

    def __repr__(self):
        return self.elapsed().__repr__()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        if self.is_running():
            self.stop()

