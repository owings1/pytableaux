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

from ..lang import Operator
from ..proof import adds, sdnode
from ..tools import group
from . import fde as FDE
from . import k3 as K3

class Meta(K3.Meta):
    name = 'K3W'
    title = 'Weak Kleene Logic'
    description = 'Three-valued logic with values T, F, and N'
    category_order = 30

class Model(K3.Model):

    def truth_function(self, oper: Operator, a, b=None, /):
        oper = Operator(oper)
        if oper.arity == 2 and (a == self.Value.N or b == self.Value.N):
            return self.Value.N
        return super().truth_function(oper, a, b)

class TableauxSystem(K3.TableauxSystem):

    branchables = {
        Operator.Negation: (None, (0, 0)),
        Operator.Assertion: ((0, 0), (0, 0)),
        Operator.Conjunction: ((1, 0), (2, 2)),
        Operator.Disjunction: ((2, 2), (2, 0)),
        # reduction
        Operator.MaterialConditional: ((0, 0), (0, 0)),
        # reduction
        Operator.MaterialBiconditional: ((0, 0), (0, 0)),
        # reduction
        Operator.Conditional: ((0, 0), (0, 0)),
        # reduction
        Operator.Biconditional: ((0, 0), (0, 0))}

@TableauxSystem.initialize
class TabRules(K3.TabRules):

    class ConjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated conjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add a designated
        node with the first conjunct, and a designated node with the negation of the
        second conjunct. On *b''* add a designated node with the negation of the first
        conjunct, and a designated node with the second conjunct. On *b'''* add
        designated nodes with the negation of each conjunct. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode( lhs, True), sdnode(~rhs, True)),
                group(sdnode(~lhs, True), sdnode( rhs, True)),
                group(sdnode(~lhs, True), sdnode(~rhs, True)))

    class ConjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, negated conjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add undesignated nodes
        for the first conjunct and its negation. On *b''* add undesignated nodes for the
        second conjunct and its negation. On *b'''* add a designated node for each conjunct.
        Then tick *n*. 
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode(lhs, False), sdnode(~lhs, False)),
                group(sdnode(rhs, False), sdnode(~rhs, False)),
                group(sdnode(lhs, True),  sdnode( rhs, True)))

    class DisjunctionDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, disjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add a designated
        node with the first disjunct, and a designated node with the negation of the
        second disjunct. On *b''* add a designated node with the negation of the first
        disjunct, and a designated node with the second disjunct. On *b'''* add a
        designated node with each disjunct. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode( lhs, True), sdnode(~rhs, True)),
                group(sdnode(~lhs, True), sdnode( rhs, True)),
                group(sdnode( lhs, True), sdnode( rhs, True)))
            
    class DisjunctionUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated disjunction node *n* on a branch *b*, make three
        new branches *b'*, *b''*, and *b'''* from b. On *b'* add undesignated nodes for
        the first disjunct and its negation. On *b''* add undesignated nodes for the
        second disjunct and its negation. On *b'''* add designated nodes for the negation
        of each disjunct. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode( lhs, False), sdnode(~lhs, False)),
                group(sdnode( rhs, False), sdnode(~rhs, False)),
                group(sdnode(~lhs, True),  sdnode(~rhs, True)))

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

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(s, True)),
                group(sdnode(s.lhs, False), sdnode(~s.lhs, False)),
                group(sdnode(s.rhs, False), sdnode(~s.rhs, False)))

    class MaterialConditionalDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a disjunction.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~s.lhs | s.rhs, d)))

    class MaterialConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a negated disjunction.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~(~s.lhs | s.rhs), d)))

    class MaterialConditionalUndesignated(MaterialConditionalDesignated):
        """
        This rule reduces to a disjunction.
        """

    class MaterialConditionalNegatedUndesignated(MaterialConditionalNegatedDesignated):
        """
        This rule reduces to a negated disjunction.
        """

    class MaterialBiconditionalDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """
        conjunct_op = Operator.MaterialConditional

    class MaterialBiconditionalNegatedDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a negated conjunction of material conditionals.
        """
        conjunct_op = Operator.MaterialConditional

    class MaterialBiconditionalUndesignated(MaterialBiconditionalDesignated):
        """
        This rule reduces to a conjunction of material conditionals.
        """

    class MaterialBiconditionalNegatedUndesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule reduces to a negated conjunction of material conditionals.
        """

    class ConditionalDesignated(MaterialConditionalDesignated):
        """
        Same as for the material conditional designated.
        """

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        Same as for the negated material conditional designated.
        """

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        Same as for the material conditional undesignated.
        """

    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated):
        """
        Same as for the negated material conditional undesignated.
        """

    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        """
        Same as for the material biconditional designated.
        """

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        Same as for the negated material biconditional designated.
        """

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        Same as for the material biconditional undesignated.
        """

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        Same as for the negated material biconditional undesignated.
        """

    rule_groups = (
        (
            # non-branching rules
            FDE.TabRules.AssertionDesignated,
            FDE.TabRules.AssertionUndesignated,
            FDE.TabRules.AssertionNegatedDesignated,
            FDE.TabRules.AssertionNegatedUndesignated,
            FDE.TabRules.ConjunctionDesignated, 
            FDE.TabRules.DisjunctionNegatedDesignated,
            FDE.TabRules.ExistentialNegatedDesignated,
            FDE.TabRules.ExistentialNegatedUndesignated,
            FDE.TabRules.UniversalNegatedDesignated,
            FDE.TabRules.UniversalNegatedUndesignated,
            FDE.TabRules.DoubleNegationDesignated,
            FDE.TabRules.DoubleNegationUndesignated,
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
            FDE.TabRules.ConjunctionUndesignated,
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
            FDE.TabRules.ExistentialDesignated,
            FDE.TabRules.ExistentialUndesignated,
        ),
        (
            FDE.TabRules.UniversalDesignated,
            FDE.TabRules.UniversalUndesignated,
        ),
    )
