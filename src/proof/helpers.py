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

from lexicals import Constant, Sentence
from models import BaseModel
from tools.abcs import abcm, abcf
from tools.mappings import MapAttrView
from tools.sets import EMPTY_SET
from utils import orepr

from .common import Access, Branch, Comparer, Node, RuleEvent, TabEvent, Target
from .tableaux import Rule, Tableau

from copy import copy
from collections.abc import (
    Callable, Iterable, Iterator, MutableMapping, ItemsView, KeysView, ValuesView
)
from itertools import chain
from typing import TypeVar

T = TypeVar('T')

class AdzHelper:

    _attr = 'adz'
    __slots__ = 'rule', 'tableau'

    def __init__(self, rule: Rule, *args, **kw):
        self.rule: Rule = rule
        self.tableau: Tableau = rule.tableau

    def _apply(self, target: Target):
        branch: Branch = target.branch
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

    def closure_score(self, target: Target) -> float:
        try:
            rules = self.tableau.rules.closure
        except AttributeError:
            rules = EMPTY_SET
        close_count = 0
        for nodes in target['adds']:
            nodes = tuple(Node(node) for node in nodes)
            for rule in rules:
                if rule.nodes_will_close_branch(nodes, target.branch):
                    close_count += 1
                    break
        return float(close_count / min(1, len(target['adds'])))

class BranchCache(MutableMapping[Branch, T]):

    _valuetype = bool

    rule: Rule
    tab: Tableau
    __cache: dict[Branch, T]

    __slots__ = '__cache', 'rule', 'tab'

    def __init__(self, *args, **kw):
        pass

    def get(self, branch: Branch, *args):
        return self.__cache.get(branch, *args)

    def keys(self) -> KeysView[Branch]:
        return self.__cache.keys()

    def values(self) -> ValuesView[T]:
        return self.__cache.values()

    def items(self) -> ItemsView[Branch, T]:
        return self.__cache.items()

    def __getitem__(self, branch: Branch) -> T:
        return self.__cache[branch]

    def __setitem__(self, branch: Branch, value: T):
        self.__cache[branch] = value

    def __delitem__(self, branch: Branch):
        del(self.__cache[branch])

    def __contains__(self, branch: Branch):
        return branch in self.__cache

    def __len__(self):
        return len(self.__cache)

    def __iter__(self) -> Iterator[Branch]:
        return iter(self.__cache)

    def __reversed__(self) -> Iterator[Branch]:
        return reversed(self.__cache)

    def __new__(cls, rule: Rule, *args):
        inst = super().__new__(cls)
        inst.__cache = {}
        inst.rule = rule
        inst.tab = rule.tableau
        def after_branch_add(branch: Branch):
            if branch.parent:
                inst[branch] = copy(inst[branch.parent])
            else:
                inst[branch] = inst._valuetype()
        def after_branch_close(branch: Branch):
            del(inst[branch])
        inst.tab.on({
            TabEvent.AFTER_BRANCH_ADD  : after_branch_add,
            TabEvent.AFTER_BRANCH_CLOSE: after_branch_close,
        })
        return inst

    # @abstract
    # def __copy__(self): ... # not clear whether to copy listeners

    def __hash__(self):
        return hash(id(self))

    def __repr__(self):
        return orepr(self, self._reprdict())

    def _reprdict(self) -> dict:
        return {'branches': len(self)}

class BranchDictCache(BranchCache):
    """
    Copies each value.
    """
    _valuetype = dict

    __slots__ = EMPTY_SET

    def __new__(cls, rule: Rule, *args):
        inst = super().__new__(cls, rule)
        def after_branch_add(branch: Branch):
            if branch.parent:
                for key in inst[branch]:
                    inst[branch][key] = copy(inst[branch.parent][key])
        inst.tab.on(TabEvent.AFTER_BRANCH_ADD, after_branch_add)
        return inst

    def __getitem__(self, branch: Branch) -> dict:
        return super().__getitem__(branch)

