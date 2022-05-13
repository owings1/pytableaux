# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
#
# ------------------
#
# pytableaux - Post 3-valued logic
from __future__ import annotations

from pytableaux.lang.lex import Constant
from pytableaux.lang.lex import Operator as Oper
from pytableaux.lang.lex import Quantified, Quantifier
from pytableaux.logics import fde as FDE
from pytableaux.logics import k3 as K3
from pytableaux.proof.common import Branch, Node
from pytableaux.proof.util import adds, group, sdnode

name = 'P3'

class Meta(K3.Meta):
    title       = 'Post 3-valued logic'
    description = 'Emil Post three-valued logic (T, F, and N) with mirror-image negation'
    category_order = 120


class Model(K3.Model):
    """
    A L{P3} model is just like a :ref:`K3 model <k3-model>` with different tables
    for some of the connectives.
    """

    def value_of_universal(self, s: Quantified, /, **kw):
        """
        Take the set of values of the sentence resulting
        from the substitution of the variable with each constant. Then apply
        the negation function to each of those values. Then take the maximum
        of those values (the `generalized disjunction`), and apply the negation
        function to that minimum value. The result is the value of the universal
        sentence.
        """
        v = s.variable
        si = s.sentence
        values = {
            self.truth_function(
                Oper.Negation,
                self.value_of(si.substitute(c, v), **kw)
            )
            for c in self.constants
        }
        return self.truth_function(Oper.Negation, max(values))

    def truth_function(self, oper: Oper, a, b=None, /):
        oper = Oper(oper)
        if oper is Oper.Negation:
            return self.back_cycle(a)
        if oper is Oper.Conjunction:
            return self.truth_function(
                Oper.Negation,
                self.truth_function(
                    Oper.Disjunction,
                    *(self.truth_function(Oper.Negation, x) for x in (a, b))
                )
            )
        return super().truth_function(oper, a, b)
        
    def back_cycle(self, value):
        seq = self.Value._seq
        i = seq.index(value)
        return seq[i - 1]

class TableauxSystem(FDE.TableauxSystem):

    branchables = {
        Oper.Negation: {
            True : {True: 0, False: 1},
        },
        Oper.Assertion: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        Oper.Conjunction: {
            False : {True: 0, False: 3},
            True  : {True: 1, False: 2},
        },
        Oper.Disjunction: {
            False : {True: 1, False: 0},
            True  : {True: 0, False: 1},
        },
        # reduction
        Oper.MaterialConditional: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        # reduction
        Oper.MaterialBiconditional: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        # reduction
        Oper.Conditional: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        # reduction
        Oper.Biconditional: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
    }

