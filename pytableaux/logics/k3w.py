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
# pytableaux - Weak Kleene Logic
from __future__ import annotations

name = 'K3W'

class Meta:
    title    = 'Weak Kleene 3-valued logic'
    category = 'Many-valued'
    description = 'Three-valued logic with values T, F, and N'
    tags = 'many-valued', 'gappy', 'non-modal', 'first-order'
    category_order = 30

from pytableaux.lang.lex import Operator as Oper
from pytableaux.proof.common import Branch, Node
from pytableaux.logics import fde as FDE, k3 as K3
from pytableaux.logics.fde import adds, group, sdnode

class Model(K3.Model):
    """
    A L{K3W} model is just like a :ref:`K3 model <k3-model>` with different tables for
    some of the connectives.
    """

    def truth_function(self, oper: Oper, a, b=None, /):
        oper = Oper(oper)
        if oper.arity == 2 and (a == self.Value.N or b == self.Value.N):
            return self.Value.N
        return super().truth_function(oper, a, b)

class TableauxSystem(FDE.TableauxSystem):
    """
    L{K3W}'s Tableaux System inherits directly from the :ref:`FDE system <fde-system>`,
    employing designation markers, and building the trunk in the same way.
    """
    branchables = {
        Oper.Negation: {
            True: {True: 0, False: 0},
        },
        Oper.Assertion: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        Oper.Conjunction: {
            False : {True: 0, False: 1},
            True  : {True: 2, False: 2},
        },
        Oper.Disjunction: {
            False : {True: 2, False: 2},
            True  : {True: 0, False: 2},
        },
        # reduction
        Oper.MaterialConditional: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        # reduction
        Oper.MaterialBiconditional: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
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

class TabRules:
    """
    The Tableaux System for L{K3W} contains the FDE closure rule, and the L{K3} closure
    rule. Several of the operator rules are the same as :ref:`FDE <fde-system>`.
    However, many rules for L{K3W} are different from FDE, given
    the behavior of the *N* value.
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

    class ConjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated conjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add a designated
        node with the first conjunct, and a designated node with the negation of the
        second conjunct. On *b''* add a designated node with the negation of the first
        conjunct, and a designated node with the second conjunct. On *b'''* add
        designated nodes with the negation of each conjunct. Then tick *n*.
        """
        negated     = True
        operator    = Oper.Conjunction
        designation = True
        branch_level = 3

        def _get_node_targets(self, node: Node, _: Branch, /):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode( lhs, True), sdnode(~rhs, True)),
                group(sdnode(~lhs, True), sdnode( rhs, True)),
                group(sdnode(~lhs, True), sdnode(~rhs, True)),
            )

    class ConjunctionUndesignated(FDE.TabRules.ConjunctionUndesignated):
        pass

    class ConjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, negated conjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add undesignated nodes
        for the first conjunct and its negation. On *b''* add undesignated nodes for the
        second conjunct and its negation. On *b'''* add a designated node for each conjunct.
        Then tick *n*. 
        """
        negated     = True
        operator    = Oper.Conjunction
        designation = False
        branch_level = 3

        def _get_node_targets(self, node: Node, _: Branch, /):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode(lhs, False), sdnode(~lhs, False)),
                group(sdnode(rhs, False), sdnode(~rhs, False)),
                group(sdnode(lhs, True),  sdnode( rhs, True)),
            )

    class DisjunctionDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, disjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add a designated
        node with the first disjunct, and a designated node with the negation of the
        second disjunct. On *b''* add a designated node with the negation of the first
        disjunct, and a designated node with the second disjunct. On *b'''* add a
        designated node with each disjunct. Then tick *n*.
        """
        operator    = Oper.Disjunction
        designation = True
        branch_level = 3

        def _get_node_targets(self, node: Node, _: Branch, /):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode( lhs, True), sdnode(~rhs, True)),
                group(sdnode(~lhs, True), sdnode( rhs, True)),
                group(sdnode( lhs, True), sdnode( rhs, True)),
            )
            
    class DisjunctionNegatedDesignated(FDE.TabRules.DisjunctionNegatedDesignated):
        pass

    class DisjunctionUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated disjunction node *n* on a branch *b*, make three
        new branches *b'*, *b''*, and *b'''* from b. On *b'* add undesignated nodes for
        the first disjunct and its negation. On *b''* add undesignated nodes for the
        second disjunct and its negation. On *b'''* add designated nodes for the negation
        of each disjunct. Then tick *n*.
        """
        operator    = Oper.Disjunction
        designation = False
        branch_level = 3

        def _get_node_targets(self, node: Node, _: Branch, /):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode( lhs, False), sdnode(~lhs, False)),
                group(sdnode( rhs, False), sdnode(~rhs, False)),
                group(sdnode(~lhs, True),  sdnode(~rhs, True)),
            )

    class DisjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        Either the disjunction is designated, or at least one of the disjuncts
        has the value V{N}. So, from an unticked, undesignated, negated
        disjunction node *n* on a branch *b*, make three branches *b'*, *b''*,
        and *b'''* from *b*. On *b'* add a designated node with the disjunction.
        On *b''* add two undesignated nodes with the first disjunct and its
        negation, respectively. On *b'''* add undesignated nodes with the second
        disjunct and its negation, respectively. Then tick *n*.
        """
        negated     = True
        operator    = Oper.Disjunction
        designation = False
        branch_level = 3

        def _get_node_targets(self, node: Node, _: Branch, /):
            s = self.sentence(node)
            return adds(
                group(sdnode(s, True)),
                group(sdnode(s.lhs, False), sdnode(~s.lhs, False)),
                group(sdnode(s.rhs, False), sdnode(~s.rhs, False)),
            )

    class MaterialConditionalDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a disjunction.
        """
        operator    = Oper.MaterialConditional
        designation = True
        branch_level = 1

        def _get_node_targets(self, node: Node, _: Branch, /):
            s = self.sentence(node)
            return adds(
                group(sdnode(~s.lhs | s.rhs, self.designation))
            )

    class MaterialConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a negated disjunction.
        """
        negated     = True
        operator    = Oper.MaterialConditional
        designation = True
        branch_level = 1

        def _get_node_targets(self, node: Node, _: Branch, /):
            s = self.sentence(node)
            return adds(
                group(sdnode(~(~s.lhs | s.rhs), self.designation))
            )

    class MaterialConditionalUndesignated(MaterialConditionalDesignated):
        """
        This rule reduces to a disjunction.
        """
        negated     = False
        designation = False

    class MaterialConditionalNegatedUndesignated(MaterialConditionalNegatedDesignated):
        """
        This rule reduces to a negated disjunction.
        """
        negated     = True
        designation = False

    class MaterialBiconditionalDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """
        operator    = Oper.MaterialBiconditional
        designation = True
        conjunct_op = Oper.MaterialConditional
        branch_level = 1

    class MaterialBiconditionalNegatedDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a negated conjunction of material conditionals.
        """
        negated     = True
        operator    = Oper.MaterialBiconditional
        designation = True
        conjunct_op = Oper.MaterialConditional
        branch_level = 1

    class MaterialBiconditionalUndesignated(MaterialBiconditionalDesignated):
        """
        This rule reduces to a conjunction of material conditionals.
        """
        designation = False

    class MaterialBiconditionalNegatedUndesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule reduces to a negated conjunction of material conditionals.
        """
        designation = False

    class ConditionalDesignated(MaterialConditionalDesignated):
        """
        Same as for the material conditional designated.
        """
        operator = Oper.Conditional

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        Same as for the negated material conditional designated.
        """
        operator = Oper.Conditional

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        Same as for the material conditional undesignated.
        """
        operator = Oper.Conditional

    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated):
        """
        Same as for the negated material conditional undesignated.
        """
        operator = Oper.Conditional

    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        """
        Same as for the material biconditional designated.
        """
        operator = Oper.Biconditional

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        Same as for the negated material biconditional designated.
        """
        operator = Oper.Biconditional

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        Same as for the material biconditional undesignated.
        """
        operator = Oper.Biconditional

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        Same as for the negated material biconditional undesignated.
        """
        operator = Oper.Biconditional

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
            ConditionalUndesignated,
            ConditionalNegatedDesignated,
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
            # five-branching rules (formerly)
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
