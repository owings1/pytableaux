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
from __future__ import annotations

from abc import abstractmethod
from collections import deque

from ..lang import (Atomic, Constant, Operated, Operator, Predicate,
                    Predicated, Sentence)
from ..models import ValueCPL
from ..proof import (AccessNode, Branch, Node, SentenceNode, SentenceWorldNode,
                     Target, WorldPair, adds, anode, filters, rules, swnode)
from ..proof.helpers import (AdzHelper, AplSentCount, FilterHelper, MaxWorlds,
                             NodeCount, NodesWorlds, PredNodes, QuitFlag,
                             WorldIndex)
from ..tools import EMPTY_SET, group, maxceil, minfloor, substitute, wraps
from . import LogicType
from . import fde as FDE


class Meta(LogicType.Meta):
    name = 'K'
    title = 'Kripke Normal Modal Logic'
    modal = True
    quantified = True
    values: type[ValueCPL] = ValueCPL
    designated_values = frozenset({values.T})
    unassigned_value = values.F
    category = 'Bivalent Modal'
    description = 'Base normal modal logic with no access relation restrictions'
    category_order = 1
    native_operators = FDE.Meta.native_operators | LogicType.Meta.modal_operators



class Model(LogicType.Model[Meta.values]):
    """
    A K model comprises a non-empty collection of K-frames, a world access
    relation, and a set of constants (the domain).
    """

    TruthFunction = FDE.Model.TruthFunction

    class Frame(LogicType.Model.Frame):
        pass

    value_of_quantified = FDE.Model.value_of_quantified

    def value_of_operated(self, s: Operated, /, *, world: int = 0):
        self._check_finished()
        if self.Meta.modal and s.operator in self.Meta.modal_operators:
            it = map(lambda w: self.value_of(s.lhs, world=w), self.R[world])
            if s.operator is Operator.Possibility:
                return maxceil(self.maxval, it, self.minval)
            if s.operator is Operator.Necessity:
                return minfloor(self.minval, it, self.maxval)
            raise NotImplementedError from ValueError(s.operator)
        return super().value_of_operated(s, world=world)

    def read_branch(self, branch: Branch, /):
        self._check_not_finished()
        for _ in map(self._read_node, branch): pass
        return super().read_branch(branch)

    def _read_node(self, node: Node, /):
        if isinstance(node, SentenceNode):
            s = node['sentence']
            self.sentences.add(s)
            self.constants.update(s.constants)
            w = node.get('world')
            if w is None:
                w = 0
            self.R[w]
            if self.is_sentence_opaque(s):
                self.set_opaque_value(s, self.values.T, world = w)
            elif self.is_sentence_literal(s):
                self.set_literal_value(s, self.values.T, world = w)
        elif isinstance(node, AccessNode):
            self.R.add(node.pair())

    def finish(self):
        self._check_not_finished()
        self._complete_frames()
        for w, frame in self.frames.items():
            for pred in deque(frame.predicates):
                self._agument_extension_with_identicals(pred, w)
            self._ensure_self_identity(w)
            self._ensure_self_existence(w)
        return super().finish()

    def _ensure_self_identity(self, w):
        if not len(self.constants):
            return
        add = self.frames[w].predicates[Predicate.Identity].pos.add
        for c in self.constants:
            # make sure each constant is self-identical
            add((c, c))

    def _ensure_self_existence(self, w):
        if not len(self.constants):
            return
        add = self.frames[w].predicates[Predicate.Existence].pos.add
        for c in self.constants:
            # make sure each constant exists
            add((c,))

    def _agument_extension_with_identicals(self, pred: Predicate, w):
        pos = self.frames[w].predicates[pred].pos
        add = pos.add
        for c in self.constants:
            identicals = self._get_identicals(c, w)
            to_add = set()
            for params in pos:
                if c in params:
                    for new_c in identicals:
                        to_add.add(substitute(params, c, new_c))
            for params in to_add:
                add(params)

    def _get_identicals(self, c: Constant, w=0) -> set[Constant]:
        interp = self.frames[w].predicates[Predicate.Identity]
        identicals = set()
        update = identicals.update
        for params in interp.pos:
            if c in params:
                update(params)
        identicals.discard(c)
        return identicals

