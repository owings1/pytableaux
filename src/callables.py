from __future__ import annotations

import containers
from containers import ABCMeta, KeyCacheFactory, AttrCacheFactory
from containers import AttrFlag, AttrNote
# from utils import AttrFlag, AttrNote
from utils import Decorators, IndexType, \
    instcheck, orepr, subclscheck

# import abc
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
import enum
from functools import partial
# import itertools
import operator as opr
from types import MappingProxyType
from typing import Annotated, Any, ClassVar, Generic, ParamSpec, TypeAlias, TypeVar, \
    final

abstract = Decorators.abstract
P = ParamSpec('P')
K = TypeVar('K')
T = TypeVar('T')

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

# CallerSpec = Callable | tuple[type, ...]
# ErrorsType = tuple[type[Exception], ...]
# FlagParamType = Union[Flag, Callable[[Flag], Flag]]

# class ABCMeta(abc.ABCMeta):
#     __attrnotes__: Mapping[str, AttrNote]
#     def __new__(cls, clsname, bases, attrs, **kw):
#         Class = super().__new__(cls, clsname, bases, attrs, **kw)
#         Class.__attrnotes__ = MappingProxyType(AttrNote.forclass(Class))
#         return Class

class Caller(Callable, metaclass = ABCMeta):

    ErrorsType = tuple[type[Exception], ...]
    FlagParamType = Flag | Callable[[Flag], Flag]

    SAFE = Flag.Safe
    LEFT = Flag.Left
    STAR = Flag.Star

    cls_flag     : ClassVar[Flag] = Flag.Blank
    safe_errs    : ClassVar[ErrorsType]
    safe_default : ClassVar[Any] = None

    # Annotated[dict, AttrFlag.MergeSubClassVar, opr.or_, MappingProxyType]
    attrhints: Mapping[str, Flag] = dict(
        flag     = Flag.Blank,
        bindargs = Flag.Bound,
        aslice   = Flag.Sliced,
        aorder   = Flag.Order,
        excepts  = Flag.Safe,
        default  = Flag.Safe,
    )
    __slots__ = (*attrhints.keys(),)

    flag     : Flag
    bindargs : tuple
    aslice   : slice
    excepts  : ErrorsType
    default  : Any

    @abstract
    def _get(self, *args): ...

    def __new__(cls: type[Caller], *args, **kw) -> Caller:
        inst = object.__new__(cls)
        inst.flag = Flag.Blank | cls.cls_flag
        return inst

    def __init__(self, *bindargs,
        flag: FlagParamType = None,
        aslice: slice = None,
        aorder: tuple[int, ...] = None,
        excepts: ErrorsType = None,
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
    def __call__(self, *args):
        # print(args)
        try: return self._get(*self.getargs(args))
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
        if f.Order in f: args = [args[n] for n in list(self.aorder)]
        return args

    def attrnames(self) -> Iterator[str]:
        f = self.flag
        hints = self.attrhints
        return (a for a in hints if hints[a] in f)

    def attritems(self) -> Iterator[tuple[str, Any]]:
        return ((a, getattr(self, a)) for a in self.attrnames())

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
            if f.Lock in f:
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

    @classmethod
    def __class_getitem__(cls, key):
        return super().__class_getitem__(key)

    def __init_subclass__(subcls: type[Caller]):
        cls = __class__
        subcls.attrhints = MappingProxyType(cls.attrhints | subcls.attrhints)

class Chain(Sequence[Callable], metaclass = ABCMeta):

    funcs: list[Callable]
    __slots__ = ('funcs',)

    ItemSpecType = Callable | tuple[type, ...]
    def __init__(self, *items: ItemSpecType):
        self.funcs = list()
        if items: self.extend(items)

    def append(self, item: ItemSpecType):
        self.funcs.append(self._genitem_(item))

    def extend(self, items: Iterable[ItemSpecType]):
        self.funcs.extend((self._genitem_(it) for it in items))

    def reverse(self):
        self.funcs.reverse()

    def bound_iterator(self, *args:P.args, **kw:P.kwargs) -> Iterator[T]:
        return (f(*args, **kw) for f in self)

    def for_caller(self, caller: Callable[[Iterator[P]], T]) -> Callable[P, T]:
        def consume(*args: P.args, **kw: P.kwargs) -> T:
            return caller(self.bound_iterator(*args, **kw))
        return consume

    @classmethod
    def _genitem_(cls, item: ItemSpecType) -> Callable:
        if callable(item): return item
        gcls, *args = item
        return subclscheck(gcls, Caller)(*args)

    def __len__(self):
        return len(self.funcs)

    def __iter__(self) -> Iterator[Callable]:
        return iter(self.funcs)

    def __contains__(self, item: Callable):
        return item in self.funcs

    def __getitem__(self, index: IndexType) -> Callable:
        return self.funcs[index]

# class KeyCacheFactory(dict[K, T]):

#     def __getitem__(self, key: K) -> T:
#         try: return super().__getitem__(key)
#         except KeyError:
#             val = self[key] = self.__fncreate__(key)
#             return val

#     def __call__(self, key: K) -> T:
#         return self[key]

#     __slots__ = ('__fncreate__',)
#     __fncreate__: Callable[[K], T]

#     def __init__(self, fncreate: Callable[[K], T]):
#         super().__init__()
#         self.__fncreate__ = fncreate

# _ga = object.__getattribute__
# class AttrCacheFactory(Generic[T]):

#     def __getattribute__(self, name: str) -> T:
#         if name.startswith('__'): return _ga(self, name)
#         cache: dict = _ga(self, '__cache__')
#         return cache[name]

#     __slots__ = ('__cache__',)
#     __cache__: KeyCacheFactory[str, T]

#     def __init__(self, fncreate: Callable[[str], T]):
#         self.__cache__ = KeyCacheFactory(fncreate)

#     def __dir__(self):
#         return list(self.__cache__.keys())

class calls:
    __new__ = None

    class func(Caller):
        'Function wrapper.'
        def _get(self, *args, **kw):
            return self.func(*args, **kw)
        def __init__(self, func: Callable, *args, **opts):
            self.func = instcheck(func, Callable)
            super().__init__(*args, **opts)
        func: Callable
        attrhints = dict(func = Flag.Blank)
        __slots__ = tuple(attrhints)

    # func(partial, 0, flag=partial(opr.and_, ~ Flag.Left))
    class method(Caller):
        'Method caller.'
        def _get(self, obj, *args, **kw):
            return getattr(obj, self.method)(*args, **kw)
        def __init__(self, method: str, *args, **opts):
            if not method.isidentifier():
                raise TypeError(method)
            self.method = method
            super().__init__(*args, **opts)
        safe_errs = (AttributeError,)
        method: str
        attrhints = dict(method = Flag.Blank)
        __slots__ = tuple(attrhints)

    def now(func, *args, **kw):
        return calls.func(func)(*args, **kw)

class gets:
    __new__ = None
    class attr(Caller):
        'Attribute getter.'
        def _get(self, obj, name: str): return getattr(obj, name)
        safe_errs = (AttributeError,)
    class key(Caller):
        'Subscript getter.'
        def _get(self, obj, key): return obj[key]
        safe_errs = (KeyError,IndexError,)
    class thru(Caller):
        'Passthrough getter.'
        def _get(self, obj, *_): return obj
        cls_flag = Flag.Left

class sets:
    __new__ = None
    class attr(Caller):
        'Attribute setter.'
        def _get(self, obj, name: str, val): setattr(obj, name, val)
        safe_errs = (AttributeError,)

methodproxy: AttrCacheFactory[Callable[[str], calls.method]] = \
    AttrCacheFactory(partial(calls.func, calls.method))

class cchain:
    __new__ = None

    def forall(*funcs: Callable[P, bool]) -> Callable[P, bool]:
        return Chain(*funcs).for_caller(all)

    def forany(*funcs: Callable[P, bool]) -> Callable[P, bool]:
        return Chain(*funcs).for_caller(any)

    def asfilter(*funcs: Callable[P, bool]) -> Callable[[Iterable[P]], filter]:
        return partial(filter, cchain.forall(*funcs))

class preds:
    __new__ = None

    instanceof: KeyCacheFactory[type, calls.func] = \
        KeyCacheFactory(partial(calls.func, isinstance))
    subclassof: KeyCacheFactory[type, calls.func] = \
        KeyCacheFactory(partial(calls.func, issubclass))

    isidentifier = cchain.forall(instanceof[str],  methodproxy.isidentifier())
