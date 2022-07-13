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
pytableaux.proof.helpers
------------------------
"""
from __future__ import annotations

from abc import abstractmethod as abstract
from collections.abc import Set
from copy import copy
from itertools import filterfalse
from types import MappingProxyType as MapProxy
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence, TypeVar

from pytableaux.errors import Emsg, check
from pytableaux.lang import Constant, Operator, Predicated, Sentence
from pytableaux.proof import (Access, Branch, Node, NodeAttr, PropMap, Rule, RuleAttr, RuleEvent,
                              RuleHelper, TabEvent, Tableau, Target, filters)
from pytableaux.tools import (EMPTY_MAP, EMPTY_SET, abcs, closure, minfloor,
                              wraps)

if TYPE_CHECKING:
    from pytableaux.proof.rules import ClosingRule

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
    'WorldIndex',
)

NOGET = object()

class AdzHelper(RuleHelper):

    __slots__ = ('rule', 'config', 'closure_rules')

    closure_rules: tuple[ClosingRule, ...]

    def __init__(self, rule, /):
        super().__init__(rule)
        self.closure_rules = self.rule.tableau.rules.groups.get('closure', EMPTY_SET)

    def _apply(self, target: Target):
        branch = target.branch
        adds = target['adds']
        for i, nodes in enumerate(adds):
            if i == 0:
                continue
            b = self.rule.branch(branch)
            b.extend(nodes)
            if self.rule.ticking:
                b.tick(target.node)
        branch.extend(adds[0])
        if self.rule.ticking:
            branch.tick(target.node)

    def closure_score(self, target: Target):
        rules = self.closure_rules
        if not len(rules):
            return 0.0
        close_count = 0
        branch = target.branch
        for nodes in target['adds']:
            # nodes = tuple(map(Node, nodes))
            for rule in rules:
                if rule.nodes_will_close_branch(nodes, branch):
                    close_count += 1
                    break
        return close_count / min(1, len(target['adds']))

class BranchCache(dict[Branch, _VT], RuleHelper):
    "Base class for caching per branch."

    __slots__ = ('rule', 'config')
    _valuetype: type[_VT] = bool

    __init__ = RuleHelper.__init__

    def listen_on(self):
        self.rule.tableau.on({
            TabEvent.AFTER_BRANCH_ADD: self.__after_branch_add,
            TabEvent.AFTER_BRANCH_CLOSE: self.__after_branch_close,
        })

    def listen_off(self):
        self.rule.tableau.off({
            TabEvent.AFTER_BRANCH_ADD: self.__after_branch_add,
            TabEvent.AFTER_BRANCH_CLOSE: self.__after_branch_close,
        })

    def __after_branch_add(self, branch: Branch):
        # Event: TabEvent.AFTER_BRANCH_ADD
        if branch.parent:
            self[branch] = copy(self[branch.parent])
        else:
            self[branch] = self._empty_value(branch)

    def __after_branch_close(self, branch,/):
        # Event: TabEvent.AFTER_BRANCH_CLOSE
        del self[branch]

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
        self.rule.tableau.on(TabEvent.AFTER_BRANCH_ADD, self.__after_branch_add)

    def listen_off(self):
        self.rule.tableau.off(TabEvent.AFTER_BRANCH_ADD, self.__after_branch_add)
        super().listen_off()

    def __after_branch_add(self, branch: Branch, /):
        # Event: TabEvent.AFTER_BRANCH_ADD
        if branch.parent is not None:
            for key in self[branch]:
                self[branch][key] = copy(self[branch.parent][key])

class QuitFlag(BranchCache[bool]):
    """
    Track the application of a flag node by the rule for each branch. A branch
    is considered flagged when the target has a non-empty ``flag`` property.
    """
    __slots__ = EMPTY_SET
    _valuetype = bool

    def listen_on(self):
        super().listen_on()
        self.rule.on(RuleEvent.AFTER_APPLY, self.__after_apply)

    def listen_off(self):
        self.rule.off(RuleEvent.AFTER_APPLY, self.__after_apply)
        super().listen_off()

    def __after_apply(self, target: Target, /):
        # Event: RuleEvent.AFTER_APPLY
        self[target.branch] = bool(target.get(NodeAttr.flag))

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
        self.rule.tableau.on(TabEvent.AFTER_NODE_ADD, self.__after_node_add)

    def listen_off(self):
        self.rule.tableau.off(TabEvent.AFTER_NODE_ADD, self.__after_node_add)
        super().listen_off()

    def __after_node_add(self, node, branch, /) -> None:
        # Event: TabEvent.AFTER_NODE_ADD
        if self[branch]:
            return
        res = self.hook(node, branch)
        if res:
            self[branch] = res

    @classmethod
    def configure_rule(cls, rulecls, config, **kw):
        super().configure_rule(rulecls, config, **kw)
        hookname = cls.hook_method_name
        value = getattr(rulecls, hookname, None)
        if value is None:
            raise Emsg.MissingAttribute(hookname, rulecls)
        check.callable(value)

class BranchTarget(BranchValueHook[Target]):
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
        self.rule.on(RuleEvent.AFTER_APPLY, self.__after_apply)

    def listen_off(self):
        self.rule.off(RuleEvent.AFTER_APPLY, self.__after_apply)
        super().listen_off()

    def __after_apply(self, target: Target):
        # Event: RuleEvent.AFTER_APPLY
        if target.get(NodeAttr.flag):
            return
        counts = self[target.branch]
        sentence = target.sentence
        counts[sentence] = counts.get(sentence, 0) + 1

class NodeCount(BranchCache[dict[Node, int]]):
    "Track the number of rule applications to each node."

    __slots__ = EMPTY_SET
    _valuetype = dict

    def listen_on(self):
        super().listen_on()
        self.rule.on(RuleEvent.AFTER_APPLY, self.__after_apply)

    def listen_off(self):
        self.rule.off(RuleEvent.AFTER_APPLY, self.__after_apply)
        super().listen_off()

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

    def __after_apply(self, target: Target, /):
        # Event: RuleEvent.AFTER_APPLY
        if target.get(NodeAttr.flag):
            return
        counts = self[target.branch]
        node = target.node
        counts[node] = counts.get(node, 0) + 1

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
        self.rule.on(RuleEvent.AFTER_APPLY, self.__after_apply)

    def listen_off(self):
        self.rule.off(RuleEvent.AFTER_APPLY, self.__after_apply)
        super().listen_off()

    def __after_apply(self, target: Target, /):
        # Event: RuleEvent.AFTER_APPLY
        if target.get(NodeAttr.flag):
            return
        self[target.branch].add((target.node, target.world))

class UnserialWorlds(BranchCache[set[int]]):
    "Track the unserial worlds on the branch."

    __slots__ = EMPTY_SET
    _valuetype = set

    def listen_on(self):
        super().listen_on()
        self.rule.tableau.on(TabEvent.AFTER_NODE_ADD, self.__after_node_add)

    def listen_off(self):
        self.rule.tableau.off(TabEvent.AFTER_NODE_ADD, self.__after_node_add)
        super().listen_off()

    def __after_node_add(self, node: Node, branch: Branch, /):
        # Event: TabEvent.AFTER_NODE_ADD
        for w in node.worlds:
            if node.get(NodeAttr.w1) == w or branch.has({NodeAttr.w1: w}):
                self[branch].discard(w)
            else:
                self[branch].add(w)

class WorldIndex(BranchDictCache[int, set[int]]):
    'Index the visible worlds for each world on the branch.'

    __slots__ = ('nodes',)

    class Nodes(BranchCache[dict[Access, Node]]):
        __slots__ = EMPTY_SET
        _valuetype = dict

        def add(self, node: Node, branch: Branch):
            self[branch][Access.fornode(node)] = node

    def __init__(self, rule, /):
        super().__init__(rule)
        self.nodes = self.Nodes(rule)

    def listen_on(self):
        super().listen_on()
        self.rule.tableau.on(TabEvent.AFTER_NODE_ADD, self.__after_node_add)

    def listen_off(self):
        self.rule.tableau.off(TabEvent.AFTER_NODE_ADD, self.__after_node_add)
        super().listen_off()

    def has(self, branch, access):
        'Whether w1 sees w2 on the given branch.'
        return access[1] in self[branch].get(access[0], EMPTY_SET)

    def intransitives(self, branch: Branch, w1: int, w2: int) -> set[int]:
        """Get all the worlds on the branch that are visible to w2, but are not
        visible to w1.
        """
        # TODO: can we make this more efficient? for each world pair,
        #       track the intransitives?
        return self[branch].get(w2, EMPTY_SET) - self[branch].get(w1, EMPTY_SET)

    def __after_node_add(self, node: Node, branch: Branch):
        # Event: TabEvent.AFTER_NODE_ADD
        if node.is_access:
            w1, w2 = Access.fornode(node)
            if w1 not in self[branch]:
                self[branch][w1] = set()
            self[branch][w1].add(w2)
            self.nodes.add(node, branch)

class FilterNodeCache(BranchCache[set[Node]]):
    "Base class for caching nodes "

    __slots__ = ('ignore_ticked', '_garbage')
    _valuetype = set

    #: Copied from Rule.ignore_ticked - whether to discard nodes
    #: after they are ticked.
    ignore_ticked: bool

    @abstract
    def __call__(self, node, branch, /) -> bool:
        'Whether to add the node to the branch set.'
        return False

    def __init__(self, rule, /):
        self.ignore_ticked = bool(getattr(rule, RuleAttr.IgnoreTicked))
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
        self.rule.tableau.on(TabEvent.AFTER_NODE_ADD, self.__after_node_add)
        if self.ignore_ticked:
            self.rule.tableau.on(TabEvent.AFTER_NODE_TICK, self.__after_node_tick)

    def listen_off(self):
        self.rule.tableau.off({
            TabEvent.AFTER_NODE_ADD: self.__after_node_add,
            TabEvent.AFTER_NODE_TICK: self.__after_node_tick,
        })
        super().listen_off()

    def __after_node_add(self, node, branch, /):
        if self(node, branch):
            self[branch].add(node)

    def __after_node_tick(self, node, branch, /):
        self[branch].discard(node)

    @classmethod
    def configure_rule(cls, rulecls, config, **kw):
        "``RuleHelper`` init hook. Verify `ignore_ticked` attribute."
        super().configure_rule(rulecls, config, **kw)
        if not abcs.isabstract(rulecls):
            if not hasattr(rulecls, RuleAttr.IgnoreTicked):
                raise Emsg.MissingAttribute(RuleAttr.IgnoreTicked)

    @classmethod
    @closure
    def node_targets():

        def make_targets_fn(cls: type[FilterNodeCache], source_fn, /):
            """
            Method decorator to only iterate through nodes matching the
            configured `FilterNodeCache` filters.

            The rule may return a falsy value for no targets, a single
            target (non-empty `Mapping`), an `Iterator` or a `Sequence`.
            
            Returns a flat tuple of targets.
            """
            targiter = make_targiter(source_fn)
            @wraps(targiter)
            def get_targets_filtered(rule: Rule, branch, /):
                helper = rule[cls]
                helper.gc()
                return tuple(targiter(rule, helper[branch], branch))
            return get_targets_filtered

        def create(it, r, b, n, /):
            return Target(it, rule = r, branch = b, node = n)

        def make_targiter(source_fn):
            @wraps(source_fn)
            def targets_gen(rule, nodes, branch, /):
                for node in nodes:
                    results = source_fn(rule, node, branch)
                    if not results:
                        # Filter anything falsy.
                        continue
                    if isinstance(results, Mapping):
                        # Single target result.
                        yield create(results, rule, branch, node)
                    else:
                        # Multiple targets result.
                        # check.inst(results, (Sequence, Iterator))
                        for res in results:
                            yield create(res, rule, branch, node)

            return targets_gen

        return make_targets_fn

class PredNodes(FilterNodeCache):
    'Track all predicated nodes on the branch.'
    __slots__ = EMPTY_SET

    def __call__(self, node: Node, _):
        return type(node.get(NodeAttr.sentence)) is Predicated

class FilterHelper(FilterNodeCache):
    """Set configurable and chainable filters in ``NodeFilters``
    class attribute.
    """
    __slots__ = ('filters', 'pred')

    filters: Mapping
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
        """``RuleHelper`` init hook.
        
        * Verify `NodeFilters`.
        * For non-abstract classes, merge `NodeFilters` and create config.
        """
        super().configure_rule(rulecls, config, **kw)
        attr = RuleAttr.NodeFilters
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
            if configs:
                setattr(rulecls, attr, configs)
            else:
                import warnings
                warnings.warn(f"EMPTY '{attr}' attribute for {rulecls}. "
                    "All nodes will be cached.")
            return cls._build_config(rulecls)

    @staticmethod
    def _build_config(rulecls,/):
        configs: Mapping = getattr(rulecls, RuleAttr.NodeFilters)
        types = tuple(fcls for fcls, flag in configs.items()
            if flag is not NotImplemented)
        filters = MapProxy(dict(zip(
            types, funcs := tuple(ftype(rulecls) for ftype in types)
        )))
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

    consts: NodeConsts.Consts

    def __init__(self, rule, /):
        super().__init__(rule)
        self.filter = self.rule[FilterHelper]
        self.consts = self.Consts(rule)

    def listen_on(self):
        super().listen_on()
        self.rule.on(RuleEvent.AFTER_APPLY, self.__after_apply)
        self.rule.tableau.on(TabEvent.AFTER_NODE_ADD, self.__after_node_add)

    def listen_off(self):
        self.rule.off(RuleEvent.AFTER_APPLY, self.__after_apply)
        self.rule.tableau.off(TabEvent.AFTER_NODE_ADD, self.__after_node_add)
        super().listen_off()

    def __after_apply(self, target: Target, /):
        # Event: RuleEvent.AFTER_APPLY
        if target.get(NodeAttr.flag):
            return
        self[target.branch][target.node].discard(target.constant)

    def __after_node_add(self, node: Node, branch, /):
        # Event: TabEvent.AFTER_NODE_ADD
        if self.filter(node, branch):
            if node not in self[branch]:
                # By tracking per node, we are tracking per world, a fortiori.
                self[branch][node] = self.consts[branch].copy()
        s = node.get(NodeAttr.sentence)
        if s is None:
            return
        consts = s.constants - self.consts[branch]
        if len(consts):
            for node in self[branch]:
                self[branch][node].update(consts)
            self.consts[branch].update(consts)

class WorldConsts(BranchDictCache[int, set[Constant]]):
    """
    Track the constants appearing at each world.
    """

    __slots__ = EMPTY_SET

    def listen_on(self):
        super().listen_on()
        self.rule.tableau.on(TabEvent.AFTER_NODE_ADD, self.__after_node_add)

    def listen_off(self):
        self.rule.tableau.off(TabEvent.AFTER_NODE_ADD, self.__after_node_add)
        super().listen_off()

    def __after_node_add(self, node: Node, branch: Branch, /):
        # Event: TabEvent.AFTER_NODE_ADD
        s = node.get(NodeAttr.sentence)
        if s is None:
            return
        world = node.get(NodeAttr.world)
        if world is None:
            world = 0
        if world not in self[branch]:
            self[branch][world] = set()
        self[branch][world].update(s.constants)

class MaxConsts(dict[Branch, int], RuleHelper):
    """
    Project the maximum number of constants per world required for each branch
    by examining the branches after the trunk is built.
    """

    __slots__ = ('rule', 'config', 'wconsts')

    def __init__(self, rule, /):
        RuleHelper.__init__(self, rule)
        self.wconsts = WorldConsts(rule)

    def listen_on(self):
        self.rule.tableau.on(TabEvent.AFTER_TRUNK_BUILD, self.__after_trunk_build)

    def listen_off(self):
        self.rule.tableau.off(TabEvent.AFTER_TRUNK_BUILD, self.__after_trunk_build)

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
            dict: A dict with the following keys:
                - *is_flag*: ``True``
                - *flag*: ``'quit'``
                - *info*: ``'RuleName:MaxConstants(n)'`` where *RuleName* is
                    ``rule.name``, and ``n`` is the computed max allowed
                    constants for the branch.
        """
        return PropMap.QuitFlag | {NodeAttr.info: (
            f'{self.rule.name}:{type(self).__name__}'
            f'({self.get(branch.origin, 1)})')}

    def __after_trunk_build(self, tableau: Tableau, /):
        # Event: TabEvent.AFTER_TRUNK_BUILD
        for branch in tableau:
            origin = branch.origin
            if origin in self:
                raise NotImplementedError('Multiple trunk branches not implemented.')
            self[origin] = self._compute(branch)

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
        s = node.get(NodeAttr.sentence)
        return len(s.quantifiers) if s else 0

