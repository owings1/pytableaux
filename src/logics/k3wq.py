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

    category_display_order = 4

import logic, helpers
from logic import negate, operate, quantify
from . import fde, k3w, k3

class Model(k3w.Model):
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
        If we order the values least to greatest as **N**, **F**, **T**, then we
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
        If we order the values least to greatest as **N**, **T**, **F**, then we
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

class TableauxSystem(fde.TableauxSystem):
    """
    K3WQ's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """

class DefaultNodeRule(fde.DefaultNodeRule):
    pass

class DefaultNewConstantRule(fde.DefaultNewConstantRule):
    pass

class DefaultAllConstantsRule(fde.DefaultAllConstantsRule):
    pass

class TableauxRules(object):
    """
    The Tableaux System for K3WQ contains the `FDE closure rule`_, and the
    `K3 closure rule`_. All of the operator rules are the same as `K3W`_. The
    rules for the quantifiers, however, are different.

    .. _FDE closure rule: fde.html#logics.fde.TableauxRules.DesignationClosure
    .. _K3 closure rule: k3.html#logics.k3w.TableauxRules.GlutClosure
    .. _FDE: fde.html
    .. _K3W: k3w.html
    """

    class DoubleNegationDesignated(k3w.TableauxRules.DoubleNegationDesignated):
        """
        This rule is the same as the `FDE DoubleNegationDesignated rule`_.

        //ruledoc//fde//DoubleNegationDesignated//

        .. _FDE DoubleNegationDesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationDesignated
        """
        pass

    class DoubleNegationUndesignated(k3w.TableauxRules.DoubleNegationUndesignated):
        """
        This rule is the same as the `FDE DoubleNegationUndesignated rule`_.

        //ruledoc//fde//DoubleNegationUndesignated//

        .. _FDE DoubleNegationUndesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationUndesignated
        """
        pass

    class AssertionDesignated(k3w.TableauxRules.AssertionDesignated):
        """
        This rule is the same as the `FDE AssertionDesignated rule`_.

        //ruledoc//fde//AssertionDesignated//

        .. _FDE AssertionDesignated rule: fde.html#logics.fde.TableauxRules.AssertionDesignated
        """
        pass

    class AssertionNegatedDesignated(k3w.TableauxRules.AssertionNegatedDesignated):
        """
        This rule is the same as the `FDE AssertionNegatedDesignated rule`_.

        //ruledoc//fde//AssertionNegatedDesignated//

        .. _FDE AssertionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedDesignated
        """
        pass

    class AssertionUndesignated(k3w.TableauxRules.AssertionUndesignated):
        """
        This rule is the same as the `FDE AssertionUndesignated rule`_.

        //ruledoc//fde//AssertionUndesignated//

        .. _FDE AssertionUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionUndesignated
        """
        pass

    class AssertionNegatedUndesignated(k3w.TableauxRules.AssertionNegatedUndesignated):
        """
        This rule is the same as the `FDE AssertionNegatedUndesignated rule`_.

        //ruledoc//fde//AssertionNegatedUndesignated//

        .. _FDE AssertionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedUndesignated
        """
        pass

    class ConjunctionDesignated(k3w.TableauxRules.ConjunctionDesignated):
        """
        This rule is the same as the `FDE ConjunctionDesignated rule`_.

        //ruledoc//fde//ConjunctionDesignated//

        .. _FDE ConjunctionDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionDesignated
        """
        pass

    class ConjunctionNegatedDesignated(k3w.TableauxRules.ConjunctionNegatedDesignated):
        """
        This rule is the same as the `K3W ConjunctionNegatedDesignated rule`_.

        //ruledoc//k3w//ConjunctionNegatedDesignated//

        .. _K3W ConjunctionNegatedDesignated rule: k3w.html#logics.k3w.TableauxRules.ConjunctionNegatedDesignated
        """
        pass

    class ConjunctionUndesignated(k3w.TableauxRules.ConjunctionUndesignated):
        """
        This rule is the same as the `FDE ConjunctionUndesignated rule`_.

        //ruledoc//fde//ConjunctionUndesignated//

        .. _FDE ConjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionUndesignated
        """
        pass

    class ConjunctionNegatedUndesignated(k3w.TableauxRules.ConjunctionNegatedUndesignated):
        """
        This rule is the same as the `K3W ConjunctionNegatedUndesignated rule`_.

        //ruledoc//k3w//ConjunctionNegatedUndesignated//

        .. _K3W ConjunctionNegatedUndesignated rule: k3w.html#logics.k3w.TableauxRules.ConjunctionNegatedUndesignated
        """
        pass

    class DisjunctionDesignated(k3w.TableauxRules.DisjunctionDesignated):
        """
        This rule is the same as the `K3W DisjunctionDesignated rule`_.

        //ruledoc//k3w//DisjunctionDesignated//

        .. _K3W DisjunctionDesignated rule: k3w.html#logics.k3w.TableauxRules.DisjunctionDesignated
        """
        pass
            
    class DisjunctionNegatedDesignated(k3w.TableauxRules.DisjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedDesignated rule`_.

        //ruledoc//fde//DisjunctionNegatedDesignated//

        .. _FDE DisjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedDesignated
        """
        pass

    class DisjunctionUndesignated(k3w.TableauxRules.DisjunctionUndesignated):
        """
        This rule is the same as the `K3W DisjunctionUndesignated rule`_.

        //ruledoc//k3w//DisjunctionUndesignated//

        .. _K3W DisjunctionUndesignated rule: k3w.html#logics.k3w.TableauxRules.DisjunctionUndesignated
        """
        pass

    class DisjunctionNegatedUndesignated(k3w.TableauxRules.DisjunctionNegatedUndesignated):
        """
        This rule is the same as the `K3W DisjunctionNegatedUndesignated rule`_.

        //ruledoc//k3w//DisjunctionNegatedUndesignated//

        .. _K3W DisjunctionNegatedUndesignated rule: k3w.html#logics.k3w.TableauxRules.DisjunctionNegatedUndesignated
        """
        pass

    class MaterialConditionalDesignated(k3w.TableauxRules.MaterialConditionalDesignated):
        """
        This rule is the same as the `K3W MaterialConditionalDesignated rule`_.

        //ruledoc//k3w//MaterialConditionalDesignated//

        .. _K3W MaterialConditionalDesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialConditionalDesignated
        """
        pass

    class MaterialConditionalNegatedDesignated(k3w.TableauxRules.MaterialConditionalNegatedDesignated):
        """
        This rule is the same as the `K3W MaterialConditionalNegatedDesignated rule`_.

        //ruledoc//k3w//MaterialConditionalNegatedDesignated//

        .. _K3W MaterialConditionalNegatedDesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialConditionalNegatedDesignated
        """
        pass

    class MaterialConditionalUndesignated(k3w.TableauxRules.MaterialConditionalUndesignated):
        """
        This rule is the same as the `K3W MaterialConditionalUndesignated rule`_.

        //ruledoc//k3w//MaterialConditionalUndesignated//

        .. _K3W MaterialConditionalUndesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialConditionalUndesignated
        """
        pass

    class MaterialConditionalNegatedUndesignated(k3w.TableauxRules.MaterialConditionalNegatedUndesignated):
        """
        This rule is the same as the `K3W MaterialConditionalNegatedUndesignated rule`_.

        //ruledoc//k3w//MaterialConditionalNegatedUndesignated//

        .. _K3W MaterialConditionalNegatedUndesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialConditionalNegatedUndesignated
        """
        pass

    class MaterialBiconditionalDesignated(k3w.TableauxRules.MaterialBiconditionalDesignated):
        """
        This rule is the same as the `K3W MaterialBiconditionalDesignated rule`_.

        //ruledoc//k3w//MaterialBiconditionalDesignated//

        .. _K3W MaterialBiconditionalDesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialBiconditionalDesignated
        """
        pass

    class MaterialBiconditionalNegatedDesignated(k3w.TableauxRules.MaterialBiconditionalNegatedDesignated):
        """
        This rule is the same as the `K3W MaterialBiconditionalNegatedDesignated rule`_.

        //ruledoc//k3w//MaterialBiconditionalNegatedDesignated//

        .. _K3W MaterialBiconditionalNegatedDesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialBiconditionalNegatedDesignated
        """
        pass

    class MaterialBiconditionalUndesignated(k3w.TableauxRules.MaterialBiconditionalUndesignated):
        """
        This rule is the same as the `K3W MaterialBiconditionalUndesignated rule`_.

        //ruledoc//k3w//MaterialBiconditionalUndesignated//

        .. _K3W MaterialBiconditionalUndesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialBiconditionalUndesignated
        """
        pass

    class MaterialBiconditionalNegatedUndesignated(k3w.TableauxRules.MaterialBiconditionalNegatedUndesignated):
        """
        This rule is the same as the `K3W MaterialBiconditionalNegatedUndesignated rule`_.

        //ruledoc//k3w//MaterialBiconditionalNegatedUndesignated//

        .. _K3W MaterialBiconditionalNegatedUndesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialBiconditionalNegatedUndesignated
        """
        pass

    class ConditionalDesignated(k3w.TableauxRules.ConditionalDesignated):
        """
        This rule is the same as the `K3W ConditionalDesignated rule`_.

        //ruledoc//k3w//ConditionalDesignated//

        .. _K3W ConditionalDesignated rule: k3w.html#logics.k3w.TableauxRules.ConditionalDesignated
        """
        pass

    class ConditionalNegatedDesignated(k3w.TableauxRules.ConditionalNegatedDesignated):
        """
        This rule is the same as the `K3W ConditionalNegatedDesignated rule`_.

        //ruledoc//k3w//ConditionalNegatedDesignated//

        .. _K3W ConditionalNegatedDesignated rule: k3w.html#logics.k3w.TableauxRules.ConditionalNegatedDesignated
        """
        pass

    class ConditionalUndesignated(k3w.TableauxRules.ConditionalUndesignated):
        """
        This rule is the same as the `K3W ConditionalUndesignated rule`_.

        //ruledoc//k3w//ConditionalUndesignated//

        .. _K3W ConditionalUndesignated rule: k3w.html#logics.k3w.TableauxRules.ConditionalUndesignated
        """
        pass

    class ConditionalNegatedUndesignated(k3w.TableauxRules.ConditionalNegatedUndesignated):
        """
        This rule is the same as the `K3W ConditionalNegatedUndesignated rule`_.

        //ruledoc//k3w//ConditionalNegatedUndesignated//

        .. _K3W ConditionalNegatedUndesignated rule: k3w.html#logics.k3w.TableauxRules.ConditionalNegatedUndesignated
        """
        pass

    class BiconditionalDesignated(k3w.TableauxRules.BiconditionalDesignated):
        """
        This rule is the same as the `K3W BiconditionalDesignated rule`_.

        //ruledoc//k3w//BiconditionalDesignated//

        .. _K3W BiconditionalDesignated rule: k3w.html#logics.k3w.TableauxRules.BiconditionalDesignated
        """
        pass

    class BiconditionalNegatedDesignated(k3w.TableauxRules.BiconditionalNegatedDesignated):
        """
        This rule is the same as the `K3W BiconditionalNegatedDesignated rule`_.

        //ruledoc//k3w//BiconditionalNegatedDesignated//

        .. _K3W BiconditionalNegatedDesignated rule: k3w.html#logics.k3w.TableauxRules.BiconditionalNegatedDesignated
        """
        pass

    class BiconditionalUndesignated(k3w.TableauxRules.BiconditionalUndesignated):
        """
        This rule is the same as the `K3W BiconditionalUndesignated rule`_.

        //ruledoc//k3w//BiconditionalUndesignated//

        .. _K3W BiconditionalUndesignated rule: k3w.html#logics.k3w.TableauxRules.BiconditionalUndesignated
        """
        pass

    class BiconditionalNegatedUndesignated(k3w.TableauxRules.BiconditionalNegatedUndesignated):
        """
        This rule is the same as the `K3W BiconditionalNegatedUndesignated rule`_.

        //ruledoc//k3w//BiconditionalNegatedUndesignated//

        .. _K3W BiconditionalNegatedUndesignated rule: k3w.html#logics.k3w.TableauxRules.BiconditionalNegatedUndesignated
        """
        pass

    class ExistentialDesignated(DefaultNewConstantRule):
        """
        From an unticked, designated existential node `n` on a branch `b`, add
        two designated nodes to `b`. One node is the result of universally
        quantifying over the disjunction of the inner sentence with its negation.
        The other node is a substitution of a constant new to `b`. Then tick `n`.
        """

        negated     = False
        quantifier  = 'Existential'
        designation = True

        branch_level = 1

        # NewConstantStoppingRule implementation

        def get_new_nodes_for_constant(self, c, node, branch):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = si.substitute(c, v)

            disji = operate('Disjunction', [si, negate(si)])
            sq = quantify('Universal', v, disji)

            return [
                {'sentence': sq, 'designated': True},
                {'sentence': r , 'designated': True},
            ]

    class ExistentialNegatedDesignated(k3w.TableauxRules.ExistentialNegatedDesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedDesignated rule`_.

        //ruledoc//fde//ExistentialNegatedDesignated//

        .. _FDE ExistentialNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedDesignated
        """

    class ExistentialUndesignated(DefaultNewConstantRule):
        """
        From an unticked, undesignated existential node `n` on a branch `b`, make
        two branches `b'` and `b''` from `b`. On `b'` add two undesignated nodes,
        one with the substituion of a constant new to `b` for the inner sentence,
        and the other with the negation of that sentence. On `b''` add a designated
        node with universal quantifier over the negation of the inner sentence.
        Then tick `n`.
        """

        negated     = False
        quantifier  = 'Existential'
        designation = False

        branch_level = 2

        # NewConstantStoppingRule implementation

        def get_new_nodes_for_constant(self, c, node, branch):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = si.substitute(c, v)
            return [
                {'sentence':        r , 'designated': False},
                {'sentence': negate(r), 'designated': False},
            ]

        def add_to_adds(self, node, branch):
            return [
                [
                    self._get_translation_node(node, branch)
                ]
            ]

        # private util

        def _get_translation_node(self, node, branch):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            sq = quantify('Universal', v, negate(si))
            return {'sentence': sq, 'designated': True}

    class ExistentialNegatedUndesignated(DefaultNewConstantRule):
        """"
        From an unticked, undesignated, negated existential node `n` on a branch
        `b`, add an undesignated node to `b` with the negation of the inner
        sentence, substituting a constant new to `b` for the variable. Then
        tick `n`.
        """

        negated     = True
        quantifier  = 'Existential'
        designation = False

        branch_level = 1

        # NewConstantStoppingRule implementation

        def get_new_nodes_for_constant(self, c, node, branch):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = si.substitute(c, v)
            return [
                {'sentence': negate(r), 'designated': False},
            ]

    class UniversalDesignated(k3w.TableauxRules.UniversalDesignated):
        """
        This rule is the same as the `FDE UniversalDesignated rule`_.

        //ruledoc//fde//UniversalDesignated//

        .. _FDE UniversalDesignated rule: fde.html#logics.fde.TableauxRules.UniversalDesignated
        """
        pass

    class UniversalNegatedDesignated(DefaultNewConstantRule):
        """
        From an unticked, designated, negated universal node `n` on a branch `b`,
        add two designated nodes to `b`. The first node is a universally quantified
        disjunction of the inner sentence and its negation. The second node is the
        negation of the inner sentence, substituting a constant new to `b` for the
        variable. Then tick `n`.
        """

        negated     = True
        quantifier  = 'Universal'
        designation = True

        branch_level = 1

        # NewConstantStoppingRule implementation

        def get_new_nodes_for_constant(self, c, node, branch):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = si.substitute(c, v)

            disji = operate('Disjunction', [si, negate(si)])
            sq = quantify('Universal', v, disji)

            return [
                {'sentence':       sq , 'designated': True},
                {'sentence': negate(r), 'designated': True},
            ]

    class UniversalUndesignated(k3w.TableauxRules.UniversalUndesignated):
        """
        This rule is the same as the `FDE UniversalUndesignated rule`_.

        //ruledoc//fde//UniversalUndesignated//

        .. _FDE UniversalUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalUndesignated
        """
        pass

    class UniversalNegatedUndesignated(ExistentialUndesignated):
        """
        From an unticked, undesignated, negated universal node `n` on a branch `b`,
        make two branches `b'` and `b''` from `b`. On `b'` add two undesignated nodes,
        one with the substitution of a constant new to `b` for the inner sentence
        of `n`, and the other with the negation of that sentence. On `b''`, add
        a designated node with the negatum of `n`. Then tick `n`.
        """

        negated     = True
        quantifier  = 'Universal'
        designation = False

        branch_level = 2

        # NewConstantStoppingRule implementation

        def get_new_nodes_for_constant(self, c, node, branch):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = si.substitute(c, v)
            return [
                {'sentence':        r , 'designated': False},
                {'sentence': negate(r), 'designated': False},
            ]

        def add_to_adds(self, node, branch):
            return [
                [
                    self._get_translation_node(node, branch)
                ]
            ]

        # private util

        def _get_translation_node(self, node, branch):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            sq = quantify('Universal', v, si)
            return {'sentence': sq, 'designated': True}

    closure_rules = list(k3.TableauxRules.closure_rules)

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