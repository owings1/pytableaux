# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
pytableaux.tools
----------------

"""
from __future__ import annotations

import functools
import keyword
import re
import sys
from abc import abstractmethod as abstract
from collections import defaultdict
from collections.abc import Callable, Mapping
from keyword import iskeyword
from types import DynamicClassAttribute as dynca
from types import FunctionType
from types import MappingProxyType as MapProxy

from pytableaux import __docformat__

__all__ = (
    'abstract',
    'closure',
    'dund',
    'dxopy',
    'EMPTY_MAP',
    'getitem',
    'isattrstr',
    'isdund',
    'isint',
    'isstr',
    'key0',
    'lazy',
    'MapProxy',
    'maxceil',
    'membr',
    'minfloor',
    'NoSetAttr',
    'operd',
    'raisr',
    'sbool',
    'select_fget',
    'thru',
    'true',
    'undund',
    'wraps',
)


EMPTY = ()
EMPTY_MAP = MapProxy({})
NOARG = object()
WRASS_SET = frozenset(functools.WRAPPER_ASSIGNMENTS)

def closure(func):
    """Closure decorator calls the argument and returns its return value.
    If the return value is a function, updates its wrapper.
    """
    ret = func()
    if type(ret) is FunctionType:
        functools.update_wrapper(ret, func)
    return ret

def thru(obj):
    'Return the argument.'
    return obj

def true(_):
    'Always returns ``True``.'
    return True

def key0(obj):
    'Get key/subscript ``0``.'
    return obj[0]

def dund(name:str) -> str:
    "Convert name to dunder format."
    return name if isdund(name) else f'__{name}__'

def isdund(name: str) -> bool:
    'Whether the string is a dunder name string.'
    return (
        len(name) > 4 and
        name[:2] == name[-2:] == '__' and
        name[2] != '_' and
        name[-3] != '_'
    )

def undund(name: str) -> str:
    "Remove dunder from the name."
    if isdund(name):
        return name[2:-2]
    return name

def isint(obj) -> bool:
    'Whether the argument is an :obj:`int` instance'
    return isinstance(obj, int)

def isattrstr(obj) -> bool:
    "Whether the argument is a non-keyword identifier string"
    return (
        isinstance(obj, str) and
        obj.isidentifier() and
        not keyword.iskeyword(obj)
    )

def isstr(obj) -> bool:
    'Whether the argument is an :obj:`str` instance'
    return isinstance(obj, str)

re_boolyes = re.compile(r'^(true|yes|1)$', re.I)
'Regex for string boolean `yes`.'

def sbool(arg: str, /) -> bool:
    "Cast string to boolean, leans toward ``False``."
    return bool(re_boolyes.match(arg))

def getitem(obj, key, default = NOARG, /):
    "Get by subscript similar to :func:`getattr`."
    try:
        return obj[key]
    except (KeyError, IndexError):
        if default is NOARG:
            raise
        return default

def select_fget(obj):
    if callable(getattr(obj, '__getitem__', None)):
        return getitem
    return getattr

def minfloor(floor, it):
    it = iter(it)
    try:
        minval = next(it)
    except StopIteration:
        raise ValueError(f"minfloor() arg is an empty sequence") from None
    for val in it:
        if val == floor:
            return val
        if val < minval:
            minval = val
    return minval

def maxceil(ceil, it):
    it = iter(it)
    try:
        maxval = next(it)
    except StopIteration:
        raise ValueError(f"maxceil() arg is an empty sequence") from None
    for val in it:
        if val == ceil:
            return val
        if val > maxval:
            maxval = val
    return maxval

@closure
def dxopy():

    def api(a, proxy = False, /, ):
        """Deep map copy, recursive for mapping values.
        Safe for circular reference. Second arg supports
        deep proxy.
        """
        if proxy:
            wrap = MapProxy
        else:
            wrap = thru
        return runner(a, {}, wrap, runner)

    def runner(a: Mapping, memo, wrap, recur):
        if (i := id(a)) in memo:
            return a
        memo[i] = True
        m = wrap({
            key: recur(value, memo, wrap, recur)
                if isinstance(value, Mapping)
                else value
            for key, value in a.items()
        })
        memo[id(m)] = True
        return m

    return api



from pytableaux.tools import abcs
from pytableaux.errors import check

class BaseMember(metaclass = abcs.AbcMeta):

    __slots__ = '__name__', '__qualname__', '__owner'

    def __set_name__(self, owner, name):
        self.__owner = owner
        self.__name__ = name
        self.__qualname__ = f'{owner.__name__}.{name}'
        self.sethook(owner, name)

    def sethook(self, owner, name):
        pass

    @property
    def owner(self):
        try:
            return self.__owner
        except AttributeError:
            pass

    @property
    def name(self):
        try:
            return self.__name__
        except AttributeError:
            return type(self).__name__

    def __repr__(self):
        if not hasattr(self, '__qualname__') or not callable(self):
            return object.__repr__(self)
        return '<callable %s at %s>' % (self.__qualname__, hex(id(self)))


class membr(BaseMember):

    __slots__ = 'cbak',

    owner: object
    cbak: tuple

    def __init__(self, cb, *args, **kw):
        self.cbak = cb, args, kw

    def sethook(self, owner, name):
        setattr(owner, name, self())

    def __call__(self):
        cb, args, kw = self.cbak
        return cb(self, *args, **kw)

    @classmethod
    def defer(cls, fdefer):
        def fd(member, *args, **kw):
            return fdefer(member, *args, **kw)
        def f(*args, **kw):
            return cls(fd, *args, **kw)
        return f



def _thru(obj, *_):
    return obj

def _thru2(_x, obj, *_):
    return obj

def _methcaller(name: str):
    if iskeyword(name) or not name.isidentifier():
        raise TypeError(f"Invalid attr name '{name}'")
    def f(obj, *args, **kw):
        return getattr(obj, name)(*args, **kw)
    f.__name__ = name
    return f

def _prevmodule(thisname = __name__, /):
    f = sys._getframe()
    while (f := f.f_back) is not None:
        val = f.f_globals.get('__name__', '__main__')
        if val != thisname:
            return val

class wraps(dict):

    __slots__ = 'only', 'original',

    def __init__(self, original = None, /, only = WRASS_SET, exclude = EMPTY, **kw):
        'Initialize argument, initial input function that will be decorated.'
        self.original = original
        only = set(map(dund, only))
        only.difference_update(map(dund, exclude))
        only.intersection_update(WRASS_SET)
        self.only = only
        if kw:
            self.update(kw)
        if original:
            self.update(original)
            if (k := '__module__') in only and k not in self:
                if (v := getattr(original, '__objclass__', None)):
                    self.setdefault(k, v)
                else:
                    self.setdefault(k, _prevmodule())

    def __call__(self, fout):
        'Decorate function. Receives the wrapper function and updates its attributes.'
        self.update(fout)
        if isinstance(fout, (classmethod, staticmethod)):
            self.write(fout.__func__)
        else:
            self.write(fout)
        return fout

    def read(self, obj):
        "Read relevant attributes from object/mapping."
        get = select_fget(obj)
        for name in self.only:
            if (value := get(obj, name, None)):
                yield name, value
            elif (value := get(obj, undund(name), None)):
                yield name, value

    def write(self, obj):
        "Write wrapped attributes to a wrapper."
        for attr, val in self.items():
            setattr(obj, attr, val)
        if callable(self.original):
            obj.__wrapped__ = self.original
        return obj

    def update(self, obj = None, /, **kw):
        """Read from an object/mapping and update relevant values. Any attributes
        already present are ignored. Returns self.
        """
        for o in obj, kw:
            if o is not None:
                for attr, val in self.read(o):
                    if attr not in self:
                        self[attr] = val
        return self

    def setdefault(self, key, value):
        "Override value if key is relevant and value is not empty."
        if key in self.only:
            if value:
                self[key] = value
                return value
            return self[key]
            
    def __setitem__(self, key, value):
        if key in self or key not in self.only:
            raise KeyError(key)
        super().__setitem__(key, value)

    def __repr__(self):
        return f'{type(self).__name__}({dict(self)})'

class operd:
    """Build operational functions: `apply` (default), `reduce`, `order`, `repeat`.
    """

    def __new__(cls, *args, **kw):
        return cls.apply(*args, **kw)

    class Base(BaseMember, Callable):

        __slots__ = 'oper', 'wrap'

        def __init__(self, oper, info = None):
            self.oper = oper
            self.wrap = wraps(info).update(oper)

        def sethook(self, owner, name):
            setattr(owner, name, self())

    class apply(Base):
        """Create a function or method from an operator, or other
        built-in function.
        """
        __slots__ = EMPTY

        def __call__(self, info = None):
            oper = check.callable(self.oper)
            @self.wrap.update(info)
            def f(*args):
                return oper(*args)
            return f

    class reduce(Base):
        """Create a reducing method using functools.reduce to apply
        a single operator/function to an arbitrarily number of arguments.

        Args:

            oper: The operator, or any two-argument function.

            info: The original or stub method being replaced, or an
                object with informational attributes (`__name__`, `__doc__`, etc.)
                to be passed through `wraps`.

            freturn: A two-argument function that takes `self` and the
                end result, e.g. to create a copy of an object, etc. This could
                be a method-caller, which would invoke the method on the first
                argument (self). Default is to return the second argument (result).

            finit: A single-argument function that takes `self` to seed
                the initial value. This could be used, for example, to ensure
                a copy is created in case the number of arguments is 0.
        """

        __slots__ = 'inout',

        inout: tuple[Callable, Callable]

        def __init__(self, oper, /, info = None, freturn = _thru2, finit = _thru):
            super().__init__(oper, info)
            self.inout = (
                _methcaller(val)
                    if isinstance(val, str) else
                check.callable(val)
                    for val in (freturn, finit))

        def __call__(self, info = None):
            oper, freturn, finit = (self.oper, *self.inout)
            @self.wrap.update(info)
            def freduce(self, *operands):
                return freturn(self, functools.reduce(oper, operands, finit(self)))
            return freduce

    class repeat(Base):
        """Create a method that accepts an arbitrary number of positional
        arguments, and repeatedly calls a one argument method for each
        argument (or, equivalently, a two-argument function with self as the
        first argument).
        """

        __slots__ = EMPTY

        def __call__(self, info = None):
            oper = check.callable(self.oper)
            @self.wrap.update(info)
            def f(self, *args):
                for arg in args: oper(self, arg)
            return f

class raisr(BaseMember):
    """Factory for raising an error. Not to be used as a decorator.
    """

    __slots__ = 'wrap', 'Error'

    def __init__(self, Error, /):
        self.Error = check.subcls(Error, Exception)
        self.wrap = wraps(only = ('name', 'qualname', 'module', 'doc'),
            doc = f"""
            Raises:
                {Error.__name__}: always
            """)

    def __call__(self, original = None, /):
        wrap = self.wrap
        if original:
            wrap.original = original
            wrap.update(original)
        Error = self.Error
        def f(self, *args, **_):
            raise Error(*args[0:1])
        return wrap(f)

    def sethook(self, owner, name):
        setattr(owner, name, self(getattr(owner.__bases__[0], name, self)))

class lazy:

    __slots__ = EMPTY

    def __new__(cls, *args, **kw):
        return cls.get(*args, **kw)

    class get(BaseMember):

        __slots__ = 'key', 'method'
        format = '_{}'.format

        def __new__(cls, key = None, /, method = None):
            """If only argument to constructor is callable, construct and call the
            instance. Otherwise create normally.
            """
            inst = object.__new__(cls)
            inst.method = method
            if not callable(key) or method is not None:
                inst.key = check.inst(key, str)
                if method is not None:
                    check.callable(method)
                return inst
            inst.key = None
            return inst(check.callable(key))

        def __call__(self, method):
            key = self.key or self.format(method.__name__)
            @wraps(method)
            def fget(self):
                try:
                    return getattr(self, key)
                except AttributeError:
                    pass
                setattr(self, key, value := method(self))
                return value
            return fget

        def sethook(self, owner, name):
            if self.key is None:
                self.key = self.format(name)
            setattr(owner, name, self(self.method))

    class prop(get):
        """Return a property with the getter. NB: a setter/deleter should be
        sure to use the correct attribute.
        """

        __slots__ = EMPTY

        @property
        def propclass(self):
            return property

        def __call__(self, method):
            fget = super().__call__(method)
            return self.propclass(fget, doc = method.__doc__)

    class dynca(prop):
        """Return a DynamicClassAttribute with the getter. NB: a setter/deleter
        should be sure to use the correct attribute.
        """

        @property
        def propclass(self):
            return dynca

        __slots__ = EMPTY

class NoSetAttr(BaseMember):
    'Lame thing that does a lame thing.'

    enabled: bool
    "Whether raising is enabled."

    _defaults = MapProxy(dict(
        efmt = (
            "Attribute '{0}' of '{1.__class__.__name__}' "
            "objects is readonly"
        ).format,

        # Control attribute name to check on the object,
        # e.g. '_readonly', in addition to this object's
        # `enabled` setting.
        attr = None,

        # If `True`: Check `attr` on the object's class;
        # If set to a `type`, check the `attr` on that class;
        # If Falsy, only check for this object's `enabled` setting.
        cls = None,
    ))

    __slots__ =  'cache', 'defaults', 'enabled',

    defaults: dict
    cache: dict

    def __init__(self, /, *, enabled = True, **defaults):
        self.enabled = bool(enabled)
        self.defaults = self._defaults | defaults
        self.cache = defaultdict(dict)

    def __call__(self, base: type, **opts):
        return self._make(base.__setattr__, **(self.defaults | opts))

    def _make(self, sa, /, efmt, attr, cls):
        if attr:
            if cls is True:
                check = self._clschecker(attr)
            elif cls:
                check = self._fixedchecker(attr, cls)
            else:
                check = self._selfchecker(attr)
            def f(obj, name, value, /):
                if self.enabled and check(obj):
                    raise AttributeError(efmt(name, obj))
                sa(obj, name, value)
        else:
            def f(obj, name, value, /):
                if self.enabled:
                    raise AttributeError(efmt(name, obj))
                sa(obj, name, value)
        return wraps(sa)(f)

    @abcs.abcf.temp
    def cached(func):
        @wraps(func)
        def f(self: NoSetAttr, *args):
            cache = self.cache[func]
            try:
                return cache[args]
            except KeyError:
                return cache.setdefault(args, func(self, *args))
        return f

    @cached
    def _fixedchecker(self, attr, obj):
        return lambda _: getattr(obj, attr, False)

    @cached
    def _callchecker(self, attr, fget):
        return lambda obj: getattr(fget(obj), attr, False)

    @cached
    def _clschecker(self, attr):
        return self._callchecker(type, attr)

    @cached
    def _selfchecker(self, attr):
        return lambda obj: getattr(obj, attr, False)

    def sethook(self, owner, name):
        func = self(owner.__bases__[0])
        func.__name__ = name
        func.__qualname__ = self.__qualname__
        setattr(owner, name, func)
