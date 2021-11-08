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

class Meta(object):
    title = 'R-mingle 3'
    category = 'Many-valued'
    description = 'Three-valued logic (True, False, Both) with a primitive Conditional operator'
    tags = ['many-valued', 'glutty', 'non-modal', 'first-order']
    category_display_order = 130

from lexicals import Operator as Oper
from . import fde, lp

class Model(lp.Model):
    """
    An RM3 model is just like an `LP model`_ with different tables for the conditional
    and bi-conditional operators.

    .. _LP model: lp.html#logics.lp.Model
    """

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//rm3//
        """
        return super().value_of_operated(sentence, **kw)

    def truth_function(self, operator, a, b=None):
        if operator == Oper.Conditional and self.nvals[a] > self.nvals[b]:
            return 'F'
        return super().truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    RM3's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    branchables = fde.TableauxSystem.branchables | {
        Oper.Conditional: {
            False  : {
                True  : 2,
                False : 1,
            },
            True : {
                True  : 0,
                False : 1,
            },
        },
        Oper.Biconditional: {
            False  : {
                True  : 2,
                False : 1,
            },
            True : {
                True  : 1,
                False : 1,
            },
        },
    }

class DefaultNodeRule(fde.DefaultNodeRule):
    pass

class TableauxRules(object):
    """
    The closure rules for RM3 are the `FDE closure rule`_, and the `LP closure rule`_.
    Most of the operator rules are the same as :ref:`FDE <FDE>`, except for the conditional
    rules. The biconditional rules are borrowed from `L3_`, since they are
    simplification rules.

    .. _FDE closure rule: fde.html#logics.fde.TableauxRules.DesignationClosure
    .. _LP closure rule: lp.html#logics.lp.TableauxRules.GapClosure
    """

    class GapClosure(lp.TableauxRules.GapClosure):
        pass

    class DesignationClosure(fde.TableauxRules.DesignationClosure):
        pass

    class DoubleNegationDesignated(fde.TableauxRules.DoubleNegationDesignated):
        pass

    class DoubleNegationUndesignated(fde.TableauxRules.DoubleNegationUndesignated):
        pass

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

    class ConditionalDesignated(DefaultNodeRule):
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

        def _get_node_targets(self, node, branch):
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

    class ConditionalNegatedDesignated(fde.TableauxRules.ConditionalNegatedDesignated):
        pass

    class ConditionalUndesignated(DefaultNodeRule):
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

        def _get_node_targets(self, node, branch):
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

    class ConditionalNegatedUndesignated(fde.TableauxRules.ConditionalNegatedUndesignated):
        pass

    class BiconditionalDesignated(DefaultNodeRule):
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

        def _get_node_targets(self, node, branch):
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

    class BiconditionalNegatedDesignated(fde.TableauxRules.BiconditionalNegatedDesignated):
        pass

    class BiconditionalUndesignated(DefaultNodeRule):
        """
        From an unticked undesignated biconditional node *n* on a branch *b*, add a
        conjunction undesignated node to *b*, with first conjunct being a conditional
        with the same operands as *n*, and the second conjunct being a conditional
        with the reversed operands of *n*, then tick *n*.
        """
        operator    = Oper.Biconditional
        designation = False
        branch_level = 2

        def _get_node_targets(self, node, branch):
            lhs, rhs = self.sentence(node)
            cond1 = Oper.Conditional.on((lhs, rhs))
            cond2 = Oper.Conditional.on((rhs, lhs))
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

    class BiconditionalNegatedUndesignated(DefaultNodeRule):
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

        def _get_node_targets(self, node, branch):
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