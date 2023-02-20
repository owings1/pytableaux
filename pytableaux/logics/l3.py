# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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

from pytableaux.lang import Operator
from pytableaux.models import ValueK3
from pytableaux.proof import Node, adds, group, sdnode

from . import fde as FDE
from . import k3 as K3

name = 'L3'

class Meta(K3.Meta):
    title       = u'Łukasiewicz 3-valued Logic'
    description = (
        'Three-valued logic (True, False, Neither) with a '
        'primitive Conditional operator'
    )
    category_order = 80
    native_operators = K3.Meta.native_operators + (Operator.Conditional, Operator.Biconditional)

class Model(K3.Model):

    def truth_function(self, operator, a, b = None) -> ValueK3:
        if operator == Operator.Conditional:
            if a == self.Value.N and b == self.Value.N:
                return self.Value.T
        return super().truth_function(operator, a, b)

class TableauxSystem(K3.TableauxSystem):

    branchables = K3.TableauxSystem.branchables | {
        Operator.Conditional: ((1, 1), (1, 0)),
        Operator.Biconditional: ((1, 1), (1, 1)),
    }

@TableauxSystem.initialize
class TabRules(K3.TabRules):

    class ConditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked designated conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*. To *b'* add a designated disjunction
        node with the negation of the antecedent as the first disjunct, and the
        consequent as the second disjunct. On *b''* add four undesignated nodes:
        a node with the antecedent, a node with the negation of the antecedent,
        a node with the consequent, and a node with the negation of the consequent.
        Then tick *n*.
        """
        operator    = Operator.Conditional
        designation = True
        branching   = 1

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode(~lhs | rhs, True)),
                group(
                    sdnode( lhs, False),
                    sdnode(~lhs, False),
                    sdnode( rhs, False),
                    sdnode(~rhs, False),
                )
            )

    class ConditionalUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked undesignated conditional node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*. On *b'* add a designated node
        with the antecedent and an undesignated node with the consequent. On *b''*,
        add undesignated nodes for the antecedent and its negation, and a designated
        with the negation of the consequent. Then tick *n*.   
        """
        operator    = Operator.Conditional
        designation = False
        branching   = 1

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            return adds(
                group(
                    sdnode(lhs, True),
                    sdnode(rhs, False),
                ),
                group(
                    sdnode( lhs, False),
                    sdnode(~lhs, False),
                    sdnode(~rhs, True),
                ),
            )

    class BiconditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked designated biconditional node *n* on a branch *b*, add
        two branches *b'* and *b''* to *b*. On *b'* add a designated material
        biconditional node with the same operands. On *b''* add four undesignated
        nodes, with the antecedent, the negation of the antecedent, the consequent,
        and the negation of the consequent, respectively. Then tick *n*.
        """
        operator    = Operator.Biconditional
        designation = True
        branching   = 1

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode(Operator.MaterialBiconditional(lhs, rhs), True)),
                group(
                    sdnode( lhs, False),
                    sdnode(~lhs, False),
                    sdnode( rhs, False),
                    sdnode(~rhs, False),
                )
            )

    class BiconditionalUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked undesignated biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add an undesignated conditional
        node with the same operands. On *b''* add an undesignated conditional node
        with the reversed operands. Then tick *n*.
        """
        operator    = Operator.Biconditional
        designation = False
        branching   = 1

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode(Operator.Conditional(lhs, rhs), False)),
                group(sdnode(Operator.Conditional(rhs, lhs), False)),
            )

    class BiconditionalNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked designated biconditional node *n* on a branch *b*, add
        two branches *b'* and *b''* to *b*. On *b'* add an undesignated negated material
        biconditional node with the same operands. On *b''* add four undesignated
        nodes, with the antecedent, the negation of the antecedent, the consequent,
        and the negation of the consequent, respectively. Then tick *n*.
        """
        negated     = True
        operator    = Operator.Biconditional
        designation = False
        branching   = 1

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode(~Operator.MaterialBiconditional(lhs, rhs), False)),
                group(
                    sdnode( lhs, False),
                    sdnode(~lhs, False),
                    sdnode( rhs, False),
                    sdnode(~rhs, False),
                )
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
            FDE.TabRules.BiconditionalNegatedDesignated,
            FDE.TabRules.ExistentialNegatedDesignated,
            FDE.TabRules.ExistentialNegatedUndesignated,
            FDE.TabRules.UniversalNegatedDesignated,
            FDE.TabRules.UniversalNegatedUndesignated,
            FDE.TabRules.DoubleNegationDesignated,
            FDE.TabRules.DoubleNegationUndesignated,
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
            ConditionalDesignated,
            ConditionalUndesignated,
            FDE.TabRules.ConditionalNegatedUndesignated,
            BiconditionalDesignated,
            BiconditionalNegatedUndesignated,
            BiconditionalUndesignated,
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
