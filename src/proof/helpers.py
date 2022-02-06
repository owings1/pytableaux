# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
    'AppliedQuitFlag',
    'AppliedSentenceCounter',
    'AppliedNodeCount',
    'AppliedNodesWorlds',
    'UnserialWorldsTracker',
    'VisibleWorldsIndex',
    'PredicatedNodesTracker',
    'FilterHelper',

    'NodeTargetCheckHelper',
    'MaxConstantsTracker',
    'AppliedNodeConstants',
    'MaxWorldsTracker',

)
from errors import (
    instcheck,
    Emsg,
)
from tools.abcs import (
    Abc, abcf, T,
    # T1, T2,
    KT, VT, P,
    # Self,
)
from tools.decorators import abstract, final, overload, static
from tools.mappings import MapAttrCover, dmap
from tools.sets import EMPTY_SET, setm, setf

from lexicals import Constant, Sentence, Predicated
from models import BaseModel
from proof.common import (
    Access,
    Branch,
    Comparer,
    Node,
    NodeFilter,
    RuleEvent,
    TabEvent,
    Target,
)
from proof.tableaux import (
    Rule,
    ClosingRule,
    Tableau,
)

from copy import copy
# from functools import partial
# from itertools import chain, filterfalse
from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    Mapping,
    Sequence,
    TypeVar,
)

class AdzHelper:

    _attr = 'adz'
    __slots__ = 'rule', 'closure_rules'

    def __init__(self, rule: Rule):
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
            return float()
        close_count = 0
        branch = target.branch
        for nodes in target['adds']:
            nodes = tuple(Node(node) for node in nodes)
            for rule in rules:
                if rule.nodes_will_close_branch(nodes, branch):
                    close_count += 1
                    break
        return float(close_count / min(1, len(target['adds'])))

class BranchCache(dmap[Branch, T]):

    _valuetype: type[T] = bool

    rule: Rule
    tab: Tableau

    __slots__ = 'rule',

    def __init__(self, rule: Rule):
        self.rule = rule
        rule.tableau.on({
            TabEvent.AFTER_BRANCH_ADD  : self.__after_branch_add,
            TabEvent.AFTER_BRANCH_CLOSE: self.__after_branch_close,
        })

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
        from tools.misc import orepr
        return orepr(self, self._reprdict())

    def _reprdict(self):
        return {'branches': len(self)}

    def copy(self, /, *, events = False):
        cls = type(self)
        if events:
            inst = cls(self.rule)
        else:
            inst = cls.__new__(cls)
            inst.rule = self.rule
        inst.update(self)
        return inst

    def _empty_value(self, branch: Branch) -> T:
        'Override, for example, if the value type takes arguments.'
        return self._valuetype()

    @classmethod
    def _from_mapping(cls, mapping):
        if not isinstance(mapping, BranchCache):
            return NotImplemented
        return mapping.copy()

    @classmethod
    def _from_iterable(cls, it):
        return NotImplemented


class BranchDictCache(BranchCache[dmap[KT, VT]]):
    'Copies each value.'

    _valuetype = dmap

    __slots__ = EMPTY_SET

    def __init__(self, *args):
        super().__init__(*args)
        self.rule.tableau.on(TabEvent.AFTER_BRANCH_ADD, self.__after_branch_add)

    def __after_branch_add(self, branch: Branch):
        if branch.parent:
            for key in self[branch]:
                self[branch][key] = copy(self[branch.parent][key])

class FilterNodeCache(BranchCache[set[Node]]):

    _valuetype = set
    
    __slots__ = 'ignore_ticked',

    ignore_ticked: bool|None

    def __init__(self, *args):
        super().__init__(*args)
        self.ignore_ticked = getattr(self.rule, 'ignore_ticked', None)
        self.rule.tableau.on({
            TabEvent.AFTER_NODE_ADD: self.__after_node_add,
            TabEvent.AFTER_NODE_TICK: self.__after_node_tick,
        })

    def __after_node_add(self, node: Node, branch: Branch):
        if self(node, branch):
            self[branch].add(node)

    def __after_node_tick(self, node: Node, branch: Branch):
        if self.ignore_ticked:
            self[branch].discard(node)

    @abstract
    def __call__(self, node: Node, branch: Branch): ...

    def copy(self: FncT, *args, **kw) -> FncT:
        inst: FncT = super().copy(*args, **kw)
        inst.ignore_ticked = self.ignore_ticked
        return inst

