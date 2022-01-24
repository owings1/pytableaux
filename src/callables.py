from __future__ import annotations

__all__ = (
    'Caller', 'calls', 'gets', 'sets', 'dels', 'raiser',
    'cchain', 'preds',
)

from decorators import abstract, final, overload, static
from errors import instcheck, subclscheck
from tools.abcs import Abc, AbcMeta, P, T, F
from utils import orepr

from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from functools import partial
import operator as opr
from typing import (
    Any, Callable, Iterable, Iterator, Literal, Mapping, Sequence,
    ParamSpec, TypeVar
)

# P = ParamSpec('P')
K = TypeVar('K')
V = TypeVar('V')
R = TypeVar('R')
# T = TypeVar('T')

import enum

@enum.unique
class Flag(enum.Flag):

    Blank  = 0
    Init   = 1
    Lock   = 2

    Bound  = 4
    Sliced = 8
    Order  = 16

    Safe   = 32
    Left   = 64
    Star   = 128
    Usr1   = 256
    User   = Safe | Star | Left | Usr1

    Copy   = 512

del(enum)

ExceptsParam = tuple[type[Exception], ...]
FlagParam = Flag | Callable[[Flag], Flag]

SETATTROK = frozenset({
    '__module__', '__name__', '__qualname__',
    '__doc__', '__annotations__',
})

class _objwrap(Callable):
    'Object wrapper to allow __dict__ attributes'

    __slots__ = 'caller', '__dict__'

    def __init__(self, caller: Callable):
        self.caller = caller

    def __call__(self, *a, **kw):
        return self.caller(*a, **kw)

class Caller(Callable[P, T], Abc):

    SAFE: Literal[Flag.Safe] = Flag.Safe
    LEFT: Literal[Flag.Left] = Flag.Left
    STAR: Literal[Flag.Star] = Flag.Star

    cls_flag     = Flag.Blank
    safe_errs    : ExceptsParam
    safe_default : Any = None

    attrhints: Mapping[str, Flag] = dict(
        flag     = Flag.Blank,
        bindargs = Flag.Bound,
        aslice   = Flag.Sliced,
        aorder   = Flag.Order,
        excepts  = Flag.Safe,
        default  = Flag.Safe,
    )
    __slots__ = tuple(attrhints)

    flag     : Flag
    bindargs : tuple
    aslice   : slice
    excepts  : ExceptsParam
    default  : Any

    @abstract
    def _call(self, *args) -> T:
        raise NotImplementedError

    def __new__(cls, *args, **kw):
        inst = object.__new__(cls)
        inst.flag = Flag.Blank | cls.cls_flag
        return inst

    def __init__(self, *bindargs,
        flag: FlagParam = None,
        aslice: slice = None,
        aorder: tuple[int, ...] = None,
        excepts: ExceptsParam = None,
        default: Any = None,
    ):
        f = self.flag
        if flag is not None:
            if callable(flag): flag = flag(f)
            # Only permit changes to user portion
            f = (f & ~f.User) | (flag & f.User)
        if aslice:
            f |= f.Sliced
            self.aslice = instcheck(aslice, slice)
        if f.Safe in f or excepts is not None:
            f |= f.Safe
            self.excepts = excepts or self.safe_errs
            if default is not None: self.default = default
            else: self.default = self.safe_default
        if aorder:
            f |= f.Order
            self.aorder = aorder
        if bindargs:
            f |= f.Bound
            self.bindargs = bindargs
        self.flag = f | f.Init | f.Lock

    @final
    def __call__(self, *args: Any, **kw) -> T:
        try: return self._call(*self.getargs(args), **kw)
        except Exception as err:
            if Flag.Safe in self.flag and isinstance(err, self.excepts):
                return self.default
            raise

    def getargs(self, args: Sequence) -> Sequence:
        f = self.flag
        if f.Star in f: args, = args
        if f.Sliced in f: args = args[self.aslice]
        if f.Bound in f:
            if f.Left in f: args = self.bindargs + args
            else: args = args + self.bindargs
        if f.Order in f: args = [args[n] for n in self.aorder]
        return args

    def attrnames(self):
        f = self.flag
        hints = self.attrhints
        return tuple(a for a in hints if hints[a] in f)

    def attritems(self):
        return tuple((a, getattr(self, a)) for a in self.attrnames())

    def attrs(self):
        return dict(self.attritems())

    def copy(self):
        cls = self.__class__
        inst = object.__new__(cls)
        for item in self.attrs().items():
            object.__setattr__(inst, *item)
        return inst

    def __setattr__(self, attr, val):
        try: f = self.flag
        except AttributeError: pass
        else:
            if f.Lock in f and attr not in SETATTROK:
                raise AttributeError(attr, f.Lock)
        object.__setattr__(self, attr, val)

    def __delattr__(self, attr):
        raise AttributeError(attr)

    def __getattr__(self, attr):
        try: f = self.flag
        except: raise AttributeError(attr)
        if f.Init not in f:
            cls = type(self)
            if attr == 'safe_errs':
                raise TypeError("'excepts' required for %s with %s" % (cls, f.Safe))
        raise AttributeError(attr)

    def __eq__(self, other):
        if self is other: return True
        if not isinstance(other, type(self)):
            return NotImplemented
        try:
            return self.attritems() == other.attritems()
            # return all(
            #     opr.eq(*items) for items in
            #     zip(self.attritems(), other.attritems(), strict = True)
            # )
        except ValueError:
            return False

    def __hash__(self):
        return hash(type(self)) + hash(self.attritems())

    def __dir__(self):
        return list(self.attrnames())

    def __repr__(self):
        return orepr(self, self.attrs)

    def __copy__(self):
        return self.copy()

    def __init_subclass__(subcls: type[Caller], **kw):
        super().__init_subclass__(**kw)
        from types import MappingProxyType
        subcls.attrhints = MappingProxyType(__class__.attrhints | subcls.attrhints)

    def asobj(self):
        return _objwrap(self)

