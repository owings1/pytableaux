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

import itertools
from abc import abstractmethod
from enum import Enum, Flag
from types import MappingProxyType as MapProxy
from typing import Any, Hashable, Iterable, NamedTuple, Sequence, TypeVar

from ..lang import Argument, Operator, Predicate, Quantifier
from ..logics import LogicType
from ..tools import EMPTY_QSET, EMPTY_SET, abcs, qsetf
from ..tools.timing import Counter, StopWatch

_KT = TypeVar('_KT')
_VT = TypeVar('_VT')

__all__ = (
    'AccessNode',
    'adds',
    'anode',
    'Branch',
    'ClosingRule',
    'ClosureNode',
    'Designation',
    'EllipsisNode',
    'filters',
    'FlagNode',
    'helpers',
    'Modal',
    'Node',
    'QuitFlagNode',
    'Rule',
    'sdnode',
    'SentenceDesignationNode',
    'SentenceNode',
    'SentenceWorldNode',
    'snode',
    'swnode',
    'Tableau',
    'System',
    'TabWriter',
    'Target',
    'WorldNode',
    'WorldPair')

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

    WORLD_KEYS = (Key.world, Key.world1, Key.world2)

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

    @classmethod
    def __prepare__(cls, clsname, bases, **kw):
        return dict(__slots__ = EMPTY_SET)

class HelperMeta(abcs.AbcMeta):

    @classmethod
    def __prepare__(cls, clsname, bases, **kw):
        return dict(__slots__=EMPTY_SET)

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
        def create(cls):
            it = itertools.repeat(False, len(cls._fields))
            return cls._make(map(StopWatch, it))

    class Flag(Flag):
        'Tableau state bit flags.'
        TICKED = 1 << 0
        CLOSED = 1 << 1
        PREMATURE = 1 << 2
        FINISHED = 1 << 3
        TIMED_OUT = 1 << 4
        TRUNK_BUILT = 1 << 5
        TIMING_INACCURATE = 1 << 6
        HAS_STEP_LIMIT = 1 << 7
        HAS_TIME_LIMIT = 1 << 8
        STARTED = 1 << 9

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

class GetLogicMetaMixinMetaType(type):

    @property
    def Meta(self) -> type[LogicType.Meta]|None:
        return LogicType.meta_for_module(self.__module__)

class SystemMeta(abcs.AbcMeta, GetLogicMetaMixinMetaType):

    @property
    def modal(self) -> bool|None:
        return self.Meta and self.Meta.modal

class System(metaclass=SystemMeta):
    'Tableaux system base class.'

    @classmethod
    @abstractmethod
    def build_trunk(cls, b: Branch, arg: Argument, /) -> None:
        """Build the trunk for an argument on the tableau.
        
        Args:
            b (Branch): The branch to construct.
            arg (Argument): The argument.
        """
        raise NotImplementedError

    @classmethod
    def branching_complexity(cls, node: Node, rules: RulesRoot, /) -> int:
        """Compute how many new branches would be added if a rule were to be
        applied to the node.

        Args:
            node (Node): The node instance.
            rules (RulesRoot): The rules on the tableau.

        Returns:
            int: The number of new branches.
        """
        return 0

    @classmethod
    def branching_complexity_hashable(cls, node: Node, /) -> Hashable:
        """Return a hashable object corresponding to a node's branching
        complexity, in order to save redundant computation time. By default
        it just returns the node itself.

        Args:
            node (Node): The node instance.

        Returns:
            A hashable object.
        """
        return node


class RuleMeta(abcs.AbcMeta, GetLogicMetaMixinMetaType):
    """Rule meta class."""

    name: str

    class State(Flag):
        'Rule state bit flags.'
        INIT = 1 << 0
        LOCKED = 1 << 1

    class Events(str, Enum):
        'Rule events.'
        BEFORE_APPLY = 'BEFORE_APPLY'
        AFTER_APPLY = 'AFTER_APPLY'

    class Legend(str, Enum):
        closure = 'closure'
        negated = 'negated'
        operator = 'operator'
        quantifier = 'quantifier'
        predicate = 'predicate'
        designation = 'designation'
        marklegend = 'marklegend'

    @property
    def modal(self) -> bool|None:
        return self.Meta and self.Meta.modal

    def __prepare__(clsname, bases, **kw):
        return dict(__slots__=EMPTY_SET, name=clsname)

    def __new__(cls, clsname, bases, ns, intermediate=False, **kw):
        self: type[Rule] = super().__new__(cls, clsname, bases, ns, **kw)
        abcs.merge_attr(self, '_defaults', mcls=cls,
            default={}, transform=MapProxy)
        abcs.merge_attr(self, 'timer_names', mcls=cls,
            default=EMPTY_QSET, transform=qsetf)
        if self.autoattrs:
            for name, value in self.induce_attrs().items():
                setattr(self, name, value)
        configs: dict[type[Rule.Helper], Any] = {}
        for parent in abcs.mroiter(self, mcls=cls):
            value = parent.Helpers
            if isinstance(value, Sequence):
                configs = dict.fromkeys(value) | configs
            else:
                configs.update(value)
        self.Helpers = MapProxy(configs)
        for helpercls, config in configs.items():
            configs[helpercls] = helpercls.configure_rule(self, config)
        isconcrete = not intermediate and not abcs.isabstract(self)
        if isconcrete:
            self.legend = tuple(self.build_legend())
            if 'branching' not in self.__dict__:
                self.branching = self.induce_branching()
        return self

    def build_legend(self):
        """Build rule class legend."""
        Leg = self.Legend
        getters = {
            Leg.operator: Operator,
            Leg.quantifier: Quantifier,
            Leg.predicate: Predicate}
        for attr in Leg:
            value = getattr(self, attr, None)
            if attr is Leg.negated:
                if value:
                    yield attr, Operator.Negation
            elif attr is Leg.designation:
                if value is not None:
                    yield attr, value
            elif attr is Leg.marklegend:
                if value is not None:
                    yield from value
            elif attr is Leg.closure:
                if value:
                    yield attr, True
            elif attr in getters:
                if value:
                    yield attr, getters[attr](value)

    def induce_attrs(self):
        return RuleNameAttrInducer(self).build() or {}

    def induce_branching(self):
        tab = Tableau()
        rule: Rule = self(tab)
        branch = tab.branch().extend(rule.example_nodes())
        target = rule.target(branch)
        if target:
            rule.apply(target)
            return len(rule.tableau) - 1
        return NotImplemented

    class AbstractHelper(metaclass=HelperMeta):
        'Rule helper interface.'

        shareable = False
        requires = EMPTY_SET

        rule: Rule
        config: Any

        @property
        def tableau(self) -> Tableau:
            return self.rule.tableau

        @abstractmethod
        def __init__(self, rule: Rule, /):
            self.rule = rule
            self.config = rule.Helpers.get(type(self))
            self.listen_on()

        def listen_on(self):
            pass

        @classmethod
        def configure_rule(cls, rulecls: type[Rule], config: Any):
            """Hook for initializing & verifiying a ``Rule`` class.
            
            Args:
                rulecls: The rule class using the helper class.
                config: Config from the rule class, if any.
            """
            pass

    class Helper(AbstractHelper):
        "Rule helper basic base class."

        __slots__ = ('rule', 'config')

        def __init__(self, rule: Rule, /):
            Rule.AbstractHelper.__init__(self, rule)

    class HelperDict(AbstractHelper, dict[_KT, _VT]):
        "Rule helper base class that also subclasses dict."

        __slots__ = ('rule', 'config')

        def __init__(self, rule: Rule, /):
            Rule.AbstractHelper.__init__(self, rule)