# BrcT = TypeVar('BrcT', bound = BranchCache)
FncT = TypeVar('FncT', bound = FilterNodeCache)

@final
class AppliedQuitFlag(BranchCache[bool]):
    """
    Track the application of a flag node by the rule for each branch. A branch
    is considered flagged when the target has a non-empty ``flag`` property.
    """
    _valuetype = bool
    _attr = 'apqf'

    __slots__ = EMPTY_SET

    def __init__(self, *args):
        super().__init__(*args)
        self.rule.on(RuleEvent.AFTER_APPLY, self)

    def __call__(self, target: Target):
        self[target.branch] = bool(target.get('flag'))

@final
class AppliedSentenceCounter(BranchCache[dmap[Sentence, int]]):
    """
    Count the times the rule has applied for a sentence per branch. This tracks
    the `sentence` property of the rule's target. The target should also include
    the `branch` key.
    """
    _valuetype = dmap
    _attr = 'apsc'
    __slots__ = EMPTY_SET

    def __init__(self, *args):
        super().__init__(*args)
        self.rule.on(RuleEvent.AFTER_APPLY, self)

    def __call__(self, target: Target):
        if target.get('flag'):
            return
        counts = self[target.branch]
        sentence = target.sentence
        counts[sentence] = counts.get(sentence, 0) + 1

@final
class AppliedNodeCount(BranchCache[dmap[Node, int]]):

    _valuetype = dmap
    _attr = 'apnc'

    __slots__ = EMPTY_SET

    def __init__(self, *args):
        super().__init__(*args)
        self.rule.on(RuleEvent.AFTER_APPLY, self)

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

@final
class AppliedNodesWorlds(BranchCache[setm[tuple[Node, int]]]):
    """
    Track the nodes applied to by the rule for each world on the branch. The
    target must have `node`, and `world` attributes. The values of the cache
    are ``(node, world)`` pairs.
    """
    _valuetype = setm
    _attr = 'apnw'

    __slots__ = EMPTY_SET

    def __init__(self, *args):
        super().__init__(*args)
        self.rule.on(RuleEvent.AFTER_APPLY, self)

    def __call__(self, target: Target):
        if target.get('flag'):
            return
        self[target.branch].add((target.node, target.world))

@final
class UnserialWorldsTracker(BranchCache[setm[int]]):
    "Track the unserial worlds on the branch."

    _valuetype = setm
    _attr = 'ust'

    __slots__ = EMPTY_SET

    def __init__(self, *args):
        super().__init__(*args)
        self.rule.tableau.on(TabEvent.AFTER_NODE_ADD, self)

    def __call__(self, node: Node, branch: Branch):
        for w in node.worlds:
            if node.get('world1') == w or branch.has({'world1': w}):
                self[branch].discard(w)
            else:
                self[branch].add(w)

@final
class VisibleWorldsIndex(BranchDictCache[int, setm[int]]):
    'Index the visible worlds for each world on the branch.'

    __slots__ = 'nodes',
    _attr = 'visw'

    class Nodes(BranchCache[dmap[Access, Node]]):
        _valuetype = dmap
        __slots__ = EMPTY_SET

        def __call__(self, node: Node, branch: Branch):
            self[branch][Access.fornode(node)] = node

    def __init__(self, *args):
        super().__init__(*args)
        self.nodes = self.Nodes(*args)
        self.rule.tableau.on(TabEvent.AFTER_NODE_ADD, self)

    def copy(self, *args, **kw):
        inst = super().copy(*args, **kw)
        if hasattr(inst, 'nodes'):
            inst.nodes.update(self.nodes)
        else:
            inst.nodes = self.nodes.copy(*args, **kw)
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