class FilterNodeCache(BranchCache):

    _valuetype = set
    
    # Induced Rule Properties

    __ignore_ticked: bool|None

    __slots__ = '__ignore_ticked',

    @property
    def ignore_ticked(self):
        if self.__ignore_ticked is not None:
            return self.__ignore_ticked
        return getattr(self.rule, 'ignore_ticked', None)

    @ignore_ticked.setter
    def ignore_ticked(self, val):
        self.__ignore_ticked = val

    def __new__(cls, rule: Rule, *args):
        inst: FilterNodeCache = super().__new__(cls, rule)
        inst.__ignore_ticked = None
        def after_node_add(node: Node, branch: Branch):
            if inst(node, branch):
                inst[branch].add(node)
        def after_node_tick(node: Node, branch: Branch):
            if inst.ignore_ticked:
                inst[branch].discard(node)
        inst.tab.on({
            TabEvent.AFTER_NODE_ADD: after_node_add,
            TabEvent.AFTER_NODE_TICK: after_node_tick,
        })
        return inst

    @abcm.abstract
    def __call__(self, *args, **kw): ...

    def __getitem__(self, branch: Branch) -> set[Node]:
        return super().__getitem__(branch)

@abcm.final
class AppliedQuitFlag(BranchCache):
    """
    Track the application of a flag node by the rule for each branch. A branch
    is considered flagged when the target has a non-empty ``flag`` property.
    """
    _valuetype = bool
    _attr = 'apqf'

    __slots__ = EMPTY_SET

    def __new__(cls, rule: Rule, *args):
        inst = super().__new__(cls, rule)
        inst.rule.on(RuleEvent.AFTER_APPLY, inst)
        return inst

    def __call__(self, target: Target):
        self[target.branch] = bool(target.get('flag'))

@abcm.final
class AppliedSentenceCounter(BranchCache):
    """
    Count the times the rule has applied for a sentence per branch. This tracks
    the `sentence` property of the rule's target. The target should also include
    the `branch` key.
    """
    _valuetype = dict
    _attr = 'apsc'

    __slots__ = EMPTY_SET

    def __new__(cls, rule: Rule, *args):
        inst = super().__new__(cls, rule)
        inst.rule.on(RuleEvent.AFTER_APPLY, inst)
        return inst

    def __call__(self, target: Target):
        if target.get('flag'):
            return
        counts = self[target.branch]
        sentence = target.sentence
        counts[sentence] = counts.get(sentence, 0) + 1

    def __getitem__(self, branch: Branch) -> dict[Sentence, int]:
        return super().__getitem__(branch)

@abcm.final
class AppliedNodeCount(BranchCache):

    _valuetype = dict
    _attr = 'apnc'

    __slots__ = EMPTY_SET

    def min(self, branch: Branch) -> int:
        if branch in self and len(self[branch]):
            return min(self[branch].values())
        return 0

    def isleast(self, node: Node, branch: Branch) -> bool:
        return self.min(branch) >= self[branch].get(node, 0)

    def __new__(cls, rule: Rule, *args):
        inst = super().__new__(cls, rule)
        inst.rule.on(RuleEvent.AFTER_APPLY, inst)
        return inst

    def __call__(self, target: Target):
        if target.get('flag'):
            return
        counts = self[target.branch]
        node = target.node
        counts[node] = counts.get(node, 0) + 1

    def __getitem__(self, branch: Branch) -> dict[Node, int]:
        return super().__getitem__(branch)

@abcm.final
class AppliedNodesWorlds(BranchCache):
    """
    Track the nodes applied to by the rule for each world on the branch. The
    target must have `node`, and `world` attributes. The values of the cache
    are ``(node, world)`` pairs.
    """
    _valuetype = set
    _attr = 'apnw'

    __slots__ = EMPTY_SET

    def __new__(cls, rule: Rule, *args):
        inst = super().__new__(cls, rule)
        inst.rule.on(RuleEvent.AFTER_APPLY, inst)
        return inst

    def __call__(self, target: Target):
        if target.get('flag'):
            return
        self[target.branch].add((target.node, target.world))

    def __getitem__(self, branch: Branch) -> set[tuple[Node, int]]:
        return super().__getitem__(branch)

