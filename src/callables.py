from __future__ import annotations

from utils import AttrFlag, AttrNote, Decorators, IndexType, RetType,\
    instcheck, orepr, subclscheck

import abc
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
import enum
from functools import partial #, partialmethod
# import itertools
import operator as opr
from types import MappingProxyType
from typing import Annotated, Any, ClassVar, Concatenate, ParamSpec, TypeVar, Union, \
    cast, final

abstract = Decorators.abstract
P = ParamSpec('P')
T = TypeVar('T')


class Flag(enum.Flag):

    Blank  = 0
    Init   = 1
    Lock   = 2

    Bound  = 4
    Sliced = 8

    Safe   = 16
    Left   = 32
    Star   = 64
    User   = Safe | Star | Left

    Copy   = 128

CallerSpec = Union[Callable, tuple[type, ...]]
ErrorsType = tuple[type[Exception], ...]
FlagParamType = Union[Flag, Callable[[Flag], Flag]]

class ABCMeta(abc.ABCMeta):
    __attrnotes__: Mapping[str, AttrNote]
    def __new__(cls, clsname, bases, attrs, **kw):
        Class = super().__new__(cls, clsname, bases, attrs, **kw)
        Class.__attrnotes__ = MappingProxyType(AttrNote.forclass(Class))
        return Class

class Caller(Callable, metaclass = ABCMeta):

    SAFE = Flag.Safe
    LEFT = Flag.Left
    STAR = Flag.Star

    cls_flag     : ClassVar[Flag] = Flag.Blank
    safe_errs    : ClassVar[ErrorsType]
    safe_default : ClassVar[Any] = None

    attrhints: Annotated[
        dict, AttrFlag.MergeSubClassVar, opr.or_, MappingProxyType
    ] = dict(
        flag     = Flag.Blank,
        bindargs = Flag.Bound,
        aslice   = Flag.Sliced,
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

    def __init__(self, *bindargs, aslice: slice = None, default: Any = None,
        flag: FlagParamType = None, excepts: ErrorsType = None):
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
        if bindargs:
            f |= f.Bound
            self.bindargs = bindargs
        self.flag = f | f.Init | f.Lock

    @final
    def __call__(self, *args):
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
            if f.Left in f: args = (*self.bindargs, *args)
            else: args = (*args, *self.bindargs)
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

    __attrnotes__: Mapping[str, AttrNote]
    def __init_subclass__(subcls: type[Caller]):
        cls: type[Caller] = __class__
        notes = (
            (k,v) for k,v in cls.__attrnotes__.items()
            if AttrFlag.MergeSubClassVar in v.flag
        )
        for attr, note in notes:
            values = getattr(cls, attr), getattr(subcls, attr)
            endvalue = note.endtype(note.merger(*values))
            setattr(subcls, attr, endvalue)

class calls:

    class attr(Caller):
        """Attribute getter."""
        def _get(self, obj, name: str):
            return getattr(obj, name)
        safe_errs = (AttributeError,)

    class key(Caller):
        """Subscript getter."""
        def _get(self, obj, key):
            return obj[key]
        safe_errs = (KeyError,IndexError,)

    class thru(Caller):
        """Passthrough getter."""
        def _get(self, obj, *_):
            return obj
        cls_flag = Flag.Left

    class func(Caller):
        """Function wrapper."""
        def _get(self, *args, **kw):
            return self.func(*args, **kw)
        def __init__(self, func: Callable, *args, **opts):
            self.func = instcheck(func, Callable)
            super().__init__(*args, **opts)
        func: Callable
        attrhints = dict(func = Flag.Blank)
        __slots__ = (*attrhints.keys(),)

    class method(Caller):
        """Method caller."""
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
        __slots__ = (*attrhints.keys(),)

    __new__ = None


class Chain(Sequence[Callable], metaclass = ABCMeta):

    funcs: list[Callable]
    __slots__ = ('funcs',)

    def __init__(self, *items: CallerSpec):
        self.funcs = list()
        if items: self.extend(items)

    # def __call__(self, obj, *args):
    #     for func in self.funcs[0:-1]:
    #         obj = func(obj)
    #     return self.funcs[-1](obj, *args)

    def append(self, item: CallerSpec):
        self.funcs.append(self._genitem_(item))

    def extend(self, items: Iterable[CallerSpec]):
        self.funcs.extend((self._genitem_(it) for it in items))

    @classmethod
    def _genitem_(cls, item: CallerSpec) -> Callable:
        if callable(item): return item
        gcls, *args = item
        return subclscheck(gcls, Caller)(*args)

    # Takes a outer predicate function, such as
    # ``all`` or ``any`` along with args, and calls
    # that func 
    # 
    # def iter1(self, func: Callable, *args, **kw):
    #     return func(f(*args, **kw) for f in self)

    # def all(self, *args, **kw):
    #     if isinstance(self, Chain):
    #         return self.iter1(all, *args, **kw)
    #     return Chain(self, *args, **kw).all
    #     # return all(f(*args, **kw) for f in self)

    # def iter2(self, *args, **kw) -> Iterator:
    #     return (f(*args, **kw) for f in self.funcs)

    def __len__(self):
        return len(self.funcs)

    def __iter__(self) -> Iterator[Callable[P, T]]:
        return iter(self.funcs)

    def __contains__(self, item: Callable):
        return item in self.funcs

    def __getitem__(self, index: IndexType) -> Callable[P, T]:
        return self.funcs[index]

    def bound_iterator(self, *args:P.args, **kw:P.kwargs) -> Iterator[T]:
        return (f(*args, **kw) for f in self)

    def for_call_consumer(self, caller: Callable[[Iterator[P]], T]) -> Callable[P, T]:
        def apply(*args: P.args, **kw: P.kwargs) -> T:
            return caller(self.bound_iterator(*args, **kw))
        return apply


class chain:

    __new__ = None

    def forall(*funcs: Callable[P, bool]) -> Callable[P, bool]:
        return Chain(*funcs).for_call_consumer(all)

    def forany(*funcs: Callable[P, bool]) -> Callable[P, bool]:
        return Chain(*funcs).for_call_consumer(any)

    def asfilter(*funcs: Callable[P, bool]) -> Callable[[Iterable[P]], filter]:
        return partial(filter, chain.forall(*funcs))

class KeyCacheFactory(dict[T, Caller]):

    __fncreate__: Callable[[T], Caller]

    def __getitem__(self, key: T) -> Caller:
        try: return super().__getitem__(key)
        except KeyError:
            return self.setdefault(key, self.__fncreate__(key))

    __call__ = __getitem__
    __slots__ = ('__fncreate__',)

    def __init__(self, fncreate):
        super().__init__()
        self.__fncreate__ = fncreate

class AttrPartialFactory:

    __fncreate__: Callable[Concatenate[str, P], Caller]
    __partialcache__: dict[str, Callable[P, Caller]]

    def __getattribute__(self, name: str) -> Callable[P, Caller]:
        ga = object.__getattribute__
        if name.startswith('__'):
            return ga(self, name)
        cache: dict = ga(self, '__partialcache__')
        try:
            return cache[name]
        except KeyError:
            fncreate = ga(self, '__fncreate__')
            return cache.setdefault(name, partial(fncreate, name))

    __slots__ = ('__fncreate__', '__partialcache__')

    def __init__(self, fncreate):
        self.__fncreate__ = fncreate
        self.__partialcache__ = {}

method = AttrPartialFactory(calls.method)

class preds:
    __new__ = None

    instanceof = KeyCacheFactory[type](partial(calls.func, isinstance))

    isidentifier = chain.forall(instanceof[str],  method.isidentifier())

