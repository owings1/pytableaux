from __future__ import annotations

__all__ = (
    'Rule',
    'BaseClosureRule',
    'BaseRule',
    'BaseNodeRule',
    'BaseQuantifierRule',
    'ExtendedQuantifierRule',
)

from tools.decorators import abstract
from lexicals import Constant, Operator, Predicate, Quantifier, Sentence
from proof.common import Branch, Node, Target
from proof.filters import NodeFilters
from proof.helpers import (
    AdzHelper,
    BranchTarget,
    FilterHelper,
    MaxConsts,
    NodeConsts,
    NodeCount,
    QuitFlag,
)
from proof.tableaux import ClosingRule, Rule

class BaseClosureRule(ClosingRule):

    Helpers = BranchTarget,

    def _get_targets(self, branch: Branch):
        target = self[BranchTarget][branch]
        if target is not None:
            return target,

    @abstract
    def _branch_target_hook(self, node: Node, branch: Branch):
        'Method for BranchTarget helper.'
        raise NotImplementedError

class BaseRule(Rule):

    Helpers = AdzHelper, FilterHelper,

    #: (AdzHelper) Whether the target node should be ticked after application.
    ticking: bool = True
    #: (FilterHelper) Whether to ignore all ticked nodes.
    ignore_ticked = True

    NodeFilters = NodeFilters.Sentence,
    # NodeFilters.Sentence
    negated    : bool = None
    operator   : Operator = None
    quantifier : Quantifier = None
    predicate  : Predicate = None

    def _apply(self, target: Target):
        'Delegates to AdzHelper._apply().'
        self[AdzHelper]._apply(target)

    def example_nodes(self):
        'Delegates to (FilterHelper.example_node(),)'
        return self[FilterHelper].example_node(),

    def sentence(self, node: Node, /) -> Sentence:
        'Delegates to NodeFilters.Sentence of FilterHelper.'
        return self[FilterHelper].filters[NodeFilters.Sentence].get(node)

    def score_candidate(self, target: Target):
        'Uses to AdzHelper.closure_score() to score the candidate target.'
        return self[AdzHelper].closure_score(target)

class BaseNodeRule(BaseRule):

    @FilterHelper.node_targets
    def _get_targets(self, node: Node, branch: Branch):
        '''Wrapped by @FilterHelper.node_targets and delegates to abstract method
        _get_node_targets(),'''
        return self._get_node_targets(node, branch)

    @abstract
    def _get_node_targets(self, node: Node, branch: Branch):
        raise NotImplementedError

class BaseQuantifierRule(BaseRule):

    Helpers = QuitFlag, MaxConsts,

    @FilterHelper.node_targets
    def _get_targets(self, node: Node, branch: Branch):
        if self[MaxConsts].max_constants_exceeded(branch, node.get('world')):
            self[FilterHelper].release(node, branch)
            if self[QuitFlag].get(branch):
                return
            return dict(
                flag = True,
                adds = ((self[MaxConsts].quit_flag(branch),),),
            )
        return self._get_node_targets(node, branch)

    @abstract
    def _get_node_targets(self, node: Node, branch: Branch):
        raise NotImplementedError

    def score_candidate(self, target: Target):
        return -1 * self.tableau.branching_complexity(target.node)

FIRST_CONST_SET = frozenset({Constant.first()})

class ExtendedQuantifierRule(BaseQuantifierRule):

    ticking = False

    Helpers = NodeConsts, NodeCount,

    def _get_node_targets(self, node: Node, branch: Branch):
        unapplied = self[NodeConsts][branch][node]
        if branch.constants_count and not len(unapplied):
            # Do not release the node from filters, since new constants
            # can appear.
            return
        constants = unapplied or FIRST_CONST_SET
        getcnodes = self._get_constant_nodes
        return (
            dict(
                adds     = (nodes,) ,
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

del(abstract)