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

from ..lang import Atomic, Constant, Operator, Predicate, Predicated
from ..models import ValueCPL
from ..proof import Target, adds, rules, swnode
from ..proof.helpers import FilterHelper, PredNodes
from ..tools import group, substitute
from . import LogicType
from . import fde as FDE


class Meta(LogicType.Meta):
    name = 'CPL'
    title = 'Classical Predicate Logic'
    values: type[ValueCPL] = ValueCPL
    designated_values = 'T'
    unassigned_value = 'F'
    description = 'Standard bivalent logic with predication, without quantification'
    category_order = 1
    native_operators = (
        Operator.Negation,
        Operator.Conjunction,
        Operator.Disjunction,
        Operator.MaterialConditional,
        Operator.MaterialBiconditional)

class Model(LogicType.Model[Meta.values]):

    class TruthFunction(LogicType.Model.TruthFunction[Meta.values]): pass

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
        interp.pos.update(map(group, self.constants))

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
        w = 0 if cls.modal else None
        b += (swnode(s, w) for s in arg.premises)
        b += swnode(~arg.conclusion, w)

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

    class IdentityIndiscernability(rules.GetNodeTargetsRule, rules.PredicatedSentenceRule):
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
    class Conditional(FDE.Rules.ConditionalDesignated): pass
    class ConditionalNegated(FDE.Rules.ConditionalNegatedDesignated): pass
    class Biconditional(FDE.Rules.BiconditionalDesignated): pass
    class BiconditionalNegated(FDE.Rules.BiconditionalNegatedDesignated): pass

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
            DoubleNegation),
        group(
            # branching rules
            ConjunctionNegated,
            Disjunction,
            MaterialConditional,
            MaterialBiconditional,
            MaterialBiconditionalNegated,
            Conditional,
            Biconditional,
            BiconditionalNegated))

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(2), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'