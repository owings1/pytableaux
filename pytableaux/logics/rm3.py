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
from . import lp as LP

class Meta(LP.Meta):
    name = 'RM3'
    title = 'R-mingle 3'
    description = (
        'Three-valued logic (True, False, Both) with a primitive '
        'Conditional operator')
    category_order = 130
    native_operators = tuple(sorted(FDE.Meta.native_operators + (
        Operator.Conditional,
        Operator.Biconditional)))

class Model(LP.Model):

    class TruthFunction(LP.Model.TruthFunction):

        def Conditional(self, a, b):
            if a > b:
                return self.values.F
            return super().Conditional(a, b)

class Rules(LP.Rules):

    class ConditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*, make
        three branches *b'*, *b''*, and *b'''* from *b*. On *b'* add an undesignated
        node with the antecedent. On *b''* add an undesignated node with the
        negation of the consequent. On *b'''* add four designated nodes, with
        the antecedent, its negation, the consequent, and its negation,
        respectively. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode( lhs, False)),
                group(sdnode(~rhs, False)),
                group(
                    sdnode( lhs, True),
                    sdnode(~lhs, True),
                    sdnode( rhs, True),
                    sdnode(~rhs, True)))

    class ConditionalUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'*, add a designated node
        with the antecedent, and an undesignated node with with consequent.
        On *b''*, add an undesignated node with the negation of the antecedent,
        and a designated node with the negation of the consequent. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(
                    sdnode( s.lhs, True),
                    sdnode( s.rhs, False)),
                group(
                    sdnode(~s.lhs, False),
                    sdnode(~s.rhs, True)))

    class BiconditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked designated biconditional node *n* on a branch *b*, make
        three branches *b'*, *b''*, and *b'''* from *b*. On *b'* add undesignated
        nodes for each of the two operands. On *b''*, add undesignated nodes fo
        the negation of each operand. On *b'''*, add four designated nodes, one
        with each operand, and one for the negation of each operand. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(
                    sdnode( lhs, False),
                    sdnode( rhs, False)),
                group(
                    sdnode(~lhs, False),
                    sdnode(~rhs, False)),
                group(
                    sdnode( lhs, True),
                    sdnode(~lhs, True),
                    sdnode( rhs, True),
                    sdnode(~rhs, True)))

    class BiconditionalUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked undesignated biconditional node *n* on a branch *b*, add a
        conjunction undesignated node to *b*, with first conjunct being a conditional
        with the same operands as *n*, and the second conjunct being a conditional
        with the reversed operands of *n*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            convert = self.operator.other
            yield adds(
                group(sdnode(convert(s.lhs, s.rhs), False)),
                group(sdnode(convert(s.rhs, s.lhs), False)))

    class BiconditionalNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked undesignated negated biconditional node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'* add an undesignated node
        for each operand. On *b''* add an undesignated nodes for the negation of
        each operand. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(
                    sdnode(s.lhs, False),
                    sdnode(s.rhs, False)),
                group(
                    sdnode(~s.lhs, False),
                    sdnode(~s.rhs, False)))

    groups = (
        group(
            # non-branching rules
            FDE.Rules.AssertionDesignated,
            FDE.Rules.AssertionUndesignated,
            FDE.Rules.AssertionNegatedDesignated,
            FDE.Rules.AssertionNegatedUndesignated,
            FDE.Rules.ConjunctionDesignated,
            FDE.Rules.DisjunctionNegatedDesignated,
            FDE.Rules.DisjunctionUndesignated,
            FDE.Rules.DisjunctionNegatedUndesignated,
            FDE.Rules.MaterialConditionalNegatedDesignated,
            FDE.Rules.MaterialConditionalUndesignated,
            FDE.Rules.ConditionalNegatedDesignated,
            ConditionalUndesignated,
            FDE.Rules.ExistentialNegatedDesignated,
            FDE.Rules.ExistentialNegatedUndesignated,
            FDE.Rules.UniversalNegatedDesignated,
            FDE.Rules.UniversalNegatedUndesignated,
            FDE.Rules.DoubleNegationDesignated,
            FDE.Rules.DoubleNegationUndesignated),
        group(
            # 2 branching rules
            FDE.Rules.ConjunctionNegatedDesignated,
            FDE.Rules.ConjunctionUndesignated,
            FDE.Rules.ConjunctionNegatedUndesignated,
            FDE.Rules.DisjunctionDesignated,
            FDE.Rules.MaterialConditionalDesignated,
            FDE.Rules.MaterialConditionalNegatedUndesignated,
            FDE.Rules.MaterialBiconditionalDesignated,
            FDE.Rules.MaterialBiconditionalNegatedDesignated,
            FDE.Rules.MaterialBiconditionalUndesignated,
            FDE.Rules.MaterialBiconditionalNegatedUndesignated,
            FDE.Rules.ConditionalNegatedUndesignated,
            FDE.Rules.BiconditionalNegatedDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated),
        group(
            # 3 branching rules
            ConditionalDesignated,
            BiconditionalDesignated),
        group(
            FDE.Rules.ExistentialDesignated,
            FDE.Rules.ExistentialUndesignated),
        group(
            FDE.Rules.UniversalDesignated,
            FDE.Rules.UniversalUndesignated))



class System(LP.System):

    branchables = LP.System.branchables | {
        Operator.Conditional: ((1, 2), (1, 0)),
        Operator.Biconditional: ((1, 2), (1, 1))}