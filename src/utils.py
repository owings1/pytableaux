
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
from errors import DuplicateKeyError, IllegalStateError
from importlib import import_module
from inspect import isclass
from itertools import islice
from time import time
from types import ModuleType
from past.builtins import basestring
emptyset = frozenset()

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

def typecheck(obj, types, name = 'parameter', err = TypeError):
    if isclass(types):
        types = (types,)
    types = tuple(
        basestring if val == str else val for val in types
    )
    if isinstance(obj, types):
        return obj
    raise err("`{0}` must be {1}, got '{2}'".format(name, types, obj.__class__))

def condcheck(cond, msg = None, name = 'parameter', err = ValueError):
    if callable(cond):
        cond = cond()
    if cond:
        return
    if msg == None:
        msg = 'Invalid value for `{0}`'.format(name)
    raise err(msg)

def nowms():
    return int(round(time() * 1000))

def cat(*args):
    return ''.join(args)

def wrparens(*args):
    return cat('(', *args, ')')

def dictrepr(d, limit = 10):
    pairs = (
        cat(k, '=', v.__name__
        if isclass(v) else v.__repr__())
        for k,v in islice(d.items(), limit)
    )
    return wrparens(', '.join(pairs))
def kwrepr(**kw): return dictrepr(kw)

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
        isstr(getattr(obj, 'name')) and
        istableau(getattr(obj, 'tableau')) and
        isinstance(getattr(obj, 'apply_count'), int) and
        isinstance(getattr(obj, 'timers'), dict) and
        isinstance(getattr(obj, 'apply_timer'), StopWatch) and
        isinstance(getattr(obj, 'search_timer'), StopWatch) and
        True
    ):
        return False
    cache.add(cls)
    return True

def safeprop(self, name, value = None):
    if hasattr(self, name):
        raise KeyError("'{}' already exists".format(name))
    setattr(self, name, value)

def sortedbyval(map):
    return list(it[1] for it in sorted((v, k) for k, v in map.items()))

def _myattr(func, cls = set, name = '_cache'):
    if not hasattr(func, name):
        setattr(func, name, cls())
    return getattr(func, name)

def rcurry(func, rargs):
    class curried(object):
        def __call__(self, *largs):
            return func(*largs, *rargs)
    return curried()

def lcurry(func, largs):
    class curried(object):
        def __call__(self, *rargs):
            return func(*largs, *rargs)
    return curried()

def Decorators():
    def privkey(method):
        name = method.__name__
        key = '.'.join(('_', __name__, '__lazy_', name))
        return (name, key)

    class Decorators(object):
        def lazyget(method):
            name, key = privkey(method)
            def fget(self):
                if key not in self.__dict__:
                    self.__dict__[key] = method(self)
                return self.__dict__[key]
            return fget
        def setonce(method):
            name, key = privkey(method)
            def fset(self, val):
                if key in self.__dict__:
                    raise AttributeError(name)
                method(self, val)
                self.__dict__[key] = val
            return fset
        def checkstate(**attrs):
            def wrap(func):
                def check(self, *args, **kw):
                    for attr, val in attrs.items():
                        if getattr(self, attr) != val:
                            raise IllegalStateError(attr)
                    return func(self, *args, **kw)
                return check
            return wrap
    return Decorators
Decorators = Decorators()
            
class Kwobj(object):

    def __init__(self, *dicts, **kw):
        for d in dicts:
            self.__dict__.update(d)
        self.__dict__.update(kw)

    def __repr__(self):
        return dictrepr(self.__dict__)

class CacheNotationData(object):

    default_fetch_name = 'default'

    @classmethod
    def load(cls, notn, name, data):
        idx = cls.__getidx(notn)
        typecheck(name, str, 'name')
        typecheck(data, dict, 'data')
        condcheck(
            name not in idx,
            '{0} {1}.{2} already defined'.format(notn, name, cls)
        )
        idx[name] = cls(data)
        return idx[name]

    @classmethod
    def fetch(cls, notn, name = None):
        if name == None:
            name = cls.default_fetch_name
        idx = cls.__getidx(notn)
        builtin = cls.__builtin[notn]
        return idx.get(name) or cls.load(notn, name, builtin[name])

    @classmethod
    def available(cls, notn):
        return sorted(set(cls.__getidx(notn)).union(cls.__builtin[notn]))

    @classmethod
    def __getidx(cls, notn):
        try:
            return cls.__instances[notn]
        except KeyError:
            raise ValueError("Invalid notation '{0}'".format(notn))

    @classmethod
    def _initcache(cls, notns, builtin):
        a_ = '_initcache'
        if cls == __class__:
            raise TypeError("Cannot invoke '{1}' on {0}".format(cls, a_))
        if hasattr(cls, '__builtin'):
            raise AttributeError("{0} has no attribute '{1}'".format(cls, a_))
        builtin = cls.__builtin = dict(builtin)
        notns = set(notns).union(builtin)
        cls.__instances = {notn: {} for notn in notns}

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

