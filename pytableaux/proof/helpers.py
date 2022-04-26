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

import functools
from copy import copy
from itertools import filterfalse
from typing import (TYPE_CHECKING, Any, Callable, Iterable, Iterator, Mapping,
                    Sequence)

from pytableaux.errors import Emsg, check
from pytableaux.lang.lex import Constant, Predicated, Sentence
from pytableaux.proof import RuleHelper
from pytableaux.proof.common import Branch, Node, Target
from pytableaux.proof.filters import NodeFilter
from pytableaux.proof.tableaux import ClosingRule, Rule
from pytableaux.proof.util import Access, RuleAttr, RuleEvent, TabEvent
from pytableaux.tools import MapProxy, abstract, closure
from pytableaux.tools.abcs import abcm
from pytableaux.tools.hybrids import EMPTY_QSET, qsetf
from pytableaux.tools.mappings import dmap
from pytableaux.tools.misc import orepr
from pytableaux.tools.sets import EMPTY_SET, setm
from pytableaux.tools.typing import KT, VT, T, TypeInstDict

if TYPE_CHECKING:
    from typing import overload
    from pytableaux.proof.tableaux import Tableau

__all__ = (
    'AdzHelper',
    'QuitFlag',
    'AplSentCount',
    'NodeCount',
    'NodesWorlds',
    'UnserialWorlds',
    'WorldIndex',
    'PredNodes',
    'FilterHelper',

    'BranchTarget',
    'MaxConsts',
    'NodeConsts',
    'MaxWorlds',
)

TargetsFn = Callable[[Rule, Branch], Sequence[Target]|None]
NodeTargetsFn  = Callable[[Rule, Iterable[Node], Branch], Any]
NodeTargetsGen = Callable[[Rule, Iterable[Node], Branch], Iterator[Target]]


class AdzHelper:

    __slots__ = 'rule', 'closure_rules'

    def __init__(self, rule: Rule,/):
        self.rule = rule
        self.closure_rules = rule.tableau.rules.groups.get('closure', EMPTY_SET)

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
            nodes = tuple(map(Node, nodes))
            for rule in rules:
                if rule.nodes_will_close_branch(nodes, branch):
                    close_count += 1
                    break
        return close_count / min(1, len(target['adds']))

class BranchCache(dmap[Branch, T], RuleHelper):

    _valuetype: type[T] = bool

    __slots__ = 'rule',
    rule: Rule

    def __new__(cls, rule: Rule,/):
        inst = super().__new__(cls)
        inst.rule = rule
        return inst

    def __init__(self, rule: Rule,/):
        self.listen_on(rule, rule.tableau)

    def copy(self, /, *, listeners:bool = False):
        cls = type(self)
        if listeners:
            inst = cls(self.rule)
        else:
            inst = cls.__new__(cls, self.rule)
        inst.update(self)
        return inst

    def listen_on(self, rule: Rule, tableau: Tableau, /):
        tableau.on(TabEvent.AFTER_BRANCH_ADD, self.__after_branch_add)
        tableau.on(TabEvent.AFTER_BRANCH_CLOSE, self.__after_branch_close)

    def listen_off(self, rule: Rule, tableau: Tableau, /):
        tableau.off(TabEvent.AFTER_BRANCH_ADD, self.__after_branch_add)
        tableau.off(TabEvent.AFTER_BRANCH_CLOSE, self.__after_branch_close)

    def __after_branch_add(self, branch: Branch):
        if branch.parent:
            self[branch] = copy(self[branch.parent])
        else:
            self[branch] = self._empty_value(branch)

    def __after_branch_close(self, branch: Branch):
        del(self[branch])

    def __repr__(self):
        return orepr(self, self._reprdict())

    def _reprdict(self):
        return dict(branches = len(self))

    @classmethod
    def _empty_value(cls, branch: Branch) -> T:
        'Override, for example, if the value type takes arguments.'
        return cls._valuetype()

    @classmethod
    def _from_mapping(cls, mapping):
        if not isinstance(mapping, BranchCache):
            return NotImplemented
        return mapping.copy()

    @classmethod
    def _from_iterable(cls, it):
        return NotImplemented

    @classmethod
    def __init_ruleclass__(cls, rulecls: type[Rule]):
        pass

