# Allowed local imports:
#
#  - errors
#  - tools.misc
from __future__ import annotations

__all__ = 'AbcMeta', 'abcm', 'Abc', 'Copyable', 'abcf',

from errors import (
    instcheck as _instcheck
)

from collections.abc import Set as _Set
from typing import (

    # importable exports
    final, overload,

    # Annotations
    Any,
    Annotated,
    Callable,
    Iterable,
    Mapping,
    Sequence,
    SupportsIndex,

    # Util references
    get_type_hints as _get_type_hints,
    get_args as _get_args,
    get_origin as _get_origin,

    # deletable references
    ParamSpec,
    TypeVar,
)
import \
    functools, \
    itertools, \
    operator as opr

# Bases (deletable)
import \
    abc as _abc, \
    enum as _enum

_EMPTY = ()
_NOARG = object()
_ABCF_ATTR = '_abc_flag'

# Type vars
T = TypeVar('T')
T1 = TypeVar('T1')
T2 = TypeVar('T2')
KT = TypeVar('KT')
VT = TypeVar('VT')
RT = TypeVar('RT')
T_co = TypeVar('T_co', covariant = True)
T_contra = TypeVar('T_contra', contravariant = True)
F = TypeVar('F', bound = Callable[..., Any])
TT = TypeVar('TT', bound = type)
Self = TypeVar('Self')
P = ParamSpec('P')

# Global decorators. Re-exported by decorators module.
@overload
def abstract(func: F) -> F: ...
abstract = _abc.abstractmethod

# from builtins import staticmethod as static

@overload
def static(cls: TT) -> TT: ...
@overload
def static(meth: Callable[..., T]) -> staticmethod[T]: ...
def static(cls):
    'Static class decorator wrapper around staticmethod'
    if not isinstance(cls, type):
        if isinstance(cls, (classmethod, staticmethod)):
            return cls
        _instcheck(cls, Callable)
        return staticmethod(cls)
    abcf.static(cls)
    d = cls.__dict__
    for name, member in d.items():
        if not callable(member) or isinstance(member, type):
            continue
        setattr(cls, name, staticmethod(member))
    if '__new__' not in d:
        if '__call__' in d:
            # If the class directly defines a __call__ method,
            # use it for __new__.
            def fnew(cls, *args, **kw):
                return cls.__call__(*args, **kw)
        else:
            def fnew(cls): return cls
        cls.__new__ = fnew
    if '__init__' not in d:
        def finit(self): raise TypeError
        cls.__init__ = finit
    return cls

@_enum.unique
class abcf(_enum.Flag):
    'Enum flag for AbcMeta functionality.'

    blank  = 0
    before = 2
    temp   = 8
    after  = 16
    static = 32
    # immut  = 64
    # protect = 128
    # locked = 256

    _cleanable = before | temp | after
    # _protectable = immut | protect | locked

    def __call__(self, obj: F) -> F:
        "Add the flag to obj's meta flag. Return obj."
        return self.set(obj, self | self.get(obj))

    @classmethod
    def get(cls, obj, default: abcf|int = blank, /) -> abcf:
        return getattr(obj, _ABCF_ATTR, cls(default))

    @classmethod
    def set(cls, obj: F, value: abcf, /) -> F:
        setattr(obj, _ABCF_ATTR, cls(value))
        return obj