class RuleNameAttrInducer:

    names = (
        'operator',
        'quantifier',
        'predicate',
        'negated',
        'designation')

    doubleneg = 'DoubleNegation'
    designates = ('Undesignated', 'Designated')
    negatedstr = 'Negated'

    obj: Any
    name: str
    todo: str
    attrs: dict[str, Any]
    notfounds: list[str]
    conflicts: dict[str, tuple[str, str, str]]

    def __init__(self, obj: Any):
        self.obj = obj
        self.name = self.obj.__name__
        self.todo = self.name
        self.attrs = {}
        self.notfounds = []
        self.conflicts = {}

    @property
    def is_doubleneg(self):
        return self.name.startswith(self.doubleneg)

    def build(self):
        for name in self.names:
            name = Rule.Legend(name).value
            if not getattr(self, f'do_{name}')(name):
                self.notfounds.append(name)
        self.find_conflicts()
        if self.conflicts:
            raise TypeError(
                f'Direct __dict__ conflicts inducing autoattrs for '
                f'{self.obj} : {self.conflicts}')
            return
        for name in self.notfounds:
            if hasattr(self.obj, name):
                self.attrs[name] = None
        if not self.todo:
            return self.attrs

    def do_operator(self, name: str):
        if self.is_doubleneg:
            return self.found(name, self.doubleneg, Operator.Negation)
        return self.common_enum(name, Operator)

    def do_quantifier(self, name: str):
        return self.common_enum(name, Quantifier)

    def do_predicate(self, name: str):
        return self.common_enum(name, Predicate.System)

    def do_negated(self, name: str):
        if self.is_doubleneg:
            return self.found(name, '', True)
        if self.todo.startswith(self.negatedstr):
            return self.found(name, self.negatedstr, True)

    def do_designation(self, name: str):
        for i, indicator in enumerate(self.designates):
            if self.todo.startswith(indicator):
                return self.found(name, indicator, bool(i))

    def found(self, name: str, indicator: str, value: Any):
        self.attrs[name] = value
        self.todo = self.todo.removeprefix(indicator)
        return True

    def find_conflicts(self):
        ns = self.obj.__dict__
        for name in filter(ns.__contains__, self.attrs):
            value = self.attrs[name]
            old = getattr(self.obj, name, value)
            if old != value:
                self.conflicts[name] = (old, value)

    def common_enum(self, name: str, it: Iterable[Operator|Quantifier|Predicate]):
        for item in it:
            if self.todo.startswith(item.name):
                return self.found(name, item.name, item)

def adds(*groups, **kw):
    """Target dict builder for `AdzHelper`.
    
    Args:
        *groups: node groups.
        **kw: dict keywords.

    Returns:
        A dict built from ``dict(adds = groups, **kw)``.
    """
    return dict(adds=groups, **kw)

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

from .common import AccessNode as AccessNode
from .common import Branch as Branch
from .common import ClosureNode as ClosureNode
from .common import Designation as Designation
from .common import DesignationNode as DesignationNode
from .common import EllipsisNode as EllipsisNode
from .common import FlagNode as FlagNode
from .common import Modal as Modal
from .common import Node as Node
from .common import QuitFlagNode as QuitFlagNode
from .common import SentenceDesignationNode as SentenceDesignationNode
from .common import SentenceNode as SentenceNode
from .common import SentenceWorldNode as SentenceWorldNode
from .common import Target as Target
from .common import WorldNode as WorldNode
from .tableaux import Rule as Rule
from .tableaux import RuleGroup as RuleGroup
from .tableaux import RuleGroups as RuleGroups
from .tableaux import RulesRoot as RulesRoot
from .tableaux import Tableau as Tableau

pass
from .rules import ClosingRule as ClosingRule

pass
from . import filters as filters
from . import helpers as helpers
from .writers import TabWriter as TabWriter