class MaxWorlds(dict[Branch, int], RuleHelper):
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
        RuleHelper.__init__(self, rule)
        self.modals = self.Modals(getattr(rule, RuleAttr.ModalOperators))

    def listen_on(self):
        self.rule.tableau.on(TabEvent.AFTER_TRUNK_BUILD, self.__after_trunk_build)

    def listen_off(self):
        self.rule.tableau.off(TabEvent.AFTER_TRUNK_BUILD, self.__after_trunk_build)

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
            dict: A dict with the following keys:
                - *is_flag*: ``True``
                - *flag*: ``'quit'``
                - *info*: ``'RuleName:MaxWorlds(n)'`` where *RuleName* is
                    ``rule.name``, and ``n`` is the computed max allowed
                    worlds for the branch.
        """
        return PropMap.QuitFlag | {NodeAttr.info: (
            f'{self.rule.name}:{type(self).__name__}({self.get(branch.origin)})')}

    def __after_trunk_build(self, tableau: Tableau, /):
        # Event: TabEvent.AFTER_TRUNK_BUILD
        for branch in tableau:
            origin = branch.origin
            # For normal logics, we will have only one trunk branch.
            if origin in self:
                raise NotImplementedError('Multiple trunk branches not implemented.')
            self[origin] = self._compute(branch)

    def _compute(self, branch: Branch, /) -> int:
        # Project the maximum number of worlds for a branch (origin) as
        # the number of worlds already on the branch + the number of modal
        # operators + 1.
        return 1 + len(branch.worlds) + sum(
            map(self.modals.__getitem__, (
                node[NodeAttr.sentence]
                for node in filterfalse(branch.is_ticked, branch)
                    if NodeAttr.sentence in node)))

    @classmethod
    def configure_rule(cls, rulecls, config, **kw):
        "``RuleHelper`` init hook. Set the `modal_operators` attribute."
        super().configure_rule(rulecls, config, **kw)
        try:
            ops = getattr(rulecls, RuleAttr.ModalOperators)
        except AttributeError:
            raise Emsg.MissingAttribute(RuleAttr.ModalOperators)
        else:
            check.inst(ops, Set)

