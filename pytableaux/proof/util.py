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
pytableaux.proof.util
^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations
from collections import deque

from typing import TYPE_CHECKING, Any, Iterable, Mapping, NamedTuple

from pytableaux.tools import MapProxy
from pytableaux.tools.abcs import Ebc, FlagEnum, eauto
from pytableaux.tools.mappings import ItemMapEnum
from pytableaux.tools.sets import EMPTY_SET
from pytableaux.tools.timing import Counter, StopWatch
from pytableaux.tools.typing import T

if TYPE_CHECKING:
    from pytableaux.lang.lex import Sentence
    from pytableaux.proof.common import Node, Target
    from pytableaux.proof.tableaux import Rule

__all__ = (
    'adds',
    'anode',
    'BranchEvent',
    'group',
    'RuleEvent',
    'sdnode',
    'swnode',
    'TabEvent',
)

def group(*items: T) -> tuple[T, ...]:
    """Tuple builder.
    
    Args:
        *items: members.

    Returns:
        The tuple of arguments.
    """
    return items

def adds(*groups: tuple[dict, ...], **kw) -> dict[str, tuple[dict, ...]|Any]:
    """Target dict builder for `AdzHelper`.
    
    Args:
        *groups: node groups.
        **kw: dict keywords.

    Returns:
        A dict built from ``dict(adds = groups, **kw)``.
    """
    return dict(adds = groups, **kw)

def sdnode(s: Sentence, d: bool):
    'Make a sentence/designated node dict.'
    return dict(sentence = s, designated = d)

def swnode(s: Sentence, w: int|None):
    'Make a sentence/world node dict. Excludes world if None.'
    if w is None:
        return dict(sentence = s)
    return dict(sentence = s, world = w)

def anode(w1: int, w2: int):
    'Make an Access node dict.'
    return Access(w1, w2)._asdict()


class ProofAttr(str, Ebc): pass
        
class NodeAttr(ProofAttr):

    designation = 'designated'
    closure = 'closure'
    flag    = 'flag'
    is_flag = 'is_flag'
    world   = 'world'


class PropMap(ItemMapEnum):

    NodeDefaults = {
        NodeAttr.designation: None,
        NodeAttr.world: None,
    }

    ClosureNode = {
        NodeAttr.closure: True,
        NodeAttr.flag: NodeAttr.closure,
        NodeAttr.is_flag: True
    },


#******  Branch Enum

class BranchEvent(Ebc):
    'Branch events.'
    AFTER_CLOSE = eauto()
    AFTER_ADD   = eauto()
    AFTER_TICK  = eauto()

#******  Helper Enum

class HelperAttr(str, Ebc):
    'Special ``RuleHelper`` class attribute names.'

    InitRuleCls = 'configure_rule'

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

    Modal = 'modal'
    "Modal flag."

class RuleEvent(Ebc):
    'Rule events.'

    BEFORE_APPLY = eauto()
    AFTER_APPLY  = eauto()

class RuleState(FlagEnum):
    'Rule state bit flags.'

    __slots__ = 'value', '_value_'

    NONE   = 0
    INIT   = 1
    LOCKED = 2

class RuleClassFlag(FlagEnum):
    "WIP: Rule class feature flags."

    __slots__ = 'value', '_value_'

    Modal = 4
    RankOptimSupported = 8


#******  Tableau Enum

class TabEvent(Ebc):
    'Tableau events.'

    AFTER_BRANCH_ADD    = eauto()
    AFTER_BRANCH_CLOSE  = eauto()
    AFTER_NODE_ADD      = eauto()
    AFTER_NODE_TICK     = eauto()
    AFTER_TRUNK_BUILD   = eauto()
    BEFORE_TRUNK_BUILD  = eauto()
    AFTER_FINISH        = eauto()

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
    TIMING_INACCURATE = 64

#******  Auxilliary Classes
class StepEntry(NamedTuple):
    #: The rule instance.
    rule   : Rule
    #: The target produced by the rule.
    target : Target
    #: The duration counter.
    duration: Counter

    def __repr__(self):
        return f'<StepEntry:{id(self)}:{self.rule.name}:{self.target.type}>'

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
