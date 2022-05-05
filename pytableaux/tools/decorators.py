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
import operator as opr
from collections import defaultdict
from inspect import Signature
from keyword import iskeyword
from types import DynamicClassAttribute as dynca
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Concatenate,
                    Generic, Iterable, Iterator, Mapping)

# Allowed local imports:
#  - errors
#  - tools.abcs
#  - tools.misc
#  - tools.typing
from pytableaux import __docformat__
from pytableaux.errors import check
from pytableaux.tools import MapProxy, abstract
from pytableaux.tools.abcs import Abc, abcf, abcm
from pytableaux.tools.typing import RT, F, P, Self, T, _property

if TYPE_CHECKING:
    from typing import overload

__all__ = (
    'lazy',
    'membr',
    'NoSetAttr',
    'operd',
    'raisr',
    'wraps',
)


EMPTY = ()
WRASS = functools.WRAPPER_ASSIGNMENTS

class _noexcept(Exception): __new__ = None

# _valfilter = _ftpartial(filter, opr.itemgetter(1))

def _valfilter(it: Iterable[T], /, *, getter = opr.itemgetter(1)) -> Iterator[T]:
    return filter(getter, it)

def _getitems(obj, *keys):
    return tuple(map(obj.__getitem__, keys))

def _getmixed(obj, k, default = None):
    try: return obj[k]
    except TypeError:
        return getattr(obj, k, default)
    except KeyError:
        return default

def _thru(obj, *_):
    return obj

def _thru2(_x, obj, *_):
    return obj

def _attrstrcheck(name: str):
    check.inst(name, str)
    if iskeyword(name):
        raise TypeError(f'{name} is a keyword')
    if not name.isidentifier():
        raise TypeError(f'{name} is not an identifier')
    return name

def _methcaller(name: str):
    name = _attrstrcheck(name)
    def f(obj, *args, **kw):
        return getattr(obj, name)(*args, **kw)
    f.__name__ = name
    return f

def _checkcallable2(obj):
    if isinstance(obj, str):
        return _methcaller(obj)
    return check.callable(obj)

class BaseMember(Abc, Generic[T]):

    __slots__ = '__name__', '__qualname__', '__owner'

    def __set_name__(self, owner: T, name):
        self.owner = owner
        self.name = name
        for hook in self._sethooks:
            hook(self, owner, name)

    @property
    def owner(self) -> T:
        try: return self.__owner
        except AttributeError: pass

    @property
    def name(self) -> str:
        try: return self.__name__
        except AttributeError: pass
        return type(self).__name__

    @owner.setter
    def owner(self, value):
        self.__owner = check.inst(value, type)
        try: self._update_qualname()
        except AttributeError: pass

    @name.setter
    def name(self, value):
        self.__name__ = _attrstrcheck(value)
        try: self._update_qualname()
        except AttributeError: pass

    def _update_qualname(self):
        self.__qualname__ = '%s.%s' % (self.owner.__name__, self.name)

    def __repr__(self):
        if not hasattr(self, '__qualname__') or not callable(self):
            return object.__repr__(self)
        return '<callable %s at %s>' % (self.__qualname__, hex(id(self)))

    _sethooks = EMPTY

    def __init_subclass__(subcls, **kw):
        super().__init_subclass__(**kw)
        hooks = dict.fromkeys(abcm.merge_mroattr(subcls, '_sethooks',
            oper = opr.add, supcls = __class__
        ))
        hook = getattr(subcls, 'sethook', None)
        if hook:
            hooks[hook] = None
            delattr(subcls, 'sethook')
        subcls._sethooks = tuple(hooks)

