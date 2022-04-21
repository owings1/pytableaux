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
#
# ------------------
#
# pytableaux - rule helpers module
from __future__ import annotations

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

import functools
from copy import copy
from typing import (TYPE_CHECKING, Any, Callable, Iterable, Iterator, Mapping,
                    Sequence, final, overload)

from pytableaux.errors import Emsg, check
from pytableaux.lexicals import Constant, Predicated, Sentence
from pytableaux.models import BaseModel
from pytableaux.proof.common import Access, Branch, Node, Target
from pytableaux.proof.filters import NodeFilter
from pytableaux.proof.tableaux import ClosingRule, Rule, Tableau
from pytableaux.proof.types import RuleAttr, RuleEvent, RuleHelper, TabEvent
from pytableaux.tools import MapProxy, abstract, closure
from pytableaux.tools.abcs import abcm
from pytableaux.tools.hybrids import EMPTY_QSET, qsetf
from pytableaux.tools.mappings import dmap
from pytableaux.tools.sets import EMPTY_SET, setf, setm
from pytableaux.tools.typing import KT, VT, P, T, TypeInstDict


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
        rule.tableau.on({
            TabEvent.AFTER_BRANCH_ADD  : self.__after_branch_add,
            TabEvent.AFTER_BRANCH_CLOSE: self.__after_branch_close,
        })

    def copy(self, /, *, events = False):
        cls = type(self)
        if events:
            inst = cls(self.rule)
        else:
            inst = cls.__new__(cls, self.rule)
        inst.update(self)
        return inst

    def __after_branch_add(self, branch: Branch):
        if branch.parent:
            self[branch] = copy(self[branch.parent])
        else:
            self[branch] = self._empty_value(branch)

    def __after_branch_close(self, branch: Branch):
        del(self[branch])

    # ??
    def __hash__(self):
        return id(self)

    def __repr__(self):
        from pytableaux.tools.misc import orepr
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

    def __init__(self, rule: Rule,/):
        super().__init__(rule)
        rule.tableau.on(TabEvent.AFTER_BRANCH_ADD, self.__after_branch_add)

    def __after_branch_add(self, branch: Branch):
        if branch.parent:
            for key in self[branch]:
                self[branch][key] = copy(self[branch.parent][key])

class QuitFlag(BranchCache[bool]):
    """
    Track the application of a flag node by the rule for each branch. A branch
    is considered flagged when the target has a non-empty ``flag`` property.
    """
    __slots__ = EMPTY_SET
    _valuetype = bool

    def __init__(self, rule: Rule,/):
        super().__init__(rule)
        rule.on(RuleEvent.AFTER_APPLY, self)

    def __call__(self, target: Target):
        self[target.branch] = bool(target.get('flag'))

class BranchValueHook(BranchCache[VT]):
    """Check each node as it is added, until a (truthy) value is returned,
    then cache that value for the branch and stop checking nodes.

    Calls the rule's ``check_for_target(node, branch)`` when a node is added to
    a branch. Any truthy return value is cached for the branch. Once a value
    is stored for a branch, no further nodes are check.

    NB: The rule must implement ``check_for_target(self, node, branch)``.
    """
    _valuetype = type(None)
    hook_method_name = '_branch_value_hook'

    __slots__ = 'hook',

    hook: Callable[[Node, Branch], VT|None]

    def __init__(self, rule: Rule,/):
        super().__init__(rule)
        self.hook = getattr(rule, self.hook_method_name)
        rule.tableau.on(TabEvent.AFTER_NODE_ADD, self)

    def __call__(self, node: Node, branch: Branch):
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
        if not callable(value):
            raise TypeError("Method '%s' for class '%s' not callable" % (name, rulecls))

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

    def __init__(self, rule: Rule,/):
        super().__init__(rule)
        rule.on(RuleEvent.AFTER_APPLY, self)

    def __call__(self, target: Target):
        if target.get('flag'):
            return
        counts = self[target.branch]
        sentence = target.sentence
        counts[sentence] = counts.get(sentence, 0) + 1

class NodeCount(BranchCache[dmap[Node, int]]):

    __slots__ = EMPTY_SET
    _valuetype = dmap

    def __init__(self, rule: Rule,/):
        super().__init__(rule)
        rule.on(RuleEvent.AFTER_APPLY, self)

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

    def __init__(self, rule: Rule,/):
        super().__init__(rule)
        rule.on(RuleEvent.AFTER_APPLY, self)

    def __call__(self, target: Target):
        if target.get('flag'):
            return
        self[target.branch].add((target.node, target.world))

