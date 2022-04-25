# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
pytableaux.proof
^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Mapping

from pytableaux.errors import check
from pytableaux.proof.util import HelperAttr, RuleAttr
from pytableaux.tools import MapProxy, abstract, closure
from pytableaux.tools.abcs import AbcMeta, abcm
from pytableaux.tools.hybrids import EMPTY_QSET, qsetf
from pytableaux.tools.mappings import dmap
from pytableaux.tools.sets import EMPTY_SET, setf

if TYPE_CHECKING:
    from typing import overload

    from pytableaux.proof.tableaux import Rule

class RuleHelper(metaclass = AbcMeta):
    'Rule helper interface.'

    __slots__ = EMPTY_SET

    rule: Rule

    @abstract
    def __init__(self,/): ...

    @classmethod
    def __init_ruleclass__(cls, rulecls: type[Rule], /):
        """``RuleHelper`` hook for initializing & verifiying a ``Rule`` class.
        
        Args:
            rulecls: The rule class using the helper class.
        """
        pass

    @classmethod
    def __subclasshook__(cls, subcls: type, /):
        if cls is not __class__:
            return NotImplemented
        return _check_helper_subclass(subcls)

#******  Rule Meta

class RuleMeta(AbcMeta):

    @classmethod
    def __prepare__(cls, clsname: str, bases: tuple[type, ...], **kw) -> dict[str, Any]:
        return dict(__slots__ = EMPTY_SET)

    def __new__(cls, clsname: str, bases: tuple[type, ...], ns: dict, /, *,
        helper: Mapping[type[RuleHelper], Mapping[str, Any]] = {}, **kw
    ):

        RuleBase = _rule_basecls(cls)

        Class = super().__new__(cls, clsname, bases, ns, **kw)

        if RuleBase is None:
            RuleBase = _rule_basecls(cls, Class)

        abcm.merge_mroattr(Class, RuleAttr.Helpers, supcls = RuleBase,
            default   = EMPTY_QSET,
            transform = qsetf,
        )
        abcm.merge_mroattr(Class, RuleAttr.Timers, supcls = RuleBase,
            default   = EMPTY_QSET,
            transform = qsetf,
        )
        abcm.merge_mroattr(Class, RuleAttr.DefaultOpts, supcls = RuleBase,
            default   = dmap(),
            transform = MapProxy,
        )
        
        setattr(Class, RuleAttr.OptKeys, setf(getattr(Class, RuleAttr.DefaultOpts)))
        setattr(Class, RuleAttr.Name, clsname)

        for Helper in getattr(Class, RuleAttr.Helpers):
            check.subcls(Helper, RuleHelper)
            initrulecls = getattr(Helper, HelperAttr.InitRuleCls, None)
            if initrulecls is not None:
                initrulecls(Class, **helper.get(Helper, MapProxy.EMPTY_MAP))

        return Class

def _rule_basecls(metacls: type, default: type = None, /, *, base = {}):
    try:
        return base[metacls]
    except KeyError:
        if default is not None:
            base[metacls] = default
            _rule_basecls.__kwdefaults__.update(base = MapProxy(base))
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

    names = qsetf((
        'rule',
        # HelperAttr.InitRuleCls,
        '__init__',
    ))

    def check_subclass(subcls: type):

        # print(f'check {subcls}')
        mrocheck = abcm.check_mrodict(subcls.mro(), *names)
        if mrocheck is NotImplemented or mrocheck is False:
            return mrocheck

        name = 'rule'
        if name in names:

            value = getattr(subcls, name)
            if not is_descriptor(value):
                return NotImplemented

        name = HelperAttr.InitRuleCls
        if name in names:

            value = getattr(subcls, name)
            if not callable(value):
                return NotImplemented
            params = getparams(value)
            if len(params) < 2:
                return NotImplemented
            p = params[1]
            if p.kind & posflag != p.kind:
                return NotImplemented
    
        name = '__init__'
        if name in names:

            value = getattr(subcls, name)
            if not callable(value):
                return NotImplemented
            params = getparams(value)
            if len(params) < 2:
                name = '__new__'
                value = getattr(subcls, name)
                if not callable(value):
                    return NotImplemented
                params = getparams(value)
                if len(params) < 2:
                    return NotImplemented
            p = params[1]
            if p.kind & posflag != p.kind:
                return NotImplemented

        return True

    return check_subclass
