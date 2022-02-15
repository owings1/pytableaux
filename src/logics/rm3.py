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
# pytableaux - R-mingle 3 logic
name = 'RM3'

class Meta:
    title = 'R-mingle 3'
    category = 'Many-valued'
    description = 'Three-valued logic (True, False, Both) with a primitive Conditional operator'
    tags = ['many-valued', 'glutty', 'non-modal', 'first-order']
    category_display_order = 130

from lexicals import Operator as Oper
from proof.common import Branch, Node
from . import fde as FDE, lp as LP

class Model(LP.Model):
    """
    An RM3 model is just like an `LP model`_ with different tables for the conditional
    and bi-conditional operators.

    .. _LP model: lp.html#logics.lp.Model
    """
    def truth_function(self, operator: Oper, a, b=None):
        Value = self.Value
        if operator == Oper.Conditional and Value[a] > Value[b]:
            return Value.F
        return super().truth_function(operator, a, b)

class TableauxSystem(FDE.TableauxSystem):
    """
    RM3's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    branchables = FDE.TableauxSystem.branchables | {
        Oper.Conditional: {
            False : {True: 2, False: 1},
            True  : {True: 0, False: 1},
        },
        Oper.Biconditional: {
            False : {True: 2, False: 1},
            True  : {True: 1, False: 1},
        },
    }

class TabRules:
    """
    The closure rules for RM3 are the FDE closure rule, and the LP closure rule.
    Most of the operator rules are the same as :ref:`FDE <FDE>`, except for the conditional
    rules. The biconditional rules are borrowed from `L3_`, since they are
    simplification rules.
    """

    class GapClosure(LP.TabRules.GapClosure):
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

    class ConditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*, make
        three branches *b'*, *b''*, and *b'''* from *b*. On *b'* add an undesignated
        node with the antecedent. On *b''* add an undesignated node with the
        negation of the consequent. On *b'''* add four designated nodes, with
        the antecedent, its negation, the consequent, and its negation,
        respectively. Then tick *n*.
        """
        operator    = Oper.Conditional
        designation = True
        branch_level = 3

        def _get_node_targets(self, node: Node, branch: Branch):
            lhs, rhs = self.sentence(node).operands
            return {
                'adds': [
                    [
                        {'sentence':        lhs , 'designated': False},
                    ],
                    [
                        {'sentence': rhs.negate(), 'designated': False},
                    ],
                    [
                        {'sentence':        lhs , 'designated': True},
                        {'sentence': lhs.negate(), 'designated': True},
                        {'sentence':        rhs , 'designated': True},
                        {'sentence': rhs.negate(), 'designated': True},
                    ],
                ],
            }

    class ConditionalNegatedDesignated(FDE.TabRules.ConditionalNegatedDesignated):
        pass

    class ConditionalUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'*, add a designated node
        with the antecedent, and an undesignated node with with consequent.
        On *b''*, add an undesignated node with the negation of the antecedent,
        and a designated node with the negation of the consequent. Then tick *n*.
        """
        operator    = Oper.Conditional
        designation = False
        branch_level = 2

        def _get_node_targets(self, node: Node, branch: Branch):
            lhs, rhs = self.sentence(node).operands
            return {
                'adds': [
                    [
                        {'sentence': lhs, 'designated': True},
                        {'sentence': rhs, 'designated': False},
                    ],
                    [
                        {'sentence': lhs.negate(), 'designated': False},
                        {'sentence': rhs.negate(), 'designated': True},
                    ],
                ],
            }

    class ConditionalNegatedUndesignated(FDE.TabRules.ConditionalNegatedUndesignated):
        pass

    class BiconditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked designated biconditional node *n* on a branch *b*, make
        three branches *b'*, *b''*, and *b'''* from *b*. On *b'* add undesignated
        nodes for each of the two operands. On *b''*, add undesignated nodes fo
        the negation of each operand. On *b'''*, add four designated nodes, one
        with each operand, and one for the negation of each operand. Then tick *n*.
        """
        operator    = Oper.Biconditional
        designation = True
        branch_level = 3

        def _get_node_targets(self, node: Node, branch: Branch):
            lhs, rhs = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': lhs, 'designated': False},
                        {'sentence': rhs, 'designated': False},
                    ],
                    [
                        {'sentence': lhs.negate(), 'designated': False},
                        {'sentence': rhs.negate(), 'designated': False},
                    ],
                    [
                        {'sentence':        lhs , 'designated': True},
                        {'sentence': lhs.negate(), 'designated': True},
                        {'sentence':        rhs , 'designated': True},
                        {'sentence': rhs.negate(), 'designated': True},
                    ],
                ],
            }

    class BiconditionalNegatedDesignated(FDE.TabRules.BiconditionalNegatedDesignated):
        pass

    class BiconditionalUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked undesignated biconditional node *n* on a branch *b*, add a
        conjunction undesignated node to *b*, with first conjunct being a conditional
        with the same operands as *n*, and the second conjunct being a conditional
        with the reversed operands of *n*, then tick *n*.
        """
        operator    = Oper.Biconditional
        designation = False
        branch_level = 2

        def _get_node_targets(self, node: Node, branch: Branch):
            lhs, rhs = self.sentence(node)
            cond1 = Oper.Conditional((lhs, rhs))
            cond2 = Oper.Conditional((rhs, lhs))
            return {
                'adds': [
                    [
                        {'sentence': cond1, 'designated': False},
                    ],
                    [
                        {'sentence': cond2, 'designated': False},
                    ],
                ],
            }

    class BiconditionalNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked undesignated negated biconditional node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'* add an undesignated node
        for each operand. On *b''* add an undesignated nodes for the negation of
        each operand. Then tick *n*.
        """
        negated     = True
        operator    = Oper.Biconditional
        designation = False
        branch_level = 2

        def _get_node_targets(self, node: Node, branch: Branch):
            lhs, rhs = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': lhs, 'designated': False},
                        {'sentence': rhs, 'designated': False},
                    ],
                    [
                        {'sentence': lhs.negate(), 'designated': False},
                        {'sentence': rhs.negate(), 'designated': False},
                    ],
                ],
            }

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
        GapClosure,
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
            ConditionalNegatedDesignated,
            ConditionalUndesignated,
            ExistentialNegatedDesignated,
            ExistentialNegatedUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated,
            DoubleNegationDesignated,
            DoubleNegationUndesignated,
        ],
        [
            # 2 branching rules
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
            ConditionalNegatedUndesignated,
            BiconditionalNegatedDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated,
        ],
        [
            # 3 branching rules
            ConditionalDesignated,
            BiconditionalDesignated,
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