class System(LogicType.System):

    @classmethod
    def build_trunk(cls, b, arg, /):
        """
        To build the trunk for an argument, add a node with each premise, with
        world :m:`w0`, followed by a node with the negation of the conclusion
        with world :m:`w0`.
        """
        w = 0 if cls.modal else None
        b += (swnode(s, w) for s in arg.premises)
        b += swnode(~arg.conclusion, w)

    @classmethod
    def branching_complexity(cls, node, rules, /) -> int:
        try:
            s = node['sentence']
        except KeyError:
            return 0
        negated = False
        result = 0
        for oper in s.operators:
            if not negated and oper is Operator.Negation:
                negated = True
                continue
            if negated and oper is Operator.Negation:
                name = 'DoubleNegation'
            else:
                name = oper.name
                if negated:
                    name += 'Negated'
            rulecls = rules.get(name, None)
            if rulecls:
                result += rulecls.branching
                negated = False
        return result

    @classmethod
    def branching_complexity_hashable(cls, node, /):
        try:
            return node['sentence'].operators
        except KeyError:
            pass

    class DefaultNodeRule(rules.GetNodeTargetsRule, intermediate=True):
        """Default K node rule with:
        
        - NodeFilter implements `_get_targets()` with abstract `_get_node_targets()`.
        - FilterHelper implements `example_nodes()` with its `example_node()` method.
        - AdzHelper implements `_apply()` with its `_apply()` method.
        - AdzHelper implements `score_candidate()` with its `closure_score()` method.
        - Induce attributes from class name with autoattrs=True.
        """
        NodeFilters = group(filters.NodeType)
        autoattrs = True

        def _get_node_targets(self, node: Node, branch: Branch, /):
            return self._get_sw_targets(self.sentence(node), node.get('world'))

        def _get_sw_targets(self, s: Sentence, w: int|None, /):
            raise NotImplementedError

        def __init_subclass__(cls) -> None:
            super().__init_subclass__()
            if cls._get_node_targets is __class__._get_node_targets:
                if cls._get_sw_targets is __class__._get_sw_targets:
                    @abstractmethod
                    @wraps(cls._get_sw_targets)
                    def wrapped(self, s: Sentence, w: int|None, /):
                        raise NotImplementedError
                    setattr(cls, '_get_sw_targets', wrapped)


    class OperatorNodeRule(DefaultNodeRule, rules.OperatedSentenceRule, intermediate=True):
        'Convenience mixin class for most common rules.'
        NodeType = SentenceNode

        def _get_sw_targets(self, s: Operated, w: int|None, /):
            raise NotImplementedError

        def __init_subclass__(cls) -> None:
            super().__init_subclass__()
            if cls._get_node_targets is __class__._get_node_targets:
                if cls._get_sw_targets is __class__._get_sw_targets:
                    @abstractmethod
                    @wraps(cls._get_sw_targets)
                    def wrapped(self, s: Sentence, w: int|None, /):
                        raise NotImplementedError
                    setattr(cls, '_get_sw_targets', wrapped)

