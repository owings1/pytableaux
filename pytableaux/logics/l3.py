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
from ..proof import adds, sdwnode
from ..tools import group
from . import fde as FDE
from . import k3 as K3
from . import LogicType

class Meta(K3.Meta):
    name = 'L3'
    title = u'Łukasiewicz 3-valued Logic'
    description = (
        'Three-valued logic (True, False, Neither) with a '
        'primitive Conditional operator')
    category_order = 5
    native_operators = FDE.Meta.native_operators | (
        Operator.Conditional,
        Operator.Biconditional)

class Model(FDE.Model):

    class TruthFunction(FDE.Model.TruthFunction):

        def Conditional(self, a, b, /):
            if a == b:
                return self.values.T
            return self.MaterialConditional(a, b)

class System(FDE.System): pass

class Rules(LogicType.Rules):

    closure = K3.Rules.closure

    class ConditionalDesignated(System.OperatorNodeRule):
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
                group(sdwnode(~lhs | rhs, d, w)),
                group(
                    sdwnode( lhs, not d, w),
                    sdwnode(~lhs, not d, w),
                    sdwnode( rhs, not d, w),
                    sdwnode(~rhs, not d, w)))

    class ConditionalUndesignated(System.OperatorNodeRule):
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
                group(
                    sdwnode(lhs, not d, w),
                    sdwnode(rhs, d, w)),
                group(
                    sdwnode( lhs, d, w),
                    sdwnode(~lhs, d, w),
                    sdwnode(~rhs, not d, w)))

    class BiconditionalDesignated(System.OperatorNodeRule):
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
                group(sdwnode(self.convert(lhs, rhs), d, w)),
                group(
                    sdwnode( lhs, not d, w),
                    sdwnode(~lhs, not d, w),
                    sdwnode( rhs, not d, w),
                    sdwnode(~rhs, not d, w)))

    class BiconditionalUndesignated(System.OperatorNodeRule):
        """
        From an unticked undesignated biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add an undesignated conditional
        node with the same operands. On *b''* add an undesignated conditional node
        with the reversed operands. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            convert = self.operator.other
            yield adds(
                group(sdwnode(convert(s.operands), d, w)),
                group(sdwnode(convert(reversed(s)), d, w)))

    class BiconditionalNegatedUndesignated(System.OperatorNodeRule):
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
                group(sdwnode(~self.convert(lhs, rhs), d, w)),
                group(
                    sdwnode( lhs, d, w),
                    sdwnode(~lhs, d, w),
                    sdwnode( rhs, d, w),
                    sdwnode(~rhs, d, w)))

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
        group(
            FDE.Rules.ExistentialDesignated,
            FDE.Rules.ExistentialUndesignated),
        group(
            FDE.Rules.UniversalDesignated,
            FDE.Rules.UniversalUndesignated))

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(2), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'