class BranchDictCache(BranchCache[dmap[KT, VT]]):
    'Copies each K->V item for parent branch via copy(V).'

    _valuetype = dmap

    __slots__ = EMPTY_SET

    def listen_on(self, rule: Rule, tableau: Tableau, /):
        super().listen_on(rule, tableau)
        tableau.on(TabEvent.AFTER_BRANCH_ADD, self.__after_branch_add)

    def listen_off(self, rule: Rule, tableau: Tableau, /):
        tableau.off(TabEvent.AFTER_BRANCH_ADD, self.__after_branch_add)
        super().listen_off(rule, tableau)

    def __after_branch_add(self, branch: Branch, /):
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

    def listen_on(self, rule: Rule, tableau: Tableau, /):
        super().listen_on(rule, tableau)
        rule.on(RuleEvent.AFTER_APPLY, self.__call__)

    def listen_off(self, rule: Rule, tableau: Tableau, /):
        rule.off(RuleEvent.AFTER_APPLY, self.__call__)
        super().listen_off(rule, tableau)

    def __call__(self, target: Target, /) -> None:
        self[target.branch] = bool(target.get('flag'))

class BranchValueHook(BranchCache[VT]):
    """Check each node as it is added, until a (truthy) value is returned,
    then cache that value for the branch and stop checking nodes.

    Calls the rule's ``_branch_value_hook(node, branch)`` when a node is added to
    a branch. Any truthy return value is cached for the branch. Once a value
    is stored for a branch, no further nodes are check.
    """
    _valuetype = type(None)
    hook_method_name = '_branch_value_hook'

    if TYPE_CHECKING:
        @overload
        def hook(self, node: Node, branch: Branch,/) -> VT|None:...

    __slots__ = 'hook',

    def __init__(self, rule: Rule, /):
        self.hook = getattr(rule, self.hook_method_name)
        super().__init__(rule)

    def listen_on(self, rule: Rule, tableau: Tableau, /):
        super().listen_on(rule, tableau)
        tableau.on(TabEvent.AFTER_NODE_ADD, self.__call__)

    def listen_off(self, rule: Rule, tableau: Tableau, /):
        tableau.off(TabEvent.AFTER_NODE_ADD, self.__call__)
        super().listen_off(rule, tableau)

    def __call__(self, node: Node, branch: Branch, /) -> None:
        if self[branch]:
            return
        res = self.hook(node, branch)
        if res:
            self[branch] = res

    @classmethod
    def __init_ruleclass__(cls, rulecls: type[Rule], **kw):
        super().__init_ruleclass__(rulecls, **kw)
        name = cls.hook_method_name
        value = getattr(rulecls, name, None)
        if value is None:
            raise Emsg.MissingAttribute(name, rulecls)
        check.callable(value)

class BranchTarget(BranchValueHook[Target]):
    hook_method_name = '_branch_target_hook'

class AplSentCount(BranchCache[dmap[Sentence, int]]):
    """
    Count the times the rule has applied for a sentence per branch. This tracks
    the `sentence` property of the rule's target. The target should also include
    the `branch` key.
    """
    __slots__ = EMPTY_SET
    _valuetype = dmap

    def listen_on(self, rule: Rule, tableau: Tableau, /):
        super().listen_on(rule, tableau)
        rule.on(RuleEvent.AFTER_APPLY, self.__call__)

    def listen_off(self, rule: Rule, tableau: Tableau, /):
        rule.off(RuleEvent.AFTER_APPLY, self.__call__)
        super().listen_off(rule, tableau)

    def __call__(self, target: Target):
        if target.get('flag'):
            return
        counts = self[target.branch]
        sentence = target.sentence
        counts[sentence] = counts.get(sentence, 0) + 1

class NodeCount(BranchCache[dmap[Node, int]]):

    __slots__ = EMPTY_SET
    _valuetype = dmap

    def listen_on(self, rule: Rule, tableau: Tableau, /):
        super().listen_on(rule, tableau)
        rule.on(RuleEvent.AFTER_APPLY, self.__call__)

    def listen_off(self, rule: Rule, tableau: Tableau, /):
        rule.off(RuleEvent.AFTER_APPLY, self.__call__)
        super().listen_off(rule, tableau)

    def min(self, branch: Branch) -> int:
        if branch in self and len(self[branch]):
            return min(self[branch].values())
        return 0

    def isleast(self, node: Node, branch: Branch) -> bool:
        return self.min(branch) >= self[branch].get(node, 0)

    def __call__(self, target: Target):
        if target.get('flag'):
            return
        counts = self[target.branch]
        node = target.node
        counts[node] = counts.get(node, 0) + 1

