from __future__ import annotations as _
from typing import Generator, Iterable

__all__ = (
    'Rule',

    'BaseClosureRule',

    'BaseNodeRule',
    'GetNodeTargetsRule',

    'PredicatedSentenceRule',
    'QuantifiedSentenceRule',
    'OperatedSentenceRule',

    'NarrowQuantifierRule',
    'ExtendedQuantifierRule',

    'group', 'adds'
)

from tools.abcs import abstract, overload, abcf, T
from lexicals import (
    Constant,
    Operated,
    Operator,
    Predicate,
    Predicated,
    Quantified,
    Quantifier,
    Sentence,
)
from proof.common import Branch, Node, Target
from proof.filters import NodeFilters
from proof.helpers import (
    AdzHelper,
    BranchTarget,
    FilterHelper,
    MaxConsts,
    NodeConsts,
    NodeCount,
    PredNodes,
    QuitFlag,
)
from proof.tableaux import ClosingRule, Rule
FIRST_CONST_SET = frozenset({Constant.first()})


class BaseClosureRule(ClosingRule):

    Helpers = BranchTarget,

    def _get_targets(self, branch: Branch):
        target = self[BranchTarget][branch]
        if target is not None:
            return target,

    def nodes_will_close_branch(self, nodes: Iterable[Node], branch: Branch):
        """For calculating a target's closure score. This default
        implementation delegates to the abstract ``node_will_close_branch()``."""
        for node in nodes:
            if self.node_will_close_branch(node, branch):
                return True
        return False

    @abstract
    def node_will_close_branch(self, node: Node, branch: Branch) -> bool:
        raise NotImplementedError
    @abstract
    def _branch_target_hook(self, node: Node, branch: Branch):
        'Method for BranchTarget helper.'
        raise NotImplementedError

    def group_score(self, target: Target, /):
        # Called in tableau
        return 1.0 #??
        # return self.score_candidate(target) / max(1, self.branch_level)

    def score_candidate(self, target: Target, /) -> float:
        # Closure rules have is_rank_optim = False by default.
        return 0.0

class BaseSimpleRule(Rule):

    Helpers = AdzHelper,
    #: (AdzHelper) Whether the target node should be ticked after application.
    ticking: bool = True

    def _apply(self, target: Target):
        'Delegates to AdzHelper._apply().'
        self[AdzHelper]._apply(target)

    def score_candidate(self, target: Target):
        'Uses to AdzHelper.closure_score() to score the candidate target.'
        return self[AdzHelper].closure_score(target)

class BaseNodeRule(BaseSimpleRule):
    # * * * * * 

    Helpers = FilterHelper,
    #: (FilterHelper) Whether to ignore all ticked nodes.
    ignore_ticked = True

    def example_nodes(self):
        'Delegates to (FilterHelper.example_node(),)'
        return self[FilterHelper].example_node(),

class BaseSentenceRule(BaseNodeRule):

    NodeFilters = NodeFilters.Sentence,

    negated    : bool      |None = None
    operator   : Operator  |None = None
    quantifier : Quantifier|None = None
    predicate  : Predicate |None = None

    def sentence(self, node: Node, /) -> Sentence:
        'Delegates to NodeFilters.Sentence of FilterHelper.'
        return self[FilterHelper].filters[NodeFilters.Sentence].get(node)

class PredicatedSentenceRule(BaseSentenceRule):

    Helpers = PredNodes,
    @abcf.temp
    @overload
    def sentence(self, node: Node, /) -> Predicated:...

class QuantifiedSentenceRule(BaseSentenceRule):

    @abcf.temp
    @overload
    def sentence(self, node: Node, /) -> Quantified:...

class OperatedSentenceRule(BaseSentenceRule):

    @abcf.temp
    @overload
    def sentence(self, node: Node, /) -> Operated:...

class NarrowQuantifierRule(QuantifiedSentenceRule):

    Helpers = QuitFlag, MaxConsts,

    @FilterHelper.node_targets
    def _get_targets(self, node: Node, branch: Branch):
        if self[MaxConsts].max_constants_exceeded(branch, node.get('world')):
            self[FilterHelper].release(node, branch)
            if self[QuitFlag].get(branch):
                return
            return dict(
                flag = True,
                ** adds (
                    group(self[MaxConsts].quit_flag(branch))
                ),
            )

        return self._get_node_targets(node, branch)

    @abstract
    def _get_node_targets(self, node: Node, branch: Branch):
        raise NotImplementedError

    def score_candidate(self, target: Target):
        return -1.0 * self.tableau.branching_complexity(target.node)

class ExtendedQuantifierRule(NarrowQuantifierRule):

    ticking = False

    Helpers = NodeConsts, NodeCount,

    def _get_node_targets(self, node: Node, branch: Branch) -> Generator[dict, None, None]:
        unapplied = self[NodeConsts][branch][node]
        if branch.constants_count and not len(unapplied):
            # Do not release the node from filters, since new constants
            # can appear.
            return
        constants = unapplied or FIRST_CONST_SET
        getcnodes = self._get_constant_nodes
        
        return (
            dict(
                adds     = group(nodes),
                constant = constant ,
            )
            for nodes, constant in (
                (getcnodes(node, c, branch), c)
                for c in constants
            )
            if len(unapplied) > 0
            or not branch.has_all(nodes)
        )

    @abstract
    def _get_constant_nodes(self, node: Node, c: Constant, branch: Branch, /):
        raise NotImplementedError

    def score_candidate(self, target: Target):
        if target.get('flag'):
            return 1.0
        if self[AdzHelper].closure_score(target) == 1:
            return 1.0
        node_apply_count = self[NodeCount][target.branch].get(target.node, 0)
        return 1 / (node_apply_count + 1)


class GetNodeTargetsRule(BaseNodeRule):

    @FilterHelper.node_targets
    def _get_targets(self, node: Node, branch: Branch):
        '''Wrapped by @FilterHelper.node_targets and delegates to abstract method
        _get_node_targets(),'''
        return self._get_node_targets(node, branch)

    @abstract
    def _get_node_targets(self, node: Node, branch: Branch):
        raise NotImplementedError


def group(*items: T) -> tuple[T, ...]:
    return items

def adds(*groups: tuple[dict, ...], **kw):
    return dict(adds = groups, **kw)

del(
    abstract, overload, abcf
)