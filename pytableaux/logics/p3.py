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

from ..lang import Constant, Operator, Quantified
from ..proof import Branch, Node, adds, sdnode
from ..tools import group, maxceil
from . import fde as FDE
from . import k3 as K3

class Meta(K3.Meta):
    name = 'P3'
    title = 'Post 3-valued Logic'
    description = 'Emil Post three-valued logic (T, F, and N) with mirror-image negation'
    category_order = 120

class Model(K3.Model):

    def value_of_universal(self, s: Quantified, /, **kw):
        """
        Take the set of values of the sentence resulting
        from the substitution of the variable with each constant. Then apply
        the negation function to each of those values. Then take the maximum
        of those values (the `generalized disjunction`), and apply the negation
        function to that maximum value. The result is the value of the universal
        sentence.
        """
        v = s.variable
        sub = s.sentence.substitute
        return self.truth_function(
            Operator.Negation,
            maxceil(
                self.Value.T,
                (self.truth_function(Operator.Negation, self.value_of(sub(c, v), **kw))
                    for c in self.constants)))

    def truth_function(self, oper, a, b=None, /):
        oper = Operator(oper)
        if oper is Operator.Negation:
            return self.back_cycle(a)
        if oper is Operator.Conjunction:
            return self.truth_function(
                Operator.Negation,
                self.truth_function(
                    Operator.Disjunction,
                    *(self.truth_function(Operator.Negation, x) for x in (a, b))))
        return super().truth_function(oper, a, b)

    def back_cycle(self, value):
        seq = self.Value._seq
        return seq[seq.index(value) - 1]

class System(K3.System):

    branchables = {
        Operator.Negation: (None, (1, 0)),
        Operator.Assertion: ((0, 0), (0, 0)),
        Operator.Conjunction: ((3, 0), (2, 1)),
        Operator.Disjunction: ((0, 1), (1, 0)),
        # reduction
        Operator.MaterialConditional: ((0, 0), (0, 0)),
        # reduction
        Operator.MaterialBiconditional: ((0, 0), (0, 0)),
        # reduction
        Operator.Conditional: ((0, 0), (0, 0)),
        # reduction
        Operator.Biconditional: ((0, 0), (0, 0))}

