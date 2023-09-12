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
pytableaux.proof.rules
^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from abc import abstractmethod
from collections import deque
from typing import TYPE_CHECKING, Generic, Iterable, TypeVar, final

from ..lang import (Atomic, Constant, Marking, Operated, Operator, Predicate,
                    Predicated, Quantified, Quantifier, Sentence)
from ..tools import EMPTY_SET, abcs, group, wraps
from . import WorldPair, adds, anode, filters, sdwgroup, sdwnode
from .common import AccessNode, Branch, Node, Target, SentenceNode
from .tableaux import Rule

if TYPE_CHECKING:
    from typing import overload

__all__ = (
    'BaseClosureRule',
    'BaseNodeRule',
    'ClosingRule',
    'ExtendedQuantifierRule',
    'GetNodeTargetsRule',
    'NarrowQuantifierRule',
    'OperatedSentenceRule',
    'PredicatedSentenceRule',
    'QuantifiedSentenceRule',
    'Rule')

_NT = TypeVar('_NT', bound=Node)
_ST = TypeVar('_ST', bound=Sentence)

FIRST_CONST_SET = frozenset({Constant.first()})

class NoopRule(Rule):
    "Rule stub that does not apply."

    branching = 0

    def _get_targets(self, branch: Branch, /):
        "Yields from empty set."
        yield from EMPTY_SET

    def _apply(self, target: Target, /):
        "Noop apply."
        pass

    def example_nodes(self):
        "Yields from empty set."
        yield from EMPTY_SET

class ClosingRule(Rule):
    'A closing rule has a fixed ``_apply()`` that marks the branch as closed.'

    closure = True
    defaults = dict(is_rank_optim = False)

    @final
    def _apply(self, target: Target, /):
        "Closes the branch."
        target.branch.close()

    @abstractmethod
    def nodes_will_close_branch(self, nodes: Iterable[Node], branch: Branch, /) -> bool:
        """For calculating a target's closure score.
        """
        return False

from .helpers import (AdzHelper, BranchTarget, FilterHelper, MaxConsts,
                      MaxWorlds, NodeConsts, NodeCount, PredNodes, QuitFlag,
                      UnserialWorlds, WorldIndex)


class BaseClosureRule(ClosingRule):

    Helpers = group(BranchTarget)

    def _get_targets(self, branch: Branch, /):
        """Yield the cached target from ``BranchTarget`` helper as a
        singleton, if any.
        """
        target = self[BranchTarget][branch]
        if target is not None:
            yield target

    def nodes_will_close_branch(self, nodes: Iterable[Node], branch: Branch, /) -> bool:
        """For calculating a target's closure score. This default
        implementation delegates to the abstract ``node_will_close_branch()``.

        Note that this is may be called before the node is added to the branch,
        for example, to determine whether to apply a rule.
        """
        for node in nodes:
            if self.node_will_close_branch(node, branch):
                return True
        return False

    @abstractmethod
    def node_will_close_branch(self, node: Node, branch: Branch, /) -> bool:
        return False

    @abstractmethod
    def _branch_target_hook(self, node: Node, branch: Branch, /) -> Target|None:
        'Method for ``BranchTarget`` helper.'
        pass

    def group_score(self, target: Target, /) -> float:
        # Called in tableau
        return 1.0 #??
        # return self.score_candidate(target) / max(1, 1 + self.branching)

    def score_candidate(self, target: Target, /) -> float:
        # Closure rules have is_rank_optim = False by default.
        return 0.0

class FindClosingNodeRule(BaseClosureRule):
    """For closure rules that apply to two nodes, for example, a contradictory
    node. This creates a target with a 'nodes' attribute.
    """

    def node_will_close_branch(self, node, branch, /):
        return bool(self._find_closing_node(node, branch))

    def _branch_target_hook(self, node, branch, /):
        nnode = self._find_closing_node(node, branch)
        if nnode is not None:
            return Target(nodes=(node, nnode), branch=branch)

    @abstractmethod
    def _find_closing_node(self, node: Node, branch: Branch, /) -> Node|None:
        pass

class BaseSimpleRule(Rule):

    Helpers = group(AdzHelper)
    ticking = True

    def _apply(self, target: Target, /) -> None:
        'Delegates to ``AdzHelper._apply()``.'
        self[AdzHelper]._apply(target)

    def score_candidate(self, target: Target, /) -> float:
        'Uses ``AdzHelper.closure_score()`` to score the candidate target.'
        return self[AdzHelper].closure_score(target)