class Twofer(Abc, Generic[F]):

    __slots__ = EMPTY

    if TYPE_CHECKING:
        @overload
        def __new__(cls, func: F) -> F: ...
        @overload
        def __new__(cls: type[T]) -> T: ...
        @overload
        def __call__(self, func: F) -> F: ...

    def __new__(cls, arg = None, /, *a, **kw):
        """If only argument to constructor is callable, construct and call the
        instance. Otherwise create normally.
        """
        inst = object.__new__(cls)
        if len(a) or len(kw) or not isinstance(arg, Callable):
            inst._init(arg, *a, **kw)
            return inst
        if isinstance(inst._blankinit, Callable): 
            inst._blankinit()
        return inst(arg)

    @abstract
    def __call__(self, func: F) -> F: ...

    @abstract
    def _init(self, arg = None, /, *a, **kw): ...

    def _blankinit(self):
        self._init()

class membr(BaseMember[T], Generic[T, RT]):

    __slots__ = 'cbak',

    owner: T
    cbak: tuple[Callable[..., RT], tuple, dict]

    def __init__(self, cb: Callable[..., RT], *args, **kw):
        self.cbak = cb, args, kw

    def sethook(self, owner: T, name):
        setattr(owner, name, wraps(self)(self())) # type: ignore

    def __call__(self):
        cb, args, kw = self.cbak
        return cb(self, *args, **kw)

    @classmethod
    def defer(cls, fdefer: Callable[Concatenate[membr[T, RT], P], RT]) -> Callable[P, RT]:
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

        __slots__ = 'oper', 'info'

        oper: Callable
        info: Callable|Mapping|None

        def __init__(self, oper: Callable, info: Callable|Mapping = None):
            self.oper = oper
            self.info = info

        def sethook(self, owner, name):
            if self.info is None:
                self.info = self
            setattr(owner, name, self())

        def _getinfo(self, info: Callable|Mapping = None, /) -> Callable|Mapping:
            if info is None:
                if self.info is None:
                    return self.oper
                return self.info
            return info

    class apply(Base):
        """Create a function or method from an operator, or other
        built-in function.
        """

        __slots__ = EMPTY

        def __call__(self, info: Callable|Mapping = None):
            info = self._getinfo(info)
            oper = check.callable(self.oper)
            n = len(Signature.from_callable(oper).parameters)
            if n == 1:
                def fapply(operand): return oper(operand)
            elif n == 2:
                def fapply(lhs, rhs): return oper(lhs, rhs)
            else:
                def fapply(*args): return oper(*args)
            return wraps(info)(fapply)

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

        __slots__ = 'freturn', 'finit'

        freturn: Callable
        finit: Callable

        def __init__(self, oper: Callable, /,
            info: Callable|Mapping = None,
            freturn: Callable|str = _thru2,
            finit: Callable|str = _thru,
        ):
            super().__init__(oper, info)
            self.freturn = _checkcallable2(freturn)
            self.finit = _checkcallable2(finit)

        def __call__(self, info: Callable|Mapping = None):
            info = self._getinfo(info)
            oper, freturn, finit = map(check.callable,
                (self.oper, self.freturn, self.finit),
            )
            @wraps(info)
            def freduce(self, *operands):
                return freturn(self, functools.reduce(oper, operands, finit(self)))
            return freduce

        # @staticmethod
        # def template(*argdefs, **kwdefs) -> type[operd.reduce]:
        #     'Make a templated subclass with bound arguments.'
        #     class templated(__class__):
        #         _argdefs = argdefs
        #         _kwdefs = kwdefs
        #         __slots__ = ()
        #         def __init__(self, *args, **kw):
        #             super().__init__(*(argdefs + args), **(kwdefs | kw))
        #     return templated

    # class order(Base):
    #     """Wrap an ordering func with oper like: ``oper(func(a, b), 0)``. By
    #     default, except (AttributeError, TypeError), and return ``NotImplemented``.
    #     """

    #     __slots__ = 'errs',

    #     def __init__(self, oper: Callable, /, *errs: type[Exception], info: Callable|Mapping = None):
    #         super().__init__(oper, info)
    #         if errs:
    #             if errs == (None,): self.errs = _noexcept,
    #             else: self.errs = errs
    #             for ecls in self.errs:
    #                 check.inst(ecls, type)
    #                 check.subcls(ecls, Exception)
    #         else:
    #             self.errs = AttributeError, TypeError

    #     def __call__(self, fcmp: Callable):
    #         oper, fcmp = map(check.callable, (self.oper, fcmp))
    #         errs = self.errs
    #         @wraps(oper)
    #         def f(self, other) -> bool:
    #             try:
    #                 return oper(fcmp(self, other), 0)
    #             except errs:
    #                 return NotImplemented
    #         return f

    if TYPE_CHECKING:

        @overload
        @staticmethod
        def repeat(oper: Callable, info: F) -> F: ...

        @overload
        @staticmethod
        def repeat(oper: F) -> F: ...

    class repeat(Base):
        """Create a method that accepts an arbitrary number of positional
        arguments, and repeatedly calls a one argument method for each
        argument (or, equivalently, a two-argument function with self as the
        first argument).
        """

        __slots__ = EMPTY

        def __call__(self, info: Callable|Mapping = None):
            info = self._getinfo(info)
            oper = check.callable(self.oper)
            @wraps(info)
            def f(self, *args):
                for arg in args: oper(self, arg)
            return f

