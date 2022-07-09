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
# pytableaux - Weak Kleene Logic with alternate quantification
from __future__ import annotations

import pytableaux.logics.fde as FDE
import pytableaux.logics.k3w as K3W
from pytableaux.lang import Operated, Quantified, Quantifier
from pytableaux.proof import Branch, Node, adds, group, sdnode

name = 'K3WQ'

class Meta(K3W.Meta):
    title       = 'Weak Kleene alt-Q Logic'
    description = 'Three-valued logic with values T, F, and N, with alternate quantification'
    category_order = 40

class Model(K3W.Model):

    Value = K3W.Model.Value
    # generalized conjunction
    mc_nvals = {
        Value.F: 2,
        Value.N: 1,
        Value.T: 3,
    }
    mc_cvals = {
        1: Value.N,
        2: Value.F,
        3: Value.T,
    }

    # generalized disjunction
    md_nvals = {
        Value.F: 1,
        Value.N: 3,
        Value.T: 2,
    }
    md_cvals = {
        1: Value.F,
        2: Value.T,
        3: Value.N,
    }

    def value_of_operated(self, s: Operated, /, **kw):
        return super().value_of_operated(s, **kw)

    def value_of_universal(self, s: Quantified, /, **kw):
        """
        A universal sentence is interpreted in terms of `generalized conjunction`.
        If we order the values least to greatest as V{N}, V{F}, V{T}, then we
        can define the value of a universal in terms of the `minimum` value of
        the set of values for the substitution of each constant in the model for
        the variable.
        """
        v = s.variable
        si = s.sentence
        values = {self.value_of(si.substitute(c, v), **kw) for c in self.constants}
        mc_values = {self.mc_nvals[value] for value in values}
        mc_value = min(mc_values)
        value = self.mc_cvals[mc_value]
        return value

    def value_of_existential(self, s: Quantified, **kw):
        """
        An existential sentence is interpreted in terms of `generalized disjunction`.
        If we order the values least to greatest as V{N}, V{T}, V{F}, then we
        can define the value of an existential in terms of the `maximum` value of
        the set of values for the substitution of each constant in the model for
        the variable.
        """
        v = s.variable
        si = s.sentence
        values = {self.value_of(si.substitute(c, v), **kw) for c in self.constants}
        md_values = {self.md_nvals[value] for value in values}
        md_value = max(md_values)
        value = self.md_cvals[md_value]
        return value

class TableauxSystem(K3W.TableauxSystem):
    pass

