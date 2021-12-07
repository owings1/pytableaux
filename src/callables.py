from __future__ import annotations

from utils import Annotate, AttrNote, Decorators, IndexType, \
    instcheck, orepr, subclscheck

from abc import ABCMeta
from collections.abc import Callable, Iterable, Iterator, Sequence
import enum
from functools import partial, partialmethod
import itertools
import operator as opr
from types import MappingProxyType
from typing import Annotated, Any, ClassVar, Union, \
    final

abstract = Decorators.abstract

class Flag(enum.Flag):

    Blank  = 0
    Init   = 1
    Lock   = 2

    Bound  = 4
    Sliced = 8

    Safe   = 16
    Left   = 32
    Star   = 64
    Flip   = 128
    User   = Safe | Star | Left | Flip

GetterSpec = Union[Callable, tuple[type, ...]]
ErrorsType = tuple[type[Exception], ...]
AttrHintSpec = Annotated[
    dict, {ClassVar, Annotate.SubclsMerge},
    opr.or_, MappingProxyType
]

class Callee(Callable, metaclass = ABCMeta):

    SAFE   = Flag.Safe
    LEFT   = Flag.Left
    STAR   = Flag.Star
    FLIP   = Flag.Flip

    cls_flag     : ClassVar[Flag] = Flag.Blank
    safe_errs    : ClassVar[ErrorsType]
    safe_default : ClassVar = None

    attrhints: AttrHintSpec = {
        'flag'    : Flag.Blank,
        'bindargs': Flag.Bound,
        'aslice'  : Flag.Sliced,
        'excepts' : Flag.Safe,
        'default' : Flag.Safe,
    }

    flag     : Flag
    bindargs : tuple
    aslice   : slice
    excepts  : ErrorsType
    default  : Any

    @abstract
    def _get(self, *args): ...

    __slots__ = ('flag', *attrhints.keys())

    def __new__(cls: type[Callee], *args, **kw):
        inst = object.__new__(cls)
        inst.flag = Callee.cls_flag | cls.cls_flag
        return inst

    def __init__(self, *bindargs, aslice: slice = None, default: Any = None,
        flag: Flag = None, excepts: ErrorsType = None):
        f = self.flag
        if flag is not None:
            f |= flag & f.User
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

    def getargs(self, args: tuple) -> tuple:
        f = self.flag
        if f.Star in f: args, = args
        if f.Sliced in f: args = args[self.aslice]
        if f.Bound in f:
            if f.Left in f: args = (*self.bindargs, *args)
            else: args = (*args, *self.bindargs)
        if f.Flip in f:
            return reversed(args)
        return args

    def attrnames(self) -> Iterator[str]:
        f = self.flag
        hints = self.attrhints
        return (a for a in hints if hints[a] in f)

    def attritems(self) -> Iterator[tuple[str, Any]]:
        return ((a, getattr(self, a)) for a in self.attrnames())

    def attrs(self) -> dict[str, Any]:
        return dict(self.attritems())

    def __eq__(self, other):
        if not isinstance(other, self.__class__): return NotImplemented
        try:
            itemszip = zip(self.attritems(), other.attritems(), strict = True)
            return all(opr.eq(*items) for items in itemszip)
        except ValueError:
            return False

    def copy(self) -> Callee:
        cls = self.__class__
        inst = cls.__new__(cls)
        f = self.flag
        for attr, hint in self.attrhints.items():
            if hint & f is hint:
                setattr(inst, attr, getattr(self, attr))
        inst.flag = f
        return inst

    def __setattr__(self, attr, val):
        try: f = self.flag
        except AttributeError: pass
        else:
            if f.Lock in f:
                raise AttributeError(attr, f.Lock)
        super().__setattr__(attr, val)

    def __getattr__(self, attr):
        try: f = self.flag
        except: raise AttributeError(attr)
        if f.Init not in f:
            cls = self.__class__
            if attr == 'safe_errs':
                raise TypeError("'excepts' required for %s with %s" % (cls, f.Safe))
        raise AttributeError(attr)

    def __dir__(self):
        return list(self.attrnames())

    def __repr__(self):
        return orepr(self, self.attrs)

    def __copy__(self):
        return self.copy()

    def __init_subclass__(subcls: type[Callee]):
        cls = __class__
        metas = {ClassVar, Annotate.SubclsMerge}
        note: AttrNote
        for attr, note in AttrNote.forclass(cls, metas):
            merger: Callable = note.args[-2]
            setattr(subcls, attr, note.endtype(
                merger(getattr(cls, attr), getattr(subcls, attr))
            ))

class Attr(Callee):
    """Attribute getter."""
    def _get(self, obj, name): return getattr(obj, name)
    safe_errs = (AttributeError,)

class Key(Callee):
    """Subscript getter."""
    def _get(self, obj, key): return obj[key]
    safe_errs = (KeyError,)

class It(Callee):
    """Passthrough getter."""
    def _get(self, obj, _ = None): return obj
    cls_flag = Flag.Left

class Func(Callee):
    """Function wrapper."""
    func: Callable
    def _get(self, *args): return self.func(*args)

    __slots__ = ('func')
    attrhints = {'func': Flag.Blank}

    def __init__(self, func: Callable, *bindargs, **kw):
        self.func = instcheck(func, Callable)
        super().__init__(*bindargs, **kw)

class Method(Func):
    """Method caller."""
    safe_errs = (AttributeError,)
    def __init__(self, name: str, *bindargs, **kw):
        self.func = opr.methodcaller(instcheck(name, str))
        Callee.__init__(self, *bindargs, **kw)

class iters(Sequence[Callable], metaclass = ABCMeta):
    __slots__ = ('funcs',)

    def __init__(self, *items: GetterSpec):
        self.funcs = list()
        self.extend(items)

    def __call__(self, obj, *args):
        for func in self.funcs[0:-1]:
            obj = func(obj)
        return self.funcs[-1](obj, *args)

    def __len__(self):
        return len(self.funcs)

    def __iter__(self) -> Iterator[Callable]:
        return iter(self.funcs)

    def __contains__(self, item: Callable):
        return item in self.funcs

    def __getitem__(self, index: IndexType) -> Callable:
        return self.funcs[index]


    def iter1(self, func: Callable, *args, **kw):
        return func(f(*args, **kw) for f in self)

    def all(self, *args, **kw):
        return self.iter1(all, *args, **kw)
        # return all(f(*args, **kw) for f in self)


    def iter2(self, *args, **kw) -> Iterator:
        return (f(*args, **kw) for f in self.funcs)

    def append(self, item: GetterSpec):
        self.funcs.append(self._genitem_(item))

    def extend(self, items: Iterable[GetterSpec]):
        self.funcs.extend((self._genitem_(it) for it in items))

    @classmethod
    def _genitem_(cls, item: GetterSpec) -> Callable:
        if callable(item): return item
        gcls, *args = item
        return subclscheck(gcls, Callee)(*args)


class fpreds:

    class instanceof(dict[type, Callee]):

        __slots__ = ()

        class cls(Callee):
            safe_errs = (TypeError,)
            cls_flag = Flag.Left
            def _get(self, classinfo, obj):
                return isinstance(obj, classinfo)

        __call__ = cls
        del(cls)

        def __getitem__(self, key) -> Callee:
            try: return super().__getitem__(key)
            except KeyError:
                return self.setdefault(key, self(key))

    instanceof = instanceof()

    isidentifier = iters(instanceof[str], Method('isidentifier'),).all

filters = fpreds