class NodesWorlds(BranchCache[setm[tuple[Node, int]]]):
    """
    Track the nodes applied to by the rule for each world on the branch. The
    target must have `node`, and `world` attributes. The values of the cache
    are ``(node, world)`` pairs.
    """
    __slots__ = EMPTY_SET

    _valuetype = setm

    def listen_on(self, rule: Rule, tableau: Tableau, /):
        super().listen_on(rule, tableau)
        rule.on(RuleEvent.AFTER_APPLY, self.__call__)

    def listen_off(self, rule: Rule, tableau: Tableau, /):
        rule.off(RuleEvent.AFTER_APPLY, self.__call__)
        super().listen_off(rule, tableau)

    def __call__(self, target: Target, /):
        if target.get('flag'):
            return
        self[target.branch].add((target.node, target.world))

class UnserialWorlds(BranchCache[setm[int]]):
    "Track the unserial worlds on the branch."
    __slots__ = EMPTY_SET

    _valuetype = setm

    def listen_on(self, rule: Rule, tableau: Tableau, /):
        super().listen_on(rule, tableau)
        tableau.on(TabEvent.AFTER_NODE_ADD, self.__call__)

    def listen_off(self, rule: Rule, tableau: Tableau, /):
        tableau.off(TabEvent.AFTER_NODE_ADD, self.__call__)
        super().listen_off(rule, tableau)

    def __call__(self, node: Node, branch: Branch, /):
        for w in node.worlds:
            if node.get('world1') == w or branch.has({'world1': w}):
                self[branch].discard(w)
            else:
                self[branch].add(w)

class WorldIndex(BranchDictCache[int, setm[int]]):
    'Index the visible worlds for each world on the branch.'

    __slots__ = 'nodes',

    class Nodes(BranchCache[dmap[Access, Node]]):
        _valuetype = dmap
        __slots__ = EMPTY_SET

        def __call__(self, node: Node, branch: Branch):
            self[branch][Access.fornode(node)] = node

    def __init__(self, rule: Rule,/):
        self.nodes = self.Nodes(rule)
        super().__init__(rule)

    def listen_on(self, rule: Rule, tableau: Tableau, /):
        super().listen_on(rule, tableau)
        tableau.on(TabEvent.AFTER_NODE_ADD, self.__call__)

    def listen_off(self, rule: Rule, tableau: Tableau, /):
        tableau.off(TabEvent.AFTER_NODE_ADD, self.__call__)
        super().listen_off(rule, tableau)

    def copy(self, /, *, listeners: bool = False):
        inst = super().copy(listeners = listeners)
        if listeners:
            inst.nodes.update(self.nodes)
        else:
            inst.nodes = self.nodes.copy(listeners = listeners)
        return inst

    def has(self, branch: Branch, access: Access) -> bool:
        'Whether w1 sees w2 on the given branch.'
        return access[1] in self[branch].get(access[0], EMPTY_SET)

    def intransitives(self, branch: Branch, w1: int, w2: int) -> set[int]:
        """Get all the worlds on the branch that are visible to w2, but are not
        visible to w1.
        """
        # TODO: can we make this more efficient? for each world pair,
        #       track the intransitives?
        return self[branch].get(w2, EMPTY_SET).difference(
            self[branch].get(w1, EMPTY_SET)
        )

    def __call__(self, node: Node, branch: Branch):        
        if node.is_access:
            w1, w2 = Access.fornode(node)
            if w1 not in self[branch]:
                self[branch][w1] = setm()
            self[branch][w1].add(w2)
            self.nodes(node, branch)

# * * * * *    FilterNodeCache    * * * * * #

