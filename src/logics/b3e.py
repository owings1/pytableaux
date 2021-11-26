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
# pytableaux - Bochvar 3 External logic
name = 'B3E'

class Meta(object):
    title    = 'Bochvar 3 External Logic'
    category = 'Many-valued'
    description = 'Three-valued logic (True, False, Neither) with assertion operator'
    tags = ['many-valued', 'gappy', 'non-modal', 'first-order']
    category_display_order = 50

from lexicals import Operator as Oper, Operated
from proof.common import Branch, Node
from . import k3 as K3, k3w as K3W, fde as FDE

def gap(v):
    return min(v, 1 - v)

def crunch(v):
    return v - gap(v)

class Model(K3W.Model):
    """
    A :m:`B3E` model is just like a :ref:`K3W <K3W>` with different tables for some of the connectives.
    """

    def truth_function(self, operator, a, b = None):
        if operator == Oper.Assertion:
            return self.cvals[crunch(self.nvals[a])]
        elif operator == Oper.Conditional:
            return self.truth_function(
                Oper.Disjunction,
                self.truth_function(Oper.Negation, self.truth_function(Oper.Assertion, a)),
                self.truth_function(Oper.Assertion, b)
            )
        elif operator == Oper.Biconditional:
            return FDE.Model.truth_function(self, operator, a, b)
        return super().truth_function(operator, a, b)

class TableauxSystem(FDE.TableauxSystem):
    """
    :m:`B3E`'s Tableaux System inherits directly from the :ref:`FDE system <fde-system>`,
    employing designation markers, and building the trunk in the same way.
    """

    # operator => negated => designated
    branchables = K3W.TableauxSystem.branchables | {
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

class TabRules(object):
    """
    The closure rules for :m:`B3E` are the FDE closure rule, and the K3 closure rule.
    The operator rules are mostly a mix of :ref:`FDE <FDE>` and :ref:`K3W <K3W>` rules, but
    with different rules for the assertion, conditional and biconditional operators.
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

    class AssertionNegatedDesignated(FDE.DefaultNodeRule):
        """
        From an unticked, designated, negated assertion node *n* on a branch *b*,
        add an undesignated node to *b* with the assertion of *n*, then tick *n*.
        """
        negated     = True
        operator    = Oper.Assertion
        designation = True
        branch_level = 1

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.operand, 'designated': False},
                    ],
                ],
            }

    class AssertionUndesignated(AssertionNegatedDesignated):
        """
        From an unticked, undesignated assertion node *n* on a branch *b*, add
        an undesignated node to *b* with the assertion of *n*, then tick *n*.
        """
        designation = False
        negated     = False

    class AssertionNegatedUndesignated(AssertionNegatedDesignated):
        """
        From an unticked, undesignated, negated assertion node *n* on a branch *b*, add
        a designated node to *b* with the assertion of *n*, then tick *n*.
        """
        designation = False
        negated     = True

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Operated = self.sentence(node)
            d = self.designation
            return {
                'adds': (({'sentence': s.operand, 'designated': not d},),),
            }

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

    class ConditionalDesignated(FDE.DefaultNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*,
        add a designated node to *b* with a disjunction, where the
        first disjunction is the negation of the assertion of the antecedent,
        and the second disjunct is the assertion of the consequent. Then tick *n*.
        """
        operator    = Oper.Conditional
        designation = True
        branch_level = 1

        def _get_node_targets(self, node, branch):
            lhs, rhs = self.sentence(node)
            sn = lhs.asserted().negate().disjoin(rhs.asserted())
            # keep negated neutral for inheritance below
            if self.negated:
                sn = sn.negate()
            return {
                'adds': [
                    [
                        # keep designation neutral for inheritance below
                        {'sentence': sn, 'designated': self.designation},
                    ],
                ],
            }

    class ConditionalNegatedDesignated(FDE.DefaultNodeRule):
        """
        From an unticked, designated negated conditional node *n* on a branch *b*,
        add a designated node with the antecedent, and an undesigntated node
        with the consequent to *b*. Then tick *n*.
        """
        negated     = True
        operator    = Oper.Conditional
        designation = True
        branch_level = 1

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.lhs, 'designated': True},
                        {'sentence': s.rhs, 'designated': False},
                    ],
                ],
            }

    class ConditionalUndesignated(ConditionalNegatedDesignated):
        """
        From an unticked, undesignated conditional node *n* on a branch *b*,
        add a designated node with the antecedent, and an undesigntated node
        with the consequent to *b*. Then tick *n*.
        """
        negated     = False
        designation = False

    class ConditionalNegatedUndesignated(ConditionalDesignated):
        """
        From an unticked, undesignated, negated conditional node *n* on a branch *b*,
        add an undesignated node to *b* with a negated material conditional, where the
        operands are preceded by the Assertion operator, then tick *n*.
        """
        negated     = True
        designation = False

    class BiconditionalDesignated(FDE.DefaultNodeRule):
        """
        From an unticked, designated biconditional node *n* on a branch *b*, add two
        designated nodes to *b*, one with a disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """
        designation = True
        operator    = Oper.Biconditional
        branch_level = 2

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Operated = self.sentence(node)
            lhs, rhs = s
            sn1 = lhs.asserted().negate().disjoin(rhs.asserted())
            sn2 = rhs.asserted().negate().disjoin(lhs.asserted())
            # keep negated neutral for inheritance below
            if self.negated:
                sn1 = sn1.negate()
                sn2 = sn2.negate()
            d = self.designation
            return {
                'adds': (
                        # keep designation neutral for inheritance below
                    (
                        {'sentence': sn1, 'designated': d},
                        {'sentence': sn2, 'designated': d},
                    ),
                ),
            }

    class BiconditionalNegatedDesignated(BiconditionalDesignated):
        """
        From an unticked, designated, biconditional node *n* on a branch *b*, add two
        undesignated nodes to *b*, one with a negated disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """
        designation = True
        negated     = True

    class BiconditionalUndesignated(BiconditionalDesignated):
        """
        From an unticked, undesignated biconditional node *n* on a branch *b*, add two
        undesignated nodes to *b*, one with a disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """
        designation = False
        negated     = False

    class BiconditionalNegatedUndesignated(BiconditionalUndesignated):
        """
        From an unticked, designated, biconditional node *n* on a branch *b*, add two
        undesignated nodes to *b*, one with a negated disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """
        designation = False
        negated     = True

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

    closure_rules = (
        GlutClosure,
        DesignationClosure,
    )

    rule_groups = (
        (
            AssertionDesignated,
            AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,
            ConjunctionDesignated, 
            DisjunctionNegatedDesignated,
            ConditionalNegatedDesignated,
            ConditionalUndesignated,
            ExistentialNegatedDesignated,
            ExistentialNegatedUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated,
            DoubleNegationDesignated,
            DoubleNegationUndesignated,
            # reduction rules (thus, non-branching)
            MaterialConditionalDesignated,
            MaterialConditionalUndesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalNegatedUndesignated,
            ConditionalDesignated,
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
            ConjunctionUndesignated,
        ),
        (
            # three-branching rules
            DisjunctionDesignated,
            DisjunctionUndesignated,
            ConjunctionNegatedDesignated,
            ConjunctionNegatedUndesignated,
            # (formerly) four-branching rules
            DisjunctionNegatedUndesignated,
        ),
        (
            ExistentialDesignated,
            ExistentialUndesignated,
        ),
        (
            UniversalDesignated,
            UniversalUndesignated,
        ),
    )
TableauxRules = TabRules