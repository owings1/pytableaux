# Allowed local imports:
#
#  - errors
#  - utils
#  - tools.abcs

from __future__ import annotations

__all__ = (
    # alias decorators
    'overload', 'abstract', 'final', 'static',
    # functions
    'rund',
    # class-based decorators
    'membr', 'fixed', 'operd', 'wraps',
    'raisr', 'lazy', 'NoSetAttr',
)

from errors import (
    instcheck as _instcheck,
    subclscheck as _subclscheck
)

from tools.abcs import (
    # alias decorators
    abstract,
    final,
    overload,
    static,
    # type vars
    F, TT, T, P,
    # utils
    abcm,
    # bases (deletable)
    Abc,
)
from inspect import (
    signature as _sig,
)
from keyword import (
    iskeyword as _iskeyword
)
from functools import (
    reduce as _ftreduce,
    partial as _ftpartial,
)
import operator as opr

from typing import (
    # Annotations
    Any, Callable, Generic, Mapping,
    # deletable references
    TypeVar,
)
from types import (
    # Annotations
    DynamicClassAttribute, FunctionType,
)
_EMPTY = () # deletable

# T = TypeVar('T')
# P = ParamSpec('P')
# F = TypeVar('F', bound = Callable[..., Any])
# TT = TypeVar('TT', bound = type)

R = TypeVar('R')
O = TypeVar('O')
V = TypeVar('V')
F2 = TypeVar('F2', bound = Callable[..., Any])
F_get = TypeVar('F_get', bound = Callable[[Any], Any])


class _nonerr(Exception): __new__ = None

# def _geti1(obj): return obj[1]
_valfilter = _ftpartial(filter, opr.itemgetter(1))

def _getmixed(obj, k):
    try: return obj[k]
    except TypeError:
        return getattr(obj, k, None)

def _thru(obj, *_):
    return obj

def _thru2(_x, obj, *_):
    return obj

def _attrstrcheck(name: str):
    _instcheck(name, str)
    if _iskeyword(name):
        raise TypeError('%s is a keyword' % name)
    if not name.isidentifier():
        raise TypeError('%s is not an identifier' % name)
    return name

def _methcaller(name: str):
    name = _attrstrcheck(name)
    def f(obj, *args, **kw):
        return getattr(obj, name)(*args, **kw)
    f.__name__ = name
    return f

def _checkcallable(obj):
    return _instcheck(obj, Callable)

def _checkcallable2(obj):
    if isinstance(obj, str):
        return _methcaller(obj)
    return _checkcallable(obj)

def _copyf(f: FunctionType) -> FunctionType:
    func = FunctionType(
        f.__code__, f.__globals__, f.__name__,
        f.__defaults__, f.__closure__,
    )
    return wraps(f)(func)

def rund(func):
    'Call the function immediately, and return the value.'
    return func()

class _member(Generic[T]):

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
        self.__owner = _instcheck(value, type)
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
    _sethooks = _EMPTY

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

    # __class_getitem__ = classmethod(type(list[int]))

class _twofer(Abc, Generic[F]):

    __slots__ = _EMPTY

    @overload
    def __new__(cls, func: F) -> F: ...

    @overload
    def __new__(cls: type[T]) -> T: ...

    def __new__(cls, arg = None, /, *a, **kw):
        '''If only argument to constructor is callable, construct and call the
        instance. Otherwise create normally.'''
        inst = object.__new__(cls)
        if len(a) or len(kw) or not isinstance(arg, Callable):
            inst._init(arg, *a, **kw)
            return inst
        if isinstance(inst._blankinit, Callable): 
            inst._blankinit()
        return inst(arg)

    @abstract
    @overload
    def __call__(self, func: F) -> F: ...

    @abstract
    def _init(self, arg = None, /, *a, **kw): ...

    def _blankinit(self):
        self._init()

class membr(_member[T]):

    __slots__ = 'cbak',

    owner: T

    def __init__(self, cb: Callable, *args, **kw):
        self.cbak = cb, args, kw

    def sethook(self, owner, name):
        setattr(owner, name, wraps(self)(self()))

    def __call__(self):
        cb, args, kw = self.cbak
        return cb(self, *args, **kw)

    @classmethod
    def defer(cls, fdefer: F) -> Callable[..., F]:
        def f(*args, **kw):
            def fd(member, *args, **kw):
                return fdefer(member, *args, **kw)
            return cls(fd, *args, **kw)
        return f

@static
class fixed:

    class value(_member):

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

        def sethook(self, owner, name):
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

        __slots__ = _EMPTY

        def __call__(self, method: Callable[[O], V] = None) -> prop[O, V]:
            return property(super().__call__(method), doc = self.doc)

    class dynca(value):

        __slots__ = _EMPTY

        def __call__(self, method = None) -> DynamicClassAttribute:
            return DynamicClassAttribute(super().__call__(method), doc = self.doc)
