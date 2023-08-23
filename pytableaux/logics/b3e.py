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

from ..lang import Operator as Operator
from ..proof import adds, sdnode
from ..tools import group
from . import fde as FDE
from . import k3 as K3
from . import k3w as K3W
from . import LogicType

class Meta(K3.Meta):
    name = 'B3E'
    title = 'Bochvar 3 External Logic'
    description = 'Three-valued logic (True, False, Neither) with assertion operator'
    category_order = 50
    native_operators = FDE.Meta.native_operators | [Operator.Assertion]

class Model(FDE.Model):

    class TruthFunction(K3W.Model.TruthFunction):

        def Assertion(self, v, /):
            return self.values[v // 1]
        
        def Conditional(self, a, b, /):
            return super().Conditional(*map(self.Assertion, (a, b)))

class System(FDE.System): pass

class Rules(LogicType.Rules):

    closure = K3.Rules.closure

    class AssertionNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated, negated assertion node *n* on a branch *b*,
        add an undesignated node to *b* with the assertion of *n*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            # Keep designation fixed to False for inheritance below
            yield adds(group(sdnode(s.lhs, False)))

    class AssertionUndesignated(AssertionNegatedDesignated): pass

    class AssertionNegatedUndesignated(System.OperatorNodeRule):
        """
        From an unticked, undesignated, negated assertion node *n* on a branch *b*, add
        a designated node to *b* with the assertion of *n*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s.lhs, not d)))

    class ConditionalDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*,
        add a designated node to *b* with a disjunction, where the
        first disjunction is the negation of the assertion of the antecedent,
        and the second disjunct is the assertion of the consequent. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            sn = ~+s.lhs | +s.rhs
            # keep negated neutral for inheritance below
            if self.negated:
                sn = ~sn
            # keep designation neutral for inheritance below
            yield adds(group(sdnode(sn, d)))

    class ConditionalNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated negated conditional node *n* on a branch *b*,
        add a designated node with the antecedent, and an undesigntated node
        with the consequent to *b*. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            # Keep designation fixed for inheritance below.
            yield adds(group(sdnode(s.lhs, True), sdnode(s.rhs, False)))

    class ConditionalUndesignated(ConditionalNegatedDesignated): pass
    class ConditionalNegatedUndesignated(ConditionalDesignated): pass

    class BiconditionalDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated biconditional node *n* on a branch *b*, add
        two designated nodes to *b*, one with a disjunction, where the first
        disjunct is the negated asserted antecedent, and the second disjunct is
        the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhsa = +s.lhs
            rhsa = +s.rhs
            sn1 = ~lhsa | rhsa
            sn2 = ~rhsa | lhsa
            # Keep negated neutral for inheritance below.
            if self.negated:
                sn1 = ~sn1
                sn2 = ~sn2
            # Keep designation neutral for inheritance below.
            yield adds(group(sdnode(sn1, d), sdnode(sn2, d)))

    class BiconditionalNegatedDesignated(BiconditionalDesignated): pass
    class BiconditionalUndesignated(BiconditionalDesignated): pass
    # class BiconditionalNegatedUndesignated(BiconditionalUndesignated): pass
    class BiconditionalNegatedUndesignated(System.OperatorNodeRule):

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode(lhs, d), sdnode(rhs, d)),
                group(sdnode(lhs, not d), sdnode(rhs, not d)))

    class MaterialBiconditionalUndesignated(System.OperatorNodeRule):
        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode(lhs, d), sdnode(~lhs, d)),
                group(sdnode(rhs, d), sdnode(~rhs, d)),
                group(sdnode(lhs, not d), sdnode(~rhs, not d)),
                group(sdnode(~lhs, not d), sdnode(rhs, not d)))

    class MaterialBiconditionalNegatedUndesignated(System.OperatorNodeRule):

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode(lhs, d), sdnode(~lhs, d)),
                group(sdnode(rhs, d), sdnode(~rhs, d)),
                group(sdnode(~lhs, not d), sdnode(~rhs, not d)),
                group(sdnode(lhs, not d), sdnode(rhs, not d)))

    groups = (
        group(
            FDE.Rules.AssertionDesignated,
            AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,
            FDE.Rules.ConjunctionDesignated,
            FDE.Rules.DisjunctionNegatedDesignated,
            ConditionalNegatedDesignated,
            ConditionalUndesignated,
            FDE.Rules.ExistentialNegatedDesignated,
            FDE.Rules.ExistentialNegatedUndesignated,
            FDE.Rules.UniversalNegatedDesignated,
            FDE.Rules.UniversalNegatedUndesignated,
            FDE.Rules.DoubleNegationDesignated,
            FDE.Rules.DoubleNegationUndesignated,
            # reduction rules (thus, non-branching)
            K3W.Rules.MaterialConditionalDesignated,
            K3W.Rules.MaterialConditionalUndesignated,
            K3W.Rules.MaterialConditionalNegatedDesignated,
            K3W.Rules.MaterialConditionalNegatedUndesignated,
            ConditionalDesignated,
            ConditionalNegatedUndesignated,
            K3W.Rules.MaterialBiconditionalDesignated,
            # K3W.Rules.MaterialBiconditionalUndesignated,
            K3W.Rules.MaterialBiconditionalNegatedDesignated,
            # K3W.Rules.MaterialBiconditionalNegatedUndesignated,
            BiconditionalDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedDesignated,
            ),
        group(
            # two-branching rules
            FDE.Rules.ConjunctionUndesignated,
            BiconditionalNegatedUndesignated,
            ),
        group(
            # three-branching rules
            K3W.Rules.DisjunctionDesignated,
            K3W.Rules.DisjunctionUndesignated,
            K3W.Rules.ConjunctionNegatedDesignated,
            K3W.Rules.ConjunctionNegatedUndesignated,
            # (formerly) four-branching rules
            K3W.Rules.DisjunctionNegatedUndesignated),
        group(
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedUndesignated),
        group(
            FDE.Rules.ExistentialDesignated,
            FDE.Rules.ExistentialUndesignated),
        group(
            FDE.Rules.UniversalDesignated,
            FDE.Rules.UniversalUndesignated))

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(4), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'