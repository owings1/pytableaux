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

from ..lang import Operator, Quantified, Quantifier
from ..proof import adds, rules, sdnode
from ..tools import group, maxceil, minfloor
from . import b3e as B3E
from . import fde as FDE
from . import k3 as K3
from .b3e import crunch, gap


class Meta(K3.Meta):
    name = 'GO'
    title = 'Gappy Object 3-valued Logic'
    description = (
        'Three-valued logic (True, False, Neither) with '
        'classical-like binary operators')
    category_order = 60
    native_operators = tuple(sorted(FDE.Meta.native_operators + (
        Operator.Conditional,
        Operator.Biconditional)))

class Model(K3.Model):

    class TruthFunction(K3.Model.TruthFunction):

        def Assertion(self, a):
            return self.values[crunch(self.values[a].num)]

        def Disjunction(self, a, b):
            return self.values[
                max(
                    crunch(self.values[a].num),
                    crunch(self.values[b].num))]

        def Conjunction(self, a, b):
            return self.values[
                min(
                    crunch(self.values[a].num),
                    crunch(self.values[b].num))]

        def Conditional(self, a, b):
            return self.values[
                crunch(
                    max(
                        1 - self.values[a].num,
                        self.values[b].num,
                        gap(self.values[a].num) + gap(self.values[b].num)))]

    def value_of_quantified(self, s: Quantified, /):
        it = map(crunch, map(self.value_of, map(s.unquantify, self.constants)))
        if s.quantifier is Quantifier.Existential:
            return maxceil(self.maxval, it, self.minval)
        if s.quantifier is Quantifier.Universal:
            return minfloor(self.minval, it, self.maxval)
        raise TypeError(s.quantifier)

class System(K3.System):
    """
    GO's Tableaux System inherits directly from the :ref:`FDE system <fde-system>`,
    employing designation markers, and building the trunk in the same way.
    """
    # operator => negated => designated
    branchables = {
        Operator.Negation: (None, (0, 0)),
        Operator.Assertion: ((0, 0), (0, 0)),
        Operator.Conjunction: ((0, 0), (0, 1)),
        Operator.Disjunction: ((0, 1), (0, 0)),
        Operator.MaterialConditional: ((0, 1), (0, 0)),
        Operator.MaterialBiconditional: ((0, 1), (0, 1)),
        Operator.Conditional: ((0, 1), (0, 1)),
        Operator.Biconditional: ((0, 0), (0, 1))}