@TableauxSystem.initialize
class TabRules:
    """
    The Tableaux System for L{P3} contains the FDE closure rule, and the
    L{K3} closure rule. Some of the operator rules are the same as L{FDE},
    most notably disjunction. However, many rules for L{P3} are different
    from L{FDE}, given the non-standard negation. Notably, an undesignated
    double-negation will branch.
    """

    class GlutClosure(K3.TabRules.GlutClosure):
        pass

    class DesignationClosure(FDE.TabRules.DesignationClosure):
        pass

    class DoubleNegationDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, double-negation node `n` on a branch `b`,
        add two undesignated nodes to `b`, one with the double-negatum, and one
        with the negatum. Then tick `n`.
        """
        designation = True
        negated     = True
        operator    = Oper.Negation
        branch_level = 1

        def _get_node_targets(self, node: Node, _,/):
            s = self.sentence(node)
            si = s.lhs
            d = self.designation
            return adds(
                group(sdnode(~si, not d), sdnode(si, not d))
            )

    class DoubleNegationUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, double-negation node `n` on a branch `b`,
        make two branches `b'` and `b''` from `b`. On `b'` add a designated
        node with the negatum, and on `b'` add a designated node with the
        double-negatum. Then tick `n`.
        """
        designation = False
        negated     = True
        operator    = Oper.Negation
        branch_level = 2

        def _get_node_targets(self, node: Node, _,/):
            s = self.sentence(node)
            si = s.lhs
            d = self.designation
            return adds(
                group(sdnode(~si, not d)),
                group(sdnode( si, not d)),
            )

    class AssertionDesignated(FDE.TabRules.AssertionDesignated):
        pass

    class AssertionNegatedDesignated(FDE.TabRules.AssertionNegatedDesignated):
        pass

    class AssertionUndesignated(FDE.TabRules.AssertionUndesignated):
        pass

    class AssertionNegatedUndesignated(FDE.TabRules.AssertionNegatedUndesignated):
        pass

    class ConjunctionDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated conjunction node `n` on a branch `b`, add
        four undesignated nodes to `b`, one for each conjunct, and one for the
        negation of each conjunct. Then tick `n`.
        """
        designation = True
        operator    = Oper.Conjunction
        branch_level = 1

        def _get_node_targets(self, node: Node, _,/):
            s = self.sentence(node)
            lhs, rhs = s
            d = self.designation
            return adds(
                group(
                    sdnode(~lhs, not d),
                    sdnode( lhs, not d),
                    sdnode(~rhs, not d),
                    sdnode( rhs, not d),
                )
            )

    class ConjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated conjunction node `n` on a branch
        `b`, make two branches `b'` and `b''` from `b`. On `b'` add a designated
        node with the first conjunct, and an undesignated node with the negation
        of the second conjunct. On `b''` add a designated node with the second
        conjunct, and an undesignated node with the negation of the frist conjunct.
        Then tick `n`.
        """
        designation = True
        negated     = True
        operator    = Oper.Conjunction
        branch_level = 2

        def _get_node_targets(self, node: Node, _,/):
            s = self.sentence(node)
            lhs, rhs = s
            d = self.designation
            return adds(
                group(sdnode(lhs, d), sdnode(~rhs, not d)),
                group(sdnode(rhs, d), sdnode(~lhs, not d)),
            )

    class ConjunctionUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated conjunction node `n` on a branch `b`, make
        four branches `b'`, `b''`, `b'''`, and `b''''` from `b`. On `b'`, add a
        designated node with the negation of the first conjunct. On `b''`, add
        a designated node ith the first conjunct. On `b'''`, add a designated
        node with the negation of the second conjunct. On `b''''`, add a designated
        node with the second conjunct. Then tick `n`.
        """
        designation = False
        operator    = Oper.Conjunction
        branch_level = 4

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(~lhs, not d)),
                group(sdnode( lhs, not d)),
                group(sdnode( rhs, not d)),
                group(sdnode(~rhs, not d)),
            )

    class ConjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, negated conjunction node `n` on a branch
        `b`, make three branches `b'`, `b''`, and `b'''` from `b`. On `b'`, add
        four undesignated nodes, one for each conjunct, and one for the negation
        of each conjunct. On `b''`, add a designated node with the negation of
        the first conjunct. On `b'''`, add a designated node with the negation
        of the second conjunct. Then tick `n`.
        """
        designation = False
        negated     = True
        operator    = Oper.Conjunction
        branch_level = 3

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            d = self.designation
            return adds(
                group(
                    sdnode(~lhs, d),
                    sdnode( lhs, d),
                    sdnode(~rhs, d),
                    sdnode( rhs, d),
                ),
                group(sdnode(~lhs, not d)),
                group(sdnode(~rhs, not d)),
            )

    class DisjunctionDesignated(FDE.TabRules.DisjunctionDesignated):
        pass
            
    class DisjunctionNegatedDesignated(FDE.TabRules.DisjunctionNegatedDesignated):
        pass

    class DisjunctionUndesignated(FDE.TabRules.DisjunctionUndesignated):
        pass

    class DisjunctionNegatedUndesignated(FDE.TabRules.DisjunctionNegatedUndesignated):
        pass

    class MaterialConditionalDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a disjunction.
        """
        designation = True
        operator    = Oper.MaterialConditional
        branch_level = 1

        def _get_node_targets(self, node: Node, _,/):
            s = self.sentence(node)
            return adds(
                group(sdnode(~s.lhs | s.rhs, self.designation))
            )

    class MaterialConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a disjunction.
        """
        designation = True
        negated     = True
        operator    = Oper.MaterialConditional
        branch_level = 1

        def _get_node_targets(self, node: Node, _,/):
            s = self.sentence(node)
            return adds(
                group(sdnode(~(~s.lhs | s.rhs), self.designation))
            )

    class MaterialConditionalUndesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a disjunction.
        """
        designation = False
        operator    = Oper.MaterialConditional
        branch_level = 1

        def _get_node_targets(self, node: Node, _,/):
            s = self.sentence(node)
            return adds(
                group(sdnode(~s.lhs | s.rhs, self.designation))
            )

    class MaterialConditionalNegatedUndesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a disjunction.
        """
        designation = False
        negated     = True
        operator    = Oper.MaterialConditional
        branch_level = 1

        def _get_node_targets(self, node: Node, _,/):
            s = self.sentence(node)
            return adds(
                group(sdnode(~(~s.lhs | s.rhs), self.designation))
            )

    class MaterialBiconditionalDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """
        designation = True
        operator    = Oper.MaterialBiconditional
        conjunct_op = Oper.MaterialConditional

    class MaterialBiconditionalNegatedDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """
        designation = True
        negated     = True
        operator    = Oper.MaterialBiconditional
        conjunct_op = Oper.MaterialConditional

    class MaterialBiconditionalUndesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """
        designation = False
        operator    = Oper.MaterialBiconditional
        conjunct_op = Oper.MaterialConditional

    class MaterialBiconditionalNegatedUndesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """
        designation = False
        negated     = True
        operator    = Oper.MaterialBiconditional
        conjunct_op = Oper.MaterialConditional

    class ConditionalDesignated(MaterialConditionalDesignated):
        """
        This is the same as the rule for the material conditional.
        """
        operator = Oper.Conditional

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        This is the same as the rule for the material conditional.
        """
        operator = Oper.Conditional

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        This is the same as the rule for the material conditional.
        """
        operator = Oper.Conditional

    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated):
        """
        This is the same as the rule for the material conditional.
        """
        operator = Oper.Conditional

    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        """
        This rule reduces to a conjunction of conditionals.
        """
        operator    = Oper.Biconditional
        conjunct_op = Oper.Conditional

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule reduces to a conjunction of conditionals.
        """
        operator    = Oper.Biconditional
        conjunct_op = Oper.Conditional

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        This rule reduces to a conjunction of conditionals.
        """
        operator    = Oper.Biconditional
        conjunct_op = Oper.Conditional

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        This rule reduces to a conjunction of conditionals.
        """
        operator    = Oper.Biconditional
        conjunct_op = Oper.Conditional

    class ExistentialDesignated(FDE.TabRules.ExistentialDesignated):
        pass

    class ExistentialNegatedDesignated(FDE.QuantifierFatRule):
        """
        From an unticked, designated, negated existential node `n` on a branch
        `b`, for any constant `c` on `b`, let `r` be the result of substituting
        `c` for the variable bound by the sentence of `n`. If the negation of `r`
        does not appear on `b`, then add a designated node with the negation of
        `r` to `b`. If there are no constants yet on `b`, use a new constant.
        The node `n` is never ticked.
        """
        designation = True
        negated     = True
        quantifier  = Quantifier.Existential
        branch_level = 1

        def _get_constant_nodes(self, node: Node, c: Constant, _, /):
            return sdnode(c >> self.sentence(node), self.designation),

    class ExistentialUndesignated(FDE.TabRules.ExistentialUndesignated):
        pass

    class ExistentialNegatedUndesignated(FDE.QuantifierFatRule):
        """
        From an unticked, undesignated, negated existential node `n` on a branch
        `b`, for a new constant `c` for `b`, let `r` be the result of substituting
        `c` for the variable bound by the sentence of `n`. If the negation of `r`
        does not appear on `b`, then add an undesignated node with the negation
        of `r` to `b`. If there are no constants yet on `b`, use a new constant.
        The node `n` is never ticked.
        """
        designation = True
        negated     = True
        quantifier  = Quantifier.Existential
        branch_level = 1

        def _get_constant_nodes(self, node: Node, c: Constant, _, /):
            return sdnode(~(c >> self.sentence(node)), not self.designation),

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
        designation = True
        negated     = False
        quantifier  = Quantifier.Universal
        branch_level = 1

        def _get_constant_nodes(self, node: Node, c: Constant, _, /):
            r = c >> self.sentence(node)
            d = self.designation
            return sdnode(r, not d), sdnode(~r, not d)

    class UniversalNegatedDesignated(FDE.QuantifierSkinnyRule):
        """
        From an unticked, negated universal node `n` on a branch `b`, add a
        designated node to `b` with the quantified sentence, substituting a
        constant new to `b` for the variable. Then tick `n`.
        """
        designation = True
        negated     = True
        quantifier  = Quantifier.Universal
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s = self.sentence(node)
            return adds(
                # Keep designation neutral for UniversalUndesignated
                group(sdnode(branch.new_constant() >> s, self.designation))
            )

    class UniversalUndesignated(UniversalNegatedDesignated):
        """
        From an unticked, undesignated universal node `n` on a branch `b`, add
        an undesignated node to `b` with the quantified sentence, substituting
        a constant new to `b` for the variable. Then tick `n`.
        """
        designation = False
        negated     = False

    class UniversalNegatedUndesignated(FDE.QuantifierSkinnyRule):
        """
        From an unticked, undesignated, negated universal node `n` on a branch
        `b`, make two branches `b'` and `b''` from `b`. On `b'` add a designated
        node with the negation of the quantified sentence, substituing a constant
        new to `b` for the variable. On `b''` add a designated node with the
        negatum of `n`. Then tick `n`.
        """
        designation = False
        negated     = True
        quantifier  = Quantifier.Universal
        branch_level = 2

        def _get_node_targets(self, node: Node, branch: Branch):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(branch.new_constant() >> s, not d)),
                group(sdnode(s, not d)),
            )

    closure_rules = (
        GlutClosure,
        DesignationClosure,
    )

    rule_groups = (
        (
            # non-branching rules
            AssertionDesignated,
            AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,

            ConjunctionDesignated,

            DisjunctionUndesignated,
            DisjunctionNegatedDesignated,

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

            DisjunctionDesignated,
            DisjunctionNegatedUndesignated,            
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
            ExistentialDesignated,
            UniversalUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated,
        ),
        (
            UniversalDesignated,
            ExistentialUndesignated,
            ExistentialNegatedDesignated,
            ExistentialNegatedUndesignated,
        )
    )
