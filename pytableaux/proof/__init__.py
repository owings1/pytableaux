# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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

from abc import abstractmethod
from enum import Enum, Flag, auto
from types import MappingProxyType as MapProxy
from typing import TYPE_CHECKING, Any, NamedTuple, Sequence, TypeVar

from .. import __docformat__
from ..lang import Argument, Operator, Predicate, Quantifier
from ..logics import LogicType
from ..tools import EMPTY_MAP, EMPTY_QSET, EMPTY_SET, abcs, qsetf
from ..tools.timing import Counter, StopWatch

if TYPE_CHECKING:
    from ..proof import Rule

_TT = TypeVar('_TT', bound=type)

__all__ = (
    'adds',
    'anode',
    'Branch',
    'BranchEvent',
    'ClosingRule',
    'group',
    'HelperAttr',
    'Node',
    'Rule',
    'RuleAttr',
    'RuleEvent',
    'RuleHelper',
    'RuleMeta',
    'sdnode',
    'snode',
    'swnode',
    'TabEvent',
    'Tableau',
    'TableauxSystem',
    'TabWriter',
    'Target')

NOARG = object()

class HelperAttr(str, Enum):
    'Special ``RuleHelper`` class attribute names.'

    InitRuleCls = 'configure_rule'

#******  Rule Enum

class RuleAttr(str, Enum):
    'Special ``Rule`` class attribute names.'
    Helpers = 'Helpers'
    "Rule helper classes."
    Timers = 'Timers'
    "Rule timer names."
    DefaultOpts = '_defaults'
    "Rule default options."
    NodeFilters = 'NodeFilters'
    "For `FilterHelper`."
    IgnoreTicked = 'ignore_ticked'
    "For `FilterHelper`."
    ModalOperators = 'modal_operators'
    "For `MaxWorlds` helper."
    Modal = 'modal'
    "Modal flag."
    Legend = 'legend'
    "Rule legend"

class RuleLegendAttr(str, Enum):
    negated = 'negated'
    operator = 'operator'
    quantifier = 'quantifier'
    predicate = 'predicate'
    designation = 'designation'
    closure = 'closure'

class ProofAttr(str, Enum):

    def __str__(self):
        return self.value

class NodeKey(ProofAttr):
    sentence = 'sentence'
    designation = designated = 'designated'
    world = 'world'
    world1 = w1 = 'world1'
    world2 = w2 = 'world2'
    is_flag = 'is_flag'
    flag = 'flag'
    closure = 'closure'
    quit = 'quit'
    info = 'info'
    ellipsis = 'ellipsis'

class NodeAttr(ProofAttr):
    is_access = 'is_access'
    is_modal = 'is_modal'
    ticked = 'ticked'

class PropMap(abcs.ItemMapEnum):

    NodeDefaults = {
        NodeKey.designation: None,
        NodeKey.world: None}

    ClosureNode = {
        NodeKey.closure: True,
        NodeKey.flag: NodeKey.closure,
        NodeKey.is_flag: True}

    QuitFlag = {
        NodeKey.quit: True,
        NodeKey.is_flag: True,
        NodeKey.flag: NodeKey.quit}

    EllipsisNode = {
        NodeKey.ellipsis: True}

#******  Branch Enum

class BranchEvent(Enum):
    'Branch events.'
    AFTER_CLOSE = auto()
    AFTER_ADD   = auto()
    AFTER_TICK  = auto()

#******  Helper Enum

class RuleEvent(Enum):
    'Rule events.'
    BEFORE_APPLY = auto()
    AFTER_APPLY  = auto()

class RuleState(Flag):
    'Rule state bit flags.'
    NONE   = 0
    INIT   = 1
    LOCKED = 2

#******  Tableau Enum

class TabEvent(Enum):
    'Tableau events.'
    AFTER_BRANCH_ADD    = auto()
    AFTER_BRANCH_CLOSE  = auto()
    AFTER_NODE_ADD      = auto()
    AFTER_NODE_TICK     = auto()
    AFTER_TRUNK_BUILD   = auto()
    BEFORE_TRUNK_BUILD  = auto()
    AFTER_FINISH        = auto()

class TabStatKey(Enum):
    'Tableau ``stat()`` keys.'
    FLAGS       = auto()
    STEP_ADDED  = auto()
    STEP_TICKED = auto()
    STEP_CLOSED = auto()
    INDEX       = auto()
    PARENT      = auto()
    NODES       = auto()

