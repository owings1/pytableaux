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
from ..proof import adds, sdwgroup
from ..tools import group
from . import fde as FDE
from . import l3 as L3
from . import lp as LP
from . import LogicType

class Meta(LP.Meta):
    name = 'RM3'
    title = 'R-mingle 3'
    description = (
        'Three-valued logic (True, False, Both) with a primitive '
        'Conditional operator')
    category_order = 6
    native_operators = FDE.Meta.native_operators | (
        Operator.Conditional,
        Operator.Biconditional)

class Model(LP.Model):

    class TruthFunction(FDE.Model.TruthFunction):

        def Conditional(self, a, b):
            if a > b:
                return self.values.F
            return super().Conditional(a, b)

class System(FDE.System): pass

class Rules(LogicType.Rules):

    closure = LP.Rules.closure

    class ConditionalDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*, make
        three branches *b'*, *b''*, and *b'''* from *b*. On *b'* add an undesignated
        node with the antecedent. On *b''* add an undesignated node with the
        negation of the consequent. On *b'''* add four designated nodes, with
        the antecedent, its negation, the consequent, and its negation,
        respectively. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup(( lhs, not d, w)),
                sdwgroup((~rhs, not d, w)),
                sdwgroup(
                    ( lhs, d, w),
                    (~lhs, d, w),
                    ( rhs, d, w),
                    (~rhs, d, w)))

    class ConditionalUndesignated(System.OperatorNodeRule):
        """
        From an unticked, undesignated, conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'*, add a designated node
        with the antecedent, and an undesignated node with with consequent.
        On *b''*, add an undesignated node with the negation of the antecedent,
        and a designated node with the negation of the consequent. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                sdwgroup(
                    ( s.lhs, not d, w),
                    ( s.rhs, d, w)),
                sdwgroup(
                    (~s.lhs, d, w),
                    (~s.rhs, not d, w)))

    class BiconditionalDesignated(System.OperatorNodeRule):
        """
        From an unticked designated biconditional node *n* on a branch *b*, make
        three branches *b'*, *b''*, and *b'''* from *b*. On *b'* add undesignated
        nodes for each of the two operands. On *b''*, add undesignated nodes fo
        the negation of each operand. On *b'''*, add four designated nodes, one
        with each operand, and one for the negation of each operand. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup(
                    ( lhs, not d, w),
                    ( rhs, not d, w)),
                sdwgroup(
                    (~lhs, not d, w),
                    (~rhs, not d, w)),
                sdwgroup(
                    ( lhs, d, w),
                    (~lhs, d, w),
                    ( rhs, d, w),
                    (~rhs, d, w)))

    class BiconditionalNegatedUndesignated(System.OperatorNodeRule):
        """
        From an unticked undesignated negated biconditional node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'* add an undesignated node
        for each operand. On *b''* add an undesignated nodes for the negation of
        each operand. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                sdwgroup(
                    (s.lhs, d, w),
                    (s.rhs, d, w)),
                sdwgroup(
                    (~s.lhs, d, w),
                    (~s.rhs, d, w)))

    groups = (
        group(
            # non-branching rules
            FDE.Rules.AssertionDesignated,
            FDE.Rules.AssertionUndesignated,
            FDE.Rules.AssertionNegatedDesignated,
            FDE.Rules.AssertionNegatedUndesignated,
            FDE.Rules.ConjunctionDesignated,
            FDE.Rules.ConjunctionNegatedUndesignated,
            FDE.Rules.DisjunctionNegatedDesignated,
            FDE.Rules.DisjunctionUndesignated,
            FDE.Rules.MaterialConditionalNegatedDesignated,
            FDE.Rules.MaterialConditionalUndesignated,
            FDE.Rules.ConditionalNegatedDesignated,
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
            FDE.Rules.DisjunctionDesignated,
            FDE.Rules.DisjunctionNegatedUndesignated,
            FDE.Rules.MaterialConditionalDesignated,
            FDE.Rules.MaterialConditionalNegatedUndesignated,
            FDE.Rules.MaterialBiconditionalDesignated,
            FDE.Rules.MaterialBiconditionalNegatedDesignated,
            FDE.Rules.MaterialBiconditionalUndesignated,
            FDE.Rules.MaterialBiconditionalNegatedUndesignated,
            ConditionalUndesignated,
            FDE.Rules.ConditionalNegatedUndesignated,
            FDE.Rules.BiconditionalNegatedDesignated,
            L3.Rules.BiconditionalUndesignated,
            BiconditionalNegatedUndesignated),
        group(
            # 3 branching rules
            ConditionalDesignated,
            BiconditionalDesignated),
        # quantifier rules
        *FDE.Rules.unquantifying_groups)

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(3), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'