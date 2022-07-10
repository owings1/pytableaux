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
#
# ------------------
#
# pytableaux - R-mingle 3 logic
from __future__ import annotations

import pytableaux.logics.fde as FDE
import pytableaux.logics.lp as LP
from pytableaux.lang import Operator
from pytableaux.proof import adds, group, sdnode, Node

name = 'RM3'

class Meta(LP.Meta):
    title       = 'R-mingle 3'
    description = (
        'Three-valued logic (True, False, Both) with a primitive '
        'Conditional operator'
    )
    category_order = 130
    tags = (
        'many-valued',
        'glutty',
        'non-modal',
        'first-order',
    )
    native_operators = FDE.Meta.native_operators + (Operator.Conditional, Operator.Biconditional)

class Model(LP.Model):
    """
    An RM3 model is just like an {@LP model} with different tables for the conditional
    and bi-conditional operators.
    """

    def truth_function(self, oper: Operator, a, b=None, /):
        Value = self.Value
        if oper == Operator.Conditional and Value[a] > Value[b]:
            return Value.F
        return super().truth_function(oper, a, b)

class TableauxSystem(LP.TableauxSystem):

    branchables = FDE.TableauxSystem.branchables | {
        Operator.Conditional: ((1, 2), (1, 0)),
        Operator.Biconditional: ((1, 2), (1, 1)),
    }

@TableauxSystem.initialize
class TabRules(LP.TabRules):
    """
    The closure rules for RM3 are the FDE closure rule, and the LP closure rule.
    Most of the operator rules are the same as L{FDE}, except for the conditional
    rules. The biconditional rules are borrowed from `L3_`, since they are
    simplification rules.
    """

    class ConditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*, make
        three branches *b'*, *b''*, and *b'''* from *b*. On *b'* add an undesignated
        node with the antecedent. On *b''* add an undesignated node with the
        negation of the consequent. On *b'''* add four designated nodes, with
        the antecedent, its negation, the consequent, and its negation,
        respectively. Then tick *n*.
        """
        operator    = Operator.Conditional
        designation = True
        branching   = 2

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode( lhs, False)),
                group(sdnode(~rhs, False)),
                group(
                    sdnode( lhs, True),
                    sdnode(~lhs, True),
                    sdnode( rhs, True),
                    sdnode(~rhs, True),
                )
            )

    class ConditionalUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'*, add a designated node
        with the antecedent, and an undesignated node with with consequent.
        On *b''*, add an undesignated node with the negation of the antecedent,
        and a designated node with the negation of the consequent. Then tick *n*.
        """
        operator    = Operator.Conditional
        designation = False
        branching   = 1

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode( lhs, True),  sdnode( rhs, False)),
                group(sdnode(~lhs, False), sdnode(~rhs, True)),
            )

    class BiconditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked designated biconditional node *n* on a branch *b*, make
        three branches *b'*, *b''*, and *b'''* from *b*. On *b'* add undesignated
        nodes for each of the two operands. On *b''*, add undesignated nodes fo
        the negation of each operand. On *b'''*, add four designated nodes, one
        with each operand, and one for the negation of each operand. Then tick *n*.
        """
        operator    = Operator.Biconditional
        designation = True
        branching   = 2

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode( lhs, False), sdnode( rhs, False)),
                group(sdnode(~lhs, False), sdnode(~rhs, False)),
                group(
                    sdnode( lhs, True),
                    sdnode(~lhs, True),
                    sdnode( rhs, True),
                    sdnode(~rhs, True),
                )
            )

    class BiconditionalUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked undesignated biconditional node *n* on a branch *b*, add a
        conjunction undesignated node to *b*, with first conjunct being a conditional
        with the same operands as *n*, and the second conjunct being a conditional
        with the reversed operands of *n*, then tick *n*.
        """
        operator    = Operator.Biconditional
        designation = False
        branching   = 1

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            Cond = Operator.Conditional
            return adds(
                group(sdnode(Cond(lhs, rhs), False)),
                group(sdnode(Cond(rhs, lhs), False)),
            )

    class BiconditionalNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked undesignated negated biconditional node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'* add an undesignated node
        for each operand. On *b''* add an undesignated nodes for the negation of
        each operand. Then tick *n*.
        """
        negated     = True
        operator    = Operator.Biconditional
        designation = False
        branching   = 1

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode( lhs, False), sdnode( rhs, False)),
                group(sdnode(~lhs, False), sdnode(~rhs, False)),
            )

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
            FDE.TabRules.ConditionalNegatedDesignated,
            ConditionalUndesignated,
            FDE.TabRules.ExistentialNegatedDesignated,
            FDE.TabRules.ExistentialNegatedUndesignated,
            FDE.TabRules.UniversalNegatedDesignated,
            FDE.TabRules.UniversalNegatedUndesignated,
            FDE.TabRules.DoubleNegationDesignated,
            FDE.TabRules.DoubleNegationUndesignated,
        ),
        (
            # 2 branching rules
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
            FDE.TabRules.ConditionalNegatedUndesignated,
            FDE.TabRules.BiconditionalNegatedDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated,
        ),
        (
            # 3 branching rules
            ConditionalDesignated,
            BiconditionalDesignated,
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