class TabFlag(Flag):
    'Tableau state bit flags.'
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
    rule: Rule
    "The rule instance."
    target: Target
    "The target produced by the rule."
    duration: Counter
    "The duration counter."

    def __repr__(self):
        return f'<StepEntry:{id(self)}:{self.rule.name}:{self.target.type}>'

class Access(NamedTuple):
    "An `access` int tuple (world1, world2)."

    world1: int
    "world 1"
    world2: int
    "world 2"

    @property
    def w1(self) -> int:
        """Alias for :attr:`world1`."""
        return self.world1

    @property
    def w2(self) -> int:
        """Alias for :attr:`world2`."""
        return self.world2

    @classmethod
    def fornode(cls, node):
        """Create instance from a node."""
        return cls._make(map(node.__getitem__, cls._fields))

    def tonode(self):
        """Create node from this instance."""
        return AccessNode({
            NodeKey.w1: self.world1,
            NodeKey.w2: self.world2})

    def reversed(self):
        """Create reversed instance."""
        return self._make(reversed(self))

class NodeStat(dict):

    __slots__ = EMPTY_SET

    _defaults = MapProxy({
        TabStatKey.FLAGS       : TabFlag.NONE,
        TabStatKey.STEP_ADDED  : TabFlag.NONE,
        TabStatKey.STEP_TICKED : None})

    def __init__(self):
        super().__init__(self._defaults)

class BranchStat(dict):

    __slots__ = EMPTY_SET

    _defaults = MapProxy({
        TabStatKey.FLAGS       : TabFlag.NONE,
        TabStatKey.STEP_ADDED  : TabFlag.NONE,
        TabStatKey.STEP_CLOSED : TabFlag.NONE,
        TabStatKey.INDEX       : None,
        TabStatKey.PARENT      : None})

    def __init__(self, mapping = None, /, **kw):
        super().__init__(self._defaults)
        self[TabStatKey.NODES] = {}
        if mapping is not None:
            self.update(mapping)
        if len(kw):
            self.update(kw)

    def node(self, node, /):
        'Get the stat info for the node, and create if missing.'
        # Avoid using defaultdict, since it may hide problems.
        try:
            return self[TabStatKey.NODES][node]
        except KeyError:
            return self[TabStatKey.NODES].setdefault(node, NodeStat())

    def view(self):
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


class TableauxSystem(metaclass = abcs.AbcMeta):
    'Tableaux system base class.'

    Rules: LogicType.TabRules
    modal: bool|None = None

    @classmethod
    @abstractmethod
    def build_trunk(cls, tableau: Tableau, argument: Argument, /) -> None:
        """Build the trunk for an argument on the tableau.
        
        Args:
            tableau (Tableau): The tableau instance.
            argument (Argument): The argument.
        """
        raise NotImplementedError

    @classmethod
    def branching_complexity(cls, node: Node, /) -> int:
        """Compute how many new branches would be added if a rule were to be
        applied to the node.

        Args:
            node (Node): The node instance.
        
        Returns:
            int: The number of new branches.
        """
        return 0

    @classmethod
    def add_rules(cls, logic: LogicType, rules: RulesRoot, /) -> None:
        """Populate rules/groups for a tableau.

        Args:
            logic (LogicType): The logic.
            rules (RulesRoot): The tableau's rules.
        """
        Rules = logic.TabRules
        rules.groups.create('closure').extend(Rules.closure_rules)
        for classes in Rules.rule_groups:
            rules.groups.create().extend(classes)

    @classmethod
    def initialize(cls, RulesClass=None, /, *, modal=None):
        if modal is None:
            modal = cls.modal
        def dec(RulesClass:type[LogicType.TabRules]|_TT) -> _TT:
            RulesClass.all_rules = RulesClass.closure_rules + tuple(
                r for g in RulesClass.rule_groups for r in g)
            cls.Rules = RulesClass
            for rulecls in RulesClass.all_rules:
                if modal is not None:
                    setattr(rulecls, RuleAttr.Modal, modal)
                    if not modal:
                        _disable_filter(rulecls, filters.ModalNode)
            return RulesClass
        if RulesClass:
            return dec(RulesClass)
        return dec

class RuleHelper(metaclass = abcs.AbcMeta):
    'Rule helper interface.'

    __slots__ = EMPTY_SET

    rule: Rule
    config: Any

    def __init__(self, rule: Rule, /):
        self.rule = rule
        self.config = rule.Helpers.get(type(self))
        self.listen_on()

    def listen_on(self):
        pass

    def listen_off(self):
        pass

    @classmethod
    def configure_rule(cls, rulecls, config: Any, /):
        """``RuleHelper`` hook for initializing & verifiying a ``Rule`` class.
        
        Args:
            rulecls: The rule class using the helper class.
            config: Config from the rule class, if any.
        """
        pass