@TableauxSystem.initialize
class TabRules(K3W.TabRules):

    class ExistentialDesignated(FDE.QuantifierSkinnyRule):
        """
        From an unticked, designated existential node `n` on a branch `b`, add
        two designated nodes to `b`. One node is the result of universally
        quantifying over the disjunction of the inner sentence with its negation.
        The other node is a substitution of a constant new to `b`. Then tick `n`.
        """
        designation = True
        negated     = False
        quantifier  = Quantifier.Existential
        convert     = Quantifier.Universal

        def _get_node_targets(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            v, si = s[1:]
            d = self.designation
            return adds(
                group(
                    sdnode(self.convert(v, si | ~si), d),
                    sdnode(branch.new_constant() >> s, d),
                )
            )

    class ExistentialUndesignated(FDE.QuantifierSkinnyRule):
        """
        From an unticked, undesignated existential node `n` on a branch `b`, make
        two branches `b'` and `b''` from `b`. On `b'` add two undesignated nodes,
        one with the substituion of a constant new to `b` for the inner sentence,
        and the other with the negation of that sentence. On `b''` add a designated
        node with universal quantifier over the negation of the inner sentence.
        Then tick `n`.
        """
        designation = False
        negated     = False
        quantifier  = Quantifier.Existential
        convert     = Quantifier.Universal
        branching   = 1

        def _get_node_targets(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            v, si = s[1:]
            r = branch.new_constant() >> s
            d = self.designation
            return adds(
                group(sdnode(r, d), sdnode(~r, d)),
                group(sdnode(self.convert(v, ~si), not d)),
            )

    class ExistentialNegatedUndesignated(FDE.QuantifierSkinnyRule):
        """"
        From an unticked, undesignated, negated existential node `n` on a branch
        `b`, add an undesignated node to `b` with the negation of the inner
        sentence, substituting a constant new to `b` for the variable. Then
        tick `n`.
        """
        designation = False
        negated     = True
        quantifier  = Quantifier.Existential

        def _get_node_targets(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            return adds(
                group(sdnode(~(branch.new_constant() >> s), self.designation))
            )

    class UniversalNegatedDesignated(FDE.QuantifierSkinnyRule):
        """
        From an unticked, designated, negated universal node `n` on a branch `b`,
        add two designated nodes to `b`. The first node is a universally quantified
        disjunction of the inner sentence and its negation. The second node is the
        negation of the inner sentence, substituting a constant new to `b` for the
        variable. Then tick `n`.
        """
        designation = True
        negated     = True
        quantifier  = Quantifier.Universal

        def _get_node_targets(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            v, si = s[1:]
            d = self.designation
            return adds(
                group(
                    sdnode(self.quantifier(v, si | ~si), d),
                    sdnode(~(branch.new_constant() >> s), d)
                )
            )

    class UniversalNegatedUndesignated(FDE.QuantifierSkinnyRule):
        """
        From an unticked, undesignated, negated universal node `n` on a branch `b`,
        make two branches `b'` and `b''` from `b`. On `b'` add two undesignated nodes,
        one with the substitution of a constant new to `b` for the inner sentence
        of `n`, and the other with the negation of that sentence. On `b''`, add
        a designated node with the negatum of `n`. Then tick `n`.
        """
        designation = False
        negated     = True
        quantifier  = Quantifier.Universal
        branching   = 1

        def _get_node_targets(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            v, si = s[1:]
            r = branch.new_constant() >> s
            d = self.designation
            return adds(
                group(sdnode(r, d), sdnode(~r, d)),
                group(sdnode(self.quantifier(v, si), not d)),
            )

    rule_groups = (
        (
            # non-branching rules

            FDE.TabRules.AssertionDesignated,
            FDE.TabRules.AssertionUndesignated,
            FDE.TabRules.AssertionNegatedDesignated,
            FDE.TabRules.AssertionNegatedUndesignated,
            FDE.TabRules.ConjunctionDesignated, 
            FDE.TabRules.DisjunctionNegatedDesignated,

            FDE.TabRules.ExistentialNegatedDesignated,

            FDE.TabRules.DoubleNegationDesignated,
            FDE.TabRules.DoubleNegationUndesignated,
            # reduction rules (thus, non-branching)
            K3W.TabRules.MaterialConditionalDesignated,
            K3W.TabRules.MaterialConditionalUndesignated,
            K3W.TabRules.MaterialConditionalNegatedDesignated,
            K3W.TabRules.MaterialConditionalNegatedUndesignated,
            K3W.TabRules.ConditionalDesignated,
            K3W.TabRules.ConditionalUndesignated,
            K3W.TabRules.ConditionalNegatedDesignated,
            K3W.TabRules.ConditionalNegatedUndesignated,
            K3W.TabRules.MaterialBiconditionalDesignated,
            K3W.TabRules.MaterialBiconditionalUndesignated,
            K3W.TabRules.MaterialBiconditionalNegatedDesignated,
            K3W.TabRules.MaterialBiconditionalNegatedUndesignated,
            K3W.TabRules.BiconditionalDesignated,
            K3W.TabRules.BiconditionalUndesignated,
            K3W.TabRules.BiconditionalNegatedDesignated,
            K3W.TabRules.BiconditionalNegatedUndesignated,
        ),
        (
            # two-branching rules
            FDE.TabRules.ConjunctionUndesignated,
        ),
        (
            # three-branching rules
            K3W.TabRules.DisjunctionDesignated,
            K3W.TabRules.DisjunctionUndesignated,
            K3W.TabRules.ConjunctionNegatedDesignated,
            K3W.TabRules.ConjunctionNegatedUndesignated,
            # five-branching rules (formerly)
            K3W.TabRules.DisjunctionNegatedUndesignated,
        ),
        (
            ExistentialDesignated,
            ExistentialNegatedUndesignated,
            ExistentialUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated,
        ),
        (
            FDE.TabRules.UniversalDesignated,
            FDE.TabRules.UniversalUndesignated,
        ),
    )