class FilterNodeCache(BranchCache[set[Node]]):

    __slots__ = 'ignore_ticked',
    _valuetype = set

    #: Copied from Rule.ignore_ticked - whether to discard nodes
    #: after they are ticked.
    ignore_ticked: bool

    @abstract
    def __call__(self, node: Node, branch: Branch, /) -> bool:
        'Whether to add the node to the branch set.'
        return False

    def __init__(self, rule: Rule,/):
        self.ignore_ticked = bool(getattr(rule, RuleAttr.IgnoreTicked))
        super().__init__(rule)

    def listen_on(self, rule: Rule, tableau: Tableau, /):
        super().listen_on(rule, tableau)
        tableau.on(TabEvent.AFTER_NODE_ADD, self.__after_node_add)
        if self.ignore_ticked:
            tableau.on(TabEvent.AFTER_NODE_TICK, self.__after_node_tick)

    def listen_off(self, rule: Rule, tableau: Tableau, /):
        tableau.off(TabEvent.AFTER_NODE_ADD, self.__after_node_add)
        tableau.off(TabEvent.AFTER_NODE_TICK, self.__after_node_tick)
        super().listen_off(rule, tableau)

    def copy(self, /, *, listeners: bool = False):
        inst = super().copy(listeners = listeners)
        if not listeners:
            inst.ignore_ticked = self.ignore_ticked
        return inst

    def __after_node_add(self, node: Node, branch: Branch, /):
        if self(node, branch):
            self[branch].add(node)

    def __after_node_tick(self, node: Node, branch: Branch, /):
        self[branch].discard(node)

    @classmethod
    def __init_ruleclass__(cls, rulecls: type[Rule], **kw):
        "``RuleHelper`` init hook. Verify `ignore_ticked` attribute."
        super().__init_ruleclass__(rulecls, **kw)
        if not abcm.isabstract(rulecls):
            if not hasattr(rulecls, RuleAttr.IgnoreTicked):
                raise Emsg.MissingAttribute(RuleAttr.IgnoreTicked)

class PredNodes(FilterNodeCache):
    'Track all predicated nodes on the branch.'
    __slots__ = EMPTY_SET

    def __call__(self, node: Node, _):
        return isinstance(node.get('sentence'), Predicated)

FiltersDict = TypeInstDict[NodeFilter]
NodePredFunc = Callable[[Node], bool]