class RuleMeta(abcs.AbcMeta):
    """Rule meta class."""

    @classmethod
    def __prepare__(cls, clsname, bases, **kw):
        return dict(__slots__ = EMPTY_SET, name = clsname)

    def __new__(cls, clsname, bases, ns, /, modal = NOARG, **kw):

        Class: type[Rule] = super().__new__(cls, clsname, bases, ns, **kw)

        if modal is not NOARG:
            setattr(Class, RuleAttr.Modal, modal)

        abcs.merge_attr(Class, RuleAttr.DefaultOpts, mcls = cls,
            default = {}, transform = MapProxy)

        abcs.merge_attr(Class, RuleAttr.Timers, mcls = cls,
            default = EMPTY_QSET, transform = qsetf)

        configs = {}

        for parent in abcs.mroiter(Class, mcls = cls):
            v = getattr(parent, RuleAttr.Helpers, EMPTY_MAP)
            if isinstance(v, Sequence):
                for helpercls in v:
                    configs.setdefault(helpercls, None)
            else:
                configs.update(v)

        setattr(Class, RuleAttr.Helpers, MapProxy(configs))
        for helpercls, _ in configs.items():
            setup = getattr(helpercls, HelperAttr.InitRuleCls, None)
            if setup:
                configs[helpercls] = setup(Class, ...)
        if modal is False:
            _disable_filter(Class, filters.ModalNode)
        setattr(Class, RuleAttr.Legend, tuple(_build_legend(Class)))
        return Class

def _disable_filter(rulecls, filtercls):
    if filtercls not in (filts := getattr(rulecls, RuleAttr.NodeFilters, EMPTY_SET)):
        return
    filts[filtercls] = NotImplemented
    helpercls = helpers.FilterHelper
    if not (setup := getattr(helpercls, HelperAttr.InitRuleCls, None)):
        return
    if helpercls not in (configs := getattr(rulecls, RuleAttr.Helpers)):
        return
    configs = dict(configs)
    configs[helpercls] = setup(rulecls, ...)
    setattr(rulecls, RuleAttr.Helpers, MapProxy(configs))

def _build_legend(rulecls):
    """Build rule class legend."""
    getters = {
        RuleLegendAttr.operator: Operator,
        RuleLegendAttr.quantifier: Quantifier,
        RuleLegendAttr.predicate: Predicate}
    for attr in RuleLegendAttr:
        value = getattr(rulecls, attr, None)
        if attr is RuleLegendAttr.negated:
            if value:
                yield attr, Operator.Negation
        elif attr is RuleLegendAttr.designation:
            if value is not None:
                yield attr, value
        elif attr is RuleLegendAttr.closure:
            if value:
                yield attr, True
        elif attr in getters:
            if value:
                yield attr, getters[attr](value)

def group(*items):
    """Tuple builder.
    
    Args:
        *items: members.

    Returns:
        The tuple of arguments.
    """
    return items

def adds(*groups, **kw):
    """Target dict builder for `AdzHelper`.
    
    Args:
        *groups: node groups.
        **kw: dict keywords.

    Returns:
        A dict built from ``dict(adds = groups, **kw)``.
    """
    return dict(adds = groups, **kw)

def snode(s):
    'Make a sentence node.'
    return SentenceNode({NodeKey.sentence: s})

def sdnode(s, d):
    'Make a sentence/designated node.'
    return SentenceDesignationNode({
        NodeKey.sentence: s,
        NodeKey.designation: d})

def swnode(s, w):
    'Make a sentence/world node. Excludes world if None.'
    if w is None:
        return SentenceNode({NodeKey.sentence: s})
    return SentenceWorldNode({
        NodeKey.sentence: s,
        NodeKey.world: w})

def anode(w1, w2):
    'Make an Access node.'
    return AccessNode({
        NodeKey.w1: w1,
        NodeKey.w2: w2})

from .common import AccessNode, Branch
from .common import ClosureNode as ClosureNode
from .common import Designation as Designation
from .common import EllipsisNode as EllipsisNode
from .common import FlagNode as FlagNode
from .common import QuitFlagNode as QuitFlagNode
from .common import (Node, SentenceDesignationNode, SentenceNode,
                     SentenceWorldNode, Target)
from .tableaux import Rule, RulesRoot, Tableau

pass
from .rules import ClosingRule as ClosingRule

pass
from . import filters, helpers
from .writers import TabWriter
