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
from __future__ import annotations

import pytableaux.logics.fde as FDE
import pytableaux.logics.k3 as K3
import pytableaux.logics.l3 as L3
from pytableaux.lang import Operator
from pytableaux.proof import Branch, Node, adds, group, sdnode

name = 'G3'

class Meta(K3.Meta):
    title    = 'Gödel 3-valued logic'
    category = 'Many-valued'
    description = 'Three-valued logic (T, F, N) with alternate negation and conditional'
    category_order = 90
    tags = (
        'many-valued',
        'gappy',
        'non-modal',
        'first-order',
    )
    native_operators = L3.Meta.native_operators

class Model(L3.Model):
    """
    A L{G3} model is similar to a :ref:`K3 model <k3-model>`, but with different tables
    for some of the operators.
    """

    def truth_function(self, operator: Operator, a, b = None, /):
        if operator == Operator.Negation:
            if a == 'N':
                return self.Value.F
        return super().truth_function(operator, a, b)

class TableauxSystem(K3.TableauxSystem):
    """
    L{G3}'s Tableaux System inherits directly from the :ref:`FDE system <fde-system>`,
    employing designation markers, and building the trunk in the same way.
    """

    branchables = FDE.TableauxSystem.branchables | {
        Operator.Conditional: ((1, 1), (1, 1)),
        Operator.Biconditional: ((0, 0), (0, 0)),
    }

@TableauxSystem.initialize
class TabRules(L3.TabRules):
    """
    The closure rules for L{G3} are the L{FDE} closure rule, and the L{K3} closure rule.
    The operator rules for L{G3} are mostly the rules for L{FDE}, with the exception
    of the rules for the conditional and biconditional operators, and some of
    the negation rules.
    """

    class DoubleNegationDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated double-negation node `n` on a branch `b`,
        add an undesignated node with the negatum of `n`. Then tick `n`.
        """
        designation = True
        negated     = True
        operator    = Operator.Negation

        def _get_node_targets(self, node: Node, _,/):
            return adds(
                group(sdnode(self.sentence(node), not self.designation))
            )

    class DoubleNegationUndesignated(DoubleNegationDesignated):
        """
        From an unticked, undesignated double-negation node `n` on a branch `b`,
        add a designated node with the negatum of `n`. Then tick `n`.
        """
        designation = False

    class ConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated conditional node `n` on a branch
        `b`, make two branches `b'` and `b''` from `b`. On `b'` add two designated
        nodes, one with the antecedent, and one with the negation of the consequent.
        On `b''` add two undesignated nodes, one with the antecedent, and one with
        the negation of the antecedent, and one designated node with the negation
        of the consequent. Then tick `n`.
        """
        designation = True
        negated     = True
        operator    = Operator.Conditional
        branching   = 1

        def _get_node_targets(self, node: Node, _: Branch):
            lhs, rhs = self.sentence(node)
            d = self.designation
            return adds(
                group(
                    sdnode( lhs, d),
                    sdnode(~rhs, d),
                ),
                group(
                    sdnode( lhs, not d),
                    sdnode(~lhs, not d),
                    sdnode(~rhs, d),
                ),
            )
    
    class ConditionalNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, negated conditional node `n` on a branch
        `b`, make two branches `b'` and `b''` from `b`. On `b'` add a designated
        node with the negation of the antecedent. On `b''` add an undesignated
        node with the negation of the consequent. Then tick `n`.
        """
        designation = False
        negated     = True
        operator    = Operator.Conditional
        branching   = 1

        def _get_node_targets(self, node: Node, _,/):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(~s.lhs, not d)),
                group(sdnode(~s.rhs, d)),
            )

    class BiconditionalDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        designation = True
        operator    = Operator.Biconditional
        conjunct_op = Operator.Conditional

    class BiconditionalNegatedDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        designation = True
        negated     = True
        operator    = Operator.Biconditional
        conjunct_op = Operator.Conditional

    class BiconditionalUndesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        designation = False
        negated     = False
        operator    = Operator.Biconditional
        conjunct_op = Operator.Conditional

    class BiconditionalNegatedUndesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        designation = False
        negated     = True
        operator    = Operator.Biconditional
        conjunct_op = Operator.Conditional

    rule_groups = (
        (
            # non-branching rules
            FDE.TabRules.AssertionDesignated,
            FDE.TabRules.AssertionUndesignated,
            FDE.TabRules.AssertionNegatedDesignated,
            FDE.TabRules.AssertionNegatedUndesignated,
            FDE.TabRules.ConjunctionDesignated,
            FDE.TabRules.DisjunctionNegatedDesignated,
            FDE.TabRules.DisjunctionUndesignated,
            FDE.TabRules.DisjunctionNegatedUndesignated,
            FDE.TabRules.MaterialConditionalNegatedDesignated,
            FDE.TabRules.MaterialConditionalUndesignated,

            BiconditionalDesignated,
            BiconditionalNegatedUndesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedDesignated,

            FDE.TabRules.ExistentialNegatedDesignated,
            FDE.TabRules.ExistentialNegatedUndesignated,
            FDE.TabRules.UniversalNegatedDesignated,
            FDE.TabRules.UniversalNegatedUndesignated,

            DoubleNegationDesignated,
            DoubleNegationUndesignated,
        ),
        (
            # branching rules
            FDE.TabRules.ConjunctionNegatedDesignated,
            FDE.TabRules.ConjunctionUndesignated,
            FDE.TabRules.ConjunctionNegatedUndesignated,
            FDE.TabRules.DisjunctionDesignated,
            FDE.TabRules.MaterialConditionalDesignated,
            FDE.TabRules.MaterialConditionalNegatedUndesignated,
            FDE.TabRules.MaterialBiconditionalDesignated,
            FDE.TabRules.MaterialBiconditionalNegatedDesignated,
            FDE.TabRules.MaterialBiconditionalUndesignated,
            FDE.TabRules.MaterialBiconditionalNegatedUndesignated,

            L3.TabRules.ConditionalDesignated,
            L3.TabRules.ConditionalUndesignated,
            ConditionalNegatedUndesignated,
            ConditionalNegatedDesignated,
        ),
        (
            FDE.TabRules.ExistentialDesignated,
            FDE.TabRules.ExistentialUndesignated,
        ),
        (
            FDE.TabRules.UniversalDesignated,
            FDE.TabRules.UniversalUndesignated,
        ),
    )
