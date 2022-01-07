from __future__ import annotations

import callables as cal
import errors as err
from tools import abcs

from collections.abc import Callable, Mapping
import functools
import inspect
import operator as opr
import types
import typing
#, Collection, Hashable, Sequence
#import functools
# from itertools import chain
# ClassVar, Generic, Literal, 

P = typing.ParamSpec('P')
T = typing.TypeVar('T')
V = typing.TypeVar('V')

_WRAPSINSTATTR = '__wraps__'
_valfilter = functools.partial(filter, cal.gets.key(1))
_getmixed = cal.gets.mixed(flag=cal.Caller.SAFE)
_checkcallable = cal.calls.func(err.instcheck, Callable)
_thru = cal.gets.thru()
_thru2 = cal.gets.thru(aslice = slice(1, None))
class _nonerr(Exception): __new__ = None

# _LZINSTATTR = '__lazyget__'
# _new = object.__new__
# _valisstr = cchain.reducer(gets.key(1), cal.preds.instanceof[str])
# _mapfilter = functools.partial(filter, cal.preds.instanceof[Mapping])
# _ = None
# _FIXVALCODE = (lambda *args, **kw: _).__code__
# @functools.lru_cache
# def _fixeddata(val): return dict(_ = val), {'return': type(val)}
# del(_)

def _copyf(f: types.FunctionType) -> types.FunctionType:
    func = types.FunctionType(
        f.__code__, f.__globals__, f.__name__,
        f.__defaults__, f.__closure__,
    )
    return wraps(f)(func)

class OwnerName(typing.NamedTuple):
    owner: type
    name: str

__all__ = (
    'namedf', 'rund', 'fixed', 'operd', 'deleg', 'wraps', 'abstract',
    'overload', 'raisen', 'metad', 'lazyget',
)

class NamedMember(typing.Generic[T]):

    def __set_name__(self, owner: type[T], name: str):
        self._owner_name: OwnerName[type[T], str] = OwnerName(owner, name)
        self.__name__ = name
        self.__qualname__ = '%s.%s' % (owner.__name__, name)

    def __repr__(self):
        if not hasattr(self, '__qualname__') or not callable(self):
            return object.__repr__(self)
        return '<callable %s at %s>' % (self.__qualname__, hex(id(self)))

    __slots__ = '__name__', '__qualname__', '_owner_name'

    @property
    def owner(self) -> type[T]:
        try: return self._owner_name.owner
        except AttributeError: pass

    __class_getitem__ = classmethod(type(list[int]))

class namedf(NamedMember[T]):

    __slots__ = 'cb', 'args', 'kw'

    def __init__(self, cb: Callable, *args, **kw):
        self.cb = cb
        self.args = args
        self.kw = kw

    def __set_name__(self, owner: T, name):
        super().__set_name__(owner, name)
        func = self.cb(self, *self.args, **self.kw)
        setattr(owner, name, func)

    def __call__(self):
        ...
        # return wraps(method)
        # return self.cb(*args, **kw)

class rund:

    __slots__ = ()

    def __new__(cls, func: Callable[P, typing.Any], *args, **kw) -> Callable[P, None]:
        return cal.calls.func(func)(*args, **kw)

class fixed:

    __new__ = None

    class value(NamedMember):

        __slots__ = 'value', 'doc', 'annot'

        def __init__(self, value, doc = None):
            self.value: T = value
            self.doc = doc
            # TODO: globals for annotation type search order
            vtype = type(value)
            tname = 'None' if value is None else vtype.__name__
            self.annot = {'return': tname}

        def __call__(self, method: Callable[..., T] = None) -> Callable[..., T]:
            return wraps(method)(self._getf())

        def __set_name__(self, owner, name):
            super().__set_name__(owner, name)
            func = self()
            owner.__annotations__.setdefault(name, self.annot['return'])
            setattr(owner, name, func)

        def _getf(self):
            value = self.value
            def func(*args, **kw):
                return value
            if self.owner is not None:
                wraps(None).update(self).update(dict(
                    __module__ = self.owner.__module__,
                    __annotations__ = self.annot,
                    __doc__ = self.doc,
                )).write(func)
            return func

    class prop(value):

        __slots__ = ()

        def __call__(self, method: Callable[..., T] = None) -> property | T:
            return property(super().__call__(method), doc = self.doc)

    class dynca(value):

        __slots__ = ()

        def __call__(self, method = None) -> types.DynamicClassAttribute:
            return types.DynamicClassAttribute(super().__call__(method), doc = self.doc)