class BaseNodeRule(BaseSimpleRule):

    Helpers = group(FilterHelper)
    NodeFilters = ()
    ignore_ticked = True
    '(FilterHelper) Whether to ignore all ticked nodes.'

    def example_nodes(self):
        'Delegates to ``(FilterHelper.example_node(),)``'
        yield self[FilterHelper].example_node()

class BaseSentenceRule(BaseNodeRule, Generic[_ST]):

    NodeFilters = group(filters.NodeSentence)

    negated: bool|None = None
    operator: Operator|None = None
    quantifier: Quantifier|None = None
    predicate: Predicate|None = None
    designation: bool|None = None

    def sentence(self, node: Node, /) -> _ST:
        'Delegates to ``filters.SentenceNode`` of ``FilterHelper``.'
        return self[FilterHelper].config.filters[filters.NodeSentence].sentence(node)

class PredicatedSentenceRule(BaseSentenceRule[Predicated]):
    Helpers = group(PredNodes)

class QuantifiedSentenceRule(BaseSentenceRule[Quantified]): pass
class OperatedSentenceRule(BaseSentenceRule[Operated]): pass

class GetNodeTargetsRule(BaseNodeRule, Generic[_NT]):

    @FilterHelper.node_targets
    def _get_targets(self, node: Node, branch: Branch, /):
        """Wrapped by ``@FilterHelper.node_targets`` and delegates to abstract method
        ``_get_node_targets()``.
        """
        return self._get_node_targets(node, branch)

    @abstractmethod
    def _get_node_targets(self, node: _NT, branch: Branch, /):
        yield from EMPTY_SET

class NarrowQuantifierRule(GetNodeTargetsRule[SentenceNode], QuantifiedSentenceRule):

    Helpers = (FilterHelper, QuitFlag, MaxConsts)

    @FilterHelper.node_targets
    def _get_targets(self, node: Node, branch: Branch):
        if self[MaxConsts].is_exceeded(branch, node.get(Node.Key.world)):
            self[FilterHelper].release(node, branch)
            if not self[QuitFlag].get(branch):
                fnode = self[MaxConsts].quit_flag(branch)
                yield Target(adds(group(fnode),
                    flag=fnode[Node.Key.flag],
                    branch=branch,
                    rule=self))
            return
        yield from self._get_node_targets(node, branch)

    def score_candidate(self, target: Target):
        return -1.0 * self.tableau.branching_complexity(target.node)

class ExtendedQuantifierRule(NarrowQuantifierRule):

    ticking = False
    Helpers = (AdzHelper, NodeConsts, NodeCount)

    def _get_node_targets(self, node: Node, branch: Branch):
        unapplied = self[NodeConsts][branch][node]
        if branch.constants and not unapplied:
            # Do not release the node from filters, since new constants can appear.
            return
        constants = unapplied or FIRST_CONST_SET
        for c in constants:
            nodes = deque(self._get_constant_nodes(node, c, branch))
            if unapplied or not branch.all(nodes):
                yield Target(adds(nodes,
                    constant=c,
                    branch=branch))

    @abstractmethod
    def _get_constant_nodes(self, node: Node, c: Constant, branch: Branch, /) -> Iterable[Node]:
        yield from EMPTY_SET

    def score_candidate(self, target: Target) -> float:
        if target.get(Node.Key.flag):
            return 1.0
        if self[AdzHelper].closure_score(target) == 1:
            return 1.0
        node_apply_count = self[NodeCount][target.branch][target.node]
        return 1 / (node_apply_count + 1)


class DefaultNodeRule(GetNodeTargetsRule[SentenceNode], Generic[_ST], intermediate=True):
    """Default node rule with:
    
    - BaseSimpleRule:
        - `_apply()` delegates to AdzHelper's `_apply()`. ticking is default True
        - `score_candidate()` delegates to AdzHelper's `closure_score()`
    - BaseNodeRule:
        - loads FilterHelper. ignore_ticked is default True
        - `example_nodes()` delegates to FilterHelper.
    - GetNodeTargetsRule:
        - `_get_targets()` wrapped by FilterHelper, then delegates to
        abstract `_get_node_targets()`.
    - DefaultNodeRule (this rule):
        - uses autoattrs to set attrs from the rule name.
        - implements `_get_node_targets()` with optional `_get_sd_targers()`.
            NB it is not marked as abstract but will throw NotImplementError.
        - adds a NodeDesignation filter.
    """
    NodeFilters = group(filters.NodeDesignation, filters.NodeType)
    autoattrs = True

    def _get_node_targets(self, node: SentenceNode, branch: Branch, /):
        return self._get_sdw_targets(self.sentence(node), node['designated'], node.get('world'))

    def _get_sdw_targets(self, s: _ST, d: bool, w: int|None, /):
        return self._get_sd_targets(s, d)

    def _get_sd_targets(self, s: _ST, d: bool, /):
        raise NotImplementedError

