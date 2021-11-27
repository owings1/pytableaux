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

from . import fde as FDE, l3 as L3, k3 as K3
from lexicals import Operator as Oper
class Model(L3.Model):
    """
    A :m:`G3` model is similar to a :ref:`K3 model <k3-model>`, but with different tables
    for some of the operators.
    """

    def truth_function(self, operator, a, b=None):
        if operator == Oper.Negation:
            if a == 'N':
                return 'F'
        return super().truth_function(operator, a, b)

class TableauxSystem(FDE.TableauxSystem):
    """
    :m:`G3`'s Tableaux System inherits directly from the :ref:`FDE system <fde-system>`,
    employing designation markers, and building the trunk in the same way.
    """

    branchables = FDE.TableauxSystem.branchables | {
        Oper.Conditional: {
            False : {True: 1, False: 1},
            True  : {True: 1, False: 1},
        },
        Oper.Biconditional: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
    }

class TabRules(object):
    """
    The closure rules for :m:`G3` are the FDE closure rule, and the :m:`K3` closure rule.
    The operator rules for :m:`G3` are mostly the rules for :ref:`FDE <FDE>`, with the exception
    of the rules for the conditional and biconditional operators, and some of
    the negation rules.
    """

    class GlutClosure(K3.TabRules.GlutClosure):
        pass

    class DesignationClosure(FDE.TabRules.DesignationClosure):
        pass

    class DoubleNegationDesignated(FDE.DefaultNodeRule):
        """
        From an unticked, designated double-negation node `n` on a branch `b`,
        add an undesignated node with the negatum of `n`. Then tick `n`.
        """
        negated     = True
        operator    = Oper.Negation
        designation = True
        branch_level = 1

        def _get_node_targets(self, node, branch):
            return {
                'adds': [
                    [
                        {'sentence': self.sentence(node), 'designated': False},
                    ]
                ]
            }

    class DoubleNegationUndesignated(FDE.DefaultNodeRule):
        """
        From an unticked, undesignated double-negation node `n` on a branch `b`,
        add a designated node with the negatum of `n`. Then tick `n`.
        """
        negated     = True
        operator    = Oper.Negation
        designation = False
        branch_level = 1

        def _get_node_targets(self, node, branch):
            return {
                'adds': [
                    [
                        {'sentence': self.sentence(node), 'designated': True},
                    ]
                ]
            }

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

    class ConjunctionNegatedDesignated(FDE.TabRules.ConjunctionNegatedDesignated):
        pass

    class ConjunctionUndesignated(FDE.TabRules.ConjunctionUndesignated):
        pass

    class ConjunctionNegatedUndesignated(FDE.TabRules.ConjunctionNegatedUndesignated):
        pass

    class DisjunctionDesignated(FDE.TabRules.DisjunctionDesignated):
        pass

    class DisjunctionNegatedDesignated(FDE.TabRules.DisjunctionNegatedDesignated):
        pass

    class DisjunctionUndesignated(FDE.TabRules.DisjunctionUndesignated):
        pass

    class DisjunctionNegatedUndesignated(FDE.TabRules.DisjunctionNegatedUndesignated):
        pass

    class MaterialConditionalDesignated(FDE.TabRules.MaterialConditionalDesignated):
        pass

    class MaterialConditionalNegatedDesignated(FDE.TabRules.MaterialConditionalNegatedDesignated):
        pass

    class MaterialConditionalNegatedUndesignated(FDE.TabRules.MaterialConditionalNegatedUndesignated):
        pass

    class MaterialConditionalUndesignated(FDE.TabRules.MaterialConditionalUndesignated):
        pass

    class MaterialBiconditionalDesignated(FDE.TabRules.MaterialBiconditionalDesignated):
        pass

    class MaterialBiconditionalNegatedDesignated(FDE.TabRules.MaterialBiconditionalNegatedDesignated):
        pass

    class MaterialBiconditionalUndesignated(FDE.TabRules.MaterialBiconditionalUndesignated):
        pass

    class MaterialBiconditionalNegatedUndesignated(FDE.TabRules.MaterialBiconditionalNegatedUndesignated):
        pass

    class ConditionalDesignated(L3.TableauxRules.ConditionalDesignated):
        pass

    class ConditionalNegatedDesignated(FDE.DefaultNodeRule):
        """
        From an unticked, designated, negated conditional node `n` on a branch
        `b`, make two branches `b'` and `b''` from `b`. On `b'` add two designated
        nodes, one with the antecedent, and one with the negation of the consequent.
        On `b''` add two undesignated nodes, one with the antecedent, and one with
        the negation of the antecedent, and one designated node with the negation
        of the consequent. Then tick `n`.
        """
        negated     = True
        operator    = Oper.Conditional
        designation = True
        branch_level = 2

        def _get_node_targets(self, node, branch):
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
    
    class ConditionalUndesignated(L3.TabRules.ConditionalUndesignated):
        pass
    
    class ConditionalNegatedUndesignated(L3.TabRules.ConditionalNegatedUndesignated):
        """
        From an unticked, undesignated, negated conditional node `n` on a branch
        `b`, make two branches `b'` and `b''` from `b`. On `b'` add a designated
        node with the negation of the antecedent. On `b''` add an undesignated
        node with the negation of the consequent. Then tick `n`.
        """
        negated     = True
        operator    = Oper.Conditional
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

    class BiconditionalDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        operator    = Oper.Biconditional
        designation = True
        conjunct_op = Oper.Conditional

    class BiconditionalNegatedDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        negated     = True
        operator    = Oper.Biconditional
        designation = True
        conjunct_op = Oper.Conditional

    class BiconditionalUndesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        negated     = False
        operator    = Oper.Biconditional
        designation = False
        conjunct_op = Oper.Conditional

    class BiconditionalNegatedUndesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        negated     = True
        operator    = Oper.Biconditional
        designation = False
        conjunct_op = Oper.Conditional

    class ExistentialDesignated(FDE.TabRules.ExistentialDesignated):
        pass

    class ExistentialNegatedDesignated(FDE.TabRules.ExistentialNegatedDesignated):
        pass

    class ExistentialUndesignated(FDE.TabRules.ExistentialUndesignated):
        pass

    class ExistentialNegatedUndesignated(FDE.TabRules.ExistentialNegatedUndesignated):
        pass

    class UniversalDesignated(FDE.TabRules.UniversalDesignated):
        pass

    class UniversalNegatedDesignated(FDE.TabRules.UniversalNegatedDesignated):
        pass

    class UniversalUndesignated(FDE.TabRules.UniversalUndesignated):
        pass

    class UniversalNegatedUndesignated(FDE.TabRules.UniversalNegatedUndesignated):
        pass

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
TableauxRules = TabRules