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
pytableaux.proof.util
^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Iterable, Mapping, NamedTuple

from pytableaux.errors import check
from pytableaux.tools import MapProxy, abstract, closure
from pytableaux.tools.abcs import AbcMeta, Ebc, FlagEnum, abcm, eauto
from pytableaux.tools.hybrids import EMPTY_QSET, qsetf
from pytableaux.tools.mappings import ItemMapEnum, dmap
from pytableaux.tools.sets import EMPTY_SET, setf
from pytableaux.tools.timing import Counter, StopWatch

if TYPE_CHECKING:
    from pytableaux.proof.common import Node, Target
    from pytableaux.proof.tableaux import Rule

__all__ = (
    'BranchEvent',
    'RuleEvent',
    'TabEvent',
)


def demodalize_rules(Rules: Iterable[type[Rule]]) -> None:
    """Remove ``Modal`` filter from ``NodeFilters``, and clear `modal` attribute.
    
    Args:
        Rules: Iterable of rule classes."""
    from pytableaux.proof.filters import NodeFilters
    filtersattr = RuleAttr.NodeFilters
    rmfilters = {NodeFilters.Modal}
    for rulecls in Rules:
        value = getattr(rulecls, filtersattr, None)
        if value is not None and len(value & rmfilters):
            value -= rmfilters
            setattr(rulecls, filtersattr, value)
        if getattr(rulecls, 'modal', None) is not None:
            rulecls.modal = None


class PropMap(ItemMapEnum):

    NodeDefaults = dict(world = None, designated = None)

    ClosureNode = dict(is_flag = True, flag = 'closure')

#******  Branch Enum

class BranchEvent(Ebc):
    'Branch events.'
    AFTER_BRANCH_CLOSE = eauto()
    AFTER_NODE_ADD     = eauto()
    AFTER_NODE_TICK    = eauto()

#******  Helper Enum

class HelperAttr(str, Ebc):
    'Special ``RuleHelper`` class attribute names.'

    InitRuleCls = '__init_ruleclass__'

#******  Rule Enum

class RuleAttr(str, Ebc):
    'Special ``Rule`` class attribute names.'

    Helpers     = 'Helpers'
    "Rule helper classes."

    Timers      = 'Timers'
    "Rule timer names."

    DefaultOpts = '_defaults'
    "Rule default options."

    OptKeys     = '_optkeys'
    "Rule option keys."

    Name        = 'name'
    "Rule class name attribute."

    NodeFilters = 'NodeFilters'
    "For `FilterHelper`."

    IgnoreTicked = 'ignore_ticked'
    "For `FilterHelper`."

    ModalOperators = 'modal_operators'
    "For `MaxWorlds` helper."

class RuleEvent(Ebc):
    'Rule events.'

    BEFORE_APPLY = eauto()
    AFTER_APPLY  = eauto()

class RuleFlag(FlagEnum):
    'Rule state bit flags.'

    __slots__ = 'value', '_value_'

    NONE   = 0
    INIT   = 1
    LOCKED = 2

#******  Tableau Enum

class TabEvent(Ebc):
    'Tableau events.'

    AFTER_BRANCH_ADD    = eauto()
    AFTER_BRANCH_CLOSE  = eauto()
    AFTER_NODE_ADD      = eauto()
    AFTER_NODE_TICK     = eauto()
    AFTER_TRUNK_BUILD   = eauto()
    BEFORE_TRUNK_BUILD  = eauto()

class TabStatKey(Ebc):
    'Tableau ``stat()`` keys.'

    FLAGS       = eauto()
    STEP_ADDED  = eauto()
    STEP_TICKED = eauto()
    STEP_CLOSED = eauto()
    INDEX       = eauto()
    PARENT      = eauto()
    NODES       = eauto()

class TabFlag(FlagEnum):
    'Tableau state bit flags.'

    __slots__ = 'value', '_value_'

    NONE   = 0
    TICKED = 1
    CLOSED = 2
    PREMATURE   = 4
    FINISHED    = 8
    TIMED_OUT   = 16
    TRUNK_BUILT = 32

#******  Auxilliary Classes
class StepEntry(NamedTuple):
    #: The rule instance.
    rule   : Rule
    #: The target produced by the rule.
    target : Target
    #: The duration counter.
    duration: Counter

class Access(NamedTuple):

    world1: int
    world2: int

    @property
    def w1(self) -> int:
        return self.world1

    @property
    def w2(self) -> int:
        return self.world2

    @classmethod
    def fornode(cls, node: Mapping) -> Access:
        return cls._make(map(node.__getitem__, cls._fields))

    def reversed(self) -> Access:
        return self._make(reversed(self))


class NodeStat(dict[TabStatKey, TabFlag|int|None]):

    __slots__ = EMPTY_SET

    _defaults = MapProxy({
        TabStatKey.FLAGS       : TabFlag.NONE,
        TabStatKey.STEP_ADDED  : TabFlag.NONE,
        TabStatKey.STEP_TICKED : None,
    })

    def __init__(self):
        super().__init__(self._defaults)



class BranchStat(dict[TabStatKey, TabFlag|int|dict[Any, NodeStat]|None]):

    __slots__ = EMPTY_SET

    _defaults = MapProxy({
        TabStatKey.FLAGS       : TabFlag.NONE,
        TabStatKey.STEP_ADDED  : TabFlag.NONE,
        TabStatKey.STEP_CLOSED : TabFlag.NONE,
        TabStatKey.INDEX       : None,
        TabStatKey.PARENT      : None,
    })

    def __init__(self, mapping: Mapping = None, /, **kw):
        super().__init__(self._defaults)
        self[TabStatKey.NODES] = {}
        if mapping is not None:
            self.update(mapping)
        if len(kw):
            self.update(kw)

    def node(self, node: Node, /) -> NodeStat:
        'Get the stat info for the node, and create if missing.'
        # Avoid using defaultdict, since it may hide problems.
        try:
            return self[TabStatKey.NODES][node]
        except KeyError:
            return self[TabStatKey.NODES].setdefault(node, NodeStat())

    def view(self) -> dict[TabStatKey, TabFlag|int|Any|None]:
        return {k: self[k] for k in self._defaults}

class TabTimers(NamedTuple):
    'Tableau timers data class.'

    build  : StopWatch
    trunk  : StopWatch
    tree   : StopWatch
    models : StopWatch

    @staticmethod
    def create(it = (False,) * 4):
        return TabTimers._make(map(StopWatch, it))
