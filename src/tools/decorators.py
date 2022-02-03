# Allowed local imports:
#
#  - errors
#  - tools.abcs
#  - tools.misc
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
    F, T, P, Self,
    # utils
    abcm,
    # bases
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
    WRAPPER_ASSIGNMENTS,
)
import operator as opr

from typing import (
    # Annotations
    Any, Callable, Generic, Mapping,
    TypeVar,
)
from types import (
    DynamicClassAttribute,
    FunctionType,
)
EMPTY = ()

@final
class NonError(Exception): __new__ = None

_valfilter = _ftpartial(filter, opr.itemgetter(1))

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


class Member(Generic[T]):

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

### ------------------------------ ###


def rund(func: Callable[[], T]) -> T:
    'Call the function immediately, and return the value.'
    return func()

class membr(Member[T]):

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

    class value(Member):

        __slots__ = 'value', 'doc', 'annot'

        @overload
        def __new__(cls, value: T, /, *args, **kw) -> Callable[..., T]: ...
        def __new__(cls, *args, **kw):
            inst = super().__new__(cls)
            inst._init(*args, **kw)
            return inst

        def _init(self, value, /, doc = None):
            self.value = value
            self.doc = doc
            # TODO: eval'able annotations
            self.annot = {
                'return': 'None' if value is None else type(value).__name__
            }

        def __call__(self, info = None):
            value = self.value
            wrapper = wraps(info)
            wrapper.update(
                __doc__ = self.doc,
                __annotations__ = self.annot,
            )
            def func(*args, **kw):
                return value
            return wrapper(func)

        def sethook(self, owner, name):
            func = self(self)
            # func.__module__ = owner.__module__
            setattr(owner, name, func)

    class prop(value):

        __slots__ = EMPTY

        @overload
        def __new__(cls, value: T) -> _property[Self, T]: ...
        def __new__(cls, *args, **kw):
            return super().__new__(cls, *args, **kw)

        def __call__(self, info = None):
            return property(super().__call__(info), doc = self.doc)

    class dynca(prop):

        __slots__ = EMPTY

        def __call__(self, info = None):
            return DynamicClassAttribute(
                super(fixed.prop, self).__call__(info), doc = self.doc
            )

@static
class operd:

    class Base(Member, Callable):

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

    class apply(Base):
        '''Create a function or method from an operator, or other
        built-in function.'''

        __slots__ = EMPTY

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

    def __new__(cls, *args, **kw):
        return operd.apply(*args, **kw)

    class reduce(Base):
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

    class order(Base):
        '''Wrap an ordering func with oper like: ``oper(func(a, b), 0)``. By
        default, except (AttributeError, TypeError), and return ``NotImplemented``.'''

        __slots__ = 'errs', 'fcmp'

        def __init__(self, oper: Callable, /, *errs, info = None):
            super().__init__(oper, info)
            if errs:
                if errs == (None,): self.errs = NonError,
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
        arguments, and repeatedly calls a one argument method for each
        argument (or, equivalently, a two-argument function with self as the
        first argument).'''

    @overload
    @staticmethod
    def repeat(oper: F) -> F: ...

    class _repeat(Base):

        __slots__ = EMPTY

        def __call__(self, info = None):
            info = self._getinfo(info)
            oper = _checkcallable(self.oper)
            @wraps(info)
            def f(self, *args):
                for arg in args: oper(self, arg)
            return f

    repeat = _repeat
    del(_repeat)

class wraps(Member):

    __slots__ = '_initial', '_adds'

    def __init__(self, fin: Callable | Mapping):
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

    @static
    def read(data):
        return dict(
            _valfilter((k, _getmixed(data, k)) for k in WRAPPER_ASSIGNMENTS)
        )

    def update(self, data = None, /, **kw) -> wraps:
        data = self.read(data) | self.read(kw)
        adds = self._adds
        initial = self._initial
        skip = {'__doc__', '__annotations__'}
        for attr, val in _valfilter((k, data.get(k)) for k in WRAPPER_ASSIGNMENTS):
            if attr in skip:
                if initial.get(attr):
                    continue
            adds[attr] = val
        return self

    def merged(self):
        adds = self._adds
        initial = self._initial
        return dict(
            _valfilter((k, initial.get(k, adds.get(k))) for k in WRAPPER_ASSIGNMENTS)
        )

    def write(self, obj: F) -> F:
        for attr, val in self.merged().items():
            setattr(obj, attr, val)
        # setattr(obj, '__wraps__', self)
        return obj

class raisr(Member):
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

    __slots__ = EMPTY

    def __new__(cls, *args, **kw):
        return cls.get(*args, **kw)

    class get(Twofer[F], Member):

        __slots__ = 'key', 'method'

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

    class attr(get[F]):
        __slots__ = 'name', 'method'

    class prop(get[type[Self]]):
        """Return a property with the getter. NB: a setter/deleter should be
        sure to use the correct attribute."""

        __slots__ = EMPTY

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
            return DynamicClassAttribute(
                lazy.get.__call__(self, method), doc = method.__doc__
            )

class NoSetAttr:
    'Lame thing that does a lame thing.'

    # __slots__ = '__roattr', 'efmt_fixed', 'efmt_change'

    efmt_fixed = '%s (readonly)'.__mod__
    efmt_change = '%s (immutable)'.__mod__
    enabled = True

    def __init__(self, /, attr = '_readonly', enabled = True):
        self.enabled = enabled
        self.__roattr = attr

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
        def f(obj, name, value):
            if self.enabled and check(obj):
                fail(obj, name, value)
            ok(obj, name, value)
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

del(Abc, TypeVar, EMPTY)
# ------------------------------

# Stub adapted from typing module with added annotations.
class _property(property, Generic[Self, T]):
    fget: Callable[[Self], Any] | None
    fset: Callable[[Self, Any], None] | None
    fdel: Callable[[Self], None] | None
    @overload
    def __init__(
        self,
        fget: Callable[[Self], T] | None = ...,
        fset: Callable[[Self, Any], None] | None = ...,
        fdel: Callable[[Self], None] | None = ...,
        doc: str | None = ...,
    ) -> None: ...
    __init__ = NotImplemented
    def getter(self, __fget: Callable[[Self], T]) -> _property[Self, T]: ...
    def setter(self, __fset: Callable[[Self, Any], None]) -> _property[Self, T]: ...
    def deleter(self, __fdel: Callable[[Self], None]) -> _property[Self, T]: ...
    def __get__(self, __obj: Self, __type: type | None = ...) -> T: ...
    def __set__(self, __obj: Self, __value: Any) -> None: ...
    def __delete__(self, __obj: Self) -> None: ...