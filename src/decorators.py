from __future__ import annotations

from callables import calls, cchain, gets, preds, raiser, Caller
from utils import MetaFlag, instcheck, subclscheck

from collections.abc import Callable, Collection, Hashable, Iterable, Mapping, Sequence
import functools
from functools import partial, reduce
from inspect import signature
from itertools import chain
import operator as opr
from types import DynamicClassAttribute, FunctionType, MappingProxyType
from typing import Any, ClassVar, Generic, Literal, NamedTuple, ParamSpec, TypeVar, abstractmethod

P = ParamSpec('P')
T = TypeVar('T')

_LZINSTATTR = '__lazyget__'
_WRAPSINSTATTR = '__wraps__'
_new = object.__new__
# _valisstr = cchain.reducer(gets.key(1), preds.instanceof[str])
# _mapfilter = partial(filter, preds.instanceof[Mapping])
_valfilter = partial(filter, gets.key(1))
_getmixed = gets.mixed(flag=Caller.SAFE)
_checkcallable = calls.func(instcheck, Callable)
_thru = gets.thru()
class _nonerr(Exception): __new__ = None
# _ = None
# _FIXVALCODE = (lambda *args, **kw: _).__code__
# @functools.lru_cache
# def _fixeddata(val): return dict(_ = val), {'return': type(val)}
# del(_)

def _copyf(f: FunctionType) -> FunctionType:
    func = FunctionType(
        f.__code__, f.__globals__, f.__name__,
        f.__defaults__, f.__closure__,
    )
    return wraps(f)(func)

class OwnerName(NamedTuple):
    owner: type
    name: str

class NamedMember:

    def __set_name__(self, owner, name):
        self._owner_name = OwnerName(owner, name)
        self.__name__ = name
        self.__qualname__ = '%s.%s' % (owner.__name__, name)

    def __repr__(self):
        if not hasattr(self, '__qualname__') or not callable(self):
            return object.__repr__(self)
        return '<callable %s at %s>' % (self.__qualname__, hex(id(self)))

    __slots__ = '__name__', '__qualname__', '_owner_name'

    @property
    def owner(self):
        try: return self._owner_name.owner
        except AttributeError: pass

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

        def __call__(self, method = None) -> DynamicClassAttribute:
            return DynamicClassAttribute(super().__call__(method), doc = self.doc)

class operd:

    __new__ = None

    class _base(NamedMember, Callable):

        def __init__(self, oper: Callable, info: Any = None):
            self.oper = oper
            self.info = info

        __slots__ = 'oper', 'info'

        def __set_name__(self, owner, name):
            super().__set_name__(owner, name)
            if self.info is None: self.info = self
            setattr(owner, name, self())

        def _getinfo(self, info = None):
            if info is None:
                if self.info is None: info = self.oper
                else: info = self.info
            return info

    class reduce(_base):

        def __init__(self,
            oper: Callable,
            info: Any = None,
            freturn: Callable = None,
            finit: Callable = None,
        ):
            super().__init__(oper, info)
            self.freturn = _thru if freturn is None else freturn
            self.finit = _thru if finit is None else finit

        __slots__ = 'freturn', 'finit'

        def __call__(self, info = None):
            info = self._getinfo(info)
            oper, freturn, finit = map(_checkcallable,
                (self.oper, self.freturn, self.finit),
            )
            @wraps(info)
            def freduce(self, *operands: Iterable):
                return freturn(reduce(oper, operands, finit(self)))
            return freduce

        def template(*argdefs, **kwdefs):
            class templated(__class__):
                __slots__ = ()
                def __init__(self, *args, **kw):
                    super().__init__(*(argdefs + args), **(kwdefs | kw))
            return templated

    class apply(_base):

        def __init__(self, oper: Callable | str, info: Any = None):
            oname = oper if isinstance(oper, str) else oper.__name__
            oper = getattr(opr, oname)
            super().__init__(oper, info)

        __slots__ = ()

        def __call__(self, info = None):
            info = self._getinfo(info)
            oper = _checkcallable(self.oper)
            n = len(signature(oper).parameters)
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


        def __init__(self, oper: Callable, info = None, *errs):
            super().__init__(oper, info)
            if errs:
                if errs == (None,): self.errs = (_nonerr,)
                else: self.errs = errs
            else: self.errs = AttributeError, TypeError

        __slots__ =  'errs','fcmp',

        def __call__(self, fcmp: Callable):
            info = self._getinfo(fcmp)
            oper, fcmp = map(_checkcallable, (self.oper, fcmp))
            errs = self.errs
            @wraps(info)
            def f(lhs, rhs):
                try: return oper(fcmp(lhs, rhs), 0)
                except errs: return NotImplemented
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
        @abstractmethod
        @wraps(method)
        def f(*args, **kw):
            raise NotImplementedError('abstractmethod', method)
        return f

    __slots__ = ()

class raisen(NamedMember):

    def __init__(self, ErrorType: type[Exception], msg = None):
        if msg is None: eargs = ()
        else: eargs = (msg,)
        self.raiser = raiser(ErrorType, eargs)

    __slots__ = 'raiser',

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

class metad:

    __new__ = None

    class flag:

        def __init__(self, flag: MetaFlag):
            if isinstance(flag, MetaFlag): self.flag = flag
            else: self.flag = MetaFlag[flag]

        def __call__(self, method: Callable):
            if not hasattr(method, '_metaflag'):
                method._metaflag = MetaFlag.blank
            method._metaflag |= MetaFlag(self.flag)
            return method

        __slots__ = 'flag',

    temp = flag(MetaFlag.temp)
    init_attrs = flag(MetaFlag.init_attrs)

    __slots__ = ()


V = TypeVar('V')

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
    def prop(method: Callable[[Any], V]) -> property:
        """Return a property with the getter. NB: a setter/deleter should be
        sure to use the correct cache attribute."""
        return property(__class__()(method), doc=method.__doc__)

    def format(self, name: str) -> str:
        return '_%s' % name
