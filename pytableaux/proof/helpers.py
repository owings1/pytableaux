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
from collections.abc import Set
from copy import copy
from itertools import filterfalse
from types import MappingProxyType as MapProxy
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence, TypeVar

from ..errors import Emsg, check
from ..lang import Constant, Operator, Predicated, Sentence
from ..tools import EMPTY_MAP, EMPTY_SET, abcs, minfloor, wraps
from . import Branch, Node, Rule, Tableau, Target, WorldPair, filters
from .common import QuitFlagNode
from .filters import NodeCompare

if TYPE_CHECKING:
    from ..tools import TypeInstMap
    from .rules import ClosingRule

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

    __slots__ = ('rule', 'config', 'closure_rules')

    closure_rules: tuple[ClosingRule, ...]

    def __init__(self, rule, /):
        super().__init__(rule)
        self.closure_rules = self.rule.tableau.rules.groups.get(
            'closure', EMPTY_SET)

    def _apply(self, target: Target):
        adds = target['adds']
        for i, nodes in enumerate(adds):
            if i == 0:
                continue
            branch = self.rule.branch(target.branch)
            branch.extend(nodes)
            if self.rule.ticking:
                branch.tick(target.node)
        target.branch.extend(adds[0])
        if self.rule.ticking:
            target.branch.tick(target.node)

    def closure_score(self, target: Target):
        rules = self.closure_rules
        if not len(rules):
            return 0.0
        close_count = 0
        branch = target.branch
        for nodes in target['adds']:
            # assert all(isinstance(node, Node) for node in nodes)
            # nodes = tuple(map(Node, nodes))
            for rule in rules:
                if rule.nodes_will_close_branch(nodes, branch):
                    close_count += 1
                    break
        return close_count / min(1, len(target['adds']))

class BranchCache(dict[Branch, _VT], Rule.Helper):
    "Base class for caching per branch."

    __slots__ = ('rule', 'config')
    _valuetype: type[_VT] = bool

    __init__ = Rule.Helper.__init__

    def listen_on(self):
        super().listen_on()
        def after_branch_add(branch: Branch):
            if branch.parent:
                self[branch] = copy(self[branch.parent])
            else:
                self[branch] = self._empty_value(branch)
        self.rule.tableau.on({
            Tableau.Events.AFTER_BRANCH_ADD: after_branch_add,
            Tableau.Events.AFTER_BRANCH_CLOSE: self.__delitem__})

    def __repr__(self):
        info = self._reprdict()
        pstr = ' '.join(f'{k}:{v}' for k, v in info.items())
        return f'<{type(self).__name__} {pstr}>'

    def _reprdict(self):
        return dict(branches = len(self))

    @classmethod
    def _empty_value(cls, branch,/):
        'Override, for example, if the value type takes arguments.'
        return cls._valuetype()

class BranchDictCache(BranchCache[dict[_KT, _VT]]):
    'Copies each K->V item for parent branch via copy(V).'
    __slots__ = EMPTY_SET
    _valuetype = dict

    def listen_on(self):
        super().listen_on()
        def after_branch_add(branch: Branch):
            if branch.parent:
                for key in self[branch]:
                    self[branch][key] = copy(self[branch.parent][key])
        self.rule.tableau.on(Tableau.Events.AFTER_BRANCH_ADD, after_branch_add)

