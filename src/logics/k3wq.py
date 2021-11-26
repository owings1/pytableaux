# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
name = 'K3WQ'

class Meta(object):
    title    = 'Weak Kleene 3-valued alternate-quantifier logic'
    category = 'Many-valued'
    description = 'Three-valued logic with values T, F, and N, with alternate quantification'
    tags = ['many-valued', 'gappy', 'non-modal', 'first-order']
    category_display_order = 40

from proof.common import Branch, Node, Target
from lexicals import Quantifier, Quantified
from . import fde as FDE, k3w as K3W, k3 as K3

class Model(K3W.Model):
    """
    A K3WQ model is just like a `K3W model`_ with a different treatment of the
    quantifiers

    .. _K3W model: k3w.html#logics.k3w.Model
    """

    # generalized conjunction
    mc_nvals = {
        'F': 2,
        'N': 1,
        'T': 3,
    }
    mc_cvals = {
        1: 'N',
        2: 'F',
        3: 'T',
    }

    # generalized disjunction
    md_nvals = {
        'F': 1,
        'N': 3,
        'T': 2,
    }
    md_cvals = {
        1: 'F',
        2: 'T',
        3: 'N',
    }

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//k3wq//
        """
        return super().value_of_operated(sentence, **kw)

    def value_of_universal(self, sentence, **kw):
        """
        A universal sentence is interpreted in terms of `generalized conjunction`.
        If we order the values least to greatest as :m:`N`, :m:`F`, :m:`T`, then we
        can define the value of a universal in terms of the `minimum` value of
        the set of values for the substitution of each constant in the model for
        the variable.
        """
        v = sentence.variable
        si = sentence.sentence
        values = {self.value_of(si.substitute(c, v), **kw) for c in self.constants}
        mc_values = {self.mc_nvals[value] for value in values}
        mc_value = min(mc_values)
        value = self.mc_cvals[mc_value]
        return value

    def value_of_existential(self, sentence, **kw):
        """
        An existential sentence is interpreted in terms of `generalized disjunction`.
        If we order the values least to greatest as :m:`N`, :m:`T`, :m:`F`, then we
        can define the value of an existential in terms of the `maximum` value of
        the set of values for the substitution of each constant in the model for
        the variable.
        """
        v = sentence.variable
        si = sentence.sentence
        values = {self.value_of(si.substitute(c, v), **kw) for c in self.constants}
        md_values = {self.md_nvals[value] for value in values}
        md_value = max(md_values)
        value = self.md_cvals[md_value]
        return value

class TableauxSystem(FDE.TableauxSystem):
    """
    K3WQ's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """

class DefaultNodeRule(FDE.DefaultNodeRule):
    pass

# class DefaultNewConstantRule(FDE.DefaultNewConstantRule):
#     pass

class DefaultAllConstantsRule(FDE.DefaultAllConstantsRule):
    pass

