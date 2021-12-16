from __future__ import annotations

from callables import calls, cchain, gets, preds, raiser, Caller
from utils import MetaFlag, instcheck, subclscheck

from collections.abc import Callable, Collection, Hashable, Iterable, Mapping, Sequence
import functools
from functools import partial, reduce
# from inspect import getsource
from itertools import chain
import operator as opr
from types import DynamicClassAttribute, FunctionType, MappingProxyType
from typing import Any, ClassVar, Literal, NamedTuple, ParamSpec, TypeVar, abstractmethod

P = ParamSpec('P')
T = TypeVar('T')

_ = None
_LZINSTATTR = '__lazyget__'
_WRAPSINSTATTR = '__wraps__'
_FIXVALCODE = (lambda *args, **kw: _).__code__
_new = object.__new__
# _valisstr = cchain.reducer(gets.key(1), preds.instanceof[str])
# _mapfilter = partial(filter, preds.instanceof[Mapping])
_valfilter = partial(filter, gets.key(1))
_getmixed = gets.mixed(flag=Caller.SAFE)
@functools.lru_cache
def _fixeddata(val): return dict(_ = val), {'return': type(val)}
del(_)

class OwnerName(NamedTuple):
    owner: type
    name: str

class NamedMember:

    def __set_name__(self, owner, name):
        self._owner_name = OwnerName(owner, name)
        self.__name__ = name
        self.__qualname__ = '%s.%s' % (owner.__name__, name)

    def __repr__(self):
        if not hasattr(self, '__qualname__'):
            return object.__repr__(self)
        return '<function %s at %s>' % (self.__qualname__, hex(id(self)))

    __slots__ = '__name__', '__qualname__', '_owner_name'

class fixed:

    __new__ = None

    class value(NamedMember):

        __slots__ = 'value', 'ismethod'

        def __init__(self, value):
            self.value: T = value

        def __call__(self, method: Callable = None) -> Callable[..., T]:
            return wraps(method)(self._getf())

        def __set_name__(self, owner, name):
            super().__set_name__(owner, name)
            setattr(owner, name, self())

        def _getf(self):
            glob, annot = _fixeddata(self.value)
            func = FunctionType(_FIXVALCODE, glob)
            func.__annotations__ = annot
            if hasattr(self, '_owner_name'):
                wraps(None).update(self).update(dict(
                    __module__ = self._owner_name.owner.__module__,
                    __annotations__ = func.__annotations__,
                )).write(func)
            return func

    class prop(value):

        __slots__ = ()

        def __call__(self, method = None) -> property:
            return property(super().__call__(method))

    class dynca(value):
        __slots__ = ()
        def __call__(self, method = None) -> DynamicClassAttribute:
            return DynamicClassAttribute(super().__call__(method))

class wraps:

    def __init__(self, fin: Callable | Mapping):
        'Initialize argument, intial input function that will be decorated.'
        self._adds = {}
        self._initial = self.read(fin)
        # self.update(self._initial)

    def __call__(self, fout: Callable[P, T]) -> Callable[P, T]:
        'Decorate function. Receives the wrapper function and updates its attributes.'
        self.update(self.read(fout))
        self.write(fout)
        return fout

    @classmethod
    def read(cls, obj):
        return dict(
            _valfilter(
                (k, _getmixed(obj, k)) for k in cls.attrs
            )
        )

    def update(self, data: Mapping) -> wraps:
        if not isinstance(data, Mapping):
            data = self.read(data)
        adds = self._adds
        initial = self._initial
        for attr, val in _valfilter((k, data.get(k)) for k in self.attrs):
            ival = initial.get(attr)
            if ival:
                if attr == '__doc__':
                    continue
                if attr == '__annotations__':
                    continue
            adds[attr] = val
        return self

    def merged(self):
        adds = self._adds
        initial = self._initial
        return dict(
            _valfilter(
                (k, initial.get(k, adds.get(k))) for k in self.attrs
            )
        )

    def write(self, obj: T) -> T:
        for attr, val in self.merged().items():
            try:
                setattr(obj, attr, val)
            except AttributeError:
                raise
        try:
            setattr(obj, _WRAPSINSTATTR, self)
        except AttributeError:
            raise
        return obj

    attrs = frozenset({
        '__module__', '__name__', '__qualname__',
        '__doc__', '__annotations__'
    })
    # mapattrs = frozenset({'__annotations__'})

    __slots__ = '_initial', '_adds'

class abstract:

    def __new__(cls, method: Callable[P, T]) -> Callable[P, T]:
        'Decorator'
        @abstractmethod
        @wraps(method)
        def f(*args, **kw):
            raise NotImplementedError('abstractmethod', method)
        return f

    __slots__ = ()

class raises(NamedMember):

    def __init__(self, ErrorType: type[Exception], msg = None):
        if msg is None:
            eargs = ()
        else:
            eargs = (msg,)
        self.raiser = raiser(ErrorType, eargs)

    def __call__(self, *args, **kw):
        self.raiser(*args, **kw)

    def __set_name__(self, owner, name):
        super().__set_name__(owner, name)
        r = self.raiser
        if not len(r.eargs):
            self.raiser = raiser(r.ErrorType, (
                'Method %s not allowed' % name,
            ))
            del r

    __slots__ = 'raiser',

class delegate:

    def __init__(self, target: Callable | str):
        'Initialize argument'
        if not isinstance(target, str):
            target = target.__name__
        if not preds.isidentifier(target):
            raise ValueError(target)
        self.target = calls.method(target).asobj()

    def __call__(self, method: Callable):
        'Decorate function'
        return wraps(method)(self.target)

    __slots__ = 'target', 'wraps'

class meta:

    __new__ = None

    class flag:

        def __init__(self, flag: MetaFlag):
            if not isinstance(flag, MetaFlag):
                self.flag = MetaFlag[flag]
            else:
                self.flag = flag

        def __call__(self, method: Callable):
            if not hasattr(method, '_metaflag'):
                method._metaflag = MetaFlag.blank
            method._metaflag |= MetaFlag(self.flag)
            return method

        __slots__ = 'flag',

    temp = flag(MetaFlag.temp)
    init_attrs = flag(MetaFlag.init_attrs)

    __slots__ = ()

class lazyget:

    __slots__ = '__lazyattr__',

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
        if not preds.isidentifier(testout):
            raise TypeError(testout, 'Invalid identifier')
        class templated(lazyget):
            _formatattr = fnfmt
        return templated

    # Internal decorator
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