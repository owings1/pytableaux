from __future__ import annotations

from callables import calls, cchain, gets, preds
from utils import instcheck, MetaFlag

from collections.abc import Callable
from functools import partial, wraps
import operator as opr
from types import DynamicClassAttribute, FunctionType, MappingProxyType
from typing import Any, ClassVar, ParamSpec, TypeVar, abstractmethod

P = ParamSpec('P')
T = TypeVar('T')

_LZINSTATTR = '__lazyget__'


def renamef(fnew: T, forig = None, /, **kw) -> T:
    fgv = lambda a: kw.get(a) or getattr((forig or fnew), a, getattr(fnew, a, None))
    for attr in ('__qualname__', '__name__', '__doc__'):
        setattr(fnew, attr, fgv(attr))
        # val = kw.get(attr, getattr(forig, attr, getattr(fnew, attr, None)))
        # setattr(fnew, attr, val)
    for attr in ('__annotations__',):
        setattr(fnew, attr, getattr(fnew, attr) | fgv(attr) or {})
        # setattr(fnew, getattr(fnew, attr) | fgv(attr, {})getattr(forig, attr))
    return fnew

def _asdef(c: Callable, forig: Callable = None) -> FunctionType:
    # call = f.__call__
    def f(*args, **kw): return c(*args, **kw)
    if forig: f = renamef(f, forig)
    return f

def _idstrcheck(val, errcls = ValueError):
    if not preds.isidentifier(val):
        raise errcls("invalid identifier '%s'" % val)

_new = object.__new__

class delegate:
    __slots__ = ()

    def __new__(cls, target: Callable | str):
        'argument'
        if callable(target): target = target.__name__
        _idstrcheck(target)
        return calls.func(_new(cls), calls.method(target))

    def __call__(self, method: Callable, target: Callable):
        'decorator'
        instcheck(method, Callable)
        instcheck(target, Callable)
        return _asdef(target)

class meta:

    __slots__ = ()
    __new__ = None

    class flag:

        __slots__ = ()

        def __new__(cls, flag: MetaFlag):
            'argument'
            return calls.func(_new(cls), flag)
    
        def __call__(self, method: Callable, flag: MetaFlag):
            'decorator'
            if not hasattr(method, '_metaflag'):
                method._metaflag = MetaFlag.blank
            method._metaflag |= MetaFlag(flag)
            return method

        # def named(fn: Callable[P, T]) -> Callable[P, T]:
        def named(fn: Callable) -> Callable:
            flag = MetaFlag[fn.__name__]
            @wraps(fn)
            def f(method):
                return meta.flag(flag)(method)
            return f
        # @named
        # def temp(): ...
    @flag.named
    def temp(f):...
    # @flag.named
    # class temp:
    #     ...
        # __new__: Callable[[Callable[P, T]], Callable[P, T]]
class lazyget:

    __slots__ = ('__lazyattr__',)


    def __new__(cls, method: Callable[P, T], attr: str = None) -> Callable[P, T]:
        'decorator. submethods add second parameter.'
        instcheck(method, Callable)
        if attr is None: attr = cls._formatattr(method)
        inst = _new(cls)
        inst.__lazyattr__ = attr
        return inst(method)

    def __call__(self, method: Callable[P, T]) -> Callable[P, T]:
        @wraps(method)
        def fget(obj):
            try: return getattr(obj, self.__lazyattr__)
            except AttributeError: pass
            value = method(obj)
            setattr(obj, self.__lazyattr__, value)
            return value
        setattr(fget, _LZINSTATTR, self)
        return fget
        # return renamef(fget, method)

    def attr(attr: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
        'Set the name of the cache attribute, default is _method.'
        return calls.func(lazyget, attr)

    def prop(arg) -> property:
        """Return a property with the getter. NB: a setter/deleter should be
        sure to use the correct cache attribute."""
        def wrap(attr = None):
            def toprop(method):
                return property(lazyget(method, attr))
            return toprop
        return wrap()(arg) if callable(arg) else wrap(arg)

    def template(fmt: str | Callable[[Callable], str], oper: Callable | None=opr.mod) -> type[lazyget]:
        'Returns a new factory with the given default attribute format'
        fnfmt = testout = None
        if isinstance(fmt, str):
            fnfmt = cchain.reducer(gets.attr('__name__'), partial(oper, fmt))
        elif callable(fmt):
            fnfmt = fmt
        else:
            raise TypeError(type(fmt))
        testout = fnfmt(lazyget.update)
        _idstrcheck(testout, TypeError)
        class templated(lazyget):
            _formatattr = fnfmt
        return templated

    # Decorator
    def _mod(f):
        @wraps(f)
        def mod(flaz):
            inst: lazyget = getattr(flaz, _LZINSTATTR)

            def wrap(method):
                fmod = f(inst, method)
                setattr(fmod, _LZINSTATTR, inst)
                return renamef(fmod, method)
            return wrap
        return mod
        # return renamef(mod, f)

    @_mod
    def update(self, method: Callable) -> Callable:
        """Decorates a setter method for updating the value. The value is update
        with the return value of the method."""
        def fset(obj, value):
            setattr(obj, self.__lazyattr__, method(obj, value))
        return fset

    @_mod
    def clear(self, method: Callable[P, bool]) -> Callable[P, None]:
        """Decorates a deleter method. The attribute is deleted if the method
        returns a truthy value."""
        def fdel(obj):
            if method(obj): delattr(obj, self.__lazyattr__)
        return fdel

    @classmethod
    def _formatattr(cls, method: Callable) -> str:
        return '_%s' % method.__name__

    del(_mod)


# @_argwrap
# def lazyget(name = None) -> Callable[..., Callable[..., T]]:
#     def wrap(method: Callable[..., T]) -> Callable[..., T]:
#         attr = '_%s' % method.__name__ if name is None else name
#         fgetcache = gets.attr(attr)
#         fsetcache = sets.attr(attr)
#         fdelcache = dels.attr(attr)
#         def fgetset(self) -> T:
#             try: return fgetcache(self)
#             except AttributeError: val = method(self)
#             fgetset._set(self, val)
#             return val
#         fgetset._set = fsetcache
#         fgetset._del = fdelcache
#         return renamef(fgetset, method)
#     return wrap

# @_argwrap
# def lazyprop(name = None) -> Callable[[Callable[..., T]], property | T]:
#     def wrap(method: Callable[..., T]) -> property | T:
#         return property(lazyget(name)(method))
#     return wrap

# def lazyprop_update(prop: property) -> property:
#     def wrap(method: Callable):
#         def fset(self, val):
#             val = method(self, val)
#             prop.fget._set(self, val)
#         return prop.setter(renamef(fset, method))
#     return wrap
# lazyprop.update = lazyprop_update

# def lazyprop_clear(prop: property) -> property:
#     def wrap(method: Callable):
#         def fdel(self, val):
#             if method(self): prop.fget._del(self)
#         return prop.deleter(renamef(fdel, method))
#     return wrap
# lazyprop.clear = lazyprop_clear

# del(lazyprop_update, lazyprop_clear)