@static
class abcm:
    '''Util functions. Can also be used by meta classes that
    cannot inherit from AbcMeta, like EnumMeta.'''

    def nsinit(ns: dict, bases, /, **kw):
        # iterate over copy since hooks may modify ns.
        for member in tuple(ns.values()):
            mf = abcf.get(member)
            if mf.before in mf:
                member(ns, bases, **kw)
        slots = ns.get('__slots__')
        if slots and isinstance(slots, Iterable) and not isinstance(slots, _Set):
            ns['__slots__'] = frozenset(slots)

    def clsafter(Class: type, ns: Mapping, bases, /, deleter = type.__delattr__):
        abcf.blank(Class)
        for name, member in ns.items():
            mf = abcf.get(member)
            if mf is not mf.blank and mf in mf._cleanable:
                if mf.after in mf:
                    member(Class)
                deleter(Class, name)

    # def prot_delattr_obj(obj, name):
    #     raise AttributeError(name)

    # def prot_setattr_obj(obj, name, value, *, prot_names = None):
    #     if prot_names is not None:
    #         if name not in prot_names or not hasattr(obj, name):
    #             print(type(obj))
    #             return super(type(obj), obj).__setattr__(name, value)
    #     raise AttributeError(name)

    def isabstract(obj):
        if isinstance(obj, type):
            return bool(len(getattr(obj, '__abstractmethods__', _EMPTY)))
        return bool(getattr(obj, '__isabstractmethod__', False))

    def annotated_attrs(obj):
        'Evaluate annotions of type Annotated.'
        annot = _get_type_hints(obj, include_extras = True)
        return {
            k: _get_args(v) for k,v in annot.items()
            if _get_origin(v) is Annotated
        }

    def check_mrodict(mro: Sequence[type], *names: str):
        'Check whether methods are implemented for dynamic subclassing.'
        if len(names) and not len(mro):
            return NotImplemented
        for name in names:
            for base in mro:
                if name in base.__dict__:
                    if base.__dict__[name] is None:
                        return NotImplemented
                    break
        return True

    def merge_mroattr(subcls: type, name: str, /,
        oper = opr.or_, default: T = _NOARG, **kw
    ) -> T:
        it = abcm.mroiter(subcls, **kw)
        if default is _NOARG:
            it = (getattr(c, name) for c in it)
        else:
            it = (getattr(c, name, default) for c in it)
        return functools.reduce(oper, it)

    def mroiter(subcls: type[T], /,
        supcls: type|tuple[type, ...]|None = None, *,
        rev = True, start: SupportsIndex = 0
    ) -> Iterable[type[T]]:
        it = subcls.mro()
        if rev:
            it = reversed(it)
        if supcls is not None:
            it = filter(lambda c: issubclass(c, supcls), it)
        if start != 0:
            it = itertools.islice(it, start)
        return it

class AbcMeta(_abc.ABCMeta):
    'Abc Meta class with before/after hooks.'

    def __new__(cls, clsname, bases, ns: dict, /, **kw):
        abcm.nsinit(ns, bases, **kw)
        Class = super().__new__(cls, clsname, bases, ns, **kw)
        abcm.clsafter(Class, ns, bases, **kw)
        return Class

    # def __delattr__(cls, name):
    #     print('__delattr__', cls.__qualname__, name)
    #     cf = abcf.get(cls)
    #     if cf is not cf.blank and cf in cf._protectable:
    #         raise AttributeError(name)
    #     super().__delattr__(name)

    # def __setattr__(cls, name, value):
    #     print('__setattr__', cls.__qualname__, name)
    #     cf = abcf.get(cls)
    #     if cf is not cf.blank and cf in cf._protectable:
    #         if cf.locked in cf or (cf.immut in cf and hasattr(cls, name)):
    #             raise AttributeError(name)
    #     super().__setattr__(name, value)

class Abc(metaclass = AbcMeta):
    'Convenience for using AbcMeta as metaclass.'
    __slots__ = _EMPTY

class EnumDictType(_enum._EnumDict):
    'Stub type for annotation reference.'
    _member_names: list[str]
    _last_values : list[Any]
    _ignore      : list[str]
    _auto_called : bool
    _cls_name    : str

class Copyable(Abc):

    __slots__ = _EMPTY

    @abstract
    def copy(self: T) -> T:
        raise NotImplementedError

    def __copy__(self):
        return self.copy()

    @classmethod
    def __subclasshook__(cls, subcls: type):
        if cls is not __class__:
            return NotImplemented
        return abcm.check_mrodict(subcls.mro(), '__copy__', 'copy', '__deepcopy__')

del(_abc, _enum, TypeVar, ParamSpec)