class QuantifierNodeRule(DefaultNodeRule[Quantified], QuantifiedSentenceRule, intermediate=True): pass
class QuantifierSkinnyRule(NarrowQuantifierRule, QuantifierNodeRule, intermediate=True): pass
class QuantifierFatRule(ExtendedQuantifierRule, QuantifierNodeRule, intermediate=True): pass

class OperatorNodeRule(DefaultNodeRule[Operated], OperatedSentenceRule, intermediate=True):

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        pass
        if abcs.isabstract(cls):
            return
        if all(
            getattr(cls, name) is getattr(__class__, name)
            for name in (
                '_get_targets',
                '_get_node_targets',
                '_get_sdw_targets',
                '_get_sd_targets')):
                @abstractmethod
                @wraps(cls._get_sd_targets)
                def wrapped(self, s: Sentence, d: bool, /):
                    raise NotImplementedError
                setattr(cls, '_get_sd_targets', wrapped)

class FlippingRule(OperatorNodeRule, intermediate=True):

    def _get_sdw_targets(self, s, d, w, /):
        yield adds(sdwgroup((s, not d, w)))

class NegatingFlippingRule(OperatorNodeRule, intermediate=True):

    def _get_sdw_targets(self, s, d, w, /):
        yield adds(sdwgroup((~s, not d, w)))

class OperandsRule(OperatorNodeRule, intermediate=True):

    def _get_sdw_targets(self, s, d, w, /):
        yield adds(sdwgroup(*((s, d, w) for s in s)))

class FlippingOperandsRule(OperatorNodeRule, intermediate=True):

    def _get_sdw_targets(self, s, d, w, /):
        yield adds(sdwgroup(*((s, not d, w) for s in s)))

class NegatingOperandsRule(OperatorNodeRule, intermediate=True):

    def _get_sdw_targets(self, s, d, w, /):
        yield adds(sdwgroup(*((~s, d, w) for s in s)))

class BranchingOperandsRule(OperatorNodeRule, intermediate=True):

    def _get_sdw_targets(self, s, d, w, /):
        yield adds(*(map(sdwgroup, ((s, d, w) for s in s))))

class NegatingBranchingOperandsRule(OperatorNodeRule, intermediate=True):

    def _get_sdw_targets(self, s, d, w, /):
        yield adds(*(map(sdwgroup, ((~s, d, w) for s in s))))

class ConjunctionReducingRule(OperatorNodeRule, intermediate=True):

    conjoined: Operator

    def _get_sdw_targets(self, s, d, w, /):
        oper = self.conjoined
        lhs, rhs = s
        s = oper(lhs, rhs) & oper(rhs, lhs)
        if self.negated:
            s = ~s
        yield adds(sdwgroup((s, d, w)))

class MaterialConditionalConjunctsReducingRule(ConjunctionReducingRule, intermediate=True):
    conjoined = Operator.MaterialConditional

class ConditionalConjunctsReducingRule(ConjunctionReducingRule, intermediate=True):
    conjoined = Operator.Conditional

class MaterialConditionalReducingRule(OperatorNodeRule, intermediate=True):
    "This rule reduces to a disjunction."

    def _get_sdw_targets(self, s, d, w, /):
        sn = ~s.lhs | s.rhs
        if self.negated:
            sn = ~sn
        yield adds(sdwgroup((sn, d, w)))

class ModalOperatorRule(OperatorNodeRule, intermediate=True):

    Helpers = (QuitFlag, MaxWorlds)

    @FilterHelper.node_targets
    def _get_targets(self, node: Node, branch: Branch, /):
        """Wrapped by ``@FilterHelper.node_targets``. Checks MaxWorlds,
        and delegates to abstract method ``_get_node_targets()``.
        """
        # Check for max worlds reached
        res = self._check_maxworlds(node, branch)
        if res:
            if res is not True:
                yield res
            return
        yield from self._get_node_targets(node, branch)

    @abstractmethod
    def _get_node_targets(self, node: Node, branch: Branch, /) -> Iterable[Target]:
        yield from EMPTY_SET

    if TYPE_CHECKING:
        @overload
        def new_designation(self, d: bool) -> bool: ...
        @overload
        def new_negated(self, v: bool) -> bool: ...

    new_designation = staticmethod(bool)
    new_negated = staticmethod(bool)

    def _check_maxworlds(self, node: Node, branch: Branch, /) -> bool|dict:
        # Check for max worlds reached
        if self[MaxWorlds].is_exceeded(branch):
            self[FilterHelper].release(node, branch)
            if not self[QuitFlag].get(branch):
                fnode = self[MaxWorlds].quit_flag(branch)
                return adds(group(fnode), flag=fnode[Node.Key.flag])
            return True
        return False

