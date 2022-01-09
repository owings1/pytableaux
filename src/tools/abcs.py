# Keep this module sparse on dependencies.
from __future__ import annotations
from errors import instcheck as _instcheck
import typing

EMPTY = ()

__all__ = 'AbcMeta', 'abcm', 'Abc', 'Copyable', 'abcf',

class std:
    'Various standard/common imports'
    import abc
    from collections.abc import Sequence
    import functools
    import operator as opr
    from typing import Generic

from collections.abc import Callable#, Iterable
# P = typing.ParamSpec('P')
T = typing.TypeVar('T')
F = typing.TypeVar('F', bound = Callable[..., typing.Any])

import enum

#: The method attribute name for storing metaf.
_metaflag_attr = '_metaflag'

@enum.unique
class abcf(enum.Flag):
    'Enum flag for AbcMeta functionality.'

    blank  = 0
    nsinit = 4
    temp   = 8
    after  = 16
    final  = 32
    nsclean = nsinit | temp

    def __call__(self, obj: F) -> F:
        "Add the flag to the obj's _metaflag attribute. Return obj."
        return self.set(obj, self | self.get(obj, self.blank))
        # f = getattr(obj, _metaflag_attr, self.blank)
        # setattr(obj, _metaflag_attr, f | self)
        # return obj

    @classmethod
    def get(cls, obj, default = None) -> abcf|None:
        return getattr(obj, _metaflag_attr, default)

    @classmethod
    def set(cls, obj: F, value: abcf) -> F:
        setattr(obj, _metaflag_attr, cls(value))
        return obj

del(enum)

class AbcMeta(std.abc.ABCMeta):
    'General purpose metaclass and utility methods.'

    #: The method attribute name for marking class init tasks.
    _metaflag_attr = '_metaflag'

    def __new__(cls, clsname, bases, ns: dict, /, **kw):
        cls.nsinit(ns, bases, **kw)
        Class = super().__new__(cls, clsname, bases, ns, **kw)
        cls.nsclean(Class, ns, bases, **kw)
        return Class

    @staticmethod
    def nsinit(ns: dict, bases, /, **kw):
        'Before class create.'
        # iterate over copy since hooks may modify ns.
        for v in tuple(ns.values()):
            mf = abcf.get(v, abcf.blank)
            if mf.nsinit in mf:
                _instcheck(v, Callable)(ns, bases, **kw)

    @staticmethod
    def nsclean(Class, ns: dict, bases, /, deleter = delattr, **kw):
        'After class create.'
        for k, v in tuple(ns.items()):
            mf = abcf.get(v, abcf.blank)
            if mf is not mf.blank:
                if mf.after in mf:
                    _instcheck(v, Callable)(Class)
                    deleter(Class, k)
                elif mf in mf.nsclean:
                    deleter(Class, k)

    @staticmethod
    def merge_mroattr(subcls: type, attr: str, supcls: type = None, oper = std.opr.or_) -> dict:
        if supcls is None: subcls = subcls
        return std.functools.reduce(oper, (
            getattr(c, attr)
            for c in reversed(subcls.mro())
            if issubclass(c, supcls or subcls)
        ))

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

    from typing import (
        overload,
    )
    from abc import (
        abstractmethod as abstract
    )

    @staticmethod
    def final(f: T) -> T:
        return abcf.final(f)

    def isabstract(obj):
        return bool(getattr(obj, '__isabstractmethod__', False))

    def annotated_attrs(obj):
        'Evaluate annotions of type Annotated.'
        annot = typing.get_type_hints(obj, include_extras = True)
        return {
            k: typing.get_args(v) for k,v in annot.items()
            if typing.get_origin(v) is typing.Annotated
        }

class Abc(metaclass = AbcMeta):
    'Convenience for using AbcMeta as metaclass.'
    __slots__ = EMPTY

class Copyable(Abc):

    __slots__ = EMPTY

    @abcm.abstract
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