class UnserialWorlds(BranchCache[setm[int]]):
    "Track the unserial worlds on the branch."
    __slots__ = EMPTY_SET

    _valuetype = setm

    def __init__(self, rule: Rule,/):
        super().__init__(rule)
        rule.tableau.on(TabEvent.AFTER_NODE_ADD, self)

    def __call__(self, node: Node, branch: Branch):
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
        super().__init__(rule)
        self.nodes = self.Nodes(rule)
        rule.tableau.on(TabEvent.AFTER_NODE_ADD, self)

    def copy(self, /, *, events = False):
        inst = super().copy(events = events)
        if events:
            inst.nodes.update(self.nodes)
        else:
            inst.nodes = self.nodes.copy(events = events)
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
        super().__init__(rule)
        self.ignore_ticked = bool(getattr(rule, RuleAttr.IgnoreTicked))
        rule.tableau.on(TabEvent.AFTER_NODE_ADD, self.__after_node_add)
        if self.ignore_ticked:
            rule.tableau.on(TabEvent.AFTER_NODE_TICK, self.__after_node_tick)

    def copy(self, /, *, events = False):
        inst = super().copy(events = events)
        if not events:
            inst.ignore_ticked = self.ignore_ticked
        return inst

    def __after_node_add(self, node: Node, branch: Branch):
        if self(node, branch):
            self[branch].add(node)

    def __after_node_tick(self, node: Node, branch: Branch):
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

class FilterHelper(FilterNodeCache):
    """
    Set configurable and chainable filters in ``NodeFilters``
    class attribute.
    """
    __slots__ = 'filters', '_garbage', 'pred',

    filters: TypeInstDict[NodeFilter[type[Rule]]]
    "Mapping from ``NodeFilter`` class to instance."

    pred: Callable[[Node], bool]
    "A single predicate of all filters."

    _garbage: setm[tuple[Branch, Node]]

    def __init__(self, rule: Rule,/):
        super().__init__(rule)
        self._garbage = setm()
        self.filters = MapProxy({
            Filter: Filter(rule)
            for Filter in getattr(rule, RuleAttr.NodeFilters)
        })
        self.pred = self.create_pred(self.filters)

    def copy(self, /, *, events = False):
        inst: FilterHelper = super().copy(events = events)
        if events:
            inst._garbage.update(self._garbage)
        else:
            inst._garbage = self._garbage.copy()
            inst.filters = MapProxy(self.filters.copy())
            inst.pred = self.create_pred(inst.filters)
        return inst

    def filter(self, node: Node, branch: Branch, /) -> bool:
        """Whether the node passes the filter."""
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
            if n:
                node.update(n)
        return node

    def release(self, node: Node, branch: Branch, /):
        'Mark the node/branch entry for garbage collection.'
        self._garbage.add((branch, node))

    def gc(self):
        'Run garbage collection. Remove entries queued by ``.release()``.'
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

    @staticmethod
    def create_pred(filters: Mapping[Any, NodeFilter], /) -> Callable[[Node], bool]:
        """Create a predicate function for all the filters.

        Unlike the ``.filter()``, this does not consider the `ignore_ticked` setting.
        """
        funcs = filters.values()
        def pred(node: Node,/) -> bool:
            return all(f(node) for f in funcs)
        return pred

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
            Method decoratorp to only iterate through nodes matching the
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
                        # print(type(results), rule.name)
                        for res in results:# filter(bool, results):
                            # if not(res):
                            #     print(res)
                            # Filter anything falsy.
                            yield create(res, rule, branch, node)

            return targets_gen

        return make_targets_fn