class operd:

    __new__ = None

    class _base(NamedMember, Callable):

        def __init__(self, oper: Callable, info = None):
            self.oper = oper
            self.info = info

        __slots__ = 'oper', 'info'

        def __set_name__(self, owner, name):
            super().__set_name__(owner, name)
            if self.info is None: self.info = self
            f = self()
            setattr(owner, name, f)

        def _getinfo(self, info = None):
            if info is None:
                if self.info is None: info = self.oper
                else: info = self.info
            return info

    class reduce(_base):

        def __init__(self,
            oper: Callable,
            info: typing.Any = None,
            freturn: Callable = None,
            finit: Callable = None,
        ):
            super().__init__(oper, info)
            self.freturn = _thru2 if freturn is None else freturn
            self.finit = _thru if finit is None else finit

        __slots__ = 'freturn', 'finit'

        def __call__(self, info = None):
            info = self._getinfo(info)
            oper, freturn, finit = map(_checkcallable,
                (self.oper, self.freturn, self.finit),
            )
            @wraps(info)
            def freduce(self, *operands):
                return freturn(self, functools.reduce(oper, operands, finit(self)))
            return freduce

        def template(*argdefs, **kwdefs):
            class templated(__class__):
                __slots__ = ()
                def __init__(self, *args, **kw):
                    super().__init__(*(argdefs + args), **(kwdefs | kw))
            return templated

    class apply(_base):

        def __init__(self, oper: Callable | str, info = None):
            oname = oper if isinstance(oper, str) else oper.__name__
            oper = getattr(opr, oname)
            super().__init__(oper, info)

        __slots__ = ()

        def __call__(self, info = None):
            info = self._getinfo(info)
            oper = _checkcallable(self.oper)
            n = len(inspect.signature(oper).parameters)
            if n == 1:
                def fapply(operand): return oper(operand)
            elif n == 2:
                def fapply(lhs, rhs): return oper(lhs, rhs)
            else:
                def fapply(*args): return oper(*args)
            return wraps(info)(fapply)

    class order(_base):
        '''Wrap an ordering func with oper like: ``oper(func(a, b), 0)``. By
        default, except (AttributeError, TypeError), and return
        ``NotImplemented``.'''

        def __init__(self, oper: Callable,/, *errs, info = None):
            super().__init__(oper, info)
            if errs:
                if errs == (None,): self.errs = (_nonerr,)
                else: self.errs = errs
                for ecls in self.errs:
                    err.instcheck(ecls, type)
                    err.subclscheck(ecls, Exception)
            else: self.errs = AttributeError, TypeError

        __slots__ =  'errs','fcmp',

        def __call__(self, fcmp: Callable):
            info = self._getinfo(fcmp)
            oper, fcmp = map(_checkcallable, (self.oper, fcmp))
            errs = self.errs
            @wraps(oper)
            def f(self, other) -> bool:
                try: return oper(fcmp(self, other), 0)
                except errs: return NotImplemented
            # w = wraps(oper)
            # w.update(info)
            # w._adds.setdefault('__annotations__', {})['return'] = bool
            return f

    class iterself(_base):
        'Self-reduce / pac-man args.'

        __slots__ = ()

        def __call__(self, info = None):
            info = self._getinfo(info)
            oper = _checkcallable(self.oper)
            @wraps(info)
            def fiter(self, *args):
                for arg in args: oper(self, arg)
            return fiter

class deleg:
    __new__ = None

    class copy(NamedMember):

        def __init__(self, target: Callable):
            'Initialize argument'
            self.target = target

        __slots__ = 'target',

        def __call__(self, method: Callable):
            'Decorate function'
            return wraps(method)(_copyf(self.target))

        def __set_name__(self, owner, name):
            super().__set_name__(owner, name)
            setattr(owner, name, self(self))

class wraps(NamedMember):

    def __init__(self, fin: Callable | Mapping):
        'Initialize argument, intial input function that will be decorated.'
        self._adds = {}
        self._initial = self.read(fin)

    def __call__(self, fout: Callable[P, T]) -> Callable[P, T]:
        'Decorate function. Receives the wrapper function and updates its attributes.'
        self.update(self.read(fout))
        self.write(fout)
        return fout

    @classmethod
    def read(cls, obj):
        it = _valfilter((k, _getmixed(obj, k)) for k in cls.attrs)
        return dict(it)

    def update(self, data: Mapping) -> wraps:
        if not isinstance(data, Mapping):
            data = self.read(data)
        adds = self._adds
        initial = self._initial
        for attr, val in _valfilter((k, data.get(k)) for k in self.attrs):
            if attr in ('__doc__', '__annotations__'):
                if initial.get(attr): continue
            adds[attr] = val
        return self

    def merged(self):
        adds = self._adds
        initial = self._initial
        it = _valfilter((k, initial.get(k, adds.get(k))) for k in self.attrs)
        return dict(it)

    def write(self, obj: T) -> T:
        for attr, val in self.merged().items():
            setattr(obj, attr, val)
        setattr(obj, _WRAPSINSTATTR, self)
        return obj

    attrs = frozenset({
        '__module__', '__name__', '__qualname__',
        '__doc__', '__annotations__'
    })

    __slots__ = '_initial', '_adds'

