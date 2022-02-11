from __future__ import annotations

__all__ = (

)

from errors import (
    Emsg,
    # instcheck,
    subclscheck,
)

from tools.abcs import (
    AbcMeta, AbcEnum, FlagEnum, MapProxy,
    abcm,
    abstract,
    # closure,
    # overload,
    closure,
    static,
    T, T_co,
)
# from tools.callables import preds
from tools.hybrids import qsetf, EMPTY_QSET
from tools.mappings import dmap
from tools.sets import setf, EMPTY_SET
from tools.timing import StopWatch

import enum
# from itertools import chain
# import operator as opr
from typing import (
    Any,
    Callable,
    # Generic,
    Mapping,
    NamedTuple,
    # Protocol,
    # Sequence,
    # TypeVar,
)
# _NOGET = object()

class RuleAttr(str, AbcEnum):
    Helpers     = 'Helpers'
    Timers      = 'Timers'
    NodeFilters = 'NodeFilters'
    DefaultOpts = '_defaults'
    OptKeys     = '_optkeys'
    Name        = 'name'

class HelperAttr(str, AbcEnum):
    InitRuleCls = '__init_ruleclass__'

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

class RuleFlag(FlagEnum):
    NONE   = 0
    INIT   = 1
    LOCKED = 2

class RuleMeta(AbcMeta):

    @classmethod
    def __prepare__(cls, clsname: str, bases: tuple[type, ...], **kw) -> dict[str, Any]:
        return dmap(__slots__ = EMPTY_SET)

    def __new__(cls, clsname: str, bases: tuple[type, ...], ns: dict, /, *,
        helper: Mapping[type[RuleHelperType], Mapping[str, Any]] = {}, **kw
    ):

        RuleBase = _rule_basecls(cls)

        Class = super().__new__(cls, clsname, bases, ns, **kw)

        if RuleBase is None:
            RuleBase = _rule_basecls(cls, Class)

        for name in (RuleAttr.Helpers, RuleAttr.Timers):
            value = abcm.merge_mroattr(Class, name, supcls = RuleBase,
                default = EMPTY_QSET,
                transform = qsetf,
            )
            if name is RuleAttr.Helpers:
                for Helper in value:
                    subclscheck(Helper, RuleHelperType)

        for name in (RuleAttr.NodeFilters,):
            # Load latest first.
            if hasattr(Class, name):
                abcm.merge_mroattr(Class, name, supcls = RuleBase,
                    reverse = False,
                    default = EMPTY_QSET,
                    transform = qsetf,
                )

        for name in (RuleAttr.DefaultOpts,):
            abcm.merge_mroattr(Class, name, supcls = RuleBase,
                default = dmap(),
                transform = MapProxy,
            )
        
        setattr(Class, RuleAttr.OptKeys, setf(getattr(Class, RuleAttr.DefaultOpts)))
        setattr(Class, RuleAttr.Name, clsname)

        emptymap = MapProxy()
        for Helper in getattr(Class, RuleAttr.Helpers):
            finit = getattr(Helper, HelperAttr.InitRuleCls, None)
            if finit is not None:
                finit(Class, **helper.get(Helper, emptymap))

        return Class

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

class RuleHelperType(metaclass = AbcMeta):

    __slots__ = EMPTY_SET

    rule: Any

    @abstract
    def __init__(self, rule: Any, /):
        self.rule = rule

    @classmethod
    @abstract
    def __init_ruleclass__(cls, rulecls: type, /):
        pass

    @classmethod
    def __subclasshook__(cls, subcls: type, /):
        if cls is not __class__:
            return NotImplemented
        return _check_helper_subclass(subcls)

if 'Util Functions' or True:

    def _rule_basecls(metacls: type, default: type = None, /, *, base = {}):
        try:
            return base[metacls]
        except KeyError:
            if default is not None:
                base[metacls] = default
                _rule_basecls.__kwdefaults__ |= dict(base = MapProxy(base))
            return default

    @closure
    def _check_helper_subclass():
        from inspect import Parameter, Signature

        def is_descriptor(obj):
            return (
                hasattr(obj, '__get__') or
                hasattr(obj, '__set__') or
                hasattr(obj, '__delete__')
            )

        posflag = (
            Parameter.POSITIONAL_ONLY |
            Parameter.POSITIONAL_OR_KEYWORD |
            Parameter.VAR_POSITIONAL
        )
        def getparams(value: Callable, /, *,
            fromcb: Callable[[Callable], Signature] = Signature.from_callable
        ):
            return list(fromcb(value).parameters.values())

        def notimplinfo(*args):
            # print(*args)
            return NotImplemented

        names = qsetf((
            'rule',
            # HelperAttr.InitRuleCls,
            '__init__',
        ))

        def check(subcls: type):

            check = abcm.check_mrodict(subcls.mro(), *names)
            if check is NotImplemented or check is False:
                return check

            name = 'rule'
            if name in names:

                value = getattr(subcls, name)
                if not is_descriptor(value):
                    return notimplinfo(subcls, name, value)

            name = HelperAttr.InitRuleCls
            if name in names:

                value = getattr(subcls, name)
                if not callable(value):
                    return notimplinfo(subcls, name, value)
                params = getparams(value)
                if len(params) < 2:
                    return notimplinfo(subcls, name, 'params', params)
                p = params[1]
                if p.kind & posflag != p.kind:
                    return notimplinfo(subcls, name, 'param', p, p.kind)
        
            name = '__init__'
            if name in names:

                value = getattr(subcls, name)
                if not callable(value):
                    return notimplinfo(subcls, name, value)
                params = getparams(value)
                if len(params) < 2:
                    name = '__new__'
                    value = getattr(subcls, name)
                    if not callable(value):
                        return notimplinfo(subcls, name, value)
                    params = getparams(value)
                    if len(params) < 2:
                        return notimplinfo(subcls, name, value)
                p = params[1]
                if p.kind & posflag != p.kind:
                    return notimplinfo(subcls, name, 'param', p, p.kind)

            return True

        return check

del(
    abstract, closure, static
)