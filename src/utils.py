
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
import importlib, time
from errors import IllegalStateError
from types import ModuleType
from past.builtins import basestring

def get_module(package, arg):    
    if isinstance(arg, ModuleType):
        return arg
    if isinstance(arg, basestring):
        if '.' not in arg:
            arg = package + '.' + arg
        return importlib.import_module(arg.lower())
    raise TypeError("Argument must be module or string")

def get_logic(name):
    """
    Get the logic module from the specified name. The following
    inputs all return the :ref:`FDE <FDE>` logic module: *'fde'*, *'FDE'*,
    *'logics.fde'*. If a module is passed, it is returned.

    :param str name: The logic name.
    :return: The module for the given logic.
    :rtype: module
    :raises ModuleNotFoundError:
    """
    return get_module('logics', name)

def nowms():
    return int(round(time.time() * 1000))

def cat(*args):
    return ''.join(args)

def isstr(arg):
    return isinstance(arg, basestring)

def isint(arg):
    return isinstance(arg, int)

def sortedbyval(map):
    return list(it[1] for it in sorted((v, k) for k, v in map.items()))

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

