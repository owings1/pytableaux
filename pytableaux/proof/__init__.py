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
from typing import TYPE_CHECKING, Any, NamedTuple, Self, Sequence, TypeVar

from ..lang import Argument, Operator, Predicate, Quantifier
from ..logics import LogicType
from ..tools import EMPTY_QSET, EMPTY_SET, abcs, qsetf
from ..tools.timing import Counter, StopWatch

if TYPE_CHECKING:
    from ..proof import Rule

_TT = TypeVar('_TT', bound=type)

__all__ = (
    'adds',
    'anode',
    'Branch',
    'ClosingRule',
    'group',
    'Node',
    'Rule',
    'sdnode',
    'snode',
    'swnode',
    'Tableau',
    'TableauxSystem',
    'TabWriter',
    'Target')

NOARG = object()

class WorldPair(NamedTuple):
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
            Node.Key.world1: self.world1,
            Node.Key.world2: self.world2})

    def reversed(self):
        """Create reversed instance."""
        return self._make(reversed(self))

class NodeMeta(abcs.AbcMeta):
    """Node meta class."""

    class Key(str, Enum):
        "Node keys."
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

        def __str__(self):
            return self.value

    class PropMap(abcs.ItemMapEnum):
        Defaults = dict(
            designated = None,
            world = None)
        Closure = dict(
            closure = True,
            flag = 'closure',
            is_flag = True)
        QuitFlag = dict(
            quit = True,
            flag = 'quit',
            is_flag = True)
        Ellipsis = dict(
            ellipsis = True)

class BranchMeta(abcs.AbcMeta):
    """Branch meta class."""

    class Events(str, Enum):
        'Branch events.'
        AFTER_CLOSE = 'AFTER_CLOSE'
        AFTER_ADD   = 'AFTER_ADD'
        AFTER_TICK  = 'AFTER_TICK'

class TableauMeta(abcs.AbcMeta):
    """Tableau meta class."""

    class Events(str, Enum):
        'Tableau events.'
        AFTER_BRANCH_ADD    = 'AFTER_BRANCH_ADD'
        AFTER_BRANCH_CLOSE  = 'AFTER_BRANCH_CLOSE'
        AFTER_NODE_ADD      = 'AFTER_NODE_ADD'
        AFTER_NODE_TICK     = 'AFTER_NODE_TICK'
        AFTER_TRUNK_BUILD   = 'AFTER_TRUNK_BUILD'
        BEFORE_TRUNK_BUILD  = 'BEFORE_TRUNK_BUILD'
        AFTER_RULE_APPLY    = 'AFTER_RULE_APPLY'
        AFTER_FINISH        = 'AFTER_FINISH'

    class Timers(NamedTuple):
        'Tableau timers data class.'
        build  : StopWatch
        trunk  : StopWatch
        tree   : StopWatch
        models : StopWatch

        @classmethod
        def create(cls, it = (False,) * 4):
            return cls._make(map(StopWatch, it))

    class Flag(Flag):
        'Tableau state bit flags.'
        # NONE   = 0
        TICKED = 1
        CLOSED = 2
        PREMATURE = 4
        FINISHED = 8
        TIMED_OUT = 16
        TRUNK_BUILT = 32
        TIMING_INACCURATE = 64
        HAS_STEP_LIMIT = 128
        HAS_TIME_LIMIT = 256
        STARTED = 512

    class StatKey(str, Enum):
        'Tableau ``stat()`` keys.'
        FLAGS       = 'FLAGS'
        STEP_ADDED  = 'STEP_ADDED'
        STEP_TICKED = 'STEP_TICKED'
        STEP_CLOSED = 'STEP_CLOSED'
        INDEX       = 'INDEX'
        PARENT      = 'PARENT'
        NODES       = 'NODES'

    class StepEntry(NamedTuple):
        rule: Rule
        "The rule instance."
        target: Target
        "The target produced by the rule."
        duration: Counter
        "The duration counter."

        def __repr__(self):
            return f'<StepEntry:{id(self)}:{self.rule.name}:{self.target.type}>'

class TableauxSystem(metaclass = abcs.AbcMeta):
    'Tableaux system base class.'

    Rules: type[LogicType.TabRules]
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
                    rulecls.modal = modal
                    if not modal:
                        rulecls.disable_filter(filters.ModalNode)
            return RulesClass
        if RulesClass:
            return dec(RulesClass)
        return dec