@static
class operd:

    class _base(_member, Callable):

        __slots__ = 'oper', 'info'

        def __init__(self, oper: Callable, info = None):
            self.oper = oper
            self.info = info

        def sethook(self, owner, name):
            if self.info is None:
                self.info = self
            setattr(owner, name, self())

        def _getinfo(self, info = None):
            if info is None:
                if self.info is None:
                    info = self.oper
                else:
                    info = self.info
            return info

    class apply(_base):

        __slots__ = _EMPTY

        def __call__(self, info = None):
            info = self._getinfo(info)
            oper = _checkcallable(self.oper)
            n = len(_sig(oper).parameters)
            if n == 1:
                def fapply(operand): return oper(operand)
            elif n == 2:
                def fapply(lhs, rhs): return oper(lhs, rhs)
            else:
                def fapply(*args): return oper(*args)
            return wraps(info)(fapply)

    class reduce(_base):
        '''Create a reducing method using functools.reduce to apply
        a single operator/function to an arbitrarily number of arguments.

        :param oper: The operator, or any two-argument function.

        :param info: The original or stub method being replaced, or an
            object with informational attributes (__name__, __doc__, etc.)
            to be passed through `wraps`.

        :param freturn: A two-argument function that takes `self` and the
            end result, e.g. to create a copy of an object, etc. This could
            be a method-caller, which would invoke the method on the first
            argument (self). Default is to return the second argument (result).

        :param finit: A single-argument function that takes `self` to seed
            the initial value. This could be used, for example, to ensure
            a copy is created in case the number of arguments is 0.
        '''

        __slots__ = 'freturn', 'finit'

        def __init__(self, oper: Callable, /,
            info = None, freturn: Callable = _thru2, finit: Callable = _thru,
        ):
            super().__init__(oper, info)
            self.freturn = _checkcallable2(freturn)
            self.finit = _checkcallable2(finit)

        def __call__(self, info = None):
            info = self._getinfo(info)
            oper, freturn, finit = map(_checkcallable,
                (self.oper, self.freturn, self.finit),
            )
            @wraps(info)
            def freduce(self, *operands):
                return freturn(self, _ftreduce(oper, operands, finit(self)))
            return freduce

        def template(*argdefs, **kwdefs) -> type[operd.reduce]:
            'Make a templated subclass with bound arguments.'
            class templated(__class__):
                _argdefs = argdefs
                _kwdefs = kwdefs
                __slots__ = ()
                def __init__(self, *args, **kw):
                    super().__init__(*(argdefs + args), **(kwdefs | kw))
            return templated

    class order(_base):
        '''Wrap an ordering func with oper like: ``oper(func(a, b), 0)``. By
        default, except (AttributeError, TypeError), and return
        ``NotImplemented``.'''

        __slots__ =  'errs','fcmp',

        def __init__(self, oper: Callable, /, *errs, info = None):
            super().__init__(oper, info)
            if errs:
                if errs == (None,): self.errs = _nonerr,
                else: self.errs = errs
                for ecls in self.errs:
                    _instcheck(ecls, type)
                    _subclscheck(ecls, Exception)
            else:
                self.errs = AttributeError, TypeError

        def __call__(self, fcmp: Callable):
            # info = self._getinfo(fcmp)
            oper, fcmp = map(_checkcallable, (self.oper, fcmp))
            errs = self.errs
            @wraps(oper)
            def f(self, other) -> bool:
                try:
                    return oper(fcmp(self, other), 0)
                except errs:
                    return NotImplemented
            return f

    @overload
    @staticmethod
    def repeat(oper: Callable, info: F) -> F:
        '''Create a method that accepts an arbitrary number of positional
        arguments, and repeatedly calls a one argument method with for each
        argument (or, equivalently, a two-argument function with self as the
        first argument).'''

    @overload
    @staticmethod
    def repeat(oper: F) -> F: ...

    class _repeat(_base):

        __slots__ = _EMPTY

        def __call__(self, info = None):
            info = self._getinfo(info)
            oper = _checkcallable(self.oper)
            @wraps(info)
            def f(self, *args):
                for arg in args: oper(self, arg)
            return f

    repeat = _repeat

class wraps(_member):

    __slots__ = '_initial', '_adds'

    def __init__(self, fin: Callable | Mapping):
        'Initialize argument, intial input function that will be decorated.'
        self._adds = {}
        self._initial = self.read(fin)

    def __call__(self, fout: F) -> F:
        'Decorate function. Receives the wrapper function and updates its attributes.'
        self.update(self.read(fout))
        if isinstance(fout, (classmethod, staticmethod)):
            self.write(fout.__func__)
        else:
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
        return dict(
            _valfilter((k, initial.get(k, adds.get(k))) for k in self.attrs)
        )

    def write(self, obj: F) -> F:
        for attr, val in self.merged().items():
            setattr(obj, attr, val)
        # setattr(obj, '__wraps__', self)
        return obj

    attrs = frozenset((
        '__module__', '__name__', '__qualname__',
        '__doc__', '__annotations__'
    ))

