from __future__ import annotations

from errors import instcheck, subclscheck
from tools.abcs import Abc, AbcMeta, abcm
from utils import orepr

# from abc import abstractmethod
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from functools import partial
import operator as opr
from typing import Any, ClassVar, Literal, ParamSpec, TypeVar

P = ParamSpec('P')
K = TypeVar('K')
V = TypeVar('V')
T = TypeVar('T')

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

class Caller(Callable, Abc):

    SAFE: Literal[Flag.Safe] = Flag.Safe
    LEFT: Literal[Flag.Left] = Flag.Left
    STAR: Literal[Flag.Star] = Flag.Star

    cls_flag     : ClassVar[Flag] = Flag.Blank
    safe_errs    : ClassVar[ExceptsParam]
    safe_default : ClassVar[Any] = None

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

    @abcm.abstract
    def _call(self, *args):
        raise NotImplementedError

    def __new__(cls, *args, **kw) -> Caller:
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

    @abcm.final
    def __call__(self, *args, **kw):
        try: return self._call(*self.getargs(args), **kw)
        except Exception as err:
            if Flag.Safe in self.flag and isinstance(err, self.excepts):
                return self.default
            raise

    def getargs(self, args: tuple) -> Iterable:
        f = self.flag
        if f.Star in f: args, = args
        if f.Sliced in f: args = args[self.aslice]
        if f.Bound in f:
            if f.Left in f: args = self.bindargs + args
            else: args = args + self.bindargs
        if f.Order in f: args = [args[n] for n in self.aorder]
        return args

    def attrnames(self) -> list[str]:
        f = self.flag
        hints = self.attrhints
        return list(a for a in hints if hints[a] in f)

    def attritems(self) -> list[tuple[str, Any]]:
        return list((a, getattr(self, a)) for a in self.attrnames())

    def attrs(self) -> dict[str, Any]:
        return dict(self.attritems())

    def copy(self) -> Caller:
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
            cls = self.__class__
            if attr == 'safe_errs':
                raise TypeError("'excepts' required for %s with %s" % (cls, f.Safe))
        raise AttributeError(attr)

    def __eq__(self, other):
        if self is other: return True
        if not isinstance(other, self.__class__):
            return NotImplemented
        try:
            a, b = self.attritems(), other.attritems()
            itemszip = zip(a, b, strict = True)
            return all(opr.eq(*items) for items in itemszip)
        except ValueError:
            return False

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

ChainItem = Callable | tuple[Caller, tuple]

class Chain(Sequence[Callable], Abc):

    funcs: list[Callable]
    __slots__ = 'funcs',

    def __init__(self, *items: ChainItem):
        self.funcs = list()
        if items: self.extend(items)

    def append(self, item: ChainItem):
        self.funcs.append(self._genitem_(item))

    def extend(self, items: Iterable[ChainItem]):
        self.funcs.extend(map(self._genitem_, items))

    def reverse(self):
        self.funcs.reverse()

    def clear(self):
        self.funcs.clear()

    def bound_iterator(self, *args:P.args, **kw:P.kwargs) -> Iterator[T]:
        return (f(*args, **kw) for f in self)

    def recur_iterator(self, *args, **kw) -> Iterator:
        it = iter(self)
        val = next(it)(*args, **kw)
        yield val
        for func in it:
            val = func(val)
            yield val

    def for_caller(self, caller: Callable[[Iterator[P]], T]) -> Callable[P, T]:
        def consume(*args: P.args, **kw: P.kwargs) -> T:
            return caller(self.bound_iterator(*args, **kw))
        return consume

    def reduce(self, *args, **kw):
        for val in self.recur_iterator(*args, **kw): pass
        return val

    @classmethod
    def _genitem_(cls, item: ChainItem) -> Callable:
        if callable(item): return item
        gcls, *args = item
        return subclscheck(gcls, Caller)(*args)

    def __len__(self):
        return len(self.funcs)

    def __iter__(self) -> Iterator[Callable]:
        yield from self.funcs

    def __contains__(self, item: Callable):
        return item in self.funcs

    def __getitem__(self, index: int|slice) -> Callable:
        return self.funcs[index]

class calls:

    __new__ = None

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

    def now(func, *args, **kw):
        return calls.func(func)(*args, **kw)

class gets:

    __new__ = None

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

    class thru(Caller):
        'Passthrough getter.'
        def _call(self, obj, *_): return obj
        cls_flag = Flag.Left

class sets:

    __new__ = None

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

class dels:

    __new__ = None

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

class cchain:

    __new__ = None

    def forall(*funcs: Callable[P, bool]) -> Callable[P, bool]:
        return Chain(*funcs).for_caller(all)

    def forany(*funcs: Callable[P, bool]) -> Callable[P, bool]:
        return Chain(*funcs).for_caller(any)

    def asfilter(*funcs: Callable[P, bool]) -> Callable[[Iterable[P]], filter]:
        return partial(filter, cchain.forall(*funcs))

    def reducer(*funcs: Callable[P, T]) -> Callable[P, T]:
        return Chain(*funcs).reduce

def predcachetype(pred: Callable[[T, K], bool]) \
    -> type[dict[K, Callable[[T], bool]]]:
    'Returns a dict type that generates and caches predicates.'
    outerfn = calls.func
    setdefault = dict.setdefault
    def missing(self, key):
        return setdefault(self, key, outerfn(pred, key))
    ns = dict(__missing__ = missing, __slots__ = ())
    n = pred.__name__
    clsname = n[0].upper() + n[1:] + 'PartialCache'
    return AbcMeta(clsname, (dict,), ns)

class preds:

    __new__ = None

    instanceof = predcachetype(isinstance)()
    subclassof = predcachetype(issubclass)()
    isidentifier = cchain.forall(instanceof[str], str.isidentifier)

    from keyword import iskeyword

    isattrstr = cchain.forall(
        instanceof[str],
        str.isidentifier,
        cchain.reducer(iskeyword, opr.not_),
    )

('Chain', 'calls', 'gets', 'sets', 'dels', 'raiser','cchain', 'preds')