@static
class calls:

    class func(Caller):
        'Function wrapper.'

        def _call(self, *args, **kw):
            return self.func(*args, **kw)

        def __init__(self, func: Callable, *args, **opts):
            self.func = instcheck(func, Callable)
            super().__init__(*args, **opts)

        func: Callable
        attrhints = dict(func = Flag.Blank)
        __slots__ = tuple(attrhints)

    class method(Caller):
        'Method caller.'

        def _call(self, obj, *args, **kw):
            return getattr(obj, self.method)(*args, **kw)

        def __init__(self, method: str, *args, **opts):
            if not method.isidentifier():
                raise TypeError(method)
            self.method = method
            super().__init__(*args, **opts)

        method: str
        safe_errs = AttributeError,
        attrhints = dict(method = Flag.Blank)
        __slots__ = tuple(attrhints)

    def now(func: Callable[P, T], *args: P.args, **kw: P.kwargs) -> T:
        return func(*args, **kw)

@static
class gets:

    class attr(Caller):
        'Attribute getter.'
        def _call(self, obj, name: str):
            return getattr(obj, name)
        safe_errs = AttributeError,

    class key(Caller):
        'Subscript getter.'
        def _call(self, obj, key): return obj[key]
        safe_errs = KeyError, IndexError,

    class mixed(Caller):
        'Attribute or subscript.'

        def _call(self, obj, keyattr):
            if Flag.Usr1 in self.flag:
                return self.__attrfirst(obj, keyattr)
            try: return obj[keyattr]
            except TypeError: return getattr(obj, keyattr)

        def __attrfirst(self, obj, keyattr):
            try: return getattr(obj, keyattr)
            except AttributeError as e:
                try: return obj[keyattr]
                except TypeError: raise e from None
    
        def __init__(self, *args, attrfirst = False, **kw):
            if attrfirst: self.flag |= Flag.Usr1
            super().__init__(*args, **kw)

        safe_errs = AttributeError, KeyError, IndexError

    class thru(Caller[..., T]):
        'Passthrough getter.'
        def _call(self, obj: Any, *_) -> T:
            return obj
        cls_flag = Flag.Left