class FilterHelper(FilterNodeCache):
    """Set configurable and chainable filters in ``NodeFilters``
    class attribute.
    """
    __slots__ = 'filters', '_garbage', 'pred',

    filters: FiltersDict
    "Mapping from ``NodeFilter`` class to instance."

    pred: NodePredFunc
    """A single predicate of all filters. To also check the `ignore_ticked`
    setting, use ``.filter()``.
    """

    _garbage: setm[tuple[Branch, Node]]

    def __init__(self, rule: Rule,/):
        self._garbage = setm()
        self.filters, self.pred = self._build_filters_pred(rule)
        super().__init__(rule)

    @staticmethod
    def _build_filters_pred(rule: Rule) -> tuple[FiltersDict, NodePredFunc]:
        filters = MapProxy(zip(
            types := getattr(rule, RuleAttr.NodeFilters),
            funcs := tuple(ftype(rule) for ftype in types)
        ))
        def pred(node, /):
            return all(f(node) for f in funcs)
        return filters, pred

    def copy(self, /, *, listeners:bool = False):
        inst: FilterHelper = super().copy(listeners = listeners)
        if listeners:
            inst._garbage.update(self._garbage)
        else:
            inst._garbage = self._garbage.copy()
            inst.filters = self.filters
            inst.pred = self.pred
        return inst

    def filter(self, node: Node, branch: Branch, /) -> bool:
        """Whether the node passes the filter. If `ignore_ticked` is `True`,
        first checks whether the node is ticked, after which the combined
        filters predicate ``.pred()`` is checked.
        
        Args:
            node: The node.
            branch: The node's branch.
        
        Return:
            Whether the node meets the filter conditions and `ignore_ticked`
            setting.
        """
        if self.ignore_ticked and branch.is_ticked(node):
            return False
        return self.pred(node)

    if TYPE_CHECKING:
        @overload
        def __call__(self, node: Node, branch: Branch, /) -> bool: ...

    __call__ = filter

    def example_node(self) -> dict[str, Any]:
        """Construct an example node based on the filter conditions."""
        node = {}
        for filt in self.filters.values():
            n = filt.example_node()
            if n is not None:
                node.update(n)
        return node

    def release(self, node: Node, branch: Branch, /) -> None:
        """Mark the node/branch entry for garbage collection.

        Args:
            node: The node.
            branch: The node's branch.
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

    def _reprdict(self) -> dict:
        return super()._reprdict() | dict(
            filters = '(%s) %s' % (
                len(self.filters),
                ','.join(map(str, self.filters.keys()))
            ),
        )

    @classmethod
    def __init_ruleclass__(cls, rulecls: type[Rule], **kw):
        "``RuleHelper`` init hook. Verify and merge the `NodeFilters` attribute."
        super().__init_ruleclass__(rulecls, **kw)
        attr = RuleAttr.NodeFilters
        values = abcm.merge_mroattr(rulecls, attr, supcls = Rule,
            reverse = False,
            default = EMPTY_QSET,
            transform = qsetf,
        )
        if values:
            for Filter in values:
                check.subcls(check.inst(Filter, type), NodeFilter)
        else:
            if not abcm.isabstract(rulecls):
                import warnings
                warnings.warn(
                    f"EMPTY '{attr}' attribute for {rulecls}. "
                    "All nodes will be cached."
                )

    @classmethod
    @closure
    def node_targets():

        def make_targets_fn(cls: type[FilterHelper], node_targets_fn: NodeTargetsFn) -> TargetsFn:
            """
            Method decorator to only iterate through nodes matching the
            configured FilterHelper filters.

            The rule may return a falsy value for no targets, a single
            target (non-empty Mapping), an Iterator or a Sequence.
            
            Returns a flat list of targets.
            """
            fiter_targets = make_targets_iter(node_targets_fn)
            @functools.wraps(fiter_targets)
            def get_targets_filtered(rule: Rule, branch: Branch):
                helper = rule[cls]
                helper.gc()
                nodes = helper[branch]
                return tuple(fiter_targets(rule, nodes, branch))
            return get_targets_filtered

        def create(it, r: Rule, b: Branch, n: Node) -> Target:
            return Target(it, rule = r, branch = b, node = n)

        def make_targets_iter(node_targets_fn: NodeTargetsFn) -> NodeTargetsGen:
            @functools.wraps(node_targets_fn)
            def targets_gen(rule: Rule, nodes: Iterable[Node], branch: Branch):
                for node in nodes:
                    results = node_targets_fn(rule, node, branch)
                    if not results:
                        # Filter anything falsy.
                        continue
                    if isinstance(results, Mapping):
                        # Single target result.
                        yield create(results, rule, branch, node)
                    else:
                        # Multiple targets result.
                        check.inst(results, (Sequence, Iterator))
                        for res in results:
                            yield create(res, rule, branch, node)

            return targets_gen

        return make_targets_fn

class NodeConsts(BranchDictCache[Node, set[Constant]]):
    """Track the unapplied constants per branch for each potential node.
    The rule's target should have `branch`, `node` and `constant` properties.

    Only nodes that are applicable according to the rule's ``NodeFilter`` helper.
    method are tracked.
    """

    _valuetype = dmap

    class Consts(BranchCache[set[Constant]]):
        _valuetype = set
        __slots__ = EMPTY_SET

    if TYPE_CHECKING:
        @overload
        def filter(self, node: Node, branch: Branch, /) -> bool: ...

    consts: NodeConsts.Consts
    __slots__ = 'consts', 'filter',

    def __init__(self, rule: Rule,/):
        self.filter = rule.helpers[FilterHelper]
        self.consts = self.Consts(rule)
        super().__init__(rule)

    def listen_on(self, rule: Rule, tableau: Tableau, /):
        super().listen_on(rule, tableau)
        rule.on(RuleEvent.AFTER_APPLY, self.__after_apply)
        tableau.on(TabEvent.AFTER_NODE_ADD, self.__call__)

    def listen_off(self, rule: Rule, tableau: Tableau, /):
        rule.off(RuleEvent.AFTER_APPLY, self.__after_apply)
        tableau.off(TabEvent.AFTER_NODE_ADD, self.__call__)
        super().listen_off(rule, tableau)

    def __after_apply(self, target: Target, /):
        if target.get('flag'):
            return
        self[target.branch][target.node].discard(target.constant)

    def __call__(self, node: Node, branch: Branch, /):
        if self.filter(node, branch):
            if node not in self[branch]:
                # By tracking per node, we are tracking per world, a fortiori.
                self[branch][node] = self.consts[branch].copy()
        s: Sentence = node.get('sentence')
        if s is None:
            return
        consts = s.constants - self.consts[branch]
        if len(consts):
            for node in self[branch]:
                self[branch][node].update(consts)
            self.consts[branch].update(consts)

class WorldConsts(BranchDictCache[int, set[Constant]]):

    __slots__ = EMPTY_SET

    def listen_on(self, rule: Rule, tableau: Tableau, /):
        super().listen_on(rule, tableau)
        tableau.on(TabEvent.AFTER_NODE_ADD, self.__call__)

    def listen_off(self, rule: Rule, tableau: Tableau, /):
        tableau.off(TabEvent.AFTER_NODE_ADD, self.__call__)
        super().listen_off(rule, tableau)

    def __call__(self, node: Node, branch: Branch, /):
        s: Sentence = node.get('sentence')
        if s is None:
            return
        world = node.get('world')
        if world is None:
            world = 0
        if world not in self[branch]:
            self[branch][world] = set()
        self[branch][world].update(s.constants)

class MaxConsts(dict[Branch, int], RuleHelper):
    """
    Project the maximum number of constants per world required for a branch
    by examining the branches after the trunk is built.
    """
    __slots__ = (
        'rule',
        'world_consts',
    )

    def __init__(self, rule: Rule, /):
        self.rule = rule
        self.world_consts = WorldConsts(rule)
        self.listen_on(rule, rule.tableau)

    def listen_on(self, rule: Rule, tableau: Tableau, /):
        tableau.on(TabEvent.AFTER_TRUNK_BUILD, self.__call__)

    def listen_off(self, rule: Rule, tableau: Tableau, /):
        tableau.off(TabEvent.AFTER_TRUNK_BUILD, self.__call__)

    def is_reached(self, branch: Branch, world: int = 0, /) -> bool:
        """
        Whether we have already reached or exceeded the max number of constants
        projected for the branch (origin) at the given world.

        Args:
            branch: The branch.
            world (int): The world.
        """
        if world is None:
            world = 0
        maxc = self.get(branch.origin, 1)
        return len(self.world_consts[branch][world]) >= maxc

    def is_exceeded(self, branch: Branch, world: int = 0, /) -> bool:
        """
        Whether we have exceeded the max number of constants projected for
        the branch (origin) at the given world.

        Args:
            branch: The branch.
            world (int): The world.
        """
        if world is None:
            world = 0
        maxc = self.get(branch.origin, 1)
        return len(self.world_consts[branch][world]) > maxc

    def quit_flag(self, branch: Branch, /) -> dict:
        """Generate a quit flag node for the branch. Return value is a ``dict``
        with the following keys:

        - *is_flag*: ``True``
        - *flag*: ``'quit'``
        - *info*: ``'RuleName:MaxConstants({n})'`` where *RuleName* is ``rule.name``,
            and ``n`` is the computed max allowed constants for the branch.

        Args:
            branch: The branch.

        Returns:
            The node dict.
        """
        maxc = self.get(branch.origin, 1)
        info = f'{self.rule.name}:{type(self).__name__}({maxc})'
        return dict(is_flag = True, flag = 'quit', info = info)

    def __call__(self, tableau: Tableau, /) -> None:
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
        """
        node_needed_constants = sum([
            self._compute_needed_constants_for_node(node)
            for node in branch
        ])
        return max(1, len(branch.constants)) * max(1, node_needed_constants) + 1

    def _compute_needed_constants_for_node(self, node: Node,/) -> int:
        s: Sentence = node.get('sentence')
        return len(s.quantifiers) if s else 0

