from __future__ import annotations

from errors import Emsg, instcheck

from tools.abcs import (
    AbcMeta, AbcEnum, FlagEnum, MapProxy,
    overload, static,
    T, T_co,
)
from tools.callables import preds
from tools.hybrids import qsetf
from tools.sets import EMPTY_SET
from tools.timing import StopWatch

import enum
from itertools import chain
from typing import (
    Generic,
    Mapping,
    NamedTuple,
    TypeVar,
)

class BranchEvent(AbcEnum):
    AFTER_BRANCH_CLOSE = enum.auto()
    AFTER_NODE_ADD     = enum.auto()
    AFTER_NODE_TICK    = enum.auto()

class RuleEvent(AbcEnum):
    BEFORE_APPLY = enum.auto()
    AFTER_APPLY  = enum.auto()

class TabEvent(AbcEnum):
    AFTER_BRANCH_ADD    = enum.auto()
    AFTER_BRANCH_CLOSE  = enum.auto()
    AFTER_NODE_ADD      = enum.auto()
    AFTER_NODE_TICK     = enum.auto()
    AFTER_TRUNK_BUILD   = enum.auto()
    BEFORE_TRUNK_BUILD  = enum.auto()

class TabStatKey(AbcEnum):
    FLAGS       = enum.auto()
    STEP_ADDED  = enum.auto()
    STEP_TICKED = enum.auto()
    STEP_CLOSED = enum.auto()
    INDEX       = enum.auto()
    PARENT      = enum.auto()
    NODES       = enum.auto()

class TabFlag(FlagEnum):
    NONE   = 0
    TICKED = 1
    CLOSED = 2
    PREMATURE   = 4
    FINISHED    = 8
    TIMED_OUT   = 16
    TRUNK_BUILT = 32

class RuleMeta(AbcMeta):

    def __new__(cls, clsname, bases, ns: dict, **kw):
        helpers_attr = 'Helpers'
        helper_attrs = cls._get_helper_attrs(ns, helpers_attr)
        Class = super().__new__(cls, clsname, bases, ns, **kw)
        cls._set_helper_attrs(Class, helper_attrs, helpers_attr)
        return Class

    @staticmethod
    def _get_helper_attrs(ns: dict, clsattr: str):
        taken = dict(ns)
        attrs: dict[type, str] = {}
        raw = ns.get(clsattr, ())
        instcheck(raw, tuple)
        for item in raw:
            if isinstance(item, type):
                item = None, item
            instcheck(item, tuple)
            if len(item) != 2:
                raise Emsg.WrongLength(item, 2)
            name, Helper = item
            instcheck(Helper, type)
            if name is None:
                name = getattr(Helper, '_attr', None)
            else:
                name = instcheck(name, str)
                if name in taken:
                    raise Emsg.ValueConflict(name, taken[name])
                if not preds.isattrstr(name):
                    raise Emsg.BadAttrName(name)
            if Helper in attrs:
                # Helper class already added
                if name is not None:
                    # Check for attr name conflict.
                    if attrs[Helper] is None:
                        # Prefer named attr to unnamed.
                        attrs[Helper] = name
                        taken[name] = Helper
                    elif name != attrs[Helper]:
                        raise Emsg.DuplicateValue(name)
            else:
                attrs[Helper] = name
                if name is not None:
                    taken[name] = Helper
        return attrs

    @staticmethod
    def _set_helper_attrs(Class: type, attrs: dict, clsattr: str):
        filt = filter(bool, chain(
            * (
                c.__dict__.get(clsattr, EMPTY_SET)
                for c in reversed(Class.mro()[1:])
            ),
            (
                (v, k) for k,v in attrs.items()
            )
        ))
        hlist = qsetf((item for item in filt if item[1] != None))
        setattr(Class, clsattr, tuple(hlist))

class NodeStat(dict[TabStatKey, TabFlag|int|None]):

    __slots__ = EMPTY_SET

    _defaults = MapProxy({
        TabStatKey.FLAGS       : TabFlag.NONE,
        TabStatKey.STEP_ADDED  : TabFlag.NONE,
        TabStatKey.STEP_TICKED : None,
    })

    def __init__(self):
        super().__init__(self._defaults)



class TabTimers(NamedTuple):

    build  : StopWatch
    trunk  : StopWatch
    tree   : StopWatch
    models : StopWatch

    @static
    def create(it = (False,) * 4):
        return TabTimers._make(map(StopWatch, it))

class TypeInstMap(Mapping):
    @overload
    def __getitem__(self, key: type[T]) -> T: ...