@abcm.final
class UnserialWorldsTracker(BranchCache):
    """
    Track the unserial worlds on the branch.
    """
    _valuetype = set
    _attr = 'ust'

    __slots__ = EMPTY_SET

    def __new__(cls, rule: Rule, *args):
        inst = super().__new__(cls, rule)
        inst.tab.on(TabEvent.AFTER_NODE_ADD, inst)
        return inst

    def __call__(self, node: Node, branch: Branch):
        for w in node.worlds:
            if node.get('world1') == w or branch.has({'world1': w}):
                self[branch].discard(w)
            else:
                self[branch].add(w)

    def __getitem__(self, branch: Branch) -> set[int]:
        return super().__getitem__(branch)

@abcm.final
class VisibleWorldsIndex(BranchDictCache):
    """
    Index the visible worlds for each world on the branch.
    """
    _attr = 'visw'

    class Nodes(BranchCache):

        _valuetype = dict

        __slots__ = EMPTY_SET

        def __call__(self, node: Node, branch: Branch):
            self[branch][Access.fornode(node)] = node

        def __getitem__(self, branch: Branch) -> dict[Access, Node]:
            return super().__getitem__(branch)

    nodes: Nodes

    __slots__ = 'nodes',

    def has(self, branch: Branch, access: Access) -> bool:
        """
        Whether w1 sees w2 on the given branch.

        :param Branch branch:
        :param int w1:
        :param int w2:
        :rtype: bool
        """
        return access[1] in self[branch].get(access[0], EMPTY_SET)

    def intransitives(self, branch: Branch, w1: int, w2: int) -> set[int]:
        """
        Get all the worlds on the branch that are visible to w2, but are not
        visible to w1.
        """
        # TODO: can we make this more efficient? for each world pair,
        #       track the intransitives?
        return self[branch].get(w2, EMPTY_SET).difference(
            self[branch].get(w1, EMPTY_SET)
        )

    def __new__(cls, rule: Rule, *args):
        inst: __class__ = super().__new__(cls, rule)
        inst.tab.on(TabEvent.AFTER_NODE_ADD, inst)
        inst.nodes = __class__.Nodes(rule, *args)
        return inst

    def __call__(self, node: Node, branch: Branch):        
        if node.is_access:
            w1, w2 = Access.fornode(node)
            if w1 not in self[branch]:
                self[branch][w1] = set()
            self[branch][w1].add(w2)
            self.nodes(node, branch)

    def __getitem__(self, branch: Branch) -> dict[int, set[int]]:
        return super().__getitem__(branch)

@abcm.final
class PredicatedNodesTracker(FilterNodeCache):
    """
    Track all predicated nodes on the branch.
    """
    _attr = 'pn'
    __slots__ = EMPTY_SET
    def __call__(self, node: Node, *a, **kw) -> bool:
        s: Sentence = node.get('sentence')
        return s != None and s.is_predicated

