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

from . import fde, l3, k3
from lexicals import Operator as Oper
class Model(l3.Model):
    """
    A :m:`G3` model is similar to a :ref:`K3 model <k3-model>`, but with different tables
    for some of the operators.
    """

    def truth_function(self, operator, a, b=None):
        if operator == Oper.Negation:
            if a == 'N':
                return 'F'
        return super().truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    :m:`G3`'s Tableaux System inherits directly from the :ref:`FDE system <fde-system>`,
    employing designation markers, and building the trunk in the same way.
    """

    branchables = dict(fde.TableauxSystem.branchables)
    branchables.update({
        'Conditional': {
            False : {True: 1, False: 1},
            True  : {True: 1, False: 1},
        },
        'Biconditional': {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
    })

class DefaultNodeRule(fde.DefaultNodeRule):
    pass

class TableauxRules(object):
    """
    The closure rules for :m:`G3` are the FDE closure rule, and the :m:`K3` closure rule.
    The operator rules for :m:`G3` are mostly the rules for :ref:`FDE <FDE>`, with the exception
    of the rules for the conditional and biconditional operators, and some of
    the negation rules.
    """

    class GlutClosure(k3.TableauxRules.GlutClosure):
        pass

    class DesignationClosure(fde.TableauxRules.DesignationClosure):
        pass

    class DoubleNegationDesignated(DefaultNodeRule):
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

    class DoubleNegationUndesignated(DefaultNodeRule):
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

    class AssertionDesignated(fde.TableauxRules.AssertionDesignated):
        pass

    class AssertionNegatedDesignated(fde.TableauxRules.AssertionNegatedDesignated):
        pass

    class AssertionUndesignated(fde.TableauxRules.AssertionUndesignated):
        pass

    class AssertionNegatedUndesignated(fde.TableauxRules.AssertionNegatedUndesignated):
        pass

    class ConjunctionDesignated(fde.TableauxRules.ConjunctionDesignated):
        pass

    class ConjunctionNegatedDesignated(fde.TableauxRules.ConjunctionNegatedDesignated):
        pass

    class ConjunctionUndesignated(fde.TableauxRules.ConjunctionUndesignated):
        pass

    class ConjunctionNegatedUndesignated(fde.TableauxRules.ConjunctionNegatedUndesignated):
        pass

    class DisjunctionDesignated(fde.TableauxRules.DisjunctionDesignated):
        pass

    class DisjunctionNegatedDesignated(fde.TableauxRules.DisjunctionNegatedDesignated):
        pass

    class DisjunctionUndesignated(fde.TableauxRules.DisjunctionUndesignated):
        pass

    class DisjunctionNegatedUndesignated(fde.TableauxRules.DisjunctionNegatedUndesignated):
        pass

    class MaterialConditionalDesignated(fde.TableauxRules.MaterialConditionalDesignated):
        pass

    class MaterialConditionalNegatedDesignated(fde.TableauxRules.MaterialConditionalNegatedDesignated):
        pass

    class MaterialConditionalNegatedUndesignated(fde.TableauxRules.MaterialConditionalNegatedUndesignated):
        pass

    class MaterialConditionalUndesignated(fde.TableauxRules.MaterialConditionalUndesignated):
        pass

    class MaterialBiconditionalDesignated(fde.TableauxRules.MaterialBiconditionalDesignated):
        pass

    class MaterialBiconditionalNegatedDesignated(fde.TableauxRules.MaterialBiconditionalNegatedDesignated):
        pass

    class MaterialBiconditionalUndesignated(fde.TableauxRules.MaterialBiconditionalUndesignated):
        pass

    class MaterialBiconditionalNegatedUndesignated(fde.TableauxRules.MaterialBiconditionalNegatedUndesignated):
        pass

    class ConditionalDesignated(l3.TableauxRules.ConditionalDesignated):
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
    
    class ConditionalUndesignated(l3.TableauxRules.ConditionalUndesignated):
        pass
    
    class ConditionalNegatedUndesignated(l3.TableauxRules.ConditionalNegatedUndesignated):
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

    class BiconditionalDesignated(fde.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        operator    = Oper.Biconditional
        designation = True
        conjunct_op = Oper.Conditional

    class BiconditionalNegatedDesignated(fde.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        negated     = True
        operator    = Oper.Biconditional
        designation = True
        conjunct_op = Oper.Conditional

    class BiconditionalUndesignated(fde.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        negated     = False
        operator    = Oper.Biconditional
        designation = False
        conjunct_op = Oper.Conditional

    class BiconditionalNegatedUndesignated(fde.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        negated     = True
        operator    = Oper.Biconditional
        designation = False
        conjunct_op = Oper.Conditional

    class ExistentialDesignated(fde.TableauxRules.ExistentialDesignated):
        pass

    class ExistentialNegatedDesignated(fde.TableauxRules.ExistentialNegatedDesignated):
        pass

    class ExistentialUndesignated(fde.TableauxRules.ExistentialUndesignated):
        pass

    class ExistentialNegatedUndesignated(fde.TableauxRules.ExistentialNegatedUndesignated):
        pass

    class UniversalDesignated(fde.TableauxRules.UniversalDesignated):
        pass

    class UniversalNegatedDesignated(fde.TableauxRules.UniversalNegatedDesignated):
        pass

    class UniversalUndesignated(fde.TableauxRules.UniversalUndesignated):
        pass

    class UniversalNegatedUndesignated(fde.TableauxRules.UniversalNegatedUndesignated):
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