# -*- coding: utf-8 -*-
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
# pytableaux - Gödel 3-valued logic
name = 'G3'

class Meta(object):

    title    = 'Gödel 3-valued logic'
    category = 'Many-valued'

    description = 'Three-valued logic (T, F, N) with alternate negation and conditional'

    tags = ['many-valued', 'gappy', 'non-modal', 'first-order']

    category_display_order = 90

from . import fde, l3

class Model(l3.Model):
    """
    A G3 model is just like a `K3 model`_ with different tables for some of the connectives.

    .. _K3 model: k3.html#logics.k3.Model
    """

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//g3//
        """
        return super().value_of_operated(sentence, **kw)

    def truth_function(self, operator, a, b=None):
        if operator == 'Negation':
            if a == 'N':
                return 'F'
        return super().truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    G3's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    branchables = dict(fde.TableauxSystem.branchables)
    branchables.update({
        'Conditional': {
            False  : {
                True  : 1,
                False : 1,
            },
            True : {
                True  : 1,
                False : 1,
            },
        },
        'Biconditional': {
            False  : {
                True  : 0,
                False : 0,
            },
            True : {
                True  : 0,
                False : 0,
            },
        },
    })

class DefaultNodeRule(fde.DefaultNodeRule):
    pass

class TableauxRules(object):
    """
    The closure rules for G3 are the `FDE closure rule`_, and the `K3 closure rule`_.
    The operator rules for G3 are mostly the rules for :ref:`FDE <FDE>`, with the exception
    of the rules for the conditional and biconditional operators.

    .. _FDE closure rule: fde.html#logics.fde.TableauxRules.DesignationClosure
    .. _K3 closure rule: k3.html#logics.k3.TableauxRules.GlutClosure
    .. _FDE: fde.html
    """

    class DoubleNegationDesignated(DefaultNodeRule):
        """
        From an unticked, designated double-negation node `n` on a branch `b`,
        add an undesignated node with the negatum of `n`. Then tick `n`.
        """

        negated     = True
        operator    = 'Negation'
        designation = True
    
        branch_level = 1

        def get_target_for_node(self, node, branch):
            return {
                'adds': [
                    [
                        {'sentence': self.sentence(node), 'designated': False},
                    ]
                ]
            }

    class DoubleNegationUndesignated(l3.TableauxRules.DoubleNegationUndesignated):
        """
        From an unticked, undesignated double-negation node `n` on a branch `b`,
        add a designated node with the negatum of `n`. Then tick `n`.
        """

        negated     = True
        operator    = 'Negation'
        designation = False

        branch_level = 1

        def get_target_for_node(self, node, branch):
            return {
                'adds': [
                    [
                        {'sentence': self.sentence(node), 'designated': True},
                    ]
                ]
            }

    class AssertionDesignated(l3.TableauxRules.AssertionDesignated):
        """
        This rule is the same as the `FDE AssertionDesignated rule`_.

        //ruledoc//fde//AssertionDesignated//

        .. _FDE AssertionDesignated rule: fde.html#logics.fde.TableauxRules.AssertionDesignated
        """
        pass

    class AssertionNegatedDesignated(l3.TableauxRules.AssertionNegatedDesignated):
        """
        This rule is the same as the `FDE AssertionNegatedDesignated rule`_.

        //ruledoc//fde//AssertionNegatedDesignated//

        .. _FDE AssertionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedDesignated
        """
        pass

    class AssertionUndesignated(l3.TableauxRules.AssertionUndesignated):
        """
        This rule is the same as the `FDE AssertionUndesignated rule`_.

        //ruledoc//fde//AssertionUndesignated//

        .. _FDE AssertionUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionUndesignated
        """
        pass

    class AssertionNegatedUndesignated(l3.TableauxRules.AssertionNegatedUndesignated):
        """
        This rule is the same as the `FDE AssertionNegatedUndesignated rule`_.

        //ruledoc//fde//AssertionNegatedUndesignated//

        .. _FDE AssertionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedUndesignated
        """
        pass

    class ConjunctionDesignated(l3.TableauxRules.ConjunctionDesignated):
        """
        This rule is the same as the `FDE ConjunctionDesignated rule`_.

        //ruledoc//fde//ConjunctionDesignated//

        .. _FDE ConjunctionDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionDesignated
        """
        pass

    class ConjunctionNegatedDesignated(l3.TableauxRules.ConjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE ConjunctionNegatedDesignated rule`_.

        //ruledoc//fde//ConjunctionNegatedDesignated//

        .. _FDE ConjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionNegatedDesignated
        """
        pass

    class ConjunctionUndesignated(l3.TableauxRules.ConjunctionUndesignated):
        """
        This rule is the same as the `FDE ConjunctionUndesignated rule`_.

        //ruledoc//fde//ConjunctionUndesignated//

        .. _FDE ConjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionUndesignated
        """
        pass

    class ConjunctionNegatedUndesignated(l3.TableauxRules.ConjunctionNegatedUndesignated):
        """
        This rule is the same as the `FDE ConjunctionNegatedUndesignated rule`_.

        //ruledoc//fde//ConjunctionNegatedUndesignated//

        .. _FDE ConjunctionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionNegatedUndesignated
        """
        pass

    class DisjunctionDesignated(l3.TableauxRules.DisjunctionDesignated):
        """
        This rule is the same as the `FDE DisjunctionDesignated rule`_.

        //ruledoc//fde//DisjunctionDesignated//

        .. _FDE DisjunctionDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionDesignated
        """
        pass

    class DisjunctionNegatedDesignated(l3.TableauxRules.DisjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedDesignated rule`_.

        //ruledoc//fde//DisjunctionNegatedDesignated//

        .. _FDE DisjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedDesignated
        """
        pass

    class DisjunctionUndesignated(l3.TableauxRules.DisjunctionUndesignated):
        """
        This rule is the same as the `FDE DisjunctionUndesignated rule`_.

        //ruledoc//fde//DisjunctionUndesignated//

        .. _FDE DisjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionUndesignated
        """
        pass

    class DisjunctionNegatedUndesignated(l3.TableauxRules.DisjunctionNegatedUndesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedUndesignated rule`_.

        //ruledoc//fde//DisjunctionNegatedUndesignated//

        .. _FDE DisjunctionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedUndesignated
        """
        pass

    class MaterialConditionalDesignated(l3.TableauxRules.MaterialConditionalDesignated):
        """
        This rule is the same as the `FDE MaterialConditionalDesignated rule`_.

        //ruledoc//fde//MaterialConditionalDesignated//

        .. _FDE MaterialConditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalDesignated
        """
        pass

    class MaterialConditionalNegatedDesignated(l3.TableauxRules.MaterialConditionalNegatedDesignated):
        """
        This rule is the same as the `FDE MaterialConditionalNegatedDesignated rule`_.

        //ruledoc//fde//MaterialConditionalNegatedDesignated//

        .. _FDE MaterialConditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalNegatedDesignated
        """
        pass

    class MaterialConditionalNegatedUndesignated(l3.TableauxRules.MaterialConditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE MaterialConditionalNegatedUndesignated rule`_.

        //ruledoc//fde//MaterialConditionalNegatedUndesignated//

        .. _FDE MaterialConditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalNegatedUndesignated
        """
        pass

    class MaterialConditionalUndesignated(l3.TableauxRules.MaterialConditionalUndesignated):
        """
        This rule is the same as the `FDE MaterialConditionalUndesignated rule`_.

        //ruledoc//fde//MaterialConditionalUndesignated//

        .. _FDE MaterialConditionalUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalUndesignated
        """
        pass

    class MaterialBiconditionalDesignated(l3.TableauxRules.MaterialBiconditionalDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalDesignated rule`_.

        //ruledoc//fde//MaterialBiconditionalDesignated//

        .. _FDE MaterialBiconditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalDesignated
        """
        pass

    class MaterialBiconditionalNegatedDesignated(l3.TableauxRules.MaterialBiconditionalNegatedDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalNegatedDesignated rule`_.

        //ruledoc//fde//MaterialBiconditionalNegatedDesignated//

        .. _FDE MaterialBiconditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalNegatedDesignated
        """
        pass

    class MaterialBiconditionalUndesignated(l3.TableauxRules.MaterialBiconditionalUndesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalUndesignated rule`_.

        //ruledoc//fde//MaterialBiconditionalUndesignated//

        .. _FDE MaterialBiconditionalUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalUndesignated
        """
        pass

    class MaterialBiconditionalNegatedUndesignated(l3.TableauxRules.MaterialBiconditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalNegatedUndesignated rule`_.

        //ruledoc//fde//MaterialBiconditionalNegatedUndesignated//

        .. _FDE MaterialBiconditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalNegatedUndesignated
        """
        pass

    class ConditionalDesignated(l3.TableauxRules.ConditionalDesignated):
        """
        This rule is the same as the `L3 ConditionalDesignated rule`_.

        //ruledoc//l3//ConditionalDesignated//

        .. _L3 ConditionalDesignated rule: l3.html#logics.l3.TableauxRules.ConditionalDesignated
        """
        pass

    class ConditionalNegatedDesignated(DefaultNodeRule):
        """
        From an unticked, designated, negated conditional node `n` on a branch
        `b`, make two branches `b'` and `b''` from `b`. On `b'` add two designated
        nodes, one with the antecedent, and one with the negation of the consequent.
        On `b''` add two undesignated nodes, one with the antecedent, and one with
        the negation of the antecedent, and one designated node with the negation
        of the consequent. Then tick `n`.
        """

        negated     = True
        operator    = 'Conditional'
        designation = True

        branch_level = 2

        def get_target_for_node(self, node, branch):
            lhs, rhs = self.sentence(node).operands
            return {
                'adds': [
                    [
                        {'sentence': lhs        , 'designated': True},
                        {'sentence': rhs.negate(), 'designated': True},
                    ],
                    [
                        {'sentence': lhs        , 'designated': False},
                        {'sentence': lhs.negate(), 'designated': False},
                        {'sentence': rhs.negate(), 'designated': True},
                    ],
                ],
            }
    
    class ConditionalUndesignated(l3.TableauxRules.ConditionalUndesignated):
        """
        This rule is the same as the `L3 ConditionalUndesignated rule`_.

        //ruledoc//l3//ConditionalUndesignated//

        .. _L3 ConditionalUndesignated rule: l3.html#logics.l3.TableauxRules.ConditionalUndesignated
        """
        pass
    
    class ConditionalNegatedUndesignated(l3.TableauxRules.ConditionalNegatedUndesignated):
        """
        From an unticked, undesignated, negated conditional node `n` on a branch
        `b`, make two branches `b'` and `b''` from `b`. On `b'` add a designated
        node with the negation of the antecedent. On `b''` add an undesignated
        node with the negation of the consequent. Then tick `n`.
        """

        negated     = True
        operator    = 'Conditional'
        designation = False

        branch_level = 2

        def get_target_for_node(self, node, branch):
            lhs, rhs = self.sentence(node).operands
            return {
                'adds': [
                    [
                        {'sentence': lhs.negate(), 'designated': True},
                    ],
                    [
                        {'sentence': rhs.negate(), 'designated': False},
                    ],
                ],
            }

    class BiconditionalDesignated(fde.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
    
        operator    = 'Biconditional'
        designation = True

        conjunct_op = 'Conditional'

    class BiconditionalNegatedDesignated(fde.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
    
        negated     = True
        operator    = 'Biconditional'
        designation = True
    
        conjunct_op = 'Conditional'

    class BiconditionalUndesignated(fde.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
    
        negated     = False
        operator    = 'Biconditional'
        designation = False

        conjunct_op = 'Conditional'

    class BiconditionalNegatedUndesignated(fde.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
    
        negated     = True
        operator    = 'Biconditional'
        designation = False

        conjunct_op = 'Conditional'

    class ExistentialDesignated(l3.TableauxRules.ExistentialDesignated):
        """
        This rule is the same as the `FDE ExistentialDesignated rule`_.

        //ruledoc//fde//ExistentialDesignated//

        .. _FDE ExistentialDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialDesignated
        """
        pass

    class ExistentialNegatedDesignated(l3.TableauxRules.ExistentialNegatedDesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedDesignated rule`_.

        //ruledoc//fde//ExistentialNegatedDesignated//

        .. _FDE ExistentialNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedDesignated
        """
        pass

    class ExistentialUndesignated(l3.TableauxRules.ExistentialUndesignated):
        """
        This rule is the same as the `FDE ExistentialUndesignated rule`_.

        //ruledoc//fde//ExistentialUndesignated//

        .. _FDE ExistentialUndesignated rule: fde.html#logics.fde.TableauxRules.ExistentialUndesignated
        """
        pass

    class ExistentialNegatedUndesignated(l3.TableauxRules.ExistentialNegatedUndesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedUndesignated rule`_.

        //ruledoc//fde//ExistentialNegatedUndesignated//

        .. _FDE ExistentialNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedUndesignated
        """
        pass

    class UniversalDesignated(l3.TableauxRules.UniversalDesignated):
        """
        This rule is the same as the `FDE UniversalDesignated rule`_.

        //ruledoc//fde//UniversalDesignated//

        .. _FDE UniversalDesignated rule: fde.html#logics.fde.TableauxRules.UniversalDesignated
        """
        pass

    class UniversalNegatedDesignated(l3.TableauxRules.UniversalNegatedDesignated):
        """
        This rule is the same as the `FDE UniversalNegatedDesignated rule`_.

        //ruledoc//fde//UniversalNegatedDesignated//

        .. _FDE UniversalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.UniversalNegatedDesignated
        """
        pass

    class UniversalUndesignated(l3.TableauxRules.UniversalUndesignated):
        """
        This rule is the same as the `FDE UniversalUndesignated rule`_.

        //ruledoc//fde//UniversalUndesignated//

        .. _FDE UniversalUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalUndesignated
        """
        pass

    class UniversalNegatedUndesignated(l3.TableauxRules.UniversalNegatedUndesignated):
        """
        This rule is the same as the `FDE UniversalNegatedUndesignated rule`_.

        //ruledoc//fde//UniversalNegatedUndesignated//

        .. _FDE UniversalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalNegatedUndesignated
        """
        pass

    closure_rules = list(l3.TableauxRules.closure_rules)

    rule_groups = [
        [
            # non-branching rules
            AssertionDesignated,
            AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,
            ConjunctionDesignated,
            DisjunctionNegatedDesignated,
            DisjunctionUndesignated,
            DisjunctionNegatedUndesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalUndesignated,

            BiconditionalDesignated,
            BiconditionalNegatedUndesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedDesignated,

            ExistentialNegatedDesignated,
            ExistentialNegatedUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated,

            DoubleNegationDesignated,
            DoubleNegationUndesignated,
        ],
        [
            # branching rules
            ConjunctionNegatedDesignated,
            ConjunctionUndesignated,
            ConjunctionNegatedUndesignated,
            DisjunctionDesignated,
            MaterialConditionalDesignated,
            MaterialConditionalNegatedUndesignated,
            MaterialBiconditionalDesignated,
            MaterialBiconditionalNegatedDesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedUndesignated,

            ConditionalDesignated,
            ConditionalUndesignated,
            ConditionalNegatedUndesignated,
            ConditionalNegatedDesignated,


        ],
        [
            ExistentialDesignated,
            ExistentialUndesignated,
        ],
        [
            UniversalDesignated,
            UniversalUndesignated,
        ],
    ]