@abcm.final
class FilterHelper(FilterNodeCache):
    """
    Set configurable and chainable filters in ``NodeFilters``
    class attribute.
    """
    clsattr_node = 'NodeFilters'
    _attr = 'nf'

    __slots__ = 'callcount', '__fmap', 'filters', '__to_discard'

    rule: Rule
    callcount: int
    __fmap: dict
    filters: MapAttrView[Comparer]
    __to_discard: set

    def __call__(self, node: Node, branch: Branch) -> bool:
        return self.filter(node, branch)


    # Decorators

    @classmethod
    def node_targets(cls, fget_node_targets: Callable) -> Callable:
        """
        Method decorator to only iterate through nodes matching the
        configured FilterHelper filters.

        The rule may return a falsy value for no targets, a single
        target (True, non-empty dict, Target), an iterator or an
        iterable.
        
        Returns a flat list of targets.
        """
        fiter_targets = _targets_from_nodes_iter(fget_node_targets)
        def get_targets_filtered(rule: Rule, branch: Branch) -> list:
            helper: FilterHelper = rule.helpers[cls]
            helper.gc()
            nodes = helper[branch]
            return tuple(fiter_targets(rule, nodes, branch))
        return get_targets_filtered

    def filter(self, node: Node, branch: Branch) -> bool:
        self.callcount += 1
        if self.ignore_ticked and branch.is_ticked(node):
            return False
        for filt in self.__fmap.values():
            if not filt(node):
                return False
        return True

    def example_node(self) -> dict:
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

    def __init__(self, rule: Rule, attr: str = None, *args, **kw):
        super().__init__(rule, *args, **kw)
        self.rule = rule
        self.callcount = 0
        self.__fmap = {}#OrderedDict()
        self.filters = MapAttrView(self.__fmap)
        self.__to_discard = set()
        rawvalue = getattr(rule, self.__class__.clsattr_node, EMPTY_SET)
        for item in rawvalue:
            if isinstance(item, type):
                item = (None, item)
            name, cls = item
            self._add_filter(cls, name)

    def _add_filter(self, cls: type[Comparer], name: str = None):
        """
        Instantiate a filter class from the NodeFilters config.
        """
        if name == None:
            name = cls.__name__.lower()
        if name in self.__fmap:
            raise KeyError('%s exists' % name)
        if not isinstance(name, str):
            raise TypeError('name not a string')
        filt = cls(self.rule)
        self.__fmap[name] = filt
        # self.__flist.append(filt)

    def _reprdict(self) -> dict:
        return super()._reprdict() | {
            'filters': '(%s) %s' % (len(self.filters), self.__fmap),
        }

class Delegates:
    """
    Mixin Rule classes to delegate to helper methods.
    """

    class AdzHelper:

        class Apply(Rule):
            """
            Delegates ``_apply()`` to ``AdzHelper._apply()``.
            """
            Helpers = (AdzHelper,)
            adz: AdzHelper

            #: Whether the target node should be ticked after application.
            #:
            #: :type: bool
            ticking = True

            def _apply(self, target: Target):
                """
                :implements: Rule
                """
                self.adz._apply(target)

        class ClosureScore(Rule):
            """
            Delegates ``score_candidate()`` to ``AdzHelper.closure_score()``.
            """
            Helpers = (AdzHelper,)
            adz: AdzHelper

            def score_candidate(self, target: Target) -> float:
                """
                :overrides: Rule
                """
                return self.adz.closure_score(target)

    class FilterHelper:

        class Sentence(Rule):
            """
            Delegates ``sentence()`` to ``FilterHelper.sentence()``.
            """
            Helpers = (FilterHelper,)
            nf: FilterHelper

            def sentence(self, node: Node) -> Sentence:
                """
                :overrides: Rule
                """
                return self.nf.filters['sentence'].get(node)

        class ExampleNodes(Rule):
            """
            Delegates ``example_nodes()`` to ``FilterHelper.example_nodes()``.
            """
            Helpers = (FilterHelper,)
            nf: FilterHelper

            def example_nodes(self) -> tuple[dict]:
                """
                :implements: Rule
                """
                return (self.nf.example_node(),)

def populate_delegates():
    from inspect import getmembers, isclass
    modclasses = {
        clsname: cls for clsname, cls in globals().items()
        if isclass(cls) and cls.__module__ == __name__
    }
    for helpername, delegates in getmembers(Delegates, isclass)[0:-1]:
        helpercls = modclasses[helpername]
        for name, cls in getmembers(delegates, isclass)[0:-1]:
            setattr(helpercls, name, cls)
populate_delegates()
del(populate_delegates)