class abstract:

    def __new__(cls, method: Callable[P, T]) -> Callable[P, T]:
        'Decorator'
        @typing.abstractmethod
        @wraps(method)
        def f(*args, **kw):
            raise NotImplementedError('abstractmethod', method)
        return f

    @staticmethod
    def isabstract(method):
        return cal.preds.isabstract_method(method)

    @staticmethod
    def impl(method):
        return typing.abstractmethod(method)

    __slots__ = ()

class overload:

    def __new__(cls, method: Callable[P, T]) -> Callable[P, T]:
        'Decorator'
        ret = typing.overload(method)
        if abstract.isabstract(method):
            ret = typing.abstractmethod(ret)
        return ret

    __slots__ = ()

class final:

    def __new__(cls, method):
        'Decorator'
        return typing.final(method)

    __slots__ = ()

class raisen(NamedMember):

    def __init__(self, ErrorType: type[Exception], msg = None):
        if msg is None: eargs = ()
        else: eargs = (msg,)
        self.raiser = cal.raiser(ErrorType, eargs)

    __slots__ = 'raiser',

    def __call__(self, *args, **kw):
        self.raiser(*args, **kw)

    def __set_name__(self, owner, name):
        super().__set_name__(owner, name)
        r = self.raiser
        if not len(r.eargs):
            self.raiser = cal.raiser(r.ErrorType, (
                "Method '%s' not allowed for %s" % (name, owner),
            ))
            del r

class metad:

    F = Flag = abcs.MetaFlag

    class flag:

        F = Flag = abcs.MetaFlag
        _clsflag = F.blank
        attrname = abcs.ABCMeta._metaflag_attr
        __slots__ = 'value',

        def __new__(cls, target: Callable = None, /, *args, **kw):
            'init, and decorate if target is passed.'
            inst = object.__new__(cls)
            inst.value = cls._clsflag
            if target is None: return inst
            err.instcheck(target, Callable)
            if len(args) or len(kw): raise TypeError()
            inst.__init__()
            return inst(target)

        def __init__(self, on: F = F.blank, off = F.blank):
            "initialize the flag value."
            self.on(on)
            self.off(off)

        def __call__(self, target):
            "decorate the target."
            self.write(target)
            return target

        def on(self, value): self.value |= value

        def off(self, value): self.value &= ~value

        def write(self, target):
            attr = self.attrname
            value = getattr(target, attr, self.F.blank)
            setattr(target, attr, value | self.value)

        def __init_subclass__(subcls, on = F.blank, off = ~F.blank, **kw):
            super().__init_subclass__(**kw)
            subcls._clsflag |= on
            subcls._clsflag &= off

    class temp(flag, on = F.temp):     __slots__ = ()
    class nsinit(flag, on = F.nsinit): __slots__ = ()
    class after(flag, on = F.after): __slots__ = ()

    __slots__ = ()


class lazyget(NamedMember):

    __slots__ = 'name',

    def __init__(self, attr: str = None):
        'Initialize argument.'
        self.name = attr

    def __call__(self, method: Callable[P, T]) -> Callable[P, T]:
        name = self.name
        if name is None:
            name = self.format(method.__name__)
        @wraps(method)
        def fget(self):
            try: return getattr(self, name)
            except AttributeError: pass
            value = method(self)
            setattr(self, name, value)
            return value
        # setattr(fget, _LZINSTATTR, self)
        return fget

    @staticmethod
    def prop(method: Callable[[typing.Any], V], attr: str = None) -> property[V]:
        """Return a property with the getter. NB: a setter/deleter should be
        sure to use the correct cache attribute."""
        return property(__class__(attr)(method), doc=method.__doc__)

    @staticmethod
    def dynca(method: Callable[[typing.Any], V], attr: str = None) -> types.DynamicClassAttribute[V]:
        return types.DynamicClassAttribute(__class__(attr)(method), doc=method.__doc__)

    def format(self, name: str) -> str:
        return '_%s' % name