class MaxWorlds(dict[Branch, int], RuleHelper):
    """Project the maximum number of worlds required for a branch by examining
    the branches after the trunk is built.
    """
    __slots__ = (
        'rule',
        '_modals',
        '_modal_opfilter',
    )

    _modals: dict[Sentence, int]

    def __init__(self, rule: Rule,/):
        self.rule = rule
        self._modal_opfilter = getattr(rule, RuleAttr.ModalOperators).__contains__
        self._modals: dict[Sentence, int] = {}
        self.listen_on(rule, rule.tableau)

    def listen_on(self, rule: Rule, tableau: Tableau, /):
        tableau.on(TabEvent.AFTER_TRUNK_BUILD, self.__call__)

    def listen_off(self, rule: Rule, tableau: Tableau, /):
        tableau.off(TabEvent.AFTER_TRUNK_BUILD, self.__call__)

    def is_reached(self, branch: Branch, /) -> bool:
        """
        Whether we have already reached or exceeded the max number of worlds
        projected for the branch (origin).
        """
        origin = branch.origin
        return origin in self and len(branch.worlds) >= self[origin]

    def is_exceeded(self, branch: Branch, /) -> bool:
        """
        Whether we have exceeded the max number of worlds projected for the
        branch (origin).
        """
        origin = branch.origin
        return origin in self and len(branch.worlds) > self[origin]

    def modals(self, s: Sentence, /) -> int:
        """
        Compute and cache the modal complexity of a sentence by counting its
        modal operators.
        """
        if s not in self._modals:
            self._modals[s] = sum(map(self._modal_opfilter, s.operators))
        return self._modals[s]

    def quit_flag(self, branch: Branch, /) -> dict[str, Any]:
        """
        Generate a quit flag node for the branch.
        """
        info = f'{self.rule.name}:{type(self).__name__}({self.get(branch.origin)})'
        return dict(
            is_flag = True,
            flag = 'quit',
            info = info
        )

    def __call__(self, tableau: Tableau, /) -> None:
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
            map(self.modals, (
                node['sentence']
                for node in filterfalse(branch.is_ticked, branch)
                if 'sentence' in node
            ))
        )

    @classmethod
    def __init_ruleclass__(cls, rulecls: type[Rule], **kw):
        "``RuleHelper`` init hook. Set the `modal_operators` attribute."
        super().__init_ruleclass__(rulecls, **kw)
        if not hasattr(rulecls, RuleAttr.ModalOperators):
            raise Emsg.MissingAttribute(RuleAttr.ModalOperators)


