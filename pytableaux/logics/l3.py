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
from . import fde as FDE
from . import k3 as K3


class Meta(K3.Meta):
    name = 'L3'
    title = u'Łukasiewicz 3-valued Logic'
    description = (
        'Three-valued logic (True, False, Neither) with a '
        'primitive Conditional operator')
    category_order = 5
    native_operators = K3.Meta.native_operators | (
        Operator.Conditional,
        Operator.Biconditional)

class Model(K3.Model):

    class TruthFunction(K3.Model.TruthFunction):

        def Conditional(self, a, b, /):
            if a == b:
                return self.values.T
            return self.MaterialConditional(a, b)

class System(K3.System): pass

class Rules(K3.Rules):

    class ConditionalDesignated(rules.OperatorNodeRule):
        """
        From an unticked designated conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*. To *b'* add a designated disjunction
        node with the negation of the antecedent as the first disjunct, and the
        consequent as the second disjunct. On *b''* add four undesignated nodes:
        a node with the antecedent, a node with the negation of the antecedent,
        a node with the consequent, and a node with the negation of the consequent.
        Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup(
                    (~lhs | rhs, d, w)),
                sdwgroup(
                    ( lhs, not d, w),
                    ( rhs, not d, w),
                    (~lhs, not d, w),
                    (~rhs, not d, w)))

    class ConditionalUndesignated(rules.OperatorNodeRule):
        """
        From an unticked undesignated conditional node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*. On *b'* add a designated node
        with the antecedent and an undesignated node with the consequent. On *b''*,
        add undesignated nodes for the antecedent and its negation, and a designated
        with the negation of the consequent. Then tick *n*.   
        """

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup(
                    (lhs, not d, w),
                    (rhs, d, w)),
                sdwgroup(
                    ( lhs, d, w),
                    (~lhs, d, w),
                    (~rhs, not d, w)))

    class BiconditionalDesignated(rules.OperatorNodeRule):
        """
        From an unticked designated biconditional node *n* on a branch *b*, add
        two branches *b'* and *b''* to *b*. On *b'* add a designated material
        biconditional node with the same operands. On *b''* add four undesignated
        nodes, with the antecedent, the negation of the antecedent, the consequent,
        and the negation of the consequent, respectively. Then tick *n*.
        """

        convert = Operator.MaterialBiconditional

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup((self.convert(lhs, rhs), d, w)),
                sdwgroup(
                    ( lhs, not d, w),
                    (~lhs, not d, w),
                    ( rhs, not d, w),
                    (~rhs, not d, w)))

    class BiconditionalUndesignated(rules.OperatorNodeRule):
        """
        From an unticked undesignated biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add an undesignated conditional
        node with the same operands. On *b''* add an undesignated conditional node
        with the reversed operands. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            convert = self.operator.other
            yield adds(
                sdwgroup((convert(s.operands), d, w)),
                sdwgroup((convert(reversed(s)), d, w)))

    class BiconditionalNegatedUndesignated(rules.OperatorNodeRule):
        """
        From an unticked designated biconditional node *n* on a branch *b*, add
        two branches *b'* and *b''* to *b*. On *b'* add an undesignated negated material
        biconditional node with the same operands. On *b''* add four undesignated
        nodes, with the antecedent, the negation of the antecedent, the consequent,
        and the negation of the consequent, respectively. Then tick *n*.
        """

        convert = Operator.MaterialBiconditional

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup((~self.convert(lhs, rhs), d, w)),
                sdwgroup(
                    ( lhs, d, w),
                    (~lhs, d, w),
                    ( rhs, d, w),
                    (~rhs, d, w)))

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
            FDE.Rules.DoubleNegationDesignated,
            FDE.Rules.DoubleNegationUndesignated),
        group(
            # branching rules
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
            ConditionalDesignated,
            ConditionalUndesignated,
            FDE.Rules.ConditionalNegatedUndesignated,
            BiconditionalDesignated,
            FDE.Rules.BiconditionalNegatedDesignated,
            BiconditionalNegatedUndesignated,
            BiconditionalUndesignated),
        # quantifier rules
        *FDE.Rules.unquantifying_groups)

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(2), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'