class raisr(_member):
    '''Creates an object that raises the exception when called. When
    __set_name__ is called, creates a new function. Not to be used
    as a decorator.'''

    __slots__ = 'errtype', 'eargs', 'ekw'

    def __init__(self, errtype: type[Exception], *eargs, **ekw):
        self.errtype = _subclscheck(errtype, Exception)
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

    __slots__ = _EMPTY

    def __new__(cls, *args, **kw):
        return cls.get(*args, **kw)

    # class get(_twofer[F], _member):
    class get(_twofer[F], _member):

        __slots__ = 'key', 'method'

        @overload
        def __new__(cls, method: F) -> F: ...
        @overload
        def __new__(cls, key: str|None, method: F) -> F: ...
        @overload
        def __new__(cls, key: str|None) -> lazy.get: ...
        @overload
        def __new__(cls) -> lazy.get: ...
        __new__ = _twofer.__new__

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
                _instcheck(key, str)
            self.key = key
            if method is not None:
                _instcheck(method, Callable)
            self.method = method

        def _blankinit(self):
            self.method = self.key = None

        def sethook(self, owner, name):
            if self.key is None:
                self.key = self.format(name)
            setattr(owner, name, self(self.method))

        def format(self, name: str) -> str:
            return '_%s' % name

    class prop(get[type[O]]):#, Generic[T]):
        """Return a property with the getter. NB: a setter/deleter should be
        sure to use the correct attribute."""

        __slots__ = _EMPTY

        @overload
        def __new__(cls, func: Callable[[O], V]) -> _property[O, V]: ...
        __new__ = _twofer.__new__

        def __call__(self, method: Callable[[O], V]) -> _property[O, V]:
            return property(super().__call__(method), doc = method.__doc__)

    class dynca(prop[O]):
        """Return a DynamicClassAttribute with the getter. NB: a setter/deleter
        should be sure to use the correct attribute."""

        __slots__ = _EMPTY

        # @overload
        # def __new__(cls, func: Callable[[O], V]) -> prop[O, V]: ...
        # __new__ = _twofer.__new__

        def __call__(self, method: Callable[[O], V]) -> _property[O, V]:
            return DynamicClassAttribute(
                lazy.get.__call__(self, method), doc = method.__doc__
            )

class NoSetAttr:
    'Lame thing that does a lame thing.'

    # __slots__ = '__roattr', 'efmt_fixed', 'efmt_change'

    efmt_fixed = '%s (readonly)'.__mod__
    efmt_change = '%s (immutable)'.__mod__

    def __init__(self, roattr = '_readonly',):
        self.__roattr = roattr

    def __call__(self, basecls, cls = None, changeonly = False):
        ok = basecls.__setattr__
        if cls == True:
            check = self.clschecker
        elif cls:
            check = self.fixedchecker(cls)
        else:
            check = self.selfchecker
        if changeonly:
            fail = self.changeraiser
        else:
            fail = self.fixedraiser
        @wraps(ok)
        def f(self, name, value):
            if check(self):
                fail(self, name, value)
            ok(self, name, value)
        return f

    def fixedchecker(self, obj):
        roattr = self.roattr
        def check(self):
            return getattr(obj, roattr, False)
        return check

    def callchecker(self, fget):
        roattr = self.roattr
        def check(obj):
            return getattr(fget(obj), roattr, False)
        return check

    @lazy.prop
    def clschecker(self):
        return self.callchecker(type)

    @lazy.prop
    def selfchecker(self):
        roattr = self.roattr
        def check(obj):
            return getattr(obj, roattr, False)
        return check

    @lazy.prop
    def fixedraiser(self):
        efmt = self.efmt_fixed
        def fail(obj, name, value):
            raise AttributeError(efmt(name))
        return fail

    @lazy.prop
    def changeraiser(self):
        efmt = self.efmt_change
        def fail(obj, name, value):
            raise AttributeError(efmt(name))
        return fail

    @property
    def roattr(self):
        return self.__roattr

del(Abc, TypeVar, _EMPTY)
# ------------------------------

class _property(property, Generic[O, V]):
    fget: Callable[[O], Any] | None
    fset: Callable[[O, Any], None] | None
    fdel: Callable[[O], None] | None
    @overload
    def __init__(
        self,
        fget: Callable[[O], V] | None = ...,
        fset: Callable[[O, Any], None] | None = ...,
        fdel: Callable[[O], None] | None = ...,
        doc: str | None = ...,
    ) -> None: ...
    __init__ = NotImplemented
    def getter(self, __fget: Callable[[O], V]) -> prop[O, V]: ...
    def setter(self, __fset: Callable[[O, Any], None]) -> prop[O, V]: ...
    def deleter(self, __fdel: Callable[[O], None]) -> prop[O, V]: ...
    def __get__(self, __obj: O, __type: type | None = ...) -> V: ...
    def __set__(self, __obj: O, __value: Any) -> None: ...
    def __delete__(self, __obj: O) -> None: ...