@final
class PredicatedNodesTracker(FilterNodeCache):
    'Track all predicated nodes on the branch.'
    _attr = 'pn'
    __slots__ = EMPTY_SET

    def __call__(self, node: Node, _):
        return isinstance(node.get('sentence'), Predicated)

@final
class FilterHelper(FilterNodeCache):
    """
    Set configurable and chainable filters in ``NodeFilters``
    class attribute.
    """
    clsattr_node = 'NodeFilters'
    _attr = 'nf'

    __slots__ = 'filters', 'callcount', '__fmap', '__to_discard'

    filters: MapAttrCover[NodeFilter]
    callcount: int

    __fmap: dmap[str, NodeFilter]
    __to_discard: setm[tuple[Branch, Node]]

    def __init__(self, *args):
        super().__init__(*args)
        self.__to_discard = setm()
        self.__fmap = dmap()
        self.filters = MapAttrCover(self.__fmap)
        self.callcount = 0
        for item in getattr(self.rule, self.clsattr_node, EMPTY_SET):
            if isinstance(item, type):
                self._add_filter(item, None)
            else:
                name, cls = item
                self._add_filter(cls, name)

    def copy(self, *args, **kw):
        inst = super().copy(*args, **kw)
        try:
            inst.__to_discard.update(self.__to_discard)
        except AttributeError:
            inst.__to_discard = self.__to_discard.copy()
            inst.__fmap = self.__fmap.copy()
            inst.filters = MapAttrCover(self.__fmap)
        inst.callcount = self.callcount
        return inst

    def filter(self, node: Node, branch: Branch):
        self.callcount += 1
        if self.ignore_ticked and branch.is_ticked(node):
            return False
        for name in self.filters:
            if not self.filters[name](node):
                return False
        return True

    @overload
    def __call__(self, node: Node, branch: Branch) -> bool: ...
    __call__ = filter

    def example_node(self):
        node = {}
        for filt in self.__fmap.values():
            if callable(getattr(filt, 'example_node', None)):
                n = filt.example_node()
                if n:
                    node.update(n)
            elif callable(getattr(filt, 'example', None)):
                ret = filt.example()
                if isinstance(ret, dict):
                    node.update(ret)
        return node

    def release(self, node: Node, branch: Branch):
        self.__to_discard.add((branch, node))

    def gc(self):
        for branch, node in self.__to_discard:
            try:
                self[branch].discard(node)
            except KeyError:
                pass
        self.__to_discard.clear()

    def _add_filter(self, cls: type[Comparer], name: str = None):
        """
        Instantiate a filter class from the NodeFilters config.
        """
        if name is None:
            name = cls.__name__.lower()
        if name in self.__fmap:
            raise Emsg.DuplicateKey(name)
        self.__fmap[instcheck(name, str)] = instcheck(cls, type)(self.rule)

    def _reprdict(self) -> dict:
        return super()._reprdict() | {
            'filters': '(%s) %s' % (len(self.filters), self.__fmap),
        }

    @classmethod
    def node_targets(cls,
        fget_node_targets: Callable[[Rule, Iterable[Node], Branch], Any],
    ) -> Callable[[Rule, Branch], Sequence[Target]]:
        """
        Method decorator to only iterate through nodes matching the
        configured FilterHelper filters.

        The rule may return a falsy value for no targets, a single
        target (non-empty Mapping), an Iterator or a Sequence.
        
        Returns a flat list of targets.
        """
        fiter_targets = _targets_from_nodes_iter(fget_node_targets)
        def get_targets_filtered(rule: Rule, branch: Branch):
            helper = rule.helpers[cls]
            helper.gc()
            nodes = helper[branch]
            return tuple(fiter_targets(rule, nodes, branch))
        return get_targets_filtered

