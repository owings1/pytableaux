# Keep this module sparse on dependencies.
from __future__ import annotations
from errors import instcheck as _instcheck
import typing

EMPTY = ()
NOARG = object()

__all__ = 'AbcMeta', 'abcm', 'Abc', 'Copyable', 'abcf',

class std:
    'Various standard/common imports'
    import abc
    from collections.abc import Sequence

import functools
import itertools
import operator as opr
from typing import Iterator, SupportsIndex
from collections.abc import Callable#, Iterable
# P = typing.ParamSpec('P')
T = typing.TypeVar('T')
F = typing.TypeVar('F', bound = Callable[..., typing.Any])

import enum

# The method attribute name for storing metaf.
_abc_flag_attr = '_abc_flag'

@enum.unique
class abcf(enum.Flag):
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

class EnumDictType(enum._EnumDict):
    'Stub type for reference.'
    _member_names: list[str]
    _last_values : list[typing.Any]
    _ignore      : list[str]
    _auto_called : bool
    _cls_name    : str
del(enum)

class AbcMeta(std.abc.ABCMeta):
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
    def check_mrodict(mro: std.Sequence[type], *names: std.Sequence[str]):
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
    '''Util functions and decorators. Can also be used by meta classes that
    cannot inherit from AbcMeta, like EnumMeta.'''

    from typing import final, overload
    from abc import abstractmethod as abstract

    # @staticmethod
    # def final(f: T) -> T:
    #     return abcf.final(f)

    @staticmethod
    def isabstract(obj):
        return bool(getattr(obj, '__isabstractmethod__', False))

    @staticmethod
    def annotated_attrs(obj):
        'Evaluate annotions of type Annotated.'
        annot = typing.get_type_hints(obj, include_extras = True)
        return {
            k: typing.get_args(v) for k,v in annot.items()
            if typing.get_origin(v) is typing.Annotated
        }

    @staticmethod
    def merge_mroattr(subcls: type, attr: str, /,
        oper = opr.or_, default = NOARG, **kw
    ):
        it = abcm.mroiter(subcls, **kw)
        if default is NOARG:
            it = (getattr(c, attr) for c in it)
        else:
            it = (getattr(c, attr, default) for c in it)
        return functools.reduce(oper, it)

    @staticmethod
    def mroiter(subcls: type[T], /,
        supcls: type|tuple[type, ...] = None, *,
        rev = True, start: SupportsIndex = 0
    ) -> Iterator[type[T]]:
        it = subcls.mro()
        if rev:
            it = reversed(it)
        if supcls is not None:
            it = filter(lambda c: issubclass(c, supcls), it)
        if start != 0:
            it = itertools.islice(it, start)
        return it

    @staticmethod
    def static(obj: T) -> T:
        if not isinstance(obj, type):
            if isinstance(obj, (classmethod, staticmethod)):
                return obj
            _instcheck(obj, Callable)
            return staticmethod(obj)
        abcf.static(obj)
        d = obj.__dict__
        for name, member in d.items():
            if not callable(member) or isinstance(member, type):
                continue
            setattr(obj, name, staticmethod(member))
        if '__new__' not in d:
            if '__call__' in d:
                call = obj.__call__
                def fnew(cls, *args, **kw): return call(*args, **kw)
            else:
                def fnew(cls): return cls
            obj.__new__ = fnew
        if '__init__' not in d:
            def finit(self): raise TypeError
            obj.__init__ = finit
        return obj


# Alias for convenience import
from typing import overload
@overload
def abstract(func: F) -> F: ...
abstract = abcm.abstract

@overload
def static(obj: T) -> T: ...
static = abcm.static




class Abc(metaclass = AbcMeta):
    'Convenience for using AbcMeta as metaclass.'
    __slots__ = EMPTY

class Copyable(Abc):

    __slots__ = EMPTY

    @abstract
    def copy(self: T) -> T:
        raise NotImplementedError

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self, memo):
        inst = self.copy()
        memo[id(self)] = inst
        return inst

    @classmethod
    def __subclasshook__(cls, subcls: type):
        if cls is not __class__:
            return NotImplemented
        return cls.check_mrodict(subcls.mro(), '__copy__', 'copy', '__deepcopy__')