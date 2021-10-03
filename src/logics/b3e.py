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

from lexicals import Operated
from . import k3, k3w, fde

def gap(v):
    return min(v, 1 - v)

def crunch(v):
    return v - gap(v)

class Model(k3w.Model):
    """
    A B3E model is just like a :ref:`K3W <K3W>` with different tables for some of the connectives.
    """

    def truth_function(self, operator, a, b=None):
        if operator == 'Assertion':
            return self.cvals[crunch(self.nvals[a])]
        elif operator == 'Conditional':
            return self.truth_function(
                'Disjunction',
                self.truth_function('Negation', self.truth_function('Assertion', a)),
                self.truth_function('Assertion', b)
            )
        elif operator == 'Biconditional':
            return fde.Model.truth_function(self, operator, a, b)
        return super().truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    B3E's Tableaux System inherits directly from the :ref:`FDE system <fde-system>`,
    employing designation markers, and building the trunk in the same way.
    """

    # operator => negated => designated
    branchables = dict(k3w.TableauxSystem.branchables)
    branchables.update({
        # reduction
        'Conditional': {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        # reduction
        'Biconditional': {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
    })

class DefaultNodeRule(fde.DefaultNodeRule):
    pass

class TableauxRules(object):
    """
    The closure rules for B3E are the FDE closure rule, and the K3 closure rule.
    The operator rules are mostly a mix of :ref:`FDE <FDE>` and :ref:`K3W <K3W>` rules, but
    with different rules for the assertion, conditional and biconditional operators.
    """

    class GlutClosure(k3.TableauxRules.GlutClosure):
        pass

    class DesignationClosure(fde.TableauxRules.DesignationClosure):
        pass

    class DoubleNegationDesignated(fde.TableauxRules.DoubleNegationDesignated):
        pass

    class DoubleNegationUndesignated(fde.TableauxRules.DoubleNegationUndesignated):
        pass

    class AssertionDesignated(fde.TableauxRules.AssertionDesignated):
        pass

    class AssertionNegatedDesignated(DefaultNodeRule):
        """
        From an unticked, designated, negated assertion node *n* on a branch *b*,
        add an undesignated node to *b* with the assertion of *n*, then tick *n*.
        """
        negated     = True
        operator    = 'Assertion'
        designation = True
        branch_level = 1

        def get_target_for_node(self, node, branch):
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
        negated     = False
        designation = False

    class AssertionNegatedUndesignated(AssertionNegatedDesignated):
        """
        From an unticked, undesignated, negated assertion node *n* on a branch *b*, add
        a designated node to *b* with the assertion of *n*, then tick *n*.
        """
        negated     = True
        designation = False

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.operand, 'designated': True},
                    ],
                ],
            }

    class ConjunctionDesignated(fde.TableauxRules.ConjunctionDesignated):
        pass

    class ConjunctionNegatedDesignated(k3w.TableauxRules.ConjunctionNegatedDesignated):
        pass

    class ConjunctionUndesignated(fde.TableauxRules.ConjunctionUndesignated):
        pass

    class ConjunctionNegatedUndesignated(k3w.TableauxRules.ConjunctionNegatedUndesignated):
        pass

    class DisjunctionDesignated(k3w.TableauxRules.DisjunctionDesignated):
        pass

    class DisjunctionNegatedDesignated(fde.TableauxRules.DisjunctionNegatedDesignated):
        pass

    class DisjunctionUndesignated(k3w.TableauxRules.DisjunctionUndesignated):
        pass

    class DisjunctionNegatedUndesignated(k3w.TableauxRules.DisjunctionNegatedUndesignated):
        pass

    class MaterialConditionalDesignated(k3w.TableauxRules.MaterialConditionalDesignated):
        pass

    class MaterialConditionalNegatedDesignated(k3w.TableauxRules.MaterialConditionalNegatedDesignated):
        pass

    class MaterialConditionalUndesignated(k3w.TableauxRules.MaterialConditionalUndesignated):
        pass

    class MaterialConditionalNegatedUndesignated(k3w.TableauxRules.MaterialConditionalNegatedUndesignated):
        pass

    class MaterialBiconditionalDesignated(k3w.TableauxRules.MaterialBiconditionalDesignated):
        pass

    class MaterialBiconditionalNegatedDesignated(k3w.TableauxRules.MaterialBiconditionalNegatedDesignated):
        pass

    class MaterialBiconditionalUndesignated(k3w.TableauxRules.MaterialBiconditionalUndesignated):
        pass

    class MaterialBiconditionalNegatedUndesignated(k3w.TableauxRules.MaterialBiconditionalNegatedUndesignated):
        pass

    class ConditionalDesignated(DefaultNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*,
        add a designated node to *b* with a disjunction, where the
        first disjunction is the negation of the assertion of the antecedent,
        and the second disjunct is the assertion of the consequent. Then tick *n*.
        """
        operator    = 'Conditional'
        designation = True
        branch_level = 1

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            sn = Operated(
                'Disjunction',
                [s.lhs.asserted().negate(), s.rhs.asserted()]
            )
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

    class ConditionalNegatedDesignated(DefaultNodeRule):
        """
        From an unticked, designated negated conditional node *n* on a branch *b*,
        add a designated node with the antecedent, and an undesigntated node
        with the consequent to *b*. Then tick *n*.
        """
        negated     = True
        operator    = 'Conditional'
        designation = True
        branch_level = 1

        def get_target_for_node(self, node, branch):
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

    class BiconditionalDesignated(DefaultNodeRule):
        """
        From an unticked, designated biconditional node *n* on a branch *b*, add two
        designated nodes to *b*, one with a disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """
        operator    = 'Biconditional'
        designation = True
        branch_level = 2

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            sn1 = Operated('Disjunction', [
                s.lhs.asserted().negate(),
                s.rhs.asserted(),
            ])
            sn2 = Operated('Disjunction', [
                s.rhs.asserted().negate(),
                s.lhs.asserted(),
            ])
            # keep negated neutral for inheritance below
            if self.negated:
                sn1 = sn1.negate()
                sn2 = sn2.negate()
            return {
                'adds': [
                    [
                        # keep designation neutral for inheritance below
                        {'sentence': sn1, 'designated': d},
                        {'sentence': sn2, 'designated': d},
                    ],
                ],
            }

    class BiconditionalNegatedDesignated(BiconditionalDesignated):
        """
        From an unticked, designated, biconditional node *n* on a branch *b*, add two
        undesignated nodes to *b*, one with a negated disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """
        negated     = True
        designation = True

    class BiconditionalUndesignated(BiconditionalDesignated):
        """
        From an unticked, undesignated biconditional node *n* on a branch *b*, add two
        undesignated nodes to *b*, one with a disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """
        negated     = False
        designation = False

    class BiconditionalNegatedUndesignated(BiconditionalUndesignated):
        """
        From an unticked, designated, biconditional node *n* on a branch *b*, add two
        undesignated nodes to *b*, one with a negated disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """
        negated     = True
        designation = False

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
            # (formerly) four-branching rules
            DisjunctionNegatedUndesignated,
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