@static
class Delegates(Abc):
    'Mixin Rule classes to delegate to helper methods.'

    @static
    class AdzHelper:

        class Apply(Rule):
            'Delegates ``_apply()`` to ``AdzHelper._apply()``.'

            Helpers = AdzHelper,
            adz: AdzHelper

            __slots__ = EMPTY_SET

            #: Whether the target node should be ticked after application.
            ticking: bool = True

            def _apply(self, target: Target):
                self.adz._apply(target)

        class ClosureScore(Rule):
            """
            Delegates ``score_candidate()`` to ``AdzHelper.closure_score()``.
            """
            Helpers = AdzHelper,
            adz: AdzHelper

            __slots__ = EMPTY_SET

            def score_candidate(self, target: Target):
                return self.adz.closure_score(target)

    @static
    class FilterHelper:

        class Sentence(Rule):
            """
            Delegates ``sentence()`` to ``FilterHelper.sentence()``.
            """
            Helpers = FilterHelper,
            nf: FilterHelper

            __slots__ = EMPTY_SET

            def sentence(self, node: Node, _ = None, /) -> Sentence:
                return self.nf.filters['sentence'].get(node)

        class ExampleNodes(Rule):
            """
            Delegates ``example_nodes()`` to ``FilterHelper.example_nodes()``.
            """
            Helpers = FilterHelper,
            nf: FilterHelper

            __slots__ = EMPTY_SET

            def example_nodes(self):
                return self.nf.example_node(),

    @abcf.after
    def populate(cls):
        from inspect import getmembers, isclass
        modclasses = {
            clsname: c for clsname, c in globals().items()
            if isclass(c) and c.__module__ == cls.__module__
        }
        for helpername, delegates in getmembers(cls, isclass)[0:-1]:
            helpercls = modclasses[helpername]
            for name, c in getmembers(delegates, isclass)[0:-1]:
                setattr(helpercls, name, c)


class NodeTargetCheckHelper(BranchCache[Target]):
    """
    Calls the rule's ``check_for_target(node, branch)`` when a node is added to
    a branch. If a target is returned, it is cached relative to the branch. The
    rule can then call ``cached_target(branch)``  on the helper to retrieve the
    target. This is used primarily in closure rules for performance.

    NB: The rule must implement ``check_for_target(self, node, branch)``.
    """
    _attr = 'ntch'
    _valuetype = Target

    __slots__ = EMPTY_SET

    rule: ClosingRule

    def __init__(self, rule: ClosingRule):
        super().__init__(instcheck(rule, ClosingRule))
        rule.tableau.on(TabEvent.AFTER_NODE_ADD, self)

    def __call__(self, node: Node, branch: Branch): 
        target = self.rule.check_for_target(node, branch)
        if target:
            self[branch] = target

    def _empty_value(self, branch: Branch):
        'Override _valuetype since we cannot have an empty Target.'
        return None

class MaxConstantsTracker:
    """
    Project the maximum number of constants per world required for a branch
    by examining the branches after the trunk is built.
    """
    __slots__ = 'rule', 'branch_max_constants', 'world_constants'

    _attr = 'maxc'

    def __init__(self, rule: Rule):
        self.rule = rule
        #: Track the maximum number of constants that should be on the branch
        #: (per world) so we can halt on infinite branches. Map from ``branch.id```
        #: to ``int```.
        #: :type: dict({int: int})
        self.branch_max_constants = {}
        #: Track the constants at each world.
        #: :type: dict{int: set(Constant)}
        self.world_constants = {}

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
        if max_constants != None and len(world_constants) > max_constants:
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

    # Helper implementation

    def after_trunk_build(self, tableau: Tableau):
        for branch in tableau:
            origin = branch.origin
            # In most cases, we will have only one origin branch.
            if origin in self.branch_max_constants:
                return
            self.branch_max_constants[origin] = self._compute_max_constants(branch)

    def after_branch_add(self, branch: Branch):
        parent = branch.parent
        if parent != None and parent in self.world_constants:
            self.world_constants[branch] = {
                world : copy(self.world_constants[parent][world])
                for world in self.world_constants[parent]
            }
        else:
            self.world_constants[branch] = {}

    def after_node_add(self, node: Node, branch: Branch):
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

