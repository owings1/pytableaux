# Allowed local imports:
#
#  - errors
#  - utils
from __future__ import annotations

__all__ = 'AbcMeta', 'abcm', 'Abc', 'Copyable', 'abcf',

from errors import (
    instcheck as _instcheck
)

from typing import (

    # importable exports
    final, overload,

    # Annotations
    Any, Callable, Iterable, Iterator, Sequence, SupportsIndex,

    # Util references
    get_type_hints as _get_type_hints,
    get_args as _get_args,
    get_origin as _get_origin,
    Annotated as _Annotated,

    # deletable references
    ParamSpec, TypeVar,
)
import \
    functools, \
    itertools, \
    operator as opr

# Bases (deletable)
import \
    abc as _abc, \
    enum as _enum

_EMPTY = () # deletable
_NOARG = object()

# Type vars, importable
P = ParamSpec('P')
T = TypeVar('T')
F = TypeVar('F', bound = Callable[..., Any])
TT = TypeVar('TT', bound = type)

# Global decorators. Re-exported by decorators module.
@overload
def abstract(func: F) -> F: ...
abstract = _abc.abstractmethod

@overload
def static(cls: TT) -> TT: ...
@overload
def static(func: F) -> staticmethod[F]: ...
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
            # call = cls.__call__
            def fnew(cls, *args, **kw):
                return cls.__call__(*args, **kw)
        else:
            def fnew(cls): return cls
        cls.__new__ = fnew
    if '__init__' not in d:
        def finit(self): raise TypeError
        cls.__init__ = finit
    return cls


static

# The method attribute name for storing metaf.
_abc_flag_attr = '_abc_flag'

@_enum.unique
class abcf(_enum.Flag):
    'Enum flag for AbcMeta functionality.'

    blank  = 0
    nsinit = 4
    temp   = 8
    after  = 16
    final  = 32
    static = 64
    nsclean = nsinit | temp | after

    def __call__(self, obj: F) -> F:
        "Add the flag to the obj's _metaflag attribute. Return obj."
        return self.set(obj, self | self.get(obj, self.blank))

    @staticmethod
    def get(obj, default: abcf.blank = 'abcf.blank') -> abcf:
        return getattr(obj, _abc_flag_attr, default)

    @classmethod
    def set(cls, obj: F, value: abcf) -> F:
        setattr(obj, _abc_flag_attr, cls(value))
        return obj

abcf.get.__defaults__ = abcf.blank, 

class EnumDictType(_enum._EnumDict):
    'Stub type for annotation reference.'
    _member_names: list[str]
    _last_values : list[Any]
    _ignore      : list[str]
    _auto_called : bool
    _cls_name    : str

class AbcMeta(_abc.ABCMeta):
    'General purpose metaclass and utility methods.'

    def __new__(cls, clsname, bases, ns: dict, /, **kw):
        cls.nsinit(ns, bases, **kw)
        Class = super().__new__(cls, clsname, bases, ns, **kw)
        cls.nsclean(Class, ns, bases, **kw)
        return Class

    @staticmethod
    def nsinit(ns: dict, bases, /, **kw):
        'Before class create.'
        # iterate over copy since hooks may modify ns.
        for member in tuple(ns.values()):
            mf = abcf.get(member)
            if mf.nsinit in mf:
                member(ns, bases, **kw)

    @staticmethod
    def nsclean(Class, ns: dict, bases, /, deleter = delattr, **kw):
        'After class create.'
        for name, member in ns.items():
            mf = abcf.get(member)
            if mf is not mf.blank and mf in mf.nsclean:
                if mf.after in mf:
                    member(Class)
                deleter(Class, name)

    @staticmethod
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

class abcm:
    '''Util functions. Can also be used by meta classes that
    cannot inherit from AbcMeta, like EnumMeta.'''

    # from typing import final, overload
    # from abc import abstractmethod as abstract

    @staticmethod
    def isabstract(obj):
        return bool(getattr(obj, '__isabstractmethod__', False))

    @staticmethod
    def annotated_attrs(obj):
        'Evaluate annotions of type Annotated.'
        annot = _get_type_hints(obj, include_extras = True)
        return {
            k: _get_args(v) for k,v in annot.items()
            if _get_origin(v) is _Annotated
        }

    @staticmethod
    def merge_mroattr(subcls: type, name: str, /,
        oper = opr.or_, default: T = _NOARG, **kw
    ) -> T:
        it = abcm.mroiter(subcls, **kw)
        if default is _NOARG:
            it = (getattr(c, name) for c in it)
        else:
            it = (getattr(c, name, default) for c in it)
        return functools.reduce(oper, it)

    @staticmethod
    def mroiter(subcls: type[T], /,
        supcls: type|tuple[type, ...] = None, *,
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

class Abc(metaclass = AbcMeta):
    'Convenience for using AbcMeta as metaclass.'
    __slots__ = _EMPTY

class Copyable(Abc):

    __slots__ = _EMPTY

    @abstract
    def copy(self: T) -> T:
        raise NotImplementedError

    def __copy__(self):
        return self.copy()

    # def __deepcopy__(self, memo):
    #     inst = self.copy()
    #     memo[id(self)] = inst
    #     return inst

    @classmethod
    def __subclasshook__(cls, subcls: type):
        if cls is not __class__:
            return NotImplemented
        return cls.check_mrodict(subcls.mro(), '__copy__', 'copy', '__deepcopy__')

del(_abc, _enum, _EMPTY, TypeVar, ParamSpec)