class Rules(B3E.Rules):

    class ConjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated conjunction node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add an undesignated node to
        *b'* with one conjunct, and an undesignated node to *b''* with the other
        conjunct, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(s.lhs, not d)),
                group(sdnode(s.rhs, not d)))

    class ConjunctionUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated conjunction node *n* on a branch *b*, add a
        designated node to *b* with the negation of the conjunction, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~s, not d)))

    class ConjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, negated conjunction node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) conjuction, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s, not d)))
        
    class DisjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated disjunction node *n* on a branch *b*,
        add an undesignated node to *b* for each disjunct, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s.lhs, not d), sdnode(s.rhs, not d)))

    class DisjunctionUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated disjunction node *n* on a branch *b*, add a
        designated node to *b* with the negation of the disjunction, then tick *n*.
        """

    class DisjunctionNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated disjunction node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) disjunction, then tick *n*.
        """

    class MaterialConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated material conditional node *n* on a branch
        *b*, add an undesignated node with the negation of the antecedent, and an
        undesignated node with the consequent to *b*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~s.lhs, not d), sdnode(s.rhs, not d)))

    class MaterialConditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated, material conditional node *n* on a branch *b*,
        add a designated node to *b* with the negation of the conditional, then tick *n*.
        """

    class MaterialConditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated material conditional node *n* on a branch
        *b*, add a designated node with the (un-negated) conditional to *b*, then tick *n*.
        """

    class MaterialBiconditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated, material biconditional node *n* on a branch
        *b*, make two branches *b'* and *b''* from *b*. On *b'* add undesignated nodes for
        the negation of the antecent, and for the consequent. On *b''* add undesignated
        nodes for the antecedent, and for the negation of the consequent. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(~s.lhs, not d), sdnode( s.rhs, not d)),
                group(sdnode( s.lhs, not d), sdnode(~s.rhs, not d)))

    class MaterialBiconditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated, material biconditional node *n* on a branch *b*,
        add a designated node to *b* with the negation of the biconditional, then tick *n*.
        """

    class MaterialBiconditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated material biconditional node *n* on a branch
        *b*, add a designated node to *b* with the (un-negated) biconditional, then tick *n*.
        """

    class ConditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, conditional node *n* on a branch *b*, make two branches
        *b'* and *b''* from *b*. On *b'* add a designated node with a disjunction of the
        negated antecedent and the consequent. On *b''* add undesignated nodes for the
        antecedent, consequent, and their negations. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(
                    sdnode(~lhs | rhs, d)),
                group(
                    sdnode( lhs, not d),
                    sdnode( rhs, not d),
                    sdnode(~lhs, not d),
                    sdnode(~rhs, not d)))

    class ConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add a designated node with the
        antecedent, and an undesignated node with the consequent. On *b''* add an
        undesignated node with the negation of the antencedent, and a designated node
        with the negation of the consequent. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode( s.lhs,     d), sdnode( s.rhs, not d)),
                group(sdnode(~s.lhs, not d), sdnode(~s.rhs,     d)))

    class ConditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated conditional node *n* on a branch *b*, add a
        designated node to *b* with the negation of the conditional, then tick *n*.
        """

    class ConditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated conditional node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) conditional, then tick *n*.
        """

    class BiconditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated biconditional node *n* on a branch *b*, add two
        designated conditional nodes to *b*, one with the operands of the biconditional,
        and the other with the reversed operands. Then tick *n*.
        """
        convert = Operator.Conditional

        def _get_sd_targets(self, s, d, /):
            yield adds(group(
                sdnode(self.convert(s.lhs, s.rhs), d),
                sdnode(self.convert(s.rhs, s.lhs), d)))

    class BiconditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add a designated negated conditional
        node with the operands of the biconditional. On *b''* add a designated negated
        conditional node with the reversed operands of the biconditional. Then tick *n*.
        """
        convert = Operator.Conditional

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(~self.convert(s.lhs, s.rhs), d)),
                group(sdnode(~self.convert(s.rhs, s.lhs), d)))

    class BiconditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated biconditional node *n* on a branch *b*, add a
        designated node to *b* with the negation of the biconditional, then tick *n*.
        """

    class BiconditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated biconditional node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) biconditional, then tick *n*.
        """
        
    class ExistentialNegatedDesignated(FDE.DefaultNodeRule, rules.QuantifiedSentenceRule):
        """
        From an unticked, designated negated existential node *n* on a branch *b*,
        add a designated node *n'* to *b* with a universal sentence consisting of
        disjunction, whose first disjunct is the negated inner sentence of *n*,
        and whose second disjunct is the negation of a disjunction *d*, where the
        first disjunct of *d* is the inner sentence of *n*, and the second disjunct
        of *d* is the negation of the inner sentence of *n*. Then tick *n*.
        """
        convert = Quantifier.Universal

        def _get_sd_targets(self, s, d, /):
            v, si = s[1:]
            yield adds(
                group(sdnode(self.convert(v, ~si | ~(si | ~si)), d)))

    class ExistentialUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated existential node *n* on a branch *b*, add a
        designated node to *b* with the negation of the existential sentence, then
        tick *n*.
        """

    class ExistentialNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated negated existential node *n* on a branch *b*,
        add a designated node to *b* with the negated existential sentence (negatum),
        then tick *n*.
        """
        
    class UniversalNegatedDesignated(FDE.QuantifierSkinnyRule):
        """
        From an unticked, designated universal existential node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'*, add a designtated node
        with the standard translation of the sentence on *b*. For *b''*, substitute
        a new constant *c* for the quantified variable, and add two undesignated
        nodes to *b''*, one with the substituted inner sentence, and one with its
        negation, then tick *n*.
        """
        convert = Quantifier.Existential

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = branch.new_constant() >> s
            d = self.designation
            yield adds(
                group(sdnode(self.convert(v, ~si), d)),
                group(sdnode(r, not d), sdnode(~r, not d)))

    class UniversalUndesignated(ExistentialUndesignated):
        """
        From an unticked, undesignated universal node *n* on a branch *b*, add a designated
        node to *b* with the negation of the universal sentence, then tick *n*.
        """

    class UniversalNegatedUndesignated(ExistentialNegatedUndesignated):
        """
        From an unticked, undesignated negated universal node *n* on a branch *b*,
        add a designated node to *b* with the negated universal sentence (negatum),
        then tick *n*.
        """

    groups = (
        (
            # non-branching rules
            FDE.Rules.AssertionDesignated,
            B3E.Rules.AssertionUndesignated,
            B3E.Rules.AssertionNegatedDesignated,
            B3E.Rules.AssertionNegatedUndesignated,
            FDE.Rules.ConjunctionDesignated,
            ConjunctionUndesignated,
            ConjunctionNegatedUndesignated,
            DisjunctionNegatedDesignated,
            DisjunctionUndesignated,
            DisjunctionNegatedUndesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalUndesignated,
            MaterialConditionalNegatedUndesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedUndesignated,
            ConditionalUndesignated,
            ConditionalNegatedUndesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated,
            BiconditionalDesignated,
            FDE.Rules.ExistentialDesignated,
            ExistentialNegatedDesignated,
            ExistentialUndesignated,
            ExistentialNegatedUndesignated,
            FDE.Rules.UniversalDesignated,
            UniversalUndesignated,
            UniversalNegatedUndesignated,
            FDE.Rules.DoubleNegationDesignated,
            FDE.Rules.DoubleNegationUndesignated),
        (
            # branching rules
            FDE.Rules.DisjunctionDesignated,
            ConjunctionNegatedDesignated,
            FDE.Rules.MaterialConditionalDesignated,
            FDE.Rules.MaterialBiconditionalDesignated,
            MaterialBiconditionalNegatedDesignated,
            ConditionalDesignated,
            ConditionalNegatedDesignated,
            BiconditionalNegatedDesignated,
            UniversalNegatedDesignated))