class NodeTargetCheckHelper:
    """
    Calls the rule's ``check_for_target(node, branch)`` when a node is added to
    a branch. If a target is returned, it is cached relative to the branch. The
    rule can then call ``cached_target(branch)``  on the helper to retrieve the
    target. This is used primarily in closure rules for performance.

    NB: The rule must implement ``check_for_target(self, node, branch)``.
    """
    _attr = 'ntch'
    def __init__(self, rule: Rule, *args, **kw):
        self.rule = rule
        self.targets = {}

    def cached_target(self, branch: Branch):
        """
        Return the cached target for the branch, if any.
        """
        if branch in self.targets:
            return self.targets[branch]

    def get(self, branch: Branch, default = None) -> Target:
        return self.targets.get(branch, default)

    def __contains__(self, branch: Branch):
        return branch in self.targets

    def __len__(self):
        return len(self.targets)

    def __iter__(self) -> Iterator[Branch]:
        return iter(self.targets)

    def __getitem__(self, branch: Branch) -> Target:
        return self.targets[branch]
    # Event Listeners

    def after_node_add(self, node: Node, branch: Branch):
        target = self.rule.check_for_target(node, branch)
        if target:
            self.targets[branch] = target

class MaxConstantsTracker:
    """
    Project the maximum number of constants per world required for a branch
    by examining the branches after the trunk is built.
    """
    _attr = 'maxc'

    def __init__(self, rule: Rule, *args, **kw):
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
        try:
            return self.branch_max_constants[branch.origin]
        except KeyError:
            return 1

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
        :rtype: bool
        """
        if world == None:
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
        :rtype: bool
        """
        if world == None:
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
            if world == None:
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

class AppliedNodeConstants(object):
    """
    Track the applied and unapplied constants per branch for each potential node.
    The rule's target should have `branch`, `node` and `constant` properties.

    Only nodes that are applicable according to the rule's ``NodeFilter`` helper.
    method are tracked.
    """
    _attr = 'apcs'

    def __init__(self, rule, *args, **kw):
        self.rule = rule
        self.node_states = {}
        self.consts = {}

    def get_applied(self, node, branch):
        """
        Return the set of constants that have been applied to the node for the
        branch.
        """
        return self.node_states[branch][node]['applied']

    def get_unapplied(self, node, branch):
        """
        Return the set of constants that have not been applied to the node for
        the branch.
        """
        return self.node_states[branch][node]['unapplied']

    # helper implementation

    def after_branch_add(self, branch):
        parent = branch.parent
        if parent != None and parent in self.node_states:
            self.consts[branch] = set(self.consts[parent])
            self.node_states[branch] = {
                node : {
                    k : set(self.node_states[parent][node][k])
                    for k in self.node_states[parent][node]
                }
                for node in self.node_states[parent]
            }
        else:
            self.node_states[branch] = dict()
            self.consts[branch] = set()

    def after_node_add(self, node, branch):
        if self.__should_track_node(node, branch):
            if node not in self.node_states[branch]:
                # By tracking per node, we are tracking per world, a fortiori.
                self.node_states[branch][node] = {
                    'applied'   : set(),
                    'unapplied' : set(self.consts[branch]),
                }
        consts = node['sentence'].constants if node.has('sentence') else EMPTY_SET
        for c in consts:
            if c not in self.consts[branch]:
                for node in self.node_states[branch]:
                    self.node_states[branch][node]['unapplied'].add(c)
                self.consts[branch].add(c)

    def after_apply(self, target: Target):
        if target.get('flag'):
            return
        idx = self.node_states[target.branch][target.node]
        c = target['constant']
        idx['applied'].add(c)
        idx['unapplied'].discard(c)

    # private util

    def __should_track_node(self, node, branch):
        # TODO: remove cross-helper affinity
        return self.rule.nf(node, branch)