class QuitFlag(BranchCache[bool]):
    """
    Track the application of a flag node by the rule for each branch. A branch
    is considered flagged when the target has a non-empty ``flag`` property.
    """
    __slots__ = EMPTY_SET
    _valuetype = bool

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
    is stored for a branch, no further nodes are check.
    """
    __slots__ = ('hook',)
    _valuetype = type(None)
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
        self.rule.tableau.on(Tableau.Events.AFTER_NODE_ADD, after_node_add)

    @classmethod
    def configure_rule(cls, rulecls, config, **kw):
        super().configure_rule(rulecls, config, **kw)
        hookname = cls.hook_method_name
        value = getattr(rulecls, hookname, None)
        if value is None:
            raise Emsg.MissingAttribute(hookname, rulecls)
        check.callable(value)

class BranchTarget(BranchValueHook[Target]):
    __slots__ = EMPTY_SET
    hook_method_name = '_branch_target_hook'

class AplSentCount(BranchCache[dict[Sentence, int]]):
    """
    Count the times the rule has applied for a sentence per branch. This tracks
    the `sentence` property of the rule's target. The target should also include
    the `branch` key.
    """
    __slots__ = EMPTY_SET
    _valuetype = dict

    def listen_on(self):
        super().listen_on()
        def after_apply(target: Target):
            if target.get(Node.Key.flag):
                return
            counts = self[target.branch]
            sentence = target.sentence
            counts[sentence] = counts.get(sentence, 0) + 1
        self.rule.on(Rule.Events.AFTER_APPLY, after_apply)

class NodeCount(BranchCache[dict[Node, int]]):
    "Track the number of rule applications to each node."

    __slots__ = EMPTY_SET
    _valuetype = dict

    def listen_on(self):
        super().listen_on()
        def after_apply(target: Target):
            if target.get(Node.Key.flag):
                return
            counts = self[target.branch]
            node = target.node
            counts[node] = counts.get(node, 0) + 1
        self.rule.on(Rule.Events.AFTER_APPLY, after_apply)

    def min(self, branch: Branch) -> int:
        """Count the minimum number of applications of any node on the branch.

        Args:
            branch (Branch): The branch

        Returns:
            int: The minimum number of applications
        """        
        if branch in self and len(self[branch]):
            return minfloor(0, self[branch].values())
        return 0

    def isleast(self, node, branch, /):
        """Whether the node is one of the least-applied-to nodes on the branch.

        Args:
            node (Node): The node
            branch (Branch): The branch

        Returns:
            bool: Whether the node is a least node
        """        
        return self.min(branch) >= self[branch].get(node, 0)

class NodesWorlds(BranchCache[set[tuple[Node, int]]]):
    """
    Track the nodes applied to by the rule for each world on the branch. The
    target must have `node`, and `world` attributes. The values of the cache
    are ``(node, world)`` pairs.
    """
    __slots__ = EMPTY_SET
    _valuetype = set

    def listen_on(self):
        super().listen_on()
        def after_apply(target: Target):
            if target.get(Node.Key.flag):
                return
            self[target.branch].add((target.node, target.world))
        self.rule.on(Rule.Events.AFTER_APPLY, after_apply)

class UnserialWorlds(BranchCache[set[int]]):
    "Track the unserial worlds on the branch."

    __slots__ = EMPTY_SET
    _valuetype = set

    def listen_on(self):
        super().listen_on()
        def after_node_add(node: Node, branch: Branch):
            for w in node.worlds:
                if node.get(Node.Key.w1) == w or branch.has({Node.Key.w1: w}):
                    self[branch].discard(w)
                else:
                    self[branch].add(w)
        self.rule.tableau.on(Tableau.Events.AFTER_NODE_ADD, after_node_add)

class WorldIndex(BranchDictCache[int, set[int]]):
    'Index the visible worlds for each world on the branch.'

    __slots__ = ('nodes',)

    class Nodes(BranchCache[dict[WorldPair, Node]]):
        __slots__ = EMPTY_SET
        _valuetype = dict

        def add(self, node: Node, branch: Branch):
            self[branch][WorldPair.fornode(node)] = node

    def __init__(self, rule, /):
        super().__init__(rule)
        self.nodes = self.Nodes(rule)

    def listen_on(self):
        super().listen_on()
        def after_node_add(node: Node, branch: Branch):
            if node.is_access:
                w1, w2 = WorldPair.fornode(node)
                if w1 not in self[branch]:
                    self[branch][w1] = set()
                self[branch][w1].add(w2)
                self.nodes.add(node, branch)
        self.rule.tableau.on(Tableau.Events.AFTER_NODE_ADD, after_node_add)

    def has(self, branch, access):
        'Whether w1 sees w2 on the given branch.'
        return access[1] in self[branch].get(access[0], EMPTY_SET)

    def intransitives(self, branch: Branch, w1: int, w2: int) -> set[int]:
        """Get all the worlds on the branch that are visible to w2, but are not
        visible to w1.

        Args:
            branch (Branch): The branch.
            w1 (int): World 1.
            w2 (int): World 2.

        Returns:
            set[int]: The set of worlds.
        """
        # TODO: can we make this more efficient? for each world pair,
        #       track the intransitives?
        return self[branch].get(w2, EMPTY_SET) - self[branch].get(w1, EMPTY_SET)

class FilterNodeCache(BranchCache[set[Node]]):
    "Base class for caching nodes "

    __slots__ = ('ignore_ticked', '_garbage')
    _valuetype = set

    #: Copied from Rule.ignore_ticked - whether to discard nodes
    #: after they are ticked.
    ignore_ticked: bool

    @abstractmethod
    def __call__(self, node, branch, /) -> bool:
        'Whether to add the node to the branch set.'
        return False

    def __init__(self, rule, /):
        self.ignore_ticked = bool(rule.ignore_ticked)
        super().__init__(rule)
        self._garbage = set()

    def release(self, node, branch, /) -> None:
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
        def after_node_add(node, branch):
            if self(node, branch):
                self[branch].add(node)
        self.rule.tableau.on(Tableau.Events.AFTER_NODE_ADD, after_node_add)
        if self.ignore_ticked:
            def after_node_tick(node, branch):
                self[branch].discard(node)
            self.rule.tableau.on(Tableau.Events.AFTER_NODE_TICK, after_node_tick)

    @classmethod
    def configure_rule(cls, rulecls, config, **kw):
        "``Rule.Helper`` init hook. Verify `ignore_ticked` attribute."
        super().configure_rule(rulecls, config, **kw)
        if not abcs.isabstract(rulecls):
            try:
                rulecls.ignore_ticked
            except AttributeError:
                raise Emsg.MissingAttribute('ignore_ticked')

    @classmethod
    def node_targets(cls, source_fn, /):
        """
        Method decorator to only iterate through nodes matching the
        configured `FilterNodeCache` filters.
        """
        @wraps(source_fn)
        def wrapped(rule: Rule, branch, /):
            helper = rule[cls]
            helper.gc()
            for node in helper[branch]:
                for target in source_fn(rule, node, branch):
                    if isinstance(target, Target):
                        target.update(rule=rule, branch=branch, node=node)
                    else:
                        target = Target(target, rule=rule, branch=branch, node=node)
                    yield target
        return wrapped


class PredNodes(FilterNodeCache):
    'Track all predicated nodes on the branch.'
    __slots__ = EMPTY_SET

    def __call__(self, node: Node, _):
        return type(self.rule.sentence(node)) is Predicated

class FilterHelper(FilterNodeCache):
    """Set configurable and chainable filters in ``NodeFilters``
    class attribute.
    """
    __slots__ = ('filters', 'pred')

    filters: TypeInstMap[NodeCompare]
    "Mapping from ``NodeCompare`` class to instance."

    pred: Callable
    """A single predicate of all filters. To also check the `ignore_ticked`
    setting, use ``.filter()``.
    """

    def __init__(self, rule, /):
        super().__init__(rule)
        self.filters, self.pred = self.config

    def filter(self, node, branch: Branch, /):
        """Whether the node passes the filter. If `ignore_ticked` is `True`,
        first checks whether the node is ticked, after which the combined
        filters predicate ``.pred()`` is checked.
        
        Args:
            node: The node
            branch: The branch

        Return:
            bool: Whether the node meets the filter conditions and `ignore_ticked`
            setting.
        """
        if self.ignore_ticked and branch.is_ticked(node):
            return False
        return self.pred(node)

    __call__ = filter

    def example_node(self):
        """Construct an example node based on the filter conditions.
        
        Returns:
            dict: The node dict
        """
        node = {}
        for filt in self.filters.values():
            n = filt.example_node()
            if n is not None:
                node.update(n)
        return node

    def _reprdict(self) -> dict:
        return super()._reprdict() | dict(
            filters = '(%s) %s' % (len(self.filters),
                ','.join(map(str, self.filters.keys()))))

    @classmethod
    def configure_rule(cls, rulecls, config, **kw):
        """``Rule.Helper`` init hook.
        
        * Verify `NodeFilters`.
        * For non-abstract classes, merge `NodeFilters` and create config.
        """
        super().configure_rule(rulecls, config, **kw)
        attr = 'NodeFilters'
        configs = {}
        for relcls in abcs.mroiter(cls = rulecls, supcls = Rule, reverse = False):
            v = getattr(relcls, attr, EMPTY_MAP)
            if isinstance(v, Sequence):
                for fcls in v:
                    configs.setdefault(fcls, None)
            else:
                for fcls, flag in dict(v).items():
                    configs.setdefault(fcls, flag)
        for fcls in configs:
            check.subcls(check.inst(fcls, type), filters.NodeCompare)
        if not abcs.isabstract(rulecls):
            setattr(rulecls, attr, configs)
            if not configs:
                import warnings
                warnings.warn(f"EMPTY '{attr}' attribute for {rulecls}. "
                    "All nodes will be cached.")
            return cls._build_config(rulecls)

    @staticmethod
    def _build_config(rulecls,/):
        configs: Mapping = rulecls.NodeFilters
        types = tuple(fcls for fcls, flag in configs.items()
            if flag is not NotImplemented)
        filters = MapProxy(dict(zip(
            types, funcs := tuple(ftype(rulecls) for ftype in types))))
        def pred(node, /):
            return all(f(node) for f in funcs)
        return filters, pred

class NodeConsts(BranchDictCache[Node, set[Constant]]):
    """Track the unapplied constants per branch for each potential node.
    The rule's target should have `branch`, `node` and `constant` properties.

    Only nodes that are applicable according to the rule's ``NodeCompare`` helper.
    method are tracked.
    """

    __slots__ = ('consts', 'filter')
    _valuetype = dict

    class Consts(BranchCache[set[Constant]]):
        __slots__ = EMPTY_SET
        _valuetype = set

    consts: NodeConsts.Consts # type: ignore

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

        def after_node_add(node: Node, branch):
            if self.filter(node, branch):
                if node not in self[branch]:
                    # By tracking per node, we are tracking per world, a fortiori.
                    self[branch][node] = self.consts[branch].copy()
            s = node.get(Node.Key.sentence)
            if s is None:
                return
            consts = s.constants - self.consts[branch]
            if len(consts):
                for node in self[branch]:
                    self[branch][node].update(consts)
                self.consts[branch].update(consts)
    
        self.rule.on(Rule.Events.AFTER_APPLY, after_apply)
        self.rule.tableau.on(Tableau.Events.AFTER_NODE_ADD, after_node_add)

class WorldConsts(BranchDictCache[int, set[Constant]]):
    """
    Track the constants appearing at each world.
    """

    __slots__ = EMPTY_SET

    def listen_on(self):
        super().listen_on()
        def after_node_add(node: Node, branch: Branch):
            s = node.get(Node.Key.sentence)
            if s is None:
                return
            world = node.get(Node.Key.world)
            if world is None:
                world = 0
            if world not in self[branch]:
                self[branch][world] = set()
            self[branch][world].update(s.constants)
        self.rule.tableau.on(Tableau.Events.AFTER_NODE_ADD, after_node_add)

class MaxConsts(dict[Branch, int], Rule.Helper):
    """
    Project the maximum number of constants per world required for each branch
    by examining the branches after the trunk is built.
    """

    __slots__ = ('rule', 'config', 'wconsts')

    def __init__(self, rule, /):
        Rule.Helper.__init__(self, rule)
        self.wconsts = WorldConsts(self.rule)

    def listen_on(self):
        def after_trunk_build(tableau: Tableau):
            for branch in tableau:
                origin = branch.origin
                if origin in self:
                    raise NotImplementedError('Multiple trunk branches not implemented.')
                self[origin] = self._compute(branch)
        self.rule.tableau.on(Tableau.Events.AFTER_TRUNK_BUILD, after_trunk_build)

    def is_reached(self, branch: Branch, world = 0, /):
        """
        Whether we have already reached or exceeded the max number of constants
        projected for the branch (origin) at the given world.

        Args:
            branch (Branch): The branch
            world (int): The world. Defaults to 0.
        """
        if world is None:
            world = 0
        return len(self.wconsts[branch][world]) >= self.get(branch.origin, 1)

    def is_exceeded(self, branch: Branch, world = 0, /):
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

    def quit_flag(self, branch: Branch, /):
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
        s = node.get(Node.Key.sentence)
        return len(s.quantifiers) if s else 0

class MaxWorlds(BranchDictCache[Branch, int]):
    """Project the maximum number of worlds required for each branch by examining
    the branches after the trunk is built.
    """

    __slots__ = ('rule', 'config', 'modals')

    class Modals(dict[Sentence, int]):
        """
        Compute and cache the modal complexity of a sentence by counting its
        modal operators.
        """

        __slots__ = ('filter',)

        def __init__(self, operators: Set[Operator]):
            self.filter = operators.__contains__

        def __missing__(self, s: Sentence):
            return self.setdefault(s, sum(map(self.filter, s.operators)))

    def __init__(self, rule: Rule,/):
        super().__init__(rule)
        self.modals = self.Modals(self.rule.modal_operators)

    def listen_on(self):
        def after_trunk_build(tableau: Tableau):
            for branch in tableau:
                origin = branch.origin
                # For normal logics, we will have only one trunk branch.
                if origin in self:
                    raise NotImplementedError('Multiple trunk branches not implemented.')
                self[origin] = self._compute(branch)
        self.rule.tableau.on(Tableau.Events.AFTER_TRUNK_BUILD, after_trunk_build)

    def is_reached(self, branch: Branch, /):
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

    def is_exceeded(self, branch: Branch, /):
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

    def quit_flag(self, branch: Branch, /) -> dict[str, Any]:
        """
        Generate a quit flag node for the branch.

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
        # Project the maximum number of worlds for a branch (origin) as
        # the number of worlds already on the branch + the number of modal
        # operators + 1.
        return 1 + len(branch.worlds) + sum(
            map(self.modals.__getitem__, (
                node[Node.Key.sentence]
                for node in filterfalse(branch.is_ticked, branch)
                    if Node.Key.sentence in node)))

    @classmethod
    def configure_rule(cls, rulecls, config, **kw):
        "``Rule.Helper`` init hook. Set the `modal_operators` attribute."
        super().configure_rule(rulecls, config, **kw)
        try:
            ops = rulecls.modal_operators
        except AttributeError as err:
            raise Emsg.MissingAttribute(str(err))
        else:
            check.inst(ops, Set)
