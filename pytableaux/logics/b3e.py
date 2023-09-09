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
from ..proof import adds, sdwgroup
from ..tools import group
from . import fde as FDE
from . import k3 as K3
from . import k3w as K3W
from . import LogicType


class Meta(K3.Meta):
    name = 'B3E'
    title = 'Bochvar 3 External Logic'
    description = 'Three-valued logic (True, False, Neither) with assertion operator'
    category_order = 9
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

    class AssertionNegatedDesignated(System.FlippingOperandsRule): pass
    class AssertionUndesignated(System.OperandsRule): pass
    class AssertionNegatedUndesignated(System.FlippingOperandsRule): pass

    class MaterialBiconditionalUndesignated(System.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup((lhs, d, w), (~lhs, d, w)),
                sdwgroup((rhs, d, w), (~rhs, d, w)),
                sdwgroup((lhs, not d, w), (~rhs, not d, w)),
                sdwgroup((~lhs, not d, w), (rhs, not d, w)))

    class MaterialBiconditionalNegatedUndesignated(System.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup((lhs, d, w), (~lhs, d, w)),
                sdwgroup((rhs, d, w), (~rhs, d, w)),
                sdwgroup((~lhs, not d, w), (~rhs, not d, w)),
                sdwgroup((lhs, not d, w), (rhs, not d, w)))

    class ConditionalDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*,
        add a designated node to *b* with a disjunction, where the
        first disjunction is the negation of the assertion of the antecedent,
        and the second disjunct is the assertion of the consequent. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            sn = ~+s.lhs | +s.rhs
            # keep negated neutral for inheritance below
            if self.negated:
                sn = ~sn
            # keep designation neutral for inheritance below
            yield adds(sdwgroup((sn, d, w)))

    class ConditionalNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated negated conditional node *n* on a branch *b*,
        add a designated node with the antecedent, and an undesigntated node
        with the consequent to *b*. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            # Keep designation fixed for inheritance below.
            yield adds(sdwgroup(
                (s.lhs, True, w),
                (s.rhs, False, w)))

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

        def _get_sdw_targets(self, s, d, w, /):
            lhsa = +s.lhs
            rhsa = +s.rhs
            sn1 = ~lhsa | rhsa
            sn2 = ~rhsa | lhsa
            # Keep negated neutral for inheritance below.
            if self.negated:
                sn1 = ~sn1
                sn2 = ~sn2
            # Keep designation neutral for inheritance below.
            yield adds(sdwgroup(
                (sn1, d, w),
                (sn2, d, w)))

    class BiconditionalNegatedDesignated(BiconditionalDesignated): pass
    class BiconditionalUndesignated(BiconditionalDesignated): pass

    class BiconditionalNegatedUndesignated(System.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup((lhs, d, w), (rhs, d, w)),
                sdwgroup((lhs, not d, w), (rhs, not d, w)))

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
            K3W.Rules.MaterialBiconditionalNegatedDesignated,
            BiconditionalDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedDesignated),
        group(
            # two-branching rules
            FDE.Rules.ConjunctionUndesignated,
            BiconditionalNegatedUndesignated),
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
        # quantifier rules
        *FDE.Rules.unquantifying_groups)

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(4), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'
