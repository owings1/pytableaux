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
# pytableaux - Lukasiewicz 3-valued Logic
from __future__ import annotations

from pytableaux.lang.lex import Operator as Oper
from pytableaux.logics import fde as FDE
from pytableaux.logics import k3 as K3
from pytableaux.proof.common import Node
from pytableaux.proof.util import adds, group, sdnode

name = 'L3'

class Meta:
    title       = u'Łukasiewicz 3-valued Logic'
    category    = 'Many-valued'
    description = 'Three-valued logic (True, False, Neither) with a primitive Conditional operator'
    category_order = 80
    tags = (
        'many-valued',
        'gappy',
        'non-modal',
        'first-order',
    )

class Model(K3.Model):
    """
    An L{L3} model is just like a :ref:`K3 model <k3-model>` with different tables
    for the conditional and bi-conditional operators.
    """

    def truth_function(self, operator, a, b = None):
        if operator == Oper.Conditional:
            if a == self.Value.N and b == self.Value.N:
                return self.Value.T
        return super().truth_function(operator, a, b)

class TableauxSystem(FDE.TableauxSystem):
    """
    L{L3}'s Tableaux System inherits directly from the :ref:`FDE system <fde-system>`,
    employing designation markers, and building the trunk in the same way.
    """
    branchables = FDE.TableauxSystem.branchables | {
        Oper.Conditional: {
            False : {True: 1, False: 1},
            True  : {True: 0, False: 1},
        },
        Oper.Biconditional: {
            False : {True: 1, False: 1},
            True  : {True: 1, False: 1},
        },
    }

class TabRules:
    """
    The closure rules for L{L3} are the FDE closure rule, and the L{K3} closure rule.
    The operator rules for L{L3} are mostly the rules for L{FDE}, with
    the exception of the rules for the conditional and biconditional operators.
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
    class MaterialConditionalUndesignated(FDE.TabRules.MaterialConditionalUndesignated):
        pass
    class MaterialConditionalNegatedUndesignated(FDE.TabRules.MaterialConditionalNegatedUndesignated):
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
        From an unticked designated conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*. To *b'* add a designated disjunction
        node with the negation of the antecedent as the first disjunct, and the
        consequent as the second disjunct. On *b''* add four undesignated nodes:
        a node with the antecedent, a node with the negation of the antecedent,
        a node with the consequent, and a node with the negation of the consequent.
        Then tick *n*.
        """
        operator    = Oper.Conditional
        designation = True
        branch_level = 2

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

    class ConditionalNegatedDesignated(FDE.TabRules.ConditionalNegatedDesignated):
        pass

    class ConditionalUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked undesignated conditional node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*. On *b'* add a designated node
        with the antecedent and an undesignated node with the consequent. On *b''*,
        add undesignated nodes for the antecedent and its negation, and a designated
        with the negation of the consequent. Then tick *n*.   
        """
        operator    = Oper.Conditional
        designation = False
        branch_level = 2

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

    class ConditionalNegatedUndesignated(FDE.TabRules.ConditionalNegatedUndesignated):
        pass
        
    class BiconditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked designated biconditional node *n* on a branch *b*, add
        two branches *b'* and *b''* to *b*. On *b'* add a designated material
        biconditional node with the same operands. On *b''* add four undesignated
        nodes, with the antecedent, the negation of the antecedent, the consequent,
        and the negation of the consequent, respectively. Then tick *n*.
        """
        operator    = Oper.Biconditional
        designation = True
        branch_level = 2

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode(Oper.MaterialBiconditional(lhs, rhs), True)),
                group(
                    sdnode( lhs, False),
                    sdnode(~lhs, False),
                    sdnode( rhs, False),
                    sdnode(~rhs, False),
                )
            )

    class BiconditionalNegatedDesignated(FDE.TabRules.BiconditionalNegatedDesignated):
        pass

    class BiconditionalUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked undesignated biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add an undesignated conditional
        node with the same operands. On *b''* add an undesignated conditional node
        with the reversed operands. Then tick *n*.
        """
        operator    = Oper.Biconditional
        designation = False
        branch_level = 2

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            Cond = Oper.Conditional
            return adds(
                group(sdnode(Cond(lhs, rhs), False)),
                group(sdnode(Cond(rhs, lhs), False)),
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
        operator    = Oper.Biconditional
        designation = False
        branch_level = 2

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode(~Oper.MaterialBiconditional(lhs, rhs), False)),
                group(
                    sdnode( lhs, False),
                    sdnode(~lhs, False),
                    sdnode( rhs, False),
                    sdnode(~rhs, False),
                )
            )

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
            BiconditionalNegatedDesignated,
            ExistentialNegatedDesignated,
            ExistentialNegatedUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated,
            DoubleNegationDesignated,
            DoubleNegationUndesignated,
        ),
        (
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
            BiconditionalDesignated,
            BiconditionalNegatedUndesignated,
            BiconditionalUndesignated,
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
