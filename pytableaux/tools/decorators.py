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
from collections import ChainMap, defaultdict
from collections.abc import Mapping
from inspect import Signature
from keyword import iskeyword
import sys
from types import DynamicClassAttribute as dynca
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Concatenate,
                    Generic, Iterable, Iterator)

import traceback
# Allowed local imports:
#  - errors
#  - tools.abcs
#  - tools.misc
#  - tools.typing
from pytableaux import __docformat__
from pytableaux.errors import check
from pytableaux.tools import MapProxy, abstract, abcs, dund, getitem
from pytableaux.tools.abcs import abcf, abcm
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
WRASS_SET = frozenset(WRASS)

# class _noexcept(Exception): __new__ = None

def select_fget(obj):
    if callable(getattr(obj, '__getitem__', None)):
        return getitem
    return getattr

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

def _prevmodule(thisname = __name__, /):
    f = sys._getframe()
    while (f := f.f_back) is not None:
        val = f.f_globals.get('__name__', '__main__')
        if val != thisname:
            return val

    # sys._getframe().f_back.f_back
    # val = sys._getframe(2).f_globals.get('__name__', '__main__')
    # if val != __name__:
    #     return val

class BaseMember(Generic[T], metaclass = abcs.AbcMeta):

    __slots__ = '__name__', '__qualname__', '__owner'

    def __set_name__(self, owner: T, name):
        self.owner = owner
        self.name = name
        self.sethook(owner, name)
        # for hook in self._sethooks:
        #     hook(self, owner, name)
    def sethook(self, owner, name):
        pass

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

    # _sethooks = EMPTY

    # def __init_subclass__(subcls, **kw):
    #     super().__init_subclass__(**kw)
    #     hooks = dict.fromkeys(abcm.merge_attr(subcls, '_sethooks',
    #         oper = opr.add, supcls = __class__
    #     ))
    #     hook = getattr(subcls, 'sethook', None)
    #     if hook:
    #         hooks[hook] = None
    #         delattr(subcls, 'sethook')
    #     subcls._sethooks = tuple(hooks)
    #     if len(hooks) > 1:
    #         raise TypeError(subcls)

class Twofer(Generic[F], metaclass = abcs.AbcMeta):

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
        setattr(owner, name,
            # wraps(self,
            #     exclude = {'module'},
            # )(
                self()
            # )
        ) # type: ignore

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

        __slots__ = 'oper', 'info', 'wrap'

        oper: Callable
        info: Callable|Mapping|None

        def __init__(self, oper: Callable, info: Callable|Mapping = None):
            self.oper = oper
            self.info = info
            self.wrap = wraps(info).update(oper)

        def sethook(self, owner, name):
            if self.info is None:
                self.info = self
            setattr(owner, name, self())

    class apply(Base):
        """Create a function or method from an operator, or other
        built-in function.
        """

        __slots__ = EMPTY

        def __call__(self, info: Callable|Mapping = None):
            self.wrap.update(info)
            oper = check.callable(self.oper)
            n = len(Signature.from_callable(oper).parameters)
            if n == 1:
                def fapply(operand): return oper(operand)
            elif n == 2:
                def fapply(lhs, rhs): return oper(lhs, rhs)
            else:
                def fapply(*args): return oper(*args)
            return self.wrap(fapply)

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
            oper, freturn, finit = map(check.callable,
                (self.oper, self.freturn, self.finit),
            )
            @self.wrap.update(info)
            def freduce(self, *operands):
                return freturn(self, functools.reduce(oper, operands, finit(self)))
            return freduce

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
            oper = check.callable(self.oper)
            @self.wrap.update(info)
            def f(self, *args):
                for arg in args: oper(self, arg)
            return f

class wraps(dict[str, str]):

    __slots__ = 'only', 'original',

    def __init__(self, fin: Callable|Mapping, only = WRASS_SET, exclude = (), **kw):
        'Initialize argument, initial input function that will be decorated.'
        self.original = fin
        only = set(map(dund, only))
        only.difference_update(map(dund, exclude))
        only.intersection_update(WRASS_SET)
        self.only = only
        if kw:
            kw = {dund(k): kw[k] for k in kw}
            kw = dict(self.read(kw))
        super().update(self.read(fin), **kw)
        if (k := '__module__') in only and k not in self:
            if (v := getattr(fin, '__objclass__', None)):
                self.setdefault(k, v)
            else:
                self.setdefault(k, _prevmodule())

    def __call__(self, fout: F) -> F:
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

    def write(self, obj: F) -> F:
        "Write wrapped attributes to a wrapper."
        for attr, val in self.items():
            setattr(obj, attr, val)
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

    def __call__(self):
        Error = self.Error
        def f(self, *args, **_):
            raise Error(*args[0:1])
        f.__doc__ = f'Raises {Error.__name__}'
        return f

    def sethook(self, owner, name):
        wrap = wraps(getattr(owner.__bases__[0], name, None),
            name = name,
            module = owner.__module__,
            qualname = f'{owner.__qualname__}.{name}',
        )
        setattr(owner, name, wrap(self()))


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

    __slots__ = (
        '_cache',
        '_isroot',
        'defaults',
        'enabled',
    )
    defaults: Mapping

    _isroot: bool
    "Skip the first `__set_name__` hook."

    _cache: dict

    def __init__(self, /, *, enabled: bool = True, root: bool = False, **defaults):
        self.enabled = bool(enabled)
        self._isroot = bool(root)
        self.defaults = self._defaults | defaults
        self._cache = defaultdict(dict)

    def __call__(self, basecls: type, **opts):
        return self._make(
            basecls.__setattr__,
            *map((self.defaults | opts).get, ('efmt', 'attr', 'cls'))
        )

    def _make(self, sa: F, efmt: Callable[[str, Any], str], attr: str|None, cls: bool|type|None, /) -> F:
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