class Rules(LogicType.Rules):

    class ContradictionClosure(rules.FindClosingNodeRule):
        """
        A branch closes when a sentence and its negation both appear on a node **with the
        same world** on the branch.
        """

        def _find_closing_node(self, node, branch, /):
            s = self.sentence(node)
            if s is not None:
                return branch.find(swnode(-s, node.get('world')))

        def example_nodes(self):
            s = Atomic.first()
            w = 0 if self.modal else None
            yield swnode(s, w)
            yield swnode(~s, w)

    class SelfIdentityClosure(rules.BaseClosureRule, rules.PredicatedSentenceRule):
        """
        A branch closes when a sentence of the form :s:`~a = a` appears on the
        branch *at any world*.
        """
        negated = True
        predicate = Predicate.Identity

        def _branch_target_hook(self, node, branch, /):
            if self.node_will_close_branch(node, branch):
                return Target(node=node, branch=branch)
            self[FilterHelper].release(node, branch)
            self[PredNodes].release(node, branch)

        def node_will_close_branch(self, node, branch, /) -> bool:
            return (
                self[FilterHelper].config.pred(node) and
                len(set(self.sentence(node))) == 1)

        def example_nodes(self):
            w = 0 if self.modal else None
            c = Constant.first()
            yield swnode(~self.predicate((c, c)), w)

    class NonExistenceClosure(rules.BaseClosureRule, rules.PredicatedSentenceRule):
        """
        A branch closes when a sentence of the form :s:`~!a` appears on the branch
        *at any world*.
        """
        negated = True
        predicate = Predicate.Existence

        def _branch_target_hook(self, node, branch, /):
            if self.node_will_close_branch(node, branch):
                return Target(node=node, branch=branch)
            self[FilterHelper].release(node, branch)
            self[PredNodes].release(node, branch)

        def node_will_close_branch(self, node, branch, /):
            return self[FilterHelper](node, branch)

        def example_nodes(self):
            s = ~Predicated.first(self.predicate)
            w = 0 if self.modal else None
            yield swnode(s, w)

    class DoubleNegation(System.OperatorNodeRule):
        """
        From an unticked double negation node *n* with world *w* on a branch *b*, add a
        node to *b* with *w* and the double-negatum of *n*, then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(group(swnode(s.lhs, w)))

    class Assertion(System.OperatorNodeRule):
        """
        From an unticked assertion node *n* with world *w* on a branch *b*,
        add a node to *b* with the operand of *n* and world *w*, then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(group(swnode(s.lhs, w)))

    class AssertionNegated(System.OperatorNodeRule):
        """
        From an unticked, negated assertion node *n* with world *w* on a branch *b*,
        add a node to *b* with the negation of the assertion of *n* and world *w*,
        then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(group(swnode(~s.lhs, w)))

    class Conjunction(System.OperatorNodeRule):
        """
        From an unticked conjunction node *n* with world *w* on a branch *b*,
        for each conjunct, add a node with world *w* to *b* with the conjunct,
        then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(group(swnode(s.lhs, w), swnode(s.rhs, w)))

    class ConjunctionNegated(System.OperatorNodeRule):
        """
        From an unticked negated conjunction node *n* with world *w* on a branch *b*, for each
        conjunct, make a new branch *b'* from *b* and add a node with *w* and the negation of
        the conjunct to *b*, then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(
                group(swnode(~s.lhs, w)),
                group(swnode(~s.rhs, w)))

    class Disjunction(System.OperatorNodeRule):
        """
        From an unticked disjunction node *n* with world *w* on a branch *b*, for each disjunct,
        make a new branch *b'* from *b* and add a node with the disjunct and world *w* to *b'*,
        then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(
                group(swnode(s.lhs, w)),
                group(swnode(s.rhs, w)))

    class DisjunctionNegated(System.OperatorNodeRule):
        """
        From an unticked negated disjunction node *n* with world *w* on a branch *b*, for each
        disjunct, add a node with *w* and the negation of the disjunct to *b*, then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(group(swnode(~s.lhs, w), swnode(~s.rhs, w)))

    class MaterialConditional(System.OperatorNodeRule):
        """
        From an unticked material conditional node *n* with world *w* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with world *w* and the negation of the
        antecedent to *b'*, and add a node with world *w* and the conequent to *b''*, then tick
        *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(
                group(swnode(~s.lhs, w)),
                group(swnode( s.rhs, w)))

    class MaterialConditionalNegated(System.OperatorNodeRule):
        """
        From an unticked negated material conditional node *n* with world *w* on a branch *b*,
        add two nodes with *w* to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(group(swnode(s.lhs, w), swnode(~s.rhs, w)))

    class MaterialBiconditional(System.OperatorNodeRule):
        """
        From an unticked material biconditional node *n* with world *w* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes with world *w* to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes with world *w* to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(
                group(swnode(~s.lhs, w), swnode(~s.rhs, w)),
                group(swnode( s.rhs, w), swnode( s.lhs, w)))

    class MaterialBiconditionalNegated(System.OperatorNodeRule):
        """
        From an unticked negated material biconditional node *n* with world *w* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes with *w* to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes with
        *w* to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(
                group(swnode( s.lhs, w), swnode(~s.rhs, w)),
                group(swnode(~s.lhs, w), swnode( s.rhs, w)))

    class Conditional(MaterialConditional): pass
    class ConditionalNegated(MaterialConditionalNegated): pass
    class Biconditional(MaterialBiconditional): pass
    class BiconditionalNegated(MaterialBiconditionalNegated): pass

    class Existential(rules.NarrowQuantifierRule, System.DefaultNodeRule):
        """
        From an unticked existential node *n* with world *w* on a branch *b*, quantifying over
        variable *v* into sentence *s*, add a node with world *w* to *b* with the substitution
        into *s* of *v* with a constant new to *b*, then tick *n*.
        """

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            yield adds(
                group(swnode(branch.new_constant() >> s, node.get('world'))))

    class ExistentialNegated(System.DefaultNodeRule, rules.QuantifiedSentenceRule):
        """
        From an unticked negated existential node *n* with world *w* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a universally quantified
        node to *b* with world *w* over *v* into the negation of *s*, then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            v, si = s[1:]
            yield adds(group(swnode(self.quantifier.other(v, ~si), w)))

    class Universal(rules.ExtendedQuantifierRule, System.DefaultNodeRule):
        """
        From a universal node with world *w* on a branch *b*, quantifying over variable *v* into
        sentence *s*, result *r* of substituting a constant *c* on *b* (or a new constant if none
        exists) for *v* into *s* does not appear at *w* on *b*, add a node with *w* and *r* to
        *b*. The node *n* is never ticked.
        """

        def _get_constant_nodes(self, node, c, branch, /):
            yield swnode(c >> self.sentence(node), node.get('world'))

    class UniversalNegated(ExistentialNegated): pass

    class Possibility(System.OperatorNodeRule):
        """
        From an unticked possibility node with world *w* on a branch *b*, add a node with a
        world *w'* new to *b* with the operand of *n*, and add an access-type node with
        world1 *w* and world2 *w'* to *b*, then tick *n*.
        """
        NodeType = SentenceWorldNode
        Helpers = (QuitFlag, MaxWorlds, AplSentCount)

        def _get_node_targets(self, node, branch, /):

            # Check for max worlds reached
            if self[MaxWorlds].is_exceeded(branch):
                self[FilterHelper].release(node, branch)
                if not self[QuitFlag].get(branch):
                    fnode = self[MaxWorlds].quit_flag(branch)
                    yield adds(group(fnode), flag=fnode['flag'])
                return

            si = self.sentence(node).lhs
            w1 = node['world']
            w2 = branch.new_world()
            yield adds(
                group(swnode(si, w2), anode(w1, w2)),
                sentence=si)

        def score_candidate(self, target, /) -> float:
            """
            Overrides `AdzHelper` closure score
            """
            if target.get('flag'):
                return 1.0
            # override
            s = self.sentence(target.node)
            si = s.lhs
            # Don't bother checking for closure since we will always have a new world
            track_count = self[AplSentCount][target.branch][si]
            if track_count == 0:
                return 1.0
            return -1.0 * self[MaxWorlds].modals[s] * track_count

        def group_score(self, target, /) -> float:
            if target['candidate_score'] > 0:
                return 1.0
            s = self.sentence(target.node)
            si = s.lhs
            return -1.0 * self[AplSentCount][target.branch][si]

    class PossibilityNegated(System.OperatorNodeRule):
        """
        From an unticked negated possibility node *n* with world *w* on a branch *b*, add a
        necessity node to *b* with *w*, whose operand is the negation of the negated 
        possibilium of *n*, then tick *n*.
        """
        NodeType = SentenceWorldNode

        def _get_sw_targets(self, s, w, /):
            yield adds(group(swnode(self.operator.other(~s.lhs), w)))

    class Necessity(System.OperatorNodeRule):
        """
        From a necessity node *n* with world *w1* and operand *s* on a branch *b*, for any
        world *w2* such that an access node with w1,w2 is on *b*, if *b* does not have a node
        with *s* at *w2*, add it to *b*. The node *n* is never ticked.
        """
        ticking = False
        NodeType = SentenceWorldNode
        Helpers = (QuitFlag, MaxWorlds, NodeCount, NodesWorlds, WorldIndex)

        def _get_node_targets(self, node, branch, /):

            # Check for max worlds reached
            if self[MaxWorlds].is_exceeded(branch):
                self[FilterHelper].release(node, branch)
                if not self[QuitFlag].get(branch):
                    fnode = self[MaxWorlds].quit_flag(branch)
                    yield adds(group(fnode), flag = fnode['flag'])
                return

            # Only count least-applied-to nodes
            if not self[NodeCount].isleast(node, branch):
                return

            s = self.sentence(node)
            si = s.lhs
            w1 = node['world']

            for w2 in self[WorldIndex][branch].get(w1, EMPTY_SET):
                if (node, w2) in self[NodesWorlds][branch]:
                    continue
                add = swnode(si, w2)
                if branch.has(add):
                    continue
                # accessnode = self[WorldIndex].nodes[branch][w1, w2]
                # accessnode = branch.find(anode(w1, w2))
                nodes = (node, branch.find(anode(w1, w2)))
                yield adds(group(add),
                    sentence=si,
                    world=w2,
                    nodes=nodes)

        def score_candidate(self, target, /) -> float:
            if target.get('flag'):
                return 1.0
            # We are already restricted to least-applied-to nodes by
            # ``_get_node_targets()``
            # Check for closure
            if self[AdzHelper].closure_score(target) == 1:
                return 1.0
            # Not applied to yet
            apcount = self[NodeCount][target.branch][target.node]
            if apcount == 0:
                return 1.0
            # Pick the least branching complexity
            return -1.0 * self.tableau.branching_complexity(target.node)

        def group_score(self, target, /) -> float:
            if self.score_candidate(target) > 0:
                return 1.0
            return -1.0 * self[NodeCount][target.branch][target.node]

        def example_nodes(self):
            s = Operated.first(self.operator)
            a = WorldPair(0, 1)
            yield swnode(s, a.w1)
            yield a.tonode()

    class NecessityNegated(PossibilityNegated): pass

    class IdentityIndiscernability(System.DefaultNodeRule, rules.PredicatedSentenceRule):
        """
        From an unticked node *n* having an Identity sentence *s* at world *w* on an open branch *b*,
        and a predicated node *n'* whose sentence *s'* has a constant that is a parameter of *s*,
        if the replacement of that constant for the other constant of *s* is a sentence that does
        not appear on *b* at *w*, then add it.
        """
        ticking   = False
        predicate = Predicate.Identity

        def _get_node_targets(self, node, branch, /):
            pa, pb = self.sentence(node)
            if pa == pb:
                # Substituting a param for itself would be silly.
                return
            w = node.get('world')
            # Find other nodes with one of the identicals.
            for n in self[PredNodes][branch]:
                if n is node:
                    continue
                s = self.sentence(n)
                if pa in s.params:
                    p_old, p_new = pa, pb
                elif pb in s.params:
                    p_old, p_new = pb, pa
                else:
                    continue
                # Replace p with p1.
                params = substitute(s.params, p_old, p_new)
                # Since we have SelfIdentityClosure, we don't need a = a.
                if s.predicate == self.predicate and params[0] == params[1]:
                    continue
                # Create a node with the substituted param.
                n_new = swnode(s.predicate(params), w)
                # Check if it already appears on the branch.
                if branch.has(n_new):
                    continue
                # The rule applies.
                yield adds(group(n_new), nodes=(node, n))

        def example_nodes(self):
            s1 = Predicated.first()
            w = 0 if self.modal else None
            yield swnode(s1, w)
            s2 = self.predicate((s1[0], s1[0].next()))
            yield swnode(s2, w)

    closure = (
        ContradictionClosure,
        SelfIdentityClosure,
        NonExistenceClosure)

    groups = (
        group(
            # non-branching rules
            IdentityIndiscernability,
            Assertion,
            AssertionNegated,
            Conjunction, 
            DisjunctionNegated, 
            MaterialConditionalNegated,
            ConditionalNegated,
            DoubleNegation,
            PossibilityNegated,
            NecessityNegated,
            ExistentialNegated,
            UniversalNegated),
        group(
            # branching rules
            ConjunctionNegated,
            Disjunction,
            MaterialConditional,
            MaterialBiconditional,
            MaterialBiconditionalNegated,
            Conditional,
            Biconditional,
            BiconditionalNegated),
        group(
            # modal operator rules
            Necessity,
            Possibility),
        group(
            Existential,
            Universal))

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(2), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'