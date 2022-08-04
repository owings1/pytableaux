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

from abc import abstractmethod as abstract
from enum import auto
from types import MappingProxyType as MapProxy
from typing import TYPE_CHECKING, Any, NamedTuple, Sequence

from pytableaux import __docformat__
from pytableaux.lang import Operator, Predicate, Quantifier
from pytableaux.logics import LogicType
from pytableaux.tools import EMPTY_MAP, EMPTY_QSET, EMPTY_SET, abcs, qsetf
from pytableaux.tools.timing import Counter, StopWatch

if TYPE_CHECKING:
    from pytableaux.proof import Rule

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
    'TreeStruct',
    'Target',
)

NOARG = object()

class HelperAttr(str, abcs.Ebc):
    'Special ``RuleHelper`` class attribute names.'

    InitRuleCls = 'configure_rule'

#******  Rule Enum

class RuleAttr(str, abcs.Ebc):
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

class ProofAttr(str, abcs.Ebc):

    def __str__(self):
        return self.value

class NodeAttr(ProofAttr):

    sentence = 'sentence'
    designation = designated = 'designated'
    world   = 'world'
    world1 = w1 = 'world1'
    world2 = w2 = 'world2'
    is_flag = 'is_flag'
    flag    = 'flag'
    closure = 'closure'
    info    = 'info'

class PropMap(abcs.ItemMapEnum):

    NodeDefaults = {
        NodeAttr.designation: None,
        NodeAttr.world: None}

    ClosureNode = {
        NodeAttr.closure: True,
        NodeAttr.flag: 'closure',
        NodeAttr.is_flag: True}

    QuitFlag = {
        NodeAttr.is_flag: True,
        NodeAttr.flag: 'quit'}

#******  Branch Enum

class BranchEvent(abcs.Ebc):
    'Branch events.'
    AFTER_CLOSE = auto()
    AFTER_ADD   = auto()
    AFTER_TICK  = auto()

#******  Helper Enum

class RuleEvent(abcs.Ebc):
    'Rule events.'

    BEFORE_APPLY = auto()
    AFTER_APPLY  = auto()

class RuleState(abcs.FlagEnum):
    'Rule state bit flags.'

    __slots__ = ('value', '_value_')

    NONE   = 0
    INIT   = 1
    LOCKED = 2

#******  Tableau Enum

class TabEvent(abcs.Ebc):
    'Tableau events.'

    AFTER_BRANCH_ADD    = auto()
    AFTER_BRANCH_CLOSE  = auto()
    AFTER_NODE_ADD      = auto()
    AFTER_NODE_TICK     = auto()
    AFTER_TRUNK_BUILD   = auto()
    BEFORE_TRUNK_BUILD  = auto()
    AFTER_FINISH        = auto()

class TabStatKey(abcs.Ebc):
    'Tableau ``stat()`` keys.'

    FLAGS       = auto()
    STEP_ADDED  = auto()
    STEP_TICKED = auto()
    STEP_CLOSED = auto()
    INDEX       = auto()
    PARENT      = auto()
    NODES       = auto()

class TabFlag(abcs.FlagEnum):
    'Tableau state bit flags.'

    __slots__ = ('value', '_value_')

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
        return anode(*self)

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

    @classmethod
    @abstract
    def build_trunk(cls, tableau, argument, /) -> None:
        """Build the trunk for an argument on the tableau.
        
        Args:
            tableau (Tableau): The tableau instance.
            argument (Argument): The argument.
        """
        raise NotImplementedError

    @classmethod
    def branching_complexity(cls, node, /) -> int:
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
    def initialize(cls, RulesClass:LogicType.TabRules, /):
        RulesClass.all_rules = RulesClass.closure_rules + tuple(
            r for g in RulesClass.rule_groups for r in g)
        cls.Rules = RulesClass
        return RulesClass

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
        return dict(__slots__ = EMPTY_SET)

    def __new__(cls, clsname, bases, ns, /, modal = NOARG, **kw):

        Class: type[Rule] = super().__new__(cls, clsname, bases, ns, **kw)

        Class.name = clsname

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
        for helpercls, config in configs.items():
            setup = getattr(helpercls, HelperAttr.InitRuleCls, None)
            if setup:
                configs[helpercls] = setup(Class, config)
                if modal is False and helpercls is helpers.FilterHelper:
                    v = getattr(Class, RuleAttr.NodeFilters)
                    if filters.ModalNode in v:
                        v[filters.ModalNode] = NotImplemented
                        configs[helpercls] = setup(Class, config)

        setattr(Class, RuleAttr.Legend, _build_legend(Class))
        return Class


def _build_legend(rulecls):
    """Build rule class legend."""

    legend = {}

    if getattr(rulecls, 'negated', None):
        legend['negated'] = Operator.Negation

    if (oper := getattr(rulecls, 'operator', None)):
        legend['operator'] = Operator[oper]
    elif (quan := getattr(rulecls, 'quantifier', None)):
        legend['quantifier'] = Quantifier[quan]
    elif (pred := getattr(rulecls, 'predicate', None)):
        legend['predicate'] = Predicate(pred)

    if (des := getattr(rulecls, 'designation', None)) is not None:
        legend['designation'] = des

    try:
        if issubclass(rulecls, ClosingRule):
            legend['closure'] = True
    except NameError:
        pass

    return tuple(legend.items())

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
    return Node(dict(sentence = s))

def sdnode(s, d):
    'Make a sentence/designated node.'
    return Node(dict(sentence = s, designated = d))

def swnode(s, w):
    'Make a sentence/world node. Excludes world if None.'
    if w is None:
        return snode(s)
    return Node(dict(sentence = s, world = w))

def anode(w1, w2):
    'Make an Access node.'
    return Node(dict(world1 = w1, world2 = w2))

from pytableaux.proof.common import Branch, Node, Target
from pytableaux.proof.tableaux import Rule, RulesRoot, Tableau

pass
from pytableaux.proof.rules import ClosingRule as ClosingRule

pass
from pytableaux.proof import filters, helpers
from pytableaux.proof.tableaux import TreeStruct as TreeStruct
from pytableaux.proof.writers import TabWriter