class AppliedNodeConstants(BranchDictCache[Node, set[Constant]]):
    """Track the unapplied constants per branch for each potential node.
    The rule's target should have `branch`, `node` and `constant` properties.

    Only nodes that are applicable according to the rule's ``NodeFilter`` helper.
    method are tracked.
    """
    __slots__ = 'consts', 'filter',
    _attr = 'apcs'
    _valuetype = dmap

    class Consts(BranchCache[set[Constant]]):
        _valuetype = set
        __slots__ = EMPTY_SET

    def __init__(self, rule: Rule):
        super().__init__(rule)
        # fail fast if the rule does not have a filter.
        self.filter = rule.helpers[FilterHelper]
        self.consts = self.Consts(rule)
        rule.on(RuleEvent.AFTER_APPLY, self.__after_apply)
        rule.tableau.on(TabEvent.AFTER_NODE_ADD, self)

    def __after_apply(self, target: Target):
        if target.get('flag'): return
        self[target.branch][target.node].discard(target.constant)

    def __call__(self, node: Node, branch: Branch):
        if self.filter(node, branch):
            if node not in self[branch]:
                # By tracking per node, we are tracking per world, a fortiori.
                self[branch][node] = self.consts[branch].copy()
        s: Sentence = node.get('sentence')
        if not s: return
        consts = s.constants - self.consts[branch]
        if len(consts):
            for node in self[branch]:
                self[branch][node].update(consts)
            self.consts[branch].update(consts)

class MaxWorldsTracker:
    """
    Project the maximum number of worlds required for a branch by examining the
    branches after the trunk is built.
    """
    __slots__ = 'rule', 'branch_max_worlds', 'modal_complexities'
    _attr = 'maxw'

    modal_operators = setf(BaseModel.modal_operators)

    def __init__(self, rule, *args, **kw):
        self.rule = rule
        # Track the maximum number of worlds that should be on the branch
        # so we can halt on infinite branches.
        self.branch_max_worlds = {}
        # Cache the modal complexities
        self.modal_complexities = {}

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
        return max_worlds != None and branch.world_count >= max_worlds

    def max_worlds_exceeded(self, branch: Branch):
        """
        Whether we have exceeded the max number of worlds projected for the
        branch (origin).
        """
        max_worlds = self.get_max_worlds(branch)
        return max_worlds != None and branch.world_count > max_worlds

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

    # Helper implementation

    def after_trunk_build(self, tableau: Tableau):
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

class EllipsisExampleHelper:
    # TODO: fix for closure rules
    mynode = {'ellipsis': True}
    closenodes = []

    def __init__(self, rule: Rule, *args, **kw):
        self.rule = rule
        self.applied: set[Branch] = set()
        self.isclosure = isinstance(rule, ClosingRule)
        if self.isclosure:
            self.closenodes = list(
                dict(n)
                for n in reversed(rule.example_nodes())
            )
        self.istrunk = False

    def before_trunk_build(self, *_):
        self.istrunk = True

    def after_trunk_build(self, *_):
        self.istrunk = False

    def after_branch_add(self, branch: Branch):
        if self.applied:
            return
        if len(self.closenodes) == 1:
            self.__addnode(branch)        

    def after_node_add(self, node: Node, branch: Branch):
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

    def before_apply(self, target: Target):
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

def _targets_from_nodes_iter(fget_node_targets: Callable[P, Any]) -> Callable[P, Iterator[Target]]:
    def targets_iter(rule: Rule, nodes: Iterable[Node], branch: Branch):
        for node in nodes:
            results = fget_node_targets(rule, node, branch)
            if not results:
                # Filter anything falsy.
                continue
            if isinstance(results, Mapping):
                # Single target result.
                yield Target(results, rule = rule, branch = branch, node = node)
                continue
            instcheck(results, (Sequence, Iterator))
            # Multiple targets result.
            for res in filter(bool, results):
                assert isinstance(res, Mapping)
                # Filter anything falsy.
                yield Target(res, rule = rule, branch = branch, node = node)

    return targets_iter

del(abstract, final, overload, static)