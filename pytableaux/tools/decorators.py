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
pytableaux.tools.decorators
^^^^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import functools
import sys
from collections import defaultdict
from collections.abc import Mapping
from keyword import iskeyword
from types import DynamicClassAttribute as dynca
from typing import Any, Callable, ClassVar, Generic, TypeVar

from pytableaux import __docformat__
from pytableaux.errors import check
from pytableaux.tools import MapProxy, abcs, dund, getitem, undund


_T = TypeVar('_T')
_F = TypeVar('_F', bound=Callable)
# _P = ParamSpec('_P')
_RT = TypeVar('_RT')
# if TYPE_CHECKING:
#     from typing import overload

    # from pytableaux.tools.typing import _property

__all__ = (
    'lazy',
    'membr',
    'NoSetAttr',
    'operd',
    'raisr',
    'wraps',
)


EMPTY = ()
WRASS_SET = frozenset(functools.WRAPPER_ASSIGNMENTS)

def select_fget(obj):
    if callable(getattr(obj, '__getitem__', None)):
        return getitem
    return getattr

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

class BaseMember(Generic[_T], metaclass = abcs.AbcMeta):

    __slots__ = '__name__', '__qualname__', '__owner'

    def __set_name__(self, owner: _T, name):
        self.__owner = owner
        self.__name__ = name
        self.__qualname__ = f'{owner.__name__}.{name}'
        self.sethook(owner, name)

    def sethook(self, owner, name):
        pass

    @property
    def owner(self) -> _T:
        try:
            return self.__owner
        except AttributeError:
            pass

    @property
    def name(self) -> str:
        try:
            return self.__name__
        except AttributeError:
            return type(self).__name__

    def __repr__(self):
        if not hasattr(self, '__qualname__') or not callable(self):
            return object.__repr__(self)
        return '<callable %s at %s>' % (self.__qualname__, hex(id(self)))

class membr(BaseMember[_T], Generic[_T, _RT]):

    __slots__ = 'cbak',

    owner: _T
    cbak: tuple[Callable[..., _RT], tuple, dict]

    def __init__(self, cb: Callable[..., _RT], *args, **kw):
        self.cbak = cb, args, kw

    def sethook(self, owner: _T, name: str):
        setattr(owner, name, self())

    def __call__(self):
        cb, args, kw = self.cbak
        return cb(self, *args, **kw)

    @classmethod
    def defer(cls, fdefer: Callable) -> Callable:
    # def defer(cls, fdefer: Callable[Concatenate[membr[T, RT], P], RT]) -> Callable[P, RT]:
        def fd(member, *args, **kw):
            return fdefer(member, *args, **kw)
        def f(*args, **kw):
            return cls(fd, *args, **kw)
        return f # type: ignore

class operd:
    """Build operational functions: `apply` (default), `reduce`, `order`, `repeat`.
    """

    def __new__(cls, *args, **kw):
        return cls.apply(*args, **kw)

    class Base(BaseMember, Callable):

        __slots__ = 'oper', 'wrap'

        oper: Callable

        def __init__(self, oper: Callable, info: Any = None):
            self.oper = oper
            self.wrap = wraps(info).update(oper)

        def sethook(self, owner, name):
            setattr(owner, name, self())

    class apply(Base):
        """Create a function or method from an operator, or other
        built-in function.
        """

        __slots__ = EMPTY

        def __call__(self, info: Any = None):
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

        def __init__(self, oper: Callable, /,
            info: Any = None, freturn: Callable|str = _thru2,
            finit: Callable|str = _thru,
        ):
            super().__init__(oper, info)
            self.inout = (
                _methcaller(val)
                    if isinstance(val, str) else
                check.callable(val)
                    for val in (freturn, finit)
            )

        def __call__(self, info: Callable|Mapping = None):
            oper, freturn, finit = (self.oper, *self.inout)
            @self.wrap.update(info)
            def freduce(self, *operands):
                return freturn(self, functools.reduce(oper, operands, finit(self)))
            return freduce

    # if TYPE_CHECKING:

    #     @overload
    #     @staticmethod
    #     def repeat(oper: Callable, info: F) -> F: ...

    #     @overload
    #     @staticmethod
    #     def repeat(oper: F) -> F: ...

    class repeat(Base):
        """Create a method that accepts an arbitrary number of positional
        arguments, and repeatedly calls a one argument method for each
        argument (or, equivalently, a two-argument function with self as the
        first argument).
        """

        __slots__ = EMPTY

        def __call__(self, info: Callable|Mapping = None):
            oper = check.callable(self.oper)
            @self.wrap.update(info)
            def f(self, *args):
                for arg in args: oper(self, arg)
            return f

class wraps(dict[str, str]):

    __slots__ = 'only', 'original',

    def __init__(self, original: Callable|Mapping = None, /, only = WRASS_SET, exclude = (), **kw):
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

    def __call__(self, fout: _F) -> _F:
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

    def write(self, obj: _F) -> _F:
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

class raisr(BaseMember):
    """Factory for raising an error. Not to be used as a decorator.
    """

    __slots__ = 'wrap', 'Error'

    def __init__(self, Error: type[Exception], /):
        self.Error = check.subcls(Error, Exception)
        self.wrap = wraps(only = ('name', 'qualname', 'module', 'doc'),
            doc = f"""
            Raises:
                {Error.__name__}: always
            """
        )

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
        setattr(owner, name, self( getattr(owner.__bases__[0], name, self)))

class lazy:

    __slots__ = EMPTY

    def __new__(cls, *args, **kw):
        return cls.get(*args, **kw)

    class get(BaseMember, Generic[_F], metaclass = abcs.AbcMeta):

        __slots__ = 'key', 'method'
        format = '_{}'.format

        # if TYPE_CHECKING:
        #     @overload
        #     def __new__(cls, method: F) -> F: ...
        #     @overload
        #     def __new__(cls, key: str|None, method: F) -> F: ...
        #     @overload
        #     def __new__(cls, key: str|None) -> lazy.get: ...
        #     @overload
        #     def __new__(cls) -> lazy.get: ...

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

        def __call__(self, method: _F) -> _F:
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

    # class prop(get[type[Self]]):
    class prop(get):
        """Return a property with the getter. NB: a setter/deleter should be
        sure to use the correct attribute.
        """

        __slots__ = EMPTY

        @property
        def propclass(self):
            return property

        # if TYPE_CHECKING:
        #     @overload
        #     def __new__(cls, func: Callable[[Self], T]) -> property[Self, T]: ...

        def __call__(self, method: Callable):
        # def __call__(self, method: Callable[[Self], T]) -> property[Self, T]:
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

    _defaults: ClassVar[Mapping[str, Any]] = MapProxy(dict(
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

    defaults: dict[str, Any]

    cache: dict[Any, dict]

    def __init__(self, /, *, enabled: bool = True, **defaults):
        self.enabled = bool(enabled)
        self.defaults = self._defaults | defaults
        self.cache = defaultdict(dict)

    def __call__(self, base: type, **opts):
        return self._make(base.__setattr__, **(self.defaults | opts))

    # def _make(self, sa: _F, /, efmt: Callable[[str, Any], str], attr: str|None, cls: bool|type|None) -> _F:
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
    def cached(func: _F) -> _F:
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