class wraps(BaseMember):

    __slots__ = '_initial', '_adds'

    def __init__(self, fin: Callable|Mapping):
        'Initialize argument, intial input function that will be decorated.'
        self._adds = {}
        self._initial = self.read(fin)

    def __call__(self, fout: F) -> F:
        'Decorate function. Receives the wrapper function and updates its attributes.'
        self.update(fout)
        if isinstance(fout, (classmethod, staticmethod)):
            self.write(fout.__func__)
        else:
            self.write(fout)
        return fout

    @staticmethod
    def read(data):
        return dict(
            _valfilter((k, _getmixed(data, k)) for k in WRASS)
        )

    def update(self, data = None, /, **kw) -> wraps:
        data = self.read(data) | self.read(kw)
        adds = self._adds
        initial = self._initial
        skip = {'__doc__', '__annotations__'}
        for attr, val in _valfilter((k, data.get(k)) for k in WRASS):
            if attr in skip:
                if initial.get(attr):
                    continue
            adds[attr] = val
        return self

    def merged(self):
        adds = self._adds
        initial = self._initial
        return dict(
            _valfilter((k, initial.get(k, adds.get(k))) for k in WRASS)
        )

    def write(self, obj: F) -> F:
        for attr, val in self.merged().items():
            setattr(obj, attr, val)
        return obj

class raisr(BaseMember):
    """Creates an object that raises the exception when called. When
    `__set_name__` is called, creates a new function. Not to be used
    as a decorator.
    """

    __slots__ = 'errtype', 'eargs', 'ekw'

    def __init__(self, errtype: type[Exception], *eargs, **ekw):
        self.errtype = check.subcls(errtype, Exception)
        self.eargs = eargs
        self.ekw = ekw

    def __call__(self, *args, **kw):
        raise self.errtype(*self.eargs, *args[0:1], **self.ekw)

    def sethook(self, owner, name):
        eargs = self.eargs
        errtype = self.errtype
        ekw = self.ekw
        @wraps(self)
        def f(*args, **kw):
            raise errtype(*eargs, *args[0:1], **ekw)
        f.__doc__ = 'Raises %s' % errtype.__name__
        setattr(owner, name, f)

