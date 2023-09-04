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

from collections import deque

from ..lang import Atomic, Constant, Operated, Operator, Predicate, Predicated
from ..models import ValueCPL
from ..proof import SentenceNode, Target, WorldNode, adds, rules, swnode
from ..proof.helpers import FilterHelper, PredNodes
from ..tools import group, maxceil, minfloor, substitute
from . import LogicType
from . import fde as FDE
from . import kfde as KFDE


class Meta(LogicType.Meta):
    name = 'K'
    title = 'Kripke Normal Modal Logic'
    modal = True
    quantified = True
    values: type[ValueCPL] = ValueCPL
    designated_values = frozenset({values.T})
    unassigned_value = values.F
    description = 'Base normal modal logic with no access relation restrictions'
    category_order = 1
    native_operators = FDE.Meta.native_operators | LogicType.Meta.modal_operators
    extension_of = ('CFOL', 'KK3', 'KL3', 'KLP', 'KRM3')


class Model(LogicType.Model[Meta.values]):
    """
    A K model comprises a non-empty collection of K-frames, a world access
    relation, and a set of constants (the domain).
    """

    TruthFunction = FDE.Model.TruthFunction
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

    def _read_node(self, node, branch, /):
        super()._read_node(node, branch)
        if not isinstance(node, SentenceNode):
            return
        s = node['sentence']
        if isinstance(node, WorldNode):
            w = node['world']
        else:
            w = 0
        if self.is_sentence_opaque(s):
            self.set_opaque_value(s, self.values.T, world = w)
        elif self.is_sentence_literal(s):
            self.set_literal_value(s, self.values.T, world = w)

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
        interp = self.frames[w].predicates[Predicate.Identity]
        # make sure each constant is self-identical
        interp.pos.update((c, c) for c in self.constants)

    def _ensure_self_existence(self, w):
        if not len(self.constants):
            return
        interp = self.frames[w].predicates[Predicate.Existence]
        # make sure each constant exists
        interp.pos.update((c,) for c in self.constants)

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

class System(FDE.System):

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

    class DoubleNegation(FDE.Rules.DoubleNegationDesignated): pass
    class Assertion(FDE.Rules.AssertionDesignated): pass
    class AssertionNegated(FDE.Rules.AssertionNegatedDesignated): pass
    class Conjunction(FDE.Rules.ConjunctionDesignated): pass
    class ConjunctionNegated(FDE.Rules.ConjunctionNegatedDesignated): pass
    class Disjunction(FDE.Rules.DisjunctionDesignated): pass
    class DisjunctionNegated(FDE.Rules.DisjunctionNegatedDesignated): pass
    class MaterialConditional(FDE.Rules.MaterialConditionalDesignated): pass
    class MaterialConditionalNegated(FDE.Rules.MaterialConditionalNegatedDesignated): pass
    class MaterialBiconditional(FDE.Rules.MaterialBiconditionalDesignated): pass
    class MaterialBiconditionalNegated(FDE.Rules.MaterialBiconditionalNegatedDesignated): pass
    class Conditional(MaterialConditional): pass
    class ConditionalNegated(MaterialConditionalNegated): pass
    class Biconditional(MaterialBiconditional): pass
    class BiconditionalNegated(MaterialBiconditionalNegated): pass
    class Existential(FDE.Rules.ExistentialDesignated): pass
    class ExistentialNegated(FDE.Rules.ExistentialNegatedDesignated): pass
    class Universal(FDE.Rules.UniversalDesignated): pass
    class UniversalNegated(ExistentialNegated): pass
    class Possibility(KFDE.Rules.PossibilityDesignated): pass
    class PossibilityNegated(KFDE.Rules.PossibilityNegatedDesignated): pass
    class Necessity(KFDE.Rules.NecessityDesignated): pass
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