class TabRules(object):
    """
    The Tableaux System for K3WQ contains the `FDE closure rule`_, and the
    `K3 closure rule`_. All of the operator rules are the same as :ref:`K3W`. The
    rules for the quantifiers, however, are different.

    .. _FDE closure rule: fde.html#logics.fde.TabRules.DesignationClosure
    .. _K3 closure rule: k3.html#logics.k3w.TabRules.GlutClosure
    .. _FDE: fde.html
    .. _K3W: k3w.html
    """

    class GlutClosure(K3.TabRules.GlutClosure):
        pass

    class DesignationClosure(FDE.TabRules.DesignationClosure):
        pass

    class DoubleNegationDesignated(FDE.TabRules.DoubleNegationDesignated):
        pass

    class DoubleNegationUndesignated(FDE.TabRules.DoubleNegationUndesignated):
        pass

    class AssertionDesignated(FDE.TabRules.AssertionDesignated):
        pass

    class AssertionNegatedDesignated(FDE.TabRules.AssertionNegatedDesignated):
        pass

    class AssertionUndesignated(FDE.TabRules.AssertionUndesignated):
        pass

    class AssertionNegatedUndesignated(FDE.TabRules.AssertionNegatedUndesignated):
        pass

    class ConjunctionDesignated(FDE.TabRules.ConjunctionDesignated):
        pass

    class ConjunctionNegatedDesignated(K3W.TabRules.ConjunctionNegatedDesignated):
        pass

    class ConjunctionUndesignated(FDE.TabRules.ConjunctionUndesignated):
        pass

    class ConjunctionNegatedUndesignated(K3W.TabRules.ConjunctionNegatedUndesignated):
        pass

    class DisjunctionDesignated(K3W.TabRules.DisjunctionDesignated):
        pass
            
    class DisjunctionNegatedDesignated(FDE.TabRules.DisjunctionNegatedDesignated):
        pass

    class DisjunctionUndesignated(K3W.TabRules.DisjunctionUndesignated):
        pass

    class DisjunctionNegatedUndesignated(K3W.TabRules.DisjunctionNegatedUndesignated):
        pass

    class MaterialConditionalDesignated(K3W.TabRules.MaterialConditionalDesignated):
        pass

    class MaterialConditionalNegatedDesignated(K3W.TabRules.MaterialConditionalNegatedDesignated):
        pass

    class MaterialConditionalUndesignated(K3W.TabRules.MaterialConditionalUndesignated):
        pass

    class MaterialConditionalNegatedUndesignated(K3W.TabRules.MaterialConditionalNegatedUndesignated):
        pass

    class MaterialBiconditionalDesignated(K3W.TabRules.MaterialBiconditionalDesignated):
        pass

    class MaterialBiconditionalNegatedDesignated(K3W.TabRules.MaterialBiconditionalNegatedDesignated):
        pass

    class MaterialBiconditionalUndesignated(K3W.TabRules.MaterialBiconditionalUndesignated):
        pass

    class MaterialBiconditionalNegatedUndesignated(K3W.TabRules.MaterialBiconditionalNegatedUndesignated):
        pass

    class ConditionalDesignated(K3W.TabRules.ConditionalDesignated):
        pass

    class ConditionalNegatedDesignated(K3W.TabRules.ConditionalNegatedDesignated):
        pass

    class ConditionalUndesignated(K3W.TabRules.ConditionalUndesignated):
        pass

    class ConditionalNegatedUndesignated(K3W.TabRules.ConditionalNegatedUndesignated):
        pass

    class BiconditionalDesignated(K3W.TabRules.BiconditionalDesignated):
        pass

    class BiconditionalNegatedDesignated(K3W.TabRules.BiconditionalNegatedDesignated):
        pass

    class BiconditionalUndesignated(K3W.TabRules.BiconditionalUndesignated):
        pass

    class BiconditionalNegatedUndesignated(K3W.TabRules.BiconditionalNegatedUndesignated):
        pass

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
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Quantified = self.sentence(node)
            disji = s.sentence.disjoin(s.sentence.negate())
            sq = Quantifier.Universal(s.variable, disji)
            r = s.unquantify(branch.new_constant())
            d = self.designation
            return {
                'adds': (
                    (
                        {'sentence': sq, 'designated': d},
                        {'sentence': r , 'designated': d},
                    ),
                ),
            }

    class ExistentialNegatedDesignated(FDE.TabRules.ExistentialNegatedDesignated):
        pass

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
        branch_level = 2

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Quantified = self.sentence(node)
            r = s.unquantify(branch.new_constant())
            sq = Quantifier.Universal(s.variable, s.sentence.negate())
            d = self.designation
            return {
                'adds': (
                    (
                        {'sentence': r         , 'designated': d},
                        {'sentence': r.negate(), 'designated': d},
                    ),
                    (
                        {'sentence': sq, 'designated': not d},
                    ),
                ),
            }

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
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Quantified = self.sentence(node)
            r = s.unquantify(branch.new_constant())
            d = self.designation
            return {
                'adds': (({'sentence': r.negate(), 'designated': d},),),
            }

    class UniversalDesignated(FDE.TabRules.UniversalDesignated):
        pass

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
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Quantified = self.sentence(node)
            r = s.unquantify(branch.new_constant())
            disj = s.sentence.disjoin(s.sentence.negate())
            sq = self.quantifier(s.variable, disj)
            d = self.designation
            return {
                'adds': (
                    (
                        {'sentence': sq        , 'designated': d},
                        {'sentence': r.negate(), 'designated': d},
                    ),
                ),
            }

    class UniversalUndesignated(FDE.TabRules.UniversalUndesignated):
        pass

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
        branch_level = 2

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Quantified = self.sentence(node)
            r = s.unquantify(branch.new_constant())
            sq = self.quantifier(s.variable, s.sentence)
            d = self.designation
            return {
                'adds': (
                    (
                        {'sentence': r         , 'designated': d},
                        {'sentence': r.negate(), 'designated': d},
                    ),
                    (
                        {'sentence': sq, 'designated': not d},
                    ),
                ),
            }

    closure_rules = [
        GlutClosure,
        DesignationClosure,
    ]

    rule_groups = [
        [
            # non-branching rules

            AssertionDesignated,
            AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,
            ConjunctionDesignated, 
            DisjunctionNegatedDesignated,

            ExistentialNegatedDesignated,

            DoubleNegationDesignated,
            DoubleNegationUndesignated,
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
        ],
        [
            # two-branching rules
            ConjunctionUndesignated,
        ],
        [
            # three-branching rules
            DisjunctionDesignated,
            DisjunctionUndesignated,
            ConjunctionNegatedDesignated,
            ConjunctionNegatedUndesignated,
            # five-branching rules (formerly)
            DisjunctionNegatedUndesignated,
        ],
        [
            ExistentialDesignated,
            ExistentialNegatedUndesignated,
            ExistentialUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated,
        ],
        [
            UniversalDesignated,
            UniversalUndesignated,
        ],
    ]
TableauxRules = TabRules