class NodeConsts(BranchDictCache[Node, set[Constant]]):
    """Track the unapplied constants per branch for each potential node.
    The rule's target should have `branch`, `node` and `constant` properties.

    Only nodes that are applicable according to the rule's ``NodeFilter`` helper.
    method are tracked.
    """
    __slots__ = 'consts', 'filter',
    _valuetype = dmap

    class Consts(BranchCache[set[Constant]]):
        _valuetype = set
        __slots__ = EMPTY_SET

    def __init__(self, rule: Rule,/):
        super().__init__(rule)
        # fail fast if the rule does not have a filter.
        self.filter = rule.helpers[FilterHelper]
        self.consts = self.Consts(rule)
        rule.on(RuleEvent.AFTER_APPLY, self.__after_apply)
        rule.tableau.on(TabEvent.AFTER_NODE_ADD, self)

    def __after_apply(self, target: Target):
        if target.get('flag'):
            return
        self[target.branch][target.node].discard(target.constant)

    def __call__(self, node: Node, branch: Branch):
        if self.filter(node, branch):
            if node not in self[branch]:
                # By tracking per node, we are tracking per world, a fortiori.
                self[branch][node] = self.consts[branch].copy()
        s: Sentence = node.get('sentence')
        if not s:
            return
        consts = s.constants - self.consts[branch]
        if len(consts):
            for node in self[branch]:
                self[branch][node].update(consts)
            self.consts[branch].update(consts)

class MaxConsts:
    """
    Project the maximum number of constants per world required for a branch
    by examining the branches after the trunk is built.
    """
    __slots__ = 'rule', 'branch_max_constants', 'world_constants'

    def __init__(self, rule: Rule,/):
        self.rule = rule
        #: Track the maximum number of constants that should be on the branch
        #: (per world) so we can halt on infinite branches. Map from ``branch.id```
        #: to ``int```.
        #: :type: dict({int: int})
        self.branch_max_constants = {}
        #: Track the constants at each world.
        #: :type: dict{int: set(Constant)}
        self.world_constants = {}
        rule.tableau.on({
            TabEvent.AFTER_BRANCH_ADD  : self.__after_branch_add,
            TabEvent.AFTER_TRUNK_BUILD : self.__after_trunk_build,
            TabEvent.AFTER_NODE_ADD    : self.__after_node_add,
        })

    def get_max_constants(self, branch: Branch) -> int:
        """
        Get the projected max number of constants (per world) for the branch.
        """
        return self.branch_max_constants.get(branch.origin, 1)
        # try:
        #     return self.branch_max_constants[branch.origin]
        # except KeyError:
        #     return 1

    def get_branch_constants_at_world(self, branch: Branch, world: int) -> set[Constant]:
        """
        Get the cached set of constants at a world for the branch.

        :param tableaux.Branch branch:
        :param int world:
        :rtype: bool
        """
        # if world not in self.world_constants[branch]:
        #     self.world_constants[branch][world] = set()
        return self.world_constants[branch][world]

    def max_constants_reached(self, branch: Branch, world: int = 0) -> bool:
        """
        Whether we have already reached or exceeded the max number of constants
        projected for the branch (origin) at the given world.

        :param tableaux.Branch branch:
        :param int world:
        """
        if world is None:
            world = 0
        max_constants = self.get_max_constants(branch)
        world_constants = self.get_branch_constants_at_world(branch, world)
        return max_constants != None and len(world_constants) >= max_constants

    def max_constants_exceeded(self, branch: Branch, world: int = 0) -> bool:
        """
        Whether we have exceeded the max number of constants projected for
        the branch (origin) at the given world.

        :param tableaux.Branch branch:
        :param int world:
        """
        if world is None:
            world = 0
        max_constants = self.get_max_constants(branch)
        world_constants = self.get_branch_constants_at_world(branch, world)
        if max_constants is not None and len(world_constants) > max_constants:
            return True

    def quit_flag(self, branch: Branch) -> dict:
        """
        Generate a quit flag node for the branch. Return value is a ``dict`` with the
        following keys:

        - *is_flag*: ``True``
        - *flag*: ``'quit'``
        - *info*: ``'RuleName:MaxConstants({n})'`` where *RuleName* is ``rule.name``,
            and ``n`` is the computed max allowed constants for the branch.

        :param tableaux.Branch branch:
        :rtype: dict
        """
        info = '{0}:MaxConstants({1})'.format(self.rule.name, str(self.get_max_constants(branch)))
        return {'is_flag': True, 'flag': 'quit', 'info': info}

    # Events

    def __after_trunk_build(self, tableau: Tableau):
        for branch in tableau:
            origin = branch.origin
            # In most cases, we will have only one origin branch.
            if origin in self.branch_max_constants:
                return
            self.branch_max_constants[origin] = self._compute_max_constants(branch)

    def __after_branch_add(self, branch: Branch):
        parent = branch.parent
        if parent is not None and parent in self.world_constants:
            self.world_constants[branch] = {
                world : copy(self.world_constants[parent][world])
                for world in self.world_constants[parent]
            }
        else:
            self.world_constants[branch] = {}

    def __after_node_add(self, node: Node, branch: Branch):
        s: Sentence = node.get('sentence')
        if s:
            world = node.get('world')
            if world is None:
                world = 0
            if world not in self.world_constants[branch]:
                self.world_constants[branch][world] = set()
            self.world_constants[branch][world].update(s.constants)

    # Private util

    def _compute_max_constants(self, branch: Branch) -> int:
        """
        Project the maximum number of constants for a branch (origin) as
        the number of constants already on the branch (min 1) * the number of
        quantifiers (min 1) + 1.
        """
        node_needed_constants = sum([
            self._compute_needed_constants_for_node(node, branch)
            for node in branch
        ])
        return max(1, branch.constants_count) * max(1, node_needed_constants) + 1

    def _compute_needed_constants_for_node(self, node: Node, branch: Branch) -> int:
        s: Sentence = node.get('sentence')
        return len(s.quantifiers) if s else 0