class MaxWorldsTracker(object):
    """
    Project the maximum number of worlds required for a branch by examining the
    branches after the trunk is built.
    """
    _attr = 'maxw'

    modal_operators = set(BaseModel.modal_operators)

    def __init__(self, rule, *args, **kw):
        self.rule = rule
        # Track the maximum number of worlds that should be on the branch
        # so we can halt on infinite branches.
        self.branch_max_worlds = {}
        # Cache the modal complexities
        self.modal_complexities = {}

    def get_max_worlds(self, branch):
        """
        Get the maximum worlds projected for the branch.
        """
        origin = branch.origin
        if origin.id in self.branch_max_worlds:
            return self.branch_max_worlds[origin.id]

    def max_worlds_reached(self, branch):
        """
        Whether we have already reached or exceeded the max number of worlds
        projected for the branch (origin).
        """
        max_worlds = self.get_max_worlds(branch)
        return max_worlds != None and branch.world_count >= max_worlds

    def max_worlds_exceeded(self, branch):
        """
        Whether we have exceeded the max number of worlds projected for the
        branch (origin).
        """
        max_worlds = self.get_max_worlds(branch)
        return max_worlds != None and branch.world_count > max_worlds

    def modal_complexity(self, sentence):
        """
        Compute and cache the modal complexity of a sentence by counting its
        modal operators.
        """
        if sentence not in self.modal_complexities:
            self.modal_complexities[sentence] = len([
                o for o in sentence.operators if o in self.modal_operators
            ])
        return self.modal_complexities[sentence]

    def quit_flag(self, branch):
        """
        Generate a quit flag node for the branch.
        """
        info = '{0}:MaxWorlds({1})'.format(self.rule.name, str(self.get_max_worlds(branch)))
        return {'is_flag': True, 'flag': 'quit', 'info': info}

    # Helper implementation

    def after_trunk_build(self, tableau):
        for branch in tableau:
            origin = branch.origin
            # In most cases, we will have only one origin branch.
            if origin.id in self.branch_max_worlds:
                return
            self.branch_max_worlds[origin.id] = self.__compute_max_worlds(branch)

    # Private util

    def __compute_max_worlds(self, branch):
        # Project the maximum number of worlds for a branch (origin) as
        # the number of worlds already on the branch + the number of modal
        # operators + 1.
        node_needed_worlds = sum([
            self.__compute_needed_worlds_for_node(node, branch)
            for node in branch
        ])
        return branch.world_count + node_needed_worlds + 1

    def __compute_needed_worlds_for_node(self, node, branch):
        # we only care about unticked nodes, since ticked nodes will have
        # already created any worlds.
        if not branch.is_ticked(node) and node.has('sentence'):
            return self.modal_complexity(node['sentence'])
        return 0

class EllipsisExampleHelper(object):
    # TODO: fix for closure rules
    mynode = {'ellipsis': True}
    closenodes = []

    def __init__(self, rule, *args, **kw):
        self.rule = rule
        self.applied = set()
        from .rules import ClosureRule
        self.isclosure = isinstance(rule, ClosureRule)
        if self.isclosure:#rule.is_closure:
            self.closenodes = list(
                n if isinstance(n, dict) else n.props
                for n in reversed(rule.example_nodes())
            )
        self.istrunk = False

    def before_trunk_build(self, *_):
        self.istrunk = True

    def after_trunk_build(self, *_):
        self.istrunk = False

    def after_branch_add(self, branch):
        if self.applied:
            return
        if len(self.closenodes) == 1:
            self.__addnode(branch)        

    def after_node_add(self, node, branch):
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

    def before_apply(self, target):
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

    def __addnode(self, branch):
        self.applied.add(branch)
        branch.add(self.mynode)

def _targets_from_nodes_iter(fget_node_targets: Callable) -> Callable:
    def targets_iter(rule, nodes: Iterable[Node], branch: Branch) -> Iterable[Target]:
        results = (
            Target.list(
                fget_node_targets(rule, node, branch),
                rule = rule, branch = branch, node = node
            )
            for node in nodes
        )
        return chain.from_iterable(filter(bool, results))
    return targets_iter

