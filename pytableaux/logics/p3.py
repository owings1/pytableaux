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

from ..proof import adds, sdnode
from ..tools import group
from . import fde as FDE
from . import k3 as K3
from . import LogicType

class Meta(K3.Meta):
    name = 'P3'
    title = 'Post 3-valued Logic'
    quantified = False
    description = (
        'Emil Post three-valued logic (T, F, and N) '
        'with mirror-image negation')
    category_order = 120

class Model(FDE.Model):

    # def is_sentence_opaque(self, s, /):
    #     return type(s) is Quantified or super().is_sentence_opaque(s)

    class TruthFunction(K3.Model.TruthFunction):

        def back_cycle(self, value, /):
            return self.values_sequence[self.values_indexes[value] - 1]

        Negation = back_cycle

        def Conjunction(self, a, b, /):
            return self.Negation(self.Disjunction(*map(self.Negation, (a, b))))

    # def value_of_quantified(self, s: Quantified, /):
    # #     """
    # #     Take the set of values of the sentence resulting
    # #     from the substitution of the variable with each constant. Then apply
    # #     the negation function to each of those values. Then take the maximum
    # #     of those values (the `generalized disjunction`), and apply the negation
    # #     function to that maximum value. The result is the value of the universal
    # #     sentence.
    # #     """
    #     it = self._unquantify_value_map(s)
    #     if s.quantifier is Quantifier.Existential:
    #         return maxceil(self.maxval, it, self.unassigned_value)
    #     if s.quantifier is Quantifier.Universal:
    #         try:
    #             initial = next(it)
    #         except StopIteration:
    #             return self.unassigned_value
    #         return reduce(self.truth_function.Conjunction, it, initial)
    #     raise TypeError(s.quantifier)


class System(FDE.System): pass