class Rules(K3.Rules):

    class DoubleNegationDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, double-negation node `n` on a branch `b`,
        add two undesignated nodes to `b`, one with the double-negatum, and one
        with the negatum. Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            si = s.lhs
            yield adds(
                group(sdnode(~si, not d), sdnode(si, not d)))

    class DoubleNegationUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, double-negation node `n` on a branch `b`,
        make two branches `b'` and `b''` from `b`. On `b'` add a designated
        node with the negatum, and on `b'` add a designated node with the
        double-negatum. Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            si = s.lhs
            yield adds(
                group(sdnode(~si, not d)),
                group(sdnode( si, not d)))

    class ConjunctionDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated conjunction node `n` on a branch `b`, add
        four undesignated nodes to `b`, one for each conjunct, and one for the
        negation of each conjunct. Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(
                    sdnode(~lhs, not d),
                    sdnode( lhs, not d),
                    sdnode(~rhs, not d),
                    sdnode( rhs, not d)))

    class ConjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated conjunction node `n` on a branch
        `b`, make two branches `b'` and `b''` from `b`. On `b'` add a designated
        node with the first conjunct, and an undesignated node with the negation
        of the second conjunct. On `b''` add a designated node with the second
        conjunct, and an undesignated node with the negation of the frist conjunct.
        Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode(lhs, d), sdnode(~rhs, not d)),
                group(sdnode(rhs, d), sdnode(~lhs, not d)))

    class ConjunctionUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated conjunction node `n` on a branch `b`, make
        four branches `b'`, `b''`, `b'''`, and `b''''` from `b`. On `b'`, add a
        designated node with the negation of the first conjunct. On `b''`, add
        a designated node ith the first conjunct. On `b'''`, add a designated
        node with the negation of the second conjunct. On `b''''`, add a designated
        node with the second conjunct. Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode(~lhs, not d)),
                group(sdnode( lhs, not d)),
                group(sdnode( rhs, not d)),
                group(sdnode(~rhs, not d)))

    class ConjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, negated conjunction node `n` on a branch
        `b`, make three branches `b'`, `b''`, and `b'''` from `b`. On `b'`, add
        four undesignated nodes, one for each conjunct, and one for the negation
        of each conjunct. On `b''`, add a designated node with the negation of
        the first conjunct. On `b'''`, add a designated node with the negation
        of the second conjunct. Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(
                    sdnode(~lhs, d),
                    sdnode( lhs, d),
                    sdnode(~rhs, d),
                    sdnode( rhs, d)),
                group(sdnode(~lhs, not d)),
                group(sdnode(~rhs, not d)))

    class MaterialConditionalDesignated(FDE.OperatorNodeRule):
        "This rule reduces to a disjunction."

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~s.lhs | s.rhs, d)))

    class MaterialConditionalNegatedDesignated(FDE.OperatorNodeRule):
        "This rule reduces to a disjunction."

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~(~s.lhs | s.rhs), d)))

    class MaterialConditionalUndesignated(FDE.OperatorNodeRule):
        "This rule reduces to a disjunction."

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~s.lhs | s.rhs, d)))

    class MaterialConditionalNegatedUndesignated(FDE.OperatorNodeRule):
        "This rule reduces to a disjunction."

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~(~s.lhs | s.rhs), d)))

    class MaterialBiconditionalDesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedDesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalUndesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedUndesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class ConditionalDesignated(MaterialConditionalDesignated): pass
    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated): pass
    class ConditionalUndesignated(MaterialConditionalUndesignated): pass
    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated): pass
    class BiconditionalDesignated(FDE.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedDesignated(FDE.ConditionalConjunctsReducingRule): pass
    class BiconditionalUndesignated(FDE.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedUndesignated(FDE.ConditionalConjunctsReducingRule): pass

    class ExistentialNegatedDesignated(FDE.QuantifierFatRule):
        """
        From an unticked, designated, negated existential node `n` on a branch
        `b`, for any constant `c` on `b`, let `r` be the result of substituting
        `c` for the variable bound by the sentence of `n`. If the negation of `r`
        does not appear on `b`, then add a designated node with the negation of
        `r` to `b`. If there are no constants yet on `b`, use a new constant.
        The node `n` is never ticked.
        """

        def _get_constant_nodes(self, node: Node, c: Constant, _, /):
            yield sdnode(c >> self.sentence(node), self.designation)

    class ExistentialNegatedUndesignated(FDE.QuantifierFatRule):
        """
        From an unticked, undesignated, negated existential node `n` on a branch
        `b`, for a new constant `c` for `b`, let `r` be the result of substituting
        `c` for the variable bound by the sentence of `n`. If the negation of `r`
        does not appear on `b`, then add an undesignated node with the negation
        of `r` to `b`. If there are no constants yet on `b`, use a new constant.
        The node `n` is never ticked.
        """

        def _get_constant_nodes(self, node: Node, c: Constant, _, /):
            yield sdnode(~(c >> self.sentence(node)), not self.designation)

    class UniversalDesignated(FDE.QuantifierFatRule):
        """
        From a designated universal node `n` on a branch `b`, if there are no
        constants on `b`, add two undesignated nodes to `b`, one with the
        quantified sentence, substituting a new constant for the variable, and
        the other with the negation of that sentence. If there are constants
        already on `b`, then use any of those constants instead of a new one,
        provided that the both the nodes to be added do not already appear on
        `b`. The node is never ticked.
        """

        def _get_constant_nodes(self, node: Node, c: Constant, _, /):
            r = c >> self.sentence(node)
            d = self.designation
            yield sdnode(r, not d)
            yield sdnode(~r, not d)

    class UniversalNegatedDesignated(FDE.QuantifierSkinnyRule):
        """
        From an unticked, negated universal node `n` on a branch `b`, add a
        designated node to `b` with the quantified sentence, substituting a
        constant new to `b` for the variable. Then tick `n`.
        """

        def _get_node_targets(self, node: Node, branch: Branch):
            s = self.sentence(node)
            yield adds(
                # Keep designation neutral for UniversalUndesignated
                group(sdnode(branch.new_constant() >> s, self.designation)))

    class UniversalUndesignated(UniversalNegatedDesignated):
        """
        From an unticked, undesignated universal node `n` on a branch `b`, add
        an undesignated node to `b` with the quantified sentence, substituting
        a constant new to `b` for the variable. Then tick `n`.
        """

    class UniversalNegatedUndesignated(FDE.QuantifierSkinnyRule):
        """
        From an unticked, undesignated, negated universal node `n` on a branch
        `b`, make two branches `b'` and `b''` from `b`. On `b'` add a designated
        node with the negation of the quantified sentence, substituing a constant
        new to `b` for the variable. On `b''` add a designated node with the
        negatum of `n`. Then tick `n`.
        """

        def _get_node_targets(self, node: Node, branch: Branch):
            s = self.sentence(node)
            d = self.designation
            yield adds(
                group(sdnode(branch.new_constant() >> s, not d)),
                group(sdnode(s, not d)))

    rule_groups = (
        (
            # non-branching rules
            FDE.Rules.AssertionDesignated,
            FDE.Rules.AssertionUndesignated,
            FDE.Rules.AssertionNegatedDesignated,
            FDE.Rules.AssertionNegatedUndesignated,

            ConjunctionDesignated,

            FDE.Rules.DisjunctionUndesignated,
            FDE.Rules.DisjunctionNegatedDesignated,

            DoubleNegationDesignated,
            
            # reduction rules (thus, non-branching)
            MaterialConditionalDesignated,
            MaterialConditionalUndesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalNegatedUndesignated,
            ConditionalDesignated,
            ConditionalUndesignated,
            ConditionalNegatedDesignated,
            ConditionalNegatedUndesignated,
            MaterialBiconditionalDesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedDesignated,
            MaterialBiconditionalNegatedUndesignated,
            BiconditionalDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedDesignated,
            BiconditionalNegatedUndesignated,
        ),
        (
            # two-branching rules
            DoubleNegationUndesignated,

            ConjunctionNegatedDesignated,

            FDE.Rules.DisjunctionDesignated,
            FDE.Rules.DisjunctionNegatedUndesignated,            
        ),
        (
            # three-branching rules
            ConjunctionNegatedUndesignated,
        ),
        (
            # four-branching rules
            ConjunctionUndesignated,
        ),
        (
            FDE.Rules.ExistentialDesignated,
            UniversalUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated,
        ),
        (
            UniversalDesignated,
            FDE.Rules.ExistentialUndesignated,
            ExistentialNegatedDesignated,
            ExistentialNegatedUndesignated,
        )
    )