class lazy:

    __slots__ = EMPTY

    def __new__(cls, *args, **kw):
        return cls.get(*args, **kw)

    class get(Twofer[F], BaseMember):

        __slots__ = 'key', 'method'

        if TYPE_CHECKING:
            @overload
            def __new__(cls, method: F) -> F: ...
            @overload
            def __new__(cls, key: str|None, method: F) -> F: ...
            @overload
            def __new__(cls, key: str|None) -> lazy.get: ...
            @overload
            def __new__(cls) -> lazy.get: ...

        __new__ = Twofer.__new__

        def __call__(self, method: F) -> F:
            key = self.key or self.format(method.__name__)
            @wraps(method)
            def fget(self):
                try: return getattr(self, key)
                except AttributeError: pass
                value = method(self)
                setattr(self, key, value)
                return value
            return fget

        def _init(self, key = None, method = None, /):
            if key is not None:
                check.inst(key, str)
            self.key = key
            if method is not None:
                check.inst(method, Callable)
            self.method = method

        def _blankinit(self):
            self.method = self.key = None

        def sethook(self, owner, name):
            if self.key is None:
                self.key = self.format(name)
            setattr(owner, name, self(self.method))

        def format(self, name: str) -> str:
            return '_%s' % name

    class attr(get[F]):
        __slots__ = 'name', 'method'

    class prop(get[type[Self]]):
        """Return a property with the getter. NB: a setter/deleter should be
        sure to use the correct attribute."""

        __slots__ = EMPTY

        if TYPE_CHECKING:
            @overload
            def __new__(cls, func: Callable[[Self], T]) -> _property[Self, T]: ...

        __new__ = Twofer.__new__

        def __call__(self, method: Callable[[Self], T]) -> _property[Self, T]:
            return property(super().__call__(method), doc = method.__doc__)

    class dynca(prop[Self]):
        """Return a DynamicClassAttribute with the getter. NB: a setter/deleter
        should be sure to use the correct attribute."""

        __slots__ = EMPTY

        def __call__(self, method: Callable[[Self], T]) -> _property[Self, T]:
            return dynca(
                lazy.get.__call__(self, method), doc = method.__doc__
            )

class NoSetAttr(BaseMember):
    'Lame thing that does a lame thing.'


    _defaults: ClassVar[Mapping[str, Any]] = MapProxy(dict(cls = None, attr = None))
    efmt = "Attribute '{0}' of '{1.__class__.__name__}' objects is readonly".format

    __slots__ = 'enabled', 'defaults', '_cache', '_isroot'

    enabled: bool
    defaults: Mapping
    _cache: dict
    _isroot: bool

    def __init__(self, /, *, enabled: bool = True, root: bool = False, **defaults):
        self.enabled = bool(enabled)
        self._isroot = bool(root)
        self.defaults = self._defaults | defaults
        self._cache = defaultdict(dict)

    def __call__(self, basecls, **opts):
        opts = self.defaults | opts
        attr, cls = _getitems(opts, 'attr', 'cls')
        ok = basecls.__setattr__
        efmt = self.efmt
        return self._make(ok, efmt, attr, cls)

    def _make(self, ok, efmt, attr, cls, /):
        if attr:
            if cls == True:
                check = self._clschecker(attr)
            elif cls:
                check = self._fixedchecker(attr, cls)
            else:
                check = self._selfchecker(attr)
            def f(obj, name, value):
                if self.enabled and check(obj):
                    raise AttributeError(efmt(name, obj))
                ok(obj, name, value)
        else:
            def f(obj, name, value):
                if self.enabled:
                    raise AttributeError(efmt(name, obj))
                ok(obj, name, value)
        return wraps(ok)(f)

    @abcf.temp
    def cache(func: F) -> F:
        @wraps(func)
        def f(self: NoSetAttr, *args):
            try:
                value = self._cache[func][args]
            except KeyError:
                value = self._cache[func][args] = func(self, *args)
            return value
        return f

    @cache
    def _fixedchecker(self, attr, obj):
        def check(self):
            return getattr(obj, attr, False)
        return check

    @cache
    def _callchecker(self, attr, fget):
        def check(obj):
            return getattr(fget(obj), attr, False)
        return check

    @cache
    def _clschecker(self, attr):
        return self._callchecker(type, attr)

    @cache
    def _selfchecker(self, attr):
        def check(obj):
            return getattr(obj, attr, False)
        return check

    def sethook(self, owner, name):
        if self._isroot:
            self._isroot = False
            return
        basecls = owner.__bases__[0]
        func = self(basecls)
        func.__name__ = name
        func.__qualname__ = '%s.%s' % (owner.__qualname__, name)
        setattr(owner, name, func)
