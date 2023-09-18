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
from ..proof import adds, rules, sdwgroup
from ..tools import group
from . import l3 as L3
from . import lp as LP


class Meta(LP.Meta):
    name = 'RM3'
    title = 'R-mingle 3'
    description = (
        'Three-valued logic (True, False, Both) with a primitive '
        'Conditional operator')
    category_order = LP.Meta.category_order + 2
    native_operators = [Operator.Conditional, Operator.Biconditional]

class Model(LP.Model):

    class TruthFunction(LP.Model.TruthFunction):

        def Conditional(self, a, b):
            if a > b:
                return self.values.F
            return super().Conditional(a, b)

class System(LP.System): pass

class Rules(LP.Rules):

    class ConditionalDesignated(rules.OperatorNodeRule):
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

    class ConditionalUndesignated(rules.OperatorNodeRule):
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

    class BiconditionalDesignated(rules.OperatorNodeRule):
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

    class BiconditionalNegatedUndesignated(rules.OperatorNodeRule):
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

    BiconditionalUndesignated = L3.Rules.BiconditionalUndesignated

    nonbranching_groups = group(
        group(
            LP.Rules.AssertionDesignated,
            LP.Rules.AssertionUndesignated,
            LP.Rules.AssertionNegatedDesignated,
            LP.Rules.AssertionNegatedUndesignated,
            LP.Rules.ConjunctionDesignated,
            LP.Rules.ConjunctionNegatedUndesignated,
            LP.Rules.DisjunctionNegatedDesignated,
            LP.Rules.DisjunctionUndesignated,
            LP.Rules.MaterialConditionalNegatedDesignated,
            LP.Rules.MaterialConditionalUndesignated,
            LP.Rules.ConditionalNegatedDesignated,
            LP.Rules.DoubleNegationDesignated,
            LP.Rules.DoubleNegationUndesignated))

    branching_groups = group(
        group(
            LP.Rules.ConjunctionNegatedDesignated,
            LP.Rules.ConjunctionUndesignated,
            LP.Rules.DisjunctionDesignated,
            LP.Rules.DisjunctionNegatedUndesignated,
            LP.Rules.MaterialConditionalDesignated,
            LP.Rules.MaterialConditionalNegatedUndesignated,
            LP.Rules.MaterialBiconditionalDesignated,
            LP.Rules.MaterialBiconditionalNegatedDesignated,
            LP.Rules.MaterialBiconditionalUndesignated,
            LP.Rules.MaterialBiconditionalNegatedUndesignated,
            ConditionalUndesignated,
            LP.Rules.ConditionalNegatedUndesignated,
            LP.Rules.BiconditionalNegatedDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated),
        group(
            # 3 branching rules
            ConditionalDesignated,
            BiconditionalDesignated))

    groups = (
        *nonbranching_groups,
        *branching_groups,
        *LP.Rules.unquantifying_groups)
