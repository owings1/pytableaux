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
pytableaux.proof.helpers
------------------------
"""
from __future__ import annotations

from abc import abstractmethod
from collections import defaultdict, deque
from collections.abc import Set
from copy import copy
from functools import partial
from itertools import filterfalse
from types import MappingProxyType as MapProxy
from typing import (TYPE_CHECKING, Any, Callable, Iterator, Mapping,
                    NamedTuple, Sequence, TypeVar)

from ..errors import Emsg, check
from ..lang import Constant, Operator, Predicated, Sentence
from ..tools import EMPTY_SET, abcs, minfloor, wraps
from . import AccessNode, Branch, Node, Rule, Tableau, Target, filters
from .common import ClosureNode, QuitFlagNode, SentenceNode

if TYPE_CHECKING:
    from ..tools import TypeInstMap

_RT = TypeVar('_RT', bound=Rule)
_KT = TypeVar('_KT')
_VT = TypeVar('_VT')

__all__ = (
    'AdzHelper',
    'AplSentCount',
    'BranchTarget',
    'FilterHelper',
    'MaxConsts',
    'MaxWorlds',
    'NodeConsts',
    'NodeCount',
    'NodesWorlds',
    'PredNodes',
    'QuitFlag',
    'UnserialWorlds',
    'WorldIndex')

NOGET = object()

class AdzHelper(Rule.Helper):

    __slots__ = ('closure_rules')

    closure_rules: tuple[ClosingRule, ...]

    def __init__(self, rule, /):
        super().__init__(rule)
        self.closure_rules = self.tableau.rules.groups.get(
            'closure', EMPTY_SET)

    def _apply(self, target: Target):
        adds = target['adds']
        for i, nodes in enumerate(adds):
            if i == 0:
                continue
            branch = self.tableau.branch(target.branch)
            branch.extend(nodes)
            if self.rule.ticking:
                branch.tick(target.node)
        target.branch.extend(adds[0])
        if self.rule.ticking:
            target.branch.tick(target.node)

    def closure_score(self, target: Target):

        if not len(self.closure_rules):
            return 0.0
        close_count = 0
        branch = target.branch
        for nodes in target['adds']:
            # assert all(isinstance(node, Node) for node in nodes)
            # nodes = tuple(map(Node, nodes))
            for rule in self.closure_rules:
                if rule.nodes_will_close_branch(nodes, branch):
                    close_count += 1
                    break
        return close_count / min(1, len(target['adds']))


class BranchCache(Rule.HelperDict[Branch, _VT]):
    "Base class for caching per branch."

    valuetype: Callable[[], _VT] = bool

    def listen_on(self):
        super().listen_on()
        def after_branch_add(branch: Branch):
            if branch.parent:
                self[branch] = copy(self[branch.parent])
            else:
                self[branch] = self.valuetype()
        self.tableau.on({
            Tableau.Events.AFTER_BRANCH_ADD: after_branch_add,
            Tableau.Events.AFTER_BRANCH_CLOSE: self.__delitem__})

    def __repr__(self):
        info = self._reprdict()
        pstr = ' '.join(f'{k}:{v}' for k, v in info.items())
        return f'<{type(self).__name__} {pstr}>'

    def _reprdict(self):
        return dict(branches=len(self))

class BranchDictCache(BranchCache[dict[_KT, _VT]]):
    'Copies each K->V item for parent branch via copy(V).'

    valuetype = dict

    def listen_on(self):
        super().listen_on()
        def after_branch_add(branch: Branch):
            if branch.parent:
                for key in self[branch]:
                    self[branch][key] = copy(self[branch.parent][key])
        self.tableau.on(Tableau.Events.AFTER_BRANCH_ADD, after_branch_add)

class QuitFlag(BranchCache[bool]):
    """
    Track the application of a flag node by the rule for each branch. A branch
    is considered flagged when the target has a non-empty ``flag`` property.
    """
    valuetype = bool

    def listen_on(self):
        super().listen_on()
        def after_apply(target: Target):
            self[target.branch] = bool(target.get(Node.Key.flag))        
        self.rule.on(Rule.Events.AFTER_APPLY, after_apply)

class BranchValueHook(BranchCache[_VT]):
    """Check each node as it is added, until a (truthy) value is returned,
    then cache that value for the branch and stop checking nodes.

    Calls the rule's ``_branch_value_hook(node, branch)`` when a node is added to
    a branch. Any truthy return value is cached for the branch. Once a value
    is stored for a branch, no further nodes are checked.
    """
    __slots__ = ('hook')
    valuetype = type(None)
    hook_method_name = '_branch_value_hook'

    def __init__(self, rule, /):
        super().__init__(rule)
        self.hook = getattr(rule, self.hook_method_name)

    def listen_on(self):
        super().listen_on()
        def after_node_add(node, branch) -> None:
            if self[branch]:
                return
            res = self.hook(node, branch)
            if res:
                self[branch] = res
        self.tableau.on(Tableau.Events.AFTER_NODE_ADD, after_node_add)

    @classmethod
    def configure_rule(cls, rulecls, config):
        super().configure_rule(rulecls, config)
        hookname = cls.hook_method_name
        value = getattr(rulecls, hookname, None)
        if value is None:
            raise Emsg.MissingAttribute(hookname, rulecls)
        check.callable(value)

class BranchTarget(BranchValueHook[Target]):
    hook_method_name = '_branch_target_hook'

class AplSentCount(BranchCache[dict[tuple[Sentence, bool|None], int]]):
    """
    Count the times the rule has applied for a sentence (+/-) per branch. This tracks
    the `sentence` and `designated` properties of the rule's target.
    """
    valuetype = partial(defaultdict, int)

    def listen_on(self):
        super().listen_on()
        def after_apply(target: Target):
            if target.get(Node.Key.flag):
                return
            self[target.branch][target.sentence, target.designated] += 1
        self.rule.on(Rule.Events.AFTER_APPLY, after_apply)

class NodeCount(BranchCache[dict[Node, int]]):
    "Track the number of rule applications to each node."

    valuetype = partial(defaultdict, int)

    def listen_on(self):
        super().listen_on()
        def after_apply(target: Target):
            if target.get(Node.Key.flag):
                return            
            self[target.branch][target.node] += 1
        self.rule.on(Rule.Events.AFTER_APPLY, after_apply)

    def min(self, branch: Branch, /) -> int:
        """Count the minimum number of applications of any node on the branch.

        Args:
            branch (Branch): The branch

        Returns:
            int: The minimum number of applications
        """
        return minfloor(0, self[branch].values(), 0)

    def isleast(self, node: Node, branch: Branch, /):
        """Whether the node is one of the least-applied-to nodes on the branch.

        Args:
            node (Node): The node
            branch (Branch): The branch

        Returns:
            bool: Whether the node is a least-applied-to node
        """        
        return self.min(branch) >= self[branch][node]

class NodesWorlds(BranchCache[set[tuple[Node, int]]]):
    """
    Track the nodes applied to by the rule for each world on the branch. The
    target must have `node`, and `world` attributes. The values of the cache
    are ``(node, world)`` pairs.
    """
    valuetype = set

    def listen_on(self):
        super().listen_on()
        def after_apply(target: Target):
            if target.get(Node.Key.flag):
                return
            self[target.branch].add((target.node, target.world))
        self.rule.on(Rule.Events.AFTER_APPLY, after_apply)

class UnserialWorlds(BranchCache[set[int]]):
    "Track the unserial worlds on the branch."

    shareable = True
    valuetype = set

    def listen_on(self):
        super().listen_on()
        def after_node_add(node: Node, branch: Branch):
            for w in node.worlds():
                if node.get(Node.Key.world1) == w or branch.has({Node.Key.world1: w}):
                    self[branch].discard(w)
                else:
                    self[branch].add(w)
        self.tableau.on(Tableau.Events.AFTER_NODE_ADD, after_node_add)

class WorldIndex(BranchDictCache[int, set[int]]):
    'Index the visible worlds for each world on the branch.'

    shareable = True
    valuetype = partial(defaultdict, set)

    def listen_on(self):
        super().listen_on()
        def after_node_add(node: Node, branch: Branch):
            if not isinstance(node, AccessNode):
                return
            w1, w2 = node.pair()
            self[branch][w1].add(w2)
        self.tableau.on(Tableau.Events.AFTER_NODE_ADD, after_node_add)

    def has(self, branch: Branch, pair: tuple[int, int]) -> bool:
        """Whether w1 sees w2 on the given branch.

        Args:
            branch (Branch): The branch.
            pair (tuple[int, int]): The world pair (w1, w2).

        Returns:
            bool: Whether the access pair exists in the index.
        """
        return pair[1] in self[branch][pair[0]]

    def intransitives(self, branch: Branch, pair: tuple[int, int]) -> Iterator[int]:
        """Yield all the worlds on the branch that are visible to w2, but are
        not visible to w1.

        Args:
            branch (Branch): The branch.
            pair (tuple[int, int]): The world pair (w1, w2).

        Returns:
            Iterator[int]: The set of worlds.
        """
        access = self[branch]
        return filterfalse(access[pair[0]].__contains__, access[pair[1]])

class FilterNodeCache(BranchCache[set[Node]]):
    "Base class for caching nodes "

    valuetype = set

    config: FilterNodeCache.Config

    __slots__ = ('_garbage')

    @abstractmethod
    def __call__(self, node: Node, branch: Branch, /) -> bool:
        'Whether to add the node to the branch set.'
        if self.config.ignore_ticked and branch.is_ticked(node):
            return False
        return True

    def __init__(self, rule, /):
        super().__init__(rule)
        self._garbage = set()

    def release(self, node: Node, branch: Branch, /) -> None:
        """Mark the node/branch entry for garbage collection.

        Args:
            node (Node): The node
            branch (Branch): The branch
        """
        self._garbage.add((branch, node))

    def gc(self) -> None:
        """Run garbage collection. Remove entries queued by ``.release()``.
        
        This should be called before iterating over all nodes. It is called
        automatically by rules that use the ``@node_targets`` decorator.
        """
        if self._garbage:
            for branch, node in self._garbage:
                try:
                    self[branch].discard(node)
                except KeyError:
                    pass
            self._garbage.clear()

    def listen_on(self):
        super().listen_on()
        def after_node_add(node: Node, branch: Branch):
            if self(node, branch):
                self[branch].add(node)
        self.tableau.on(Tableau.Events.AFTER_NODE_ADD, after_node_add)
        if self.config.ignore_ticked:
            def after_node_tick(node: Node, branch: Branch):
                self[branch].discard(node)
            self.tableau.on(Tableau.Events.AFTER_NODE_TICK, after_node_tick)

    @classmethod
    def configure_rule(cls, rulecls, config):
        ":class:`Rule.Helper` init hook. Verify `ignore_ticked` attribute."
        super().configure_rule(rulecls, config)
        if not abcs.isabstract(rulecls):
            return __class__.Config(bool(rulecls.ignore_ticked))

    @classmethod
    def node_targets(cls, wrapped: Callable[[_RT, Node, Branch], Any], /):
        """
        Method decorator to only iterate through nodes matching the
        configured `FilterNodeCache` filters.
        """
        @wraps(wrapped)
        def wrapper(rule: _RT, branch: Branch, /):
            helper = rule[cls]
            helper.gc()
            for node in helper[branch]:
                for target in wrapped(rule, node, branch):
                    if isinstance(target, Target):
                        target.update(rule=rule, branch=branch, node=node)
                    else:
                        target = Target(target, rule=rule, branch=branch, node=node)
                    yield target
        return wrapper

    class Config(NamedTuple):
        ignore_ticked: bool
        """Whether to ignore and discard nodes after they are ticked."""


class PredNodes(FilterNodeCache):
    'Track all predicated nodes on the branch.'

    def __call__(self, node: Node, branch: Branch, /):
        return (
            super().__call__(node, branch) and
            type(self.rule.sentence(node)) is Predicated)

class FilterHelper(FilterNodeCache):
    """Set configurable and chainable filters in ``NodeFilters``
    class attribute.
    """

    config: FilterHelper.Config
    "The helper config with filters and pre-built predicate."

    def __call__(self, node: Node, branch: Branch, /) -> bool:
        """Whether the node passes the filter. If `ignore_ticked` is `True`,
        first checks whether the node is ticked, after which the combined
        filters predicate ``.pred()`` is checked.
        
        Args:
            node: The node
            branch: The branch

        Return:
            bool: Whether the node meets the filter conditions and
              `ignore_ticked` setting.
        """
        return (
            super().__call__(node, branch) and
            self.config.pred(node))

    def example_node(self) -> Node:
        """Construct an example node based on the filter conditions.
        
        Returns:
            dict: The node dict
        """
        node = {}
        for filt in self.config.filters.values():
            n = filt.example_node()
            if n is not None:
                node.update(n)
        if 'sentence' in node:
            w = node.get('world')
            if self.rule.modal and w is None:
                node['world'] = 0
            elif not self.rule.modal and w is not None:
                del(node['world'])
        return Node.for_mapping(node)

    def _reprdict(self) -> dict:
        return super()._reprdict() | dict(
            filters = '(%s) %s' % (len(self.config.filters),
                ','.join(map(str, self.config.filters))))

    @classmethod
    def configure_rule(cls, rulecls, config, **kw):
        """``Rule.Helper`` init hook.
        
        * Verify `NodeFilters`.
        * For non-abstract classes, merge `NodeFilters` and create config.
        """
        base_config = super().configure_rule(rulecls, config, **kw)
        configs = {}
        for relcls in abcs.mroiter(cls=rulecls, supcls=Rule, reverse=False):
            try:
                value = relcls.NodeFilters
            except AttributeError:
                continue
            if isinstance(value, type):
                value = value,
            if isinstance(value, Sequence):
                for filter_class in value:
                    configs.setdefault(filter_class, None)
            else:
                for filter_class, config in dict(value).items():
                    configs.setdefault(filter_class, config)
        for filter_class in configs:
            check.subcls(check.inst(filter_class, type), filters.CompareNode)
        if not abcs.isabstract(rulecls):
            rulecls.NodeFilters = configs
            return cls._build_config(rulecls, configs, base_config)

    @classmethod
    def _build_config(cls,
        rulecls: type[Rule],
        configs: Mapping[type[filters.CompareNode], Any],
        base_config: FilterHelper.Config, /) -> FilterHelper.Config:
        "Build the config"
        filter_classes = tuple(
            filter_class for filter_class, config in configs.items()
                if config is not NotImplemented)
        funcs = cls.PredTuple(filter_class(rulecls) for filter_class in filter_classes)
        return cls.Config(MapProxy(dict(zip(filter_classes, funcs))), funcs, *base_config)

    class Config(NamedTuple):
        filters: TypeInstMap[filters.CompareNode]
        "Mapping from ``NodeCompare`` class to instance."
        pred: FilterHelper.PredTuple
        "A single predicate of all filters."
        ignore_ticked: bool
        """Whether to ignore and discard nodes after they are ticked."""

    class PredTuple(tuple[Callable[[Node], bool]], Callable[[Node], bool]):
        "Callable tuple of predicate functions."

        __slots__ = EMPTY_SET

        def __call__(self, node: Node, /) -> bool:
            return all(func(node) for func in self)


class NodeConsts(BranchDictCache[Node, set[Constant]]):
    """Track the unapplied constants per branch for each potential node.
    The rule's target should have `branch`, `node` and `constant` properties.

    Only nodes that are applicable according to the rule's ``NodeCompare`` helper
    method are tracked.
    """

    valuetype = dict
    requires = {FilterHelper}

    filter: FilterHelper
    consts: NodeConsts.Consts

    __slots__ = ('consts', 'filter')

    def __init__(self, rule, /):
        super().__init__(rule)
        self.filter = self.rule[FilterHelper]
        self.consts = self.Consts(rule)

    def listen_on(self):
        super().listen_on()

        def after_apply(target: Target):
            if target.get(Node.Key.flag):
                return
            self[target.branch][target.node].discard(target.constant)

        def after_node_add(node: Node, branch: Branch):
            if self.filter(node, branch) and node not in self[branch]:
                # By tracking per node, we are tracking per world, a fortiori.
                self[branch][node] = self.consts[branch].copy()
            try:
                s = node['sentence']
            except KeyError:
                return
            consts = s.constants - self.consts[branch]
            if len(consts):
                for node, base in self[branch].items():
                    base.update(consts)
                self.consts[branch].update(consts)
    
        self.rule.on(Rule.Events.AFTER_APPLY, after_apply)
        self.tableau.on(Tableau.Events.AFTER_NODE_ADD, after_node_add)

    class Consts(BranchCache[set[Constant]]):
        valuetype = set

class WorldConsts(BranchDictCache[int, set[Constant]]):
    """
    Track the constants appearing at each world.
    """
    shareable = True
    valuetype = partial(defaultdict, set)

    def listen_on(self):
        super().listen_on()
        def after_node_add(node: Node, branch: Branch):
            try:
                s = node['sentence']
            except KeyError:
                return
            world = node.get(Node.Key.world)
            if world is None:
                world = 0
            self[branch][world].update(s.constants)
        self.tableau.on(Tableau.Events.AFTER_NODE_ADD, after_node_add)

class MaxConsts(Rule.HelperDict[Branch, int]):
    """
    Project the maximum number of constants per world required for each branch
    by examining the branches after the trunk is built.
    """

    shareable = True
    requires = {WorldConsts}

    wconsts: WorldConsts

    __slots__ = ('wconsts')

    def __init__(self, rule, /):
        super().__init__(rule)
        self.wconsts = WorldConsts(self.rule)

    def listen_on(self):
        super().listen_on()
        def after_trunk_build(tableau: Tableau):
            for branch in tableau:
                origin = branch.origin
                if origin in self:
                    raise NotImplementedError('Multiple trunk branches not implemented.')
                self[origin] = self._compute(branch)
        self.tableau.on(Tableau.Events.AFTER_TRUNK_BUILD, after_trunk_build)

    def is_reached(self, branch: Branch, world: int = 0, /) -> bool:
        """
        Whether we have already reached or exceeded the max number of constants
        projected for the branch (origin) at the given world.

        Args:
            branch (Branch): The branch
            world (int): The world. Defaults to 0.
        
        Returns
            bool: Whether the limit is reached for the branch and world.
        """
        if world is None:
            world = 0
        return len(self.wconsts[branch][world]) >= self.get(branch.origin, 1)

    def is_exceeded(self, branch: Branch, world: int = 0, /) -> bool:
        """
        Whether we have exceeded the max number of constants projected for
        the branch (origin) at the given world.

        Args:
            branch (Branch): The branch
            world (int): The world. Defaults to 0.
        
        Returns:
            bool: Whether constants are exceeded
        """
        if world is None:
            world = 0
        return len(self.wconsts[branch][world]) > self.get(branch.origin, 1)

    def quit_flag(self, branch: Branch, /) -> QuitFlagNode:
        """
        Generate a quit flag node for the branch.

        Args:
            branch (Branch): The branch

        Returns:
            QuitFlagNode: A QuitFlagNode with the following keys:
                - *is_flag*: ``True``
                - *flag*: ``'quit'``
                - *info*: ``'RuleName:MaxConstants(n)'`` where *RuleName* is
                    ``rule.name``, and ``n`` is the computed max allowed
                    constants for the branch.
        """
        return QuitFlagNode(Node.PropMap.QuitFlag | {Node.Key.info: (
            f'{self.rule.name}:{type(self).__name__}'
            f'({self.get(branch.origin, 1)})')})

    def _compute(self, branch: Branch, /) -> int:
        """
        Project the maximum number of constants for a branch (origin) as
        the number of constants already on the branch (min 1) * the number of
        quantifiers (min 1) + 1.

        Args:
            branch (Branch): The branch
        
        Returns:
            int: The max constants
        """
        needed = sum(map(self._compute_node, branch))
        return max(1, len(branch.constants)) * max(1, needed) + 1

    def _compute_node(self, node: Node,/) -> int:
        try:
            return len(node['sentence'].quantifiers)
        except KeyError:
            return 0

class MaxWorlds(Rule.HelperDict[Branch, int]):
    """Project the maximum number of worlds required for each branch by examining
    the branches after the trunk is built.
    """

    shareable = True

    config: MaxWorlds.Config
    modals: MaxWorlds.ModalsCounts

    __slots__ = ('modals')

    def __init__(self, rule: Rule,/):
        super().__init__(rule)
        self.modals = self.ModalsCounts(self.config)

    def listen_on(self):
        super().listen_on()
        def after_trunk_build(tableau: Tableau):
            for branch in tableau:
                origin = branch.origin
                # For normal logics, we will have only one trunk branch.
                if origin in self:
                    raise NotImplementedError('Multiple trunk branches not implemented.')
                self[origin] = self._compute(branch)
        self.tableau.on(Tableau.Events.AFTER_TRUNK_BUILD, after_trunk_build)

    def is_reached(self, branch: Branch, /) -> bool:
        """
        Whether we have already reached or exceeded the max number of worlds
        projected for the branch (origin).

        Args:
            branch (Branch): The branch

        Returns:
            bool: Whether max constants are reached
        """
        origin = branch.origin
        return origin in self and len(branch.worlds) >= self[origin]

    def is_exceeded(self, branch: Branch, /) -> bool:
        """
        Whether we have exceeded the max number of worlds projected for the
        branch (origin).

        Args:
            branch (Branch): The branch

        Returns:
            bool: Whether max constants are exceeded
        """
        origin = branch.origin
        return origin in self and len(branch.worlds) > self[origin]

    def quit_flag(self, branch: Branch, /) -> QuitFlagNode:
        """
        Generate a quit flag node for the branch.

        Args:
            branch (Branch): The branch

        Returns:
            QuitFlagNode: A QuitFlagNode with the following keys:
                - *is_flag*: ``True``
                - *flag*: ``'quit'``
                - *info*: ``'RuleName:MaxWorlds(n)'`` where *RuleName* is
                    ``rule.name``, and ``n`` is the computed max allowed
                    worlds for the branch.
        """
        return QuitFlagNode(Node.PropMap.QuitFlag | {Node.Key.info: (
            f'{self.rule.name}:{type(self).__name__}({self.get(branch.origin)})')})

    def _compute(self, branch: Branch, /) -> int:
        """Project the maximum number of worlds for a branch (origin) as
        the number of worlds already on the branch + the number of modal
        operators + 1.
        """
        return 1 + len(branch.worlds) + sum(
            map(self.modals.__getitem__, (
                node['sentence']
                for node in filterfalse(branch.is_ticked, branch)
                    if isinstance(node, SentenceNode))))

    @classmethod
    def configure_rule(cls, rulecls, config):
        "``Rule.Helper`` init hook. Set the `modal_operators` attribute."
        super().configure_rule(rulecls, config)
        try:
            return cls.Config(rulecls.Meta.modal_operators)
        except AttributeError as err:
            raise Emsg.MissingAttribute(str(err))

    class Config(NamedTuple):
        operators: Set[Operator]

    class ModalsCounts(dict[Sentence, int]):
        """
        Compute and cache the modal complexity of a sentence by counting its
        modal operators.
        """

        filter: Callable[[Operator], bool]

        __slots__ = ('filter')

        def __init__(self, config: MaxWorlds.Config):
            self.filter = config.operators.__contains__

        def __missing__(self, s: Sentence):
            return self.setdefault(s, sum(map(self.filter, s.operators)))

class EllipsisExampleHelper(Rule.Helper):
    "Documentation helper for inserting ellipsis"

    closenodes: list[Node]
    applied: set[Branch]
    isclosure: bool
    istrunk: bool
    mynode = Node.PropMap.Ellipsis

    __slots__ = ('closenodes', 'applied', 'isclosure', 'istrunk')

    def __init__(self, rule: Rule,/):
        super().__init__(rule)
        self.applied = set()
        self.isclosure = isinstance(rule, ClosingRule)
        if self.isclosure:
            self.closenodes = list(
                dict(n)
                for n in reversed(deque(rule.example_nodes())))
        else:
            self.closenodes = []
        self.istrunk = False

    def listen_on(self):
        super().listen_on()

        def before_trunk_build(*_):
            self.istrunk = True

        def after_trunk_build(*_):
            self.istrunk = False

        def after_branch_add(branch: Branch):
            if self.applied:
                return
            if len(self.closenodes) == 1:
                self.add_node(branch)        

        def after_node_add(node: Node, branch: Branch):
            if self.applied:
                return
            if node.meets(self.mynode) or isinstance(node, ClosureNode):
                return
            if self.istrunk:
                self.add_node(branch)
            elif self.closenodes and node.meets(self.closenodes[-1]):
                self.closenodes.pop()
                if len(self.closenodes) == 1:
                    self.add_node(branch)

        def before_apply(target: Target):
            if self.applied:
                return
            if self.isclosure:
                return
            self.add_node(target.branch)
        self.tableau.on({
            Tableau.Events.BEFORE_TRUNK_BUILD : before_trunk_build,
            Tableau.Events.AFTER_TRUNK_BUILD  : after_trunk_build,
            Tableau.Events.AFTER_BRANCH_ADD   : after_branch_add,
            Tableau.Events.AFTER_NODE_ADD     : after_node_add})
        self.rule.on(Rule.Events.BEFORE_APPLY, before_apply)

    def add_node(self, branch: Branch):
        self.applied.add(branch)
        branch.append(self.mynode)

from .rules import ClosingRule