class BaseAccessRule(BaseSimpleRule, intermediate=True):
    Helpers = (MaxWorlds)
    ignore_ticked = False
    ticking = False

class AccessNodeRule(GetNodeTargetsRule[AccessNode], BaseAccessRule, intermediate=True):

    Helpers = (WorldIndex)

    @FilterHelper.node_targets
    def _get_targets(self, node: Node, branch: Branch, /):
        if self[MaxWorlds].is_exceeded(branch):
            self[FilterHelper].release(node, branch)
            return
        yield from self._get_node_targets(node, branch)

class access:

    class Serial(BaseAccessRule, intermediate=True):
        """
        The Serial rule applies to a an open branch *b* when there is a world *w*
        that appears on *b*, but there is no world *w'* such that *w* accesses *w'*.

        The exception to this is when the Serial rule was the last rule to apply to
        the branch. This prevents infinite repetition of the Serial rule for open
        branches that are otherwise finished. For this reason, the Serial rule is
        ordered last in the rules, so that all other rules are checked before it.

        For a node *n* on an open branch *b* on which appears a world *w* for
        which there is no world *w'* on *b* such that *w* accesses *w'*, add a
        node to *b* with *w* as world1, and *w1* as world2, where *w1* does not
        yet appear on *b*.
        """
        Helpers = (UnserialWorlds)
        marklegend = [(Marking.tableau, ('access', 'serial'))]

        def _get_targets(self, branch: Branch, /):
            if not self._should_apply(branch):
                return
            for w in self[UnserialWorlds][branch]:
                yield Target(adds(
                    group(anode(w, branch.new_world())),
                    world=w,
                    branch=branch))

        def _should_apply(self, branch: Branch,/):
            try:
                entry = next(reversed(self.tableau.history))
            except StopIteration:
                pass
            else:
                # This tends to stop modal explosion better than the max worlds check,
                # at least in its current form (all modal operators + worlds + 1).
                if entry.rule == self and entry.target.branch == branch:
                    return False
            # As above, this is unnecessary
            if self[MaxWorlds].is_exceeded(branch):
                return False
            return True

        def example_nodes(self):
            yield sdwnode(Atomic.first(), None, 0)


    class Reflexive(AccessNodeRule, intermediate=True):

        marklegend = [(Marking.tableau, ('access', 'reflexive'))]
        defaults = dict(is_rank_optim = False)

        def _get_node_targets(self, node, branch, /):
            for w in node.worlds():
                pair = WorldPair(w, w)
                if self[WorldIndex].has(branch, pair):
                    self[FilterHelper].release(node, branch)
                    continue
                yield adds(group(pair.tonode()), world=w)

        def example_nodes(self):
            yield sdwnode(Atomic.first(), None, 0)

    class Transitive(AccessNodeRule, intermediate=True):

        NodeFilters = group(filters.NodeType)
        NodeType = AccessNode
        marklegend = [(Marking.tableau, ('access', 'transitive'))]

        def _get_node_targets(self, node, branch, /):
            w1, w2 = pair = node.pair()
            for w3 in self[WorldIndex].intransitives(branch, pair):
                nnode = anode(w1, w3)
                yield adds(group(nnode),
                    nodes=(node, branch.find(anode(w2, w3))),
                    **nnode)

        def score_candidate(self, target, /):
            # Rank the highest world
            return float(target.world2)

        def example_nodes(self):
            yield anode(0, 1)
            yield anode(1, 2)

    class Symmetric(AccessNodeRule, intermediate=True):

        NodeFilters = group(filters.NodeType)
        NodeType = AccessNode
        marklegend = [(Marking.tableau, ('access', 'symmetric'))]
        defaults = dict(is_rank_optim = False)

        def _get_node_targets(self, node, branch,/):
            pair = node.pair().reversed()
            if self[WorldIndex].has(branch, pair):
                self[FilterHelper].release(node, branch)
                return
            nnode = pair.tonode()
            yield adds(group(nnode), **nnode)