# --------------------------------------------------

class EllipsisExampleHelper:
    # TODO: fix for closure rules
    mynode = {'ellipsis': True}
    closenodes = []

    def __init__(self, rule: Rule,/):
        self.rule = rule
        self.applied: set[Branch] = set()
        self.isclosure = isinstance(rule, ClosingRule)
        if self.isclosure:
            self.closenodes = list(
                dict(n)
                for n in reversed(rule.example_nodes())
            )
        self.istrunk = False
        rule.tableau.on({
            TabEvent.BEFORE_TRUNK_BUILD : self.__before_trunk_build,
            TabEvent.AFTER_TRUNK_BUILD  : self.__after_trunk_build,
            TabEvent.AFTER_BRANCH_ADD   : self.__after_branch_add,
            TabEvent.AFTER_NODE_ADD     : self.__after_node_add,
        })
        rule.on(RuleEvent.BEFORE_APPLY, self.__before_apply)

    def __before_trunk_build(self, *_):
        self.istrunk = True

    def __after_trunk_build(self, *_):
        self.istrunk = False

    def __after_branch_add(self, branch: Branch):
        if self.applied:
            return
        if len(self.closenodes) == 1:
            self.__addnode(branch)        

    def __after_node_add(self, node: Node, branch: Branch):
        if self.applied:
            return
        if node.meets(self.mynode) or node.is_closure:
            return
        if self.istrunk:
            self.__addnode(branch)
        elif self.closenodes and node.meets(self.closenodes[-1]):
            self.closenodes.pop()
            if len(self.closenodes) == 1:
                self.__addnode(branch)

    def __before_apply(self, target: Target):
        if self.applied:
            return
        if self.isclosure:#self.rule.is_closure:
            return
        if False and target.get('adds'):
            print(target['adds'])
            adds = list(target['adds'])
            adds[0] = tuple([self.mynode] + list(adds[0]))
            target._Target__data['adds'] = adds
            self.applied.add(target.branch)
        else:
            self.__addnode(target.branch)

    def __addnode(self, branch: Branch):
        self.applied.add(branch)
        branch.add(self.mynode)
