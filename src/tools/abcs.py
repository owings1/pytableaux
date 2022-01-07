# Keep this module sparse on dependencies.
from __future__ import annotations
import errors as err

import functools
import operator as opr
import typing

T = typing.TypeVar('T')

__all__ = 'ABCMeta', 'Abc', 'Copyable', 'MetaFlag',

class std:
    'Various standard/common imports'
    from abc import ABCMeta, abstractmethod as abstract
    from collections.abc import Callable, Sequence
    import enum

class MetaFlag(std.enum.Flag):
    'Enum flag for ABCMeta functionality.'
    blank  = 0
    nsinit = 4
    temp   = 8
    after  = 16
    nsclean = nsinit | temp

class ABCMeta(std.ABCMeta):
    'General purpose metaclass and utility methods.'

    #: The method attribute name for marking class init tasks.
    _metaflag_attr = '_metaflag'

    def __new__(cls, clsname, bases, ns: dict, **kw):
        cls.nsinit(ns, bases, **kw)
        Class = super().__new__(cls, clsname, bases, ns, **kw)
        cls.nsclean(Class, ns, bases, **kw)
        return Class

    @staticmethod
    def nsinit(ns: dict, bases, /, **kw):
        mfattr = __class__._metaflag_attr
        for v in tuple(ns.values()):
            if MetaFlag.nsinit in getattr(v, mfattr, MetaFlag.blank):
                err.instcheck(v, std.Callable)(ns, bases, **kw)

    @staticmethod
    def nsclean(Class, ns: dict, bases, deleter = delattr, **kw):
        attrname = __class__._metaflag_attr
        for k, v in tuple(ns.items()):
            mf = getattr(v, attrname, MetaFlag.blank)
            if mf is not mf.blank:
                if MetaFlag.after in mf:
                    err.instcheck(v, std.Callable)(Class)
                    deleter(Class, k)
                elif mf in MetaFlag.nsclean:
                    deleter(Class, k)

    @staticmethod
    def annotated_attrs(obj) -> dict:
        annot = typing.get_type_hints(obj, include_extras = True)
        return {
            k: typing.get_args(v)
            for k,v in annot.items()
            if typing.get_origin(v) is typing.Annotated
        }

    @staticmethod
    def merge_mroattr(
        subcls: type,
        attr: str,
        supcls: type = None,
        oper: std.Callable = opr.or_
    ) -> dict:
        return functools.reduce(oper, (
            getattr(c, attr)
            for c in reversed(subcls.mro())
            if issubclass(c, supcls or subcls)
        ))

    @staticmethod
    def check_mrodict(mro: std.Sequence[type], names: std.Sequence[str]):
        if len(names) and not len(mro):
            return NotImplemented
        for name in names:
            for base in mro:
                if name in base.__dict__:
                    if base.__dict__[name] is None:
                        return NotImplemented
                    break
        return True

    # @staticmethod
    # def basesmap(bases):
    #     from typing import DefaultDict
    #     bmap = DefaultDict(list)
    #     for b in bases: bmap[b.__name__].append(b)
    #     return bmap

class Abc(metaclass = ABCMeta):
    'Convenience for using ABCMeta as metaclass.'
    __slots__ = ()

class Copyable(Abc):

    __slots__ = ()

    @std.abstract
    def copy(self: T) -> T:
        raise NotImplementedError

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self, memo):
        inst = self.copy()
        memo[id(self)] = inst
        return inst

    __subcls_methods = '__copy__', 'copy', '__deepcopy__'

    @classmethod
    def __subclasshook__(cls, subcls: type):
        if cls is not __class__:
            return NotImplemented
        return cls.check_mrodict(subcls.mro(), cls.__subcls_methods)