class OrderedAttrsView(object):

    def __init__(self, attrmap, valuelist):
        self.__list = valuelist
        self.__map = attrmap

    def __getattr__(self, name):
        try:
            return self.__map[name]
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, key):
        if isint(key):
            return self.__list[key]
        return self.__map[key]

    def __contains__(self, key):
        return key in self.__map

    def __len__(self):
        return len(self.__map)

    def __iter__(self):
        return iter(self.__list)

    def get(self, key, default = None):
        return self.__map.get(key, default)

def LinkOrderSet():

    class LinkEntry(object):
        def __init__(self, item):
            self.prev = self.next = None
            self.item = item
        def __eq__(self, other):
            return self.item == other or (
                isinstance(other, self.__class__) and
                self.item == other.item
            )
        def __hash__(self):
            return hash(self.item)
        def __repr__(self):
            return (self.item).__repr__()

    def View(obj):
        class Viewer(object):
            def __iter__(self):
                return iter(obj)
            def __reversed__(self):
                return reversed(obj)
            def __contains__(self, item):
                return item in obj
            def __len__(self):
                return len(obj)
            def first(self):
                return obj.first()
            def last(self):
                return obj.last()
        return Viewer()

    class LinkOrderSet(object):

        def item(item_method):
            def wrap(self, *args, **kw):
                item = self._genitem_(*args, **kw)
                return item_method(self, item)
            return wrap

        def iter_items(iter_item_method):
            def wrap(self, *args, **kw):
                for item in self._genitems_(*args, **kw):
                    iter_item_method(self, item)
                return 
            return wrap

        def entry(link_entry_method):
            def prep(self, item):
                if item in self:
                    raise DuplicateKeyError(item)
                entry = self.__idx[item] = LinkEntry(item)
                if self.__first == None:
                    self.__first = self.__last = entry
                    return
                if self.__first == self.__last:
                    self.__first.next = entry
                link_entry_method(self, entry)
            return prep

        def _genitem_(self, item):
            return item

        def _genitems_(self, items):
            return (self._genitem_(item) for item in items)

        @item
        @entry
        def append(self, entry):
            if self.__first == self.__last:
                self.__first.next = entry
            entry.prev = self.__last
            entry.prev.next = entry
            self.__last = entry
        add = append
        extend = iter_items(append)

        @item
        @entry
        def prepend(self, entry):
            if self.__first == self.__last:
                self.__last.prev = entry
            entry.next = self.__first
            entry.next.prev = entry
            self.__first = entry
        prextend = iter_items(prepend)

        @item
        def remove(self, item):
            entry = self.__idx.pop(item)
            if entry.prev == None:
                if entry.next == None:
                    # Empty
                    self.__first = self.__last = None
                else:
                    # Remove first
                    entry.next.prev = None
                    self.__first = entry.next
            else:
                if entry.next == None:
                    # Remove last
                    entry.prev.next = None
                    self.__last = entry.prev
                else:
                    # Remove in-between
                    entry.prev.next = entry.next
                    entry.next.prev = entry.prev

        @item
        def discard(self, item):
            if item in self:
                self.remove(item)
        
        def clear(self):
            self.__idx.clear()
            self.__first = self.__last = None

        def first(self):
            return self.__first.item if self.__first else None

        def last(self):
            return self.__last.item if self.__last else None

        @property
        @Decorators.lazyget
        def view(self):
            return View(self)

        def __init__(self):
            self.__first = self.__last = None
            self.__idx = {}

        def __len__(self):
            return len(self.__idx)

        def __contains__(self, item):
            return item in self.__idx

        def __getitem__(self, key):
            return self.__idx[key].item

        def __iter__(self):
            cur = self.__first
            while cur:
                item = cur.item
                yield item
                cur = cur.next
                    
        def __reversed__(self):
            cur = self.__last
            while cur:
                item = cur.item
                yield item
                cur = cur.prev

        def __repr__(self):
            return (self.__class__.__name__, kwrepr(
                len=len(self),
                first=self.__first,
                last=self.__last,
            )).__repr__()

    return LinkOrderSet

LinkOrderSet = LinkOrderSet()