class Rules(LogicType.Rules):

    closure = K3.Rules.closure

    class DoubleNegationDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated, double-negation node `n` on a branch `b`,
        add two undesignated nodes to `b`, one with the double-negatum, and one
        with the negatum. Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(~s.lhs, not d), sdnode(s.lhs, not d)))

    class DoubleNegationUndesignated(System.OperatorNodeRule):
        """
        From an unticked, undesignated, double-negation node `n` on a branch `b`,
        make two branches `b'` and `b''` from `b`. On `b'` add a designated
        node with the negatum, and on `b'` add a designated node with the
        double-negatum. Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(~s.lhs, not d)),
                group(sdnode( s.lhs, not d)))

    class ConjunctionDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated conjunction node `n` on a branch `b`, add
        four undesignated nodes to `b`, one for each conjunct, and one for the
        negation of each conjunct. Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(
                    sdnode(~s.lhs, not d),
                    sdnode( s.lhs, not d),
                    sdnode(~s.rhs, not d),
                    sdnode( s.rhs, not d)))

    class ConjunctionNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated, negated conjunction node `n` on a branch
        `b`, make two branches `b'` and `b''` from `b`. On `b'` add a designated
        node with the first conjunct, and an undesignated node with the negation
        of the second conjunct. On `b''` add a designated node with the second
        conjunct, and an undesignated node with the negation of the frist conjunct.
        Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(s.lhs, d), sdnode(~s.rhs, not d)),
                group(sdnode(s.rhs, d), sdnode(~s.lhs, not d)))

    class ConjunctionUndesignated(System.OperatorNodeRule):
        """
        From an unticked, undesignated conjunction node `n` on a branch `b`, make
        four branches `b'`, `b''`, `b'''`, and `b''''` from `b`. On `b'`, add a
        designated node with the negation of the first conjunct. On `b''`, add
        a designated node ith the first conjunct. On `b'''`, add a designated
        node with the negation of the second conjunct. On `b''''`, add a designated
        node with the second conjunct. Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(~s.lhs, not d)),
                group(sdnode( s.lhs, not d)),
                group(sdnode( s.rhs, not d)),
                group(sdnode(~s.rhs, not d)))

    class ConjunctionNegatedUndesignated(System.OperatorNodeRule):
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

    class MaterialConditionalDesignated(System.MaterialConditionalReducingRule): pass
    class MaterialConditionalNegatedDesignated(System.MaterialConditionalReducingRule): pass
    class MaterialConditionalUndesignated(System.MaterialConditionalReducingRule): pass
    class MaterialConditionalNegatedUndesignated(System.MaterialConditionalReducingRule): pass
    class MaterialBiconditionalDesignated(System.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedDesignated(System.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalUndesignated(System.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedUndesignated(System.MaterialConditionalConjunctsReducingRule): pass
    class ConditionalDesignated(System.MaterialConditionalReducingRule): pass
    class ConditionalNegatedDesignated(System.MaterialConditionalReducingRule): pass
    class ConditionalUndesignated(System.MaterialConditionalReducingRule): pass
    class ConditionalNegatedUndesignated(System.MaterialConditionalReducingRule): pass
    class BiconditionalDesignated(System.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedDesignated(System.ConditionalConjunctsReducingRule): pass
    class BiconditionalUndesignated(System.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedUndesignated(System.ConditionalConjunctsReducingRule): pass

    # class ExistentialNegatedDesignated(System.QuantifierFatRule):
    #     """
    #     From an unticked, designated, negated existential node `n` on a branch
    #     `b`, for any constant `c` on `b`, let `r` be the result of substituting
    #     `c` for the variable bound by the sentence of `n`. If the negation of `r`
    #     does not appear on `b`, then add a designated node with the negation of
    #     `r` to `b`. If there are no constants yet on `b`, use a new constant.
    #     The node `n` is never ticked.
    #     """

    #     def _get_constant_nodes(self, node, c, branch, /):
    #         yield sdnode(c >> self.sentence(node), self.designation)

    # class ExistentialNegatedUndesignated(System.QuantifierFatRule):
    #     """
    #     From an unticked, undesignated, negated existential node `n` on a branch
    #     `b`, for a new constant `c` for `b`, let `r` be the result of substituting
    #     `c` for the variable bound by the sentence of `n`. If the negation of `r`
    #     does not appear on `b`, then add an undesignated node with the negation
    #     of `r` to `b`. If there are no constants yet on `b`, use a new constant.
    #     The node `n` is never ticked.
    #     """

    #     def _get_constant_nodes(self, node, c, branch, /):
    #         yield sdnode(~(c >> self.sentence(node)), not self.designation)

    # class UniversalDesignated(System.QuantifierFatRule):
    #     """
    #     From a designated universal node `n` on a branch `b`, if there are no
    #     constants on `b`, add two undesignated nodes to `b`, one with the
    #     quantified sentence, substituting a new constant for the variable, and
    #     the other with the negation of that sentence. If there are constants
    #     already on `b`, then use any of those constants instead of a new one,
    #     provided that the both the nodes to be added do not already appear on
    #     `b`. The node is never ticked.
    #     """

    #     def _get_constant_nodes(self, node, c, branch, /):
    #         r = c >> self.sentence(node)
    #         d = self.designation
    #         yield sdnode(r, not d)
    #         yield sdnode(~r, not d)

    # class UniversalNegatedDesignated(System.QuantifierSkinnyRule):
    #     """
    #     From an unticked, negated universal node `n` on a branch `b`, add a
    #     designated node to `b` with the quantified sentence, substituting a
    #     constant new to `b` for the variable. Then tick `n`.
    #     """

    #     def _get_node_targets(self, node, branch, /):
    #         s = self.sentence(node)
    #         yield adds(
    #             # Keep designation neutral for UniversalUndesignated
    #             group(sdnode(branch.new_constant() >> s, self.designation)))

    # class UniversalUndesignated(UniversalNegatedDesignated): pass

    # class UniversalNegatedUndesignated(System.QuantifierSkinnyRule):
    #     """
    #     From an unticked, undesignated, negated universal node `n` on a branch
    #     `b`, make two branches `b'` and `b''` from `b`. On `b'` add a designated
    #     node with the negation of the quantified sentence, substituing a constant
    #     new to `b` for the variable. On `b''` add a designated node with the
    #     negatum of `n`. Then tick `n`.
    #     """

    #     def _get_node_targets(self, node, branch, /):
    #         s = self.sentence(node)
    #         d = self.designation
    #         yield adds(
    #             group(sdnode(branch.new_constant() >> s, not d)),
    #             group(sdnode(s, not d)))

    groups = (
        group(
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
            BiconditionalNegatedUndesignated),
        group(
            # two-branching rules
            DoubleNegationUndesignated,
            ConjunctionNegatedDesignated,
            FDE.Rules.DisjunctionDesignated,
            FDE.Rules.DisjunctionNegatedUndesignated),
        group(
            # three-branching rules
            ConjunctionNegatedUndesignated),
        group(
            # four-branching rules
            ConjunctionUndesignated),
        # group(
        #     FDE.Rules.ExistentialDesignated,
        #     UniversalUndesignated,
        #     UniversalNegatedDesignated,
        #     UniversalNegatedUndesignated),
        # group(
        #     UniversalDesignated,
        #     FDE.Rules.ExistentialUndesignated,
        #     ExistentialNegatedDesignated,
        #     ExistentialNegatedUndesignated)
            )

    @classmethod
    def _check_groups(cls):
        for branching, group in enumerate(cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'