class RuleMeta(abcs.AbcMeta):
    """Rule meta class."""

    class State(Flag):
        'Rule state bit flags.'
        INIT   = 1
        LOCKED = 2

    class Events(Enum):
        'Rule events.'
        BEFORE_APPLY = auto()
        AFTER_APPLY  = auto()

    class Legend(str, Enum):
        closure = 'closure'
        negated = 'negated'
        operator = 'operator'
        quantifier = 'quantifier'
        predicate = 'predicate'
        designation = 'designation'

        @classmethod
        def make(cls, obj):
            """Build rule class legend."""
            getters = {
                cls.operator: Operator,
                cls.quantifier: Quantifier,
                cls.predicate: Predicate}
            for attr in cls:
                value = getattr(obj, attr, None)
                if attr is cls.negated:
                    if value:
                        yield attr, Operator.Negation
                elif attr is cls.designation:
                    if value is not None:
                        yield attr, value
                elif attr is cls.closure:
                    if value:
                        yield attr, True
                elif attr in getters:
                    if value:
                        yield attr, getters[attr](value)
    @classmethod
    def __prepare__(cls, clsname, bases, **kw):
        return dict(__slots__ = EMPTY_SET, name = clsname)

    def __new__(cls, clsname, bases, ns, /, modal = NOARG, **kw):
        rulecls: type[Rule] = super().__new__(cls, clsname, bases, ns, **kw)
        if modal is not NOARG:
            rulecls.modal = modal
        abcs.merge_attr(rulecls, '_defaults', mcls = cls,
            default = {}, transform = MapProxy)
        abcs.merge_attr(rulecls, 'timer_names', mcls = cls,
            default = EMPTY_QSET, transform = qsetf)
        configs: dict[type[Rule.Helper], Any] = {}
        for parent in abcs.mroiter(rulecls, mcls = cls):
            v = parent.Helpers
            if isinstance(v, Sequence):
                for helpercls in v:
                    configs.setdefault(helpercls, None)
            else:
                configs.update(v)
        rulecls.Helpers = MapProxy(configs)
        for helpercls, _ in configs.items():
            configs[helpercls] = helpercls.configure_rule(rulecls, ...)
        if modal is False:
            rulecls.disable_filter(filters.ModalNode)
        rulecls.legend = tuple(cls.Legend.make(rulecls))
        return rulecls

    def disable_filter(self: Self|type[Rule], filtercls):
        try:
            filts = self.NodeFilters
        except AttributeError:
            return
        if filtercls not in filts:
            return
        filts[filtercls] = NotImplemented
        helpercls = helpers.FilterHelper
        if helpercls not in self.Helpers:
            return
        configs = dict(self.Helpers)
        configs[helpercls] = helpercls.configure_rule(self, ...)
        self.Helpers = MapProxy(configs)

    class Helper(metaclass = abcs.AbcMeta):
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
        def configure_rule(cls, rulecls: type[Rule], config: Any, /):
            """Hook for initializing & verifiying a ``Rule`` class.
            
            Args:
                rulecls: The rule class using the helper class.
                config: Config from the rule class, if any.
            """
            pass

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
    return SentenceNode({Node.Key.sentence: s})

def sdnode(s, d):
    'Make a sentence/designated node.'
    return SentenceDesignationNode({
        Node.Key.sentence: s,
        Node.Key.designation: d})

def swnode(s, w):
    'Make a sentence/world node. Excludes world if None.'
    if w is None:
        return SentenceNode({Node.Key.sentence: s})
    return SentenceWorldNode({
        Node.Key.sentence: s,
        Node.Key.world: w})

def anode(w1, w2):
    'Make an Access node.'
    return AccessNode({
        Node.Key.world1: w1,
        Node.Key.world2: w2})

from ..tools import group as group
from .common import AccessNode, Branch
from .common import ClosureNode as ClosureNode
from .common import Designation as Designation
from .common import EllipsisNode as EllipsisNode
from .common import FlagNode as FlagNode
from .common import Node
from .common import QuitFlagNode as QuitFlagNode
from .common import (SentenceDesignationNode, SentenceNode, SentenceWorldNode,
                     Target)
from .tableaux import Rule, RulesRoot, Tableau

pass
from .rules import ClosingRule as ClosingRule

pass
from . import filters, helpers
from .writers import TabWriter