class MaxWorlds:
    """
    Project the maximum number of worlds required for a branch by examining the
    branches after the trunk is built.
    """
    __slots__ = 'rule', 'branch_max_worlds', 'modal_complexities'

    modal_operators = setf(BaseModel.modal_operators)

    def __init__(self, rule: Rule,/):
        self.rule = rule
        # Track the maximum number of worlds that should be on the branch
        # so we can halt on infinite branches.
        self.branch_max_worlds = {}
        # Cache the modal complexities
        self.modal_complexities: dict[Sentence, int] = {}
        rule.tableau.on(TabEvent.AFTER_TRUNK_BUILD, self.__after_trunk_build)

    def get_max_worlds(self, branch: Branch):
        """
        Get the maximum worlds projected for the branch.
        """
        origin = branch.origin
        if origin.id in self.branch_max_worlds:
            return self.branch_max_worlds[origin.id]

    def max_worlds_reached(self, branch: Branch):
        """
        Whether we have already reached or exceeded the max number of worlds
        projected for the branch (origin).
        """
        max_worlds = self.get_max_worlds(branch)
        return max_worlds is not None and branch.world_count >= max_worlds

    def max_worlds_exceeded(self, branch: Branch):
        """
        Whether we have exceeded the max number of worlds projected for the
        branch (origin).
        """
        max_worlds = self.get_max_worlds(branch)
        return max_worlds is not None and branch.world_count > max_worlds

    def modal_complexity(self, sentence: Sentence):
        """
        Compute and cache the modal complexity of a sentence by counting its
        modal operators.
        """
        if sentence not in self.modal_complexities:
            self.modal_complexities[sentence] = len(
                tuple(filter(self.modal_operators.__contains__, sentence.operators))
                # [o for o in sentence.operators if o in self.modal_operators]
            )
        return self.modal_complexities[sentence]

    def quit_flag(self, branch: Branch):
        """
        Generate a quit flag node for the branch.
        """
        info = '{0}:MaxWorlds({1})'.format(self.rule.name, str(self.get_max_worlds(branch)))
        return {'is_flag': True, 'flag': 'quit', 'info': info}

    # Events

    def __after_trunk_build(self, tableau: Tableau):
        for branch in tableau:
            origin = branch.origin
            # In most cases, we will have only one origin branch.
            if origin.id in self.branch_max_worlds:
                return
            self.branch_max_worlds[origin.id] = self.__compute_max_worlds(branch)

    # Private util

    def __compute_max_worlds(self, branch: Branch):
        # Project the maximum number of worlds for a branch (origin) as
        # the number of worlds already on the branch + the number of modal
        # operators + 1.
        node_needed_worlds = sum([
            self.__compute_needed_worlds_for_node(node, branch)
            for node in branch
        ])
        return branch.world_count + node_needed_worlds + 1

    def __compute_needed_worlds_for_node(self, node: Node, branch: Branch):
        # we only care about unticked nodes, since ticked nodes will have
        # already created any worlds.
        if not branch.is_ticked(node) and node.has('sentence'):
            return self.modal_complexity(node['sentence'])
        return 0

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
        if node.has_props(self.mynode) or node.is_closure:
            return
        if self.istrunk:
            self.__addnode(branch)
        elif self.closenodes and node.has_props(self.closenodes[-1]):
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



del(abstract, final, overload)