@static
class sets:

    class attr(Caller):
        'Attribute setter.'
    
        def _call(self, obj, name: str, val):
            setattr(obj, name, val)

        def __init__(self, attr, value = Flag.Blank, **kw):
            if value is Flag.Blank:
                super().__init__(attr, aorder = (1, 0, 2), **kw)
                return
            super().__init__(attr, value, aorder = (2, 0, 1), **kw)

        safe_errs = AttributeError,
        cls_flag = Flag.Left

@static
class dels:

    class attr(Caller):
        'Attribute deleter.'
        def _call(self, obj, name: str): delattr(obj, name)
        safe_errs = AttributeError,

class raiser(Caller):
    'Error raiser.'

    def _call(self, *args, **kw):
        raise self.ErrorType(*self.eargs, *args[0:1])

    def __init__(self,
        ErrorType: type[Exception],
        eargs: Sequence = (), /):
        self.ErrorType = subclscheck(ErrorType, Exception)
        self.eargs = instcheck(eargs, Sequence)

    ErrorType: type[Exception]
    eargs: Sequence
    attrhints = dict(ErrorType = Flag.Blank, eargs = Flag.Blank)
    __slots__ = tuple(attrhints)

@static
class funciter:
    def reduce(funcs: Iterable[F], *args, **kw) -> Any:
        it = iter(funcs)
        try: value = next(it)(*args, **kw)
        except StopIteration:
            raise TypeError('reduce() of empty iterable') from None
        for f in funcs: value = f(value)
        return value

    def consume(funcs: Iterable[Callable[P, T]], consumer: Callable[[Iterable[P]], T], *args, **kw) -> T:
        return consumer(f(*args, **kw) for f in funcs)

    def filter(funcs: Iterable[Callable[P, T]], consumer: Callable[[Iterable[P]], T], *args, **kw) -> Iterator[T]:
        return filter(consumer(f(*args, **kw) for f in funcs))

@static
class cchain:

    def forall(*funcs: Callable[P, bool]) -> Callable[P, bool]:
        return partial(funciter.consume, funcs, all)

    def forany(*funcs: Callable[P, bool]) -> Callable[P, bool]:
        return partial(funciter.consume, funcs, any)

    def asfilter(*funcs: Callable[[T], bool]) -> Callable[[Iterable[T]], Iterator[T]]:
        return partial(funciter.filter, funcs, all)

    def reducer(*funcs: Callable[P, T]) -> Callable[P, T]:
        return partial(funciter.reduce, funcs)

def predcachetype(pred: Callable[[T, K], bool]) \
    -> type[dict[K, Callable[[T], bool]]]:
    'Returns a dict type that generates and caches predicates.'
    outerfn = calls.func
    setdefault = dict.setdefault
    def missing(self, key):
        return setdefault(self, key, outerfn(pred, key))
    n = pred.__name__
    clsname = n[0].upper() + n[1:] + 'PartialCache'
    return AbcMeta(
        clsname,
        (dict,),
        dict(__missing__ = missing, __slots__ = ()),
    )

@static
class preds:

    instanceof = predcachetype(isinstance)()
    subclassof = predcachetype(issubclass)()

    isidentifier = cchain.forall(instanceof[str], str.isidentifier)
    isnone = partial(opr.is_, None)
    notnone = partial(opr.is_not, None)

    from keyword import iskeyword

    isattrstr = cchain.forall(
        instanceof[str],
        str.isidentifier,
        cchain.reducer(iskeyword, opr.not_),
    )

    def true(_): return True
    def false(_): return False

