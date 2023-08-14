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
from typing import Generator, Generic, Iterable, TypeVar, final

from ..lang import Constant, Operated, Predicated, Quantified, Sentence
from ..tools import group, EMPTY_SET
from . import Branch, Node, Rule, Target, adds, filters

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

_ST = TypeVar('_ST', bound=Sentence)
FIRST_CONST_SET = frozenset({Constant.first()})

class ClosingRule(Rule):
    'A closing rule has a fixed ``_apply()`` that marks the branch as closed.'

    closure = True
    _defaults = dict(is_rank_optim = False)

    @final
    def _apply(self, target: Target, /):
        "Closes the branch."
        target.branch.close()

    @abstractmethod
    def nodes_will_close_branch(self, nodes: Iterable[Node], branch: Branch, /) -> bool:
        """For calculating a target's closure score.
        """
        raise NotImplementedError

from .helpers import (AdzHelper, BranchTarget, FilterHelper, MaxConsts,
                      NodeConsts, NodeCount, PredNodes, QuitFlag)


class NoopRule(Rule):
    "Rule stub that does not apply."

    def _get_targets(self, branch: Branch, /) -> None:
        "Returns ``None``."
        pass

    def _apply(self, target: Target, /):
        "Noop apply."
        pass

    @staticmethod
    def example_nodes():
        "Returns empty set."
        return EMPTY_SET

class BaseClosureRule(ClosingRule):

    Helpers = group(BranchTarget)

    def _get_targets(self, branch: Branch, /) -> tuple[Target]:
        """Return the cached target from ``BranchTarget`` helper as a
        singleton, if any.
        """
        target = self[BranchTarget][branch]
        if target is not None:
            yield target

    def nodes_will_close_branch(self, nodes: Iterable[Node], branch: Branch, /) -> bool:
        """For calculating a target's closure score. This default
        implementation delegates to the abstract ``node_will_close_branch()``.
        """
        for node in nodes:
            if self.node_will_close_branch(node, branch):
                return True
        return False

    @abstractmethod
    def node_will_close_branch(self, node: Node, branch: Branch, /) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _branch_target_hook(self, node: Node, branch: Branch, /):
        'Method for ``BranchTarget`` helper.'
        raise NotImplementedError

    def group_score(self, target: Target, /) -> float:
        # Called in tableau
        return 1.0 #??
        # return self.score_candidate(target) / max(1, 1 + self.branching)

    def score_candidate(self, target: Target, /) -> float:
        # Closure rules have is_rank_optim = False by default.
        return 0.0

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

    def example_nodes(self) -> tuple[dict]:
        'Delegates to ``(FilterHelper.example_node(),)``'
        yield self[FilterHelper].example_node()

class BaseSentenceRule(BaseNodeRule, Generic[_ST]):

    NodeFilters = group(filters.SentenceNode)

    negated    = None
    operator   = None
    quantifier = None
    predicate  = None

    def sentence(self, node: Node, /) -> _ST:
        'Delegates to ``filters.SentenceNode`` of ``FilterHelper``.'
        return self[FilterHelper].filters[filters.SentenceNode].sentence(node)

class PredicatedSentenceRule(BaseSentenceRule[Predicated]):

    Helpers = group(PredNodes)

class QuantifiedSentenceRule(BaseSentenceRule[Quantified]):
    pass

class OperatedSentenceRule(BaseSentenceRule[Operated]):
    pass

class NarrowQuantifierRule(QuantifiedSentenceRule):

    Helpers = (QuitFlag, MaxConsts)

    @FilterHelper.node_targets
    def _get_targets(self, node: Node, branch: Branch, /):
        if self[MaxConsts].is_exceeded(branch, node.get(Node.Key.world)):
            self[FilterHelper].release(node, branch)
            if not self[QuitFlag].get(branch):
                fnode = self[MaxConsts].quit_flag(branch)
                yield adds(group(fnode), flag = fnode[Node.Key.flag])
            return
        yield from self._get_node_targets(node, branch)

    @abstractmethod
    def _get_node_targets(self, node: Node, branch: Branch):
        raise NotImplementedError

    def score_candidate(self, target: Target):
        return -1.0 * self.tableau.branching_complexity(target.node)

class ExtendedQuantifierRule(NarrowQuantifierRule):

    ticking = False

    Helpers = (NodeConsts, NodeCount)

    def _get_node_targets(self, node: Node, branch: Branch) -> Generator[dict, None, None]:
        unapplied = self[NodeConsts][branch][node]
        if branch.constants and not unapplied:
            # Do not release the node from filters, since new constants can appear.
            return
        constants = unapplied or FIRST_CONST_SET
        for c in constants:
            nodes = deque(self._get_constant_nodes(node, c, branch))
            if unapplied or not branch.all(nodes):
                yield adds(nodes, constant=c)
                # yield dict(adds = group(nodes), constant = c)

    @abstractmethod
    def _get_constant_nodes(self, node: Node, c: Constant, branch: Branch, /):
        raise NotImplementedError

    def score_candidate(self, target: Target) -> float:
        if target.get(Node.Key.flag):
            return 1.0
        if self[AdzHelper].closure_score(target) == 1:
            return 1.0
        node_apply_count = self[NodeCount][target.branch].get(target.node, 0)
        return 1 / (node_apply_count + 1)


class GetNodeTargetsRule(BaseNodeRule):

    @FilterHelper.node_targets
    def _get_targets(self, node: Node, branch: Branch, /):
        """Wrapped by ``@FilterHelper.node_targets`` and delegates to abstract method
        ``_get_node_targets()``.
        """
        return self._get_node_targets(node, branch)

    @abstractmethod
    def _get_node_targets(self, node: Node, branch: Branch, /):
        raise NotImplementedError

