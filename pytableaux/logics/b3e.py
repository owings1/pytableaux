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
from . import k3 as K3
from . import k3w as K3W


class Meta(K3.Meta):
    name = 'B3E'
    title = 'Bochvar 3 External Logic'
    description = 'Three-valued logic (True, False, Neither) with assertion operator'
    category_order = 9
    native_operators = [Operator.Assertion]

class Model(K3.Model):

    class TruthFunction(K3W.Model.TruthFunction):

        def Assertion(self, a: Meta.values) -> Meta.values:
            return self.values[a // 1]

        def Conditional(self, a: Meta.values, b: Meta.values) -> Meta.values:
            return super().Conditional(*map(self.Assertion, (a, b)))

class System(K3.System): pass

class Rules(K3W.Rules):

    class MaterialBiconditionalUndesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup((lhs, d, w), (~lhs, d, w)),
                sdwgroup((rhs, d, w), (~rhs, d, w)),
                sdwgroup((lhs, not d, w), (~rhs, not d, w)),
                sdwgroup((~lhs, not d, w), (rhs, not d, w)))

    class MaterialBiconditionalNegatedUndesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup((lhs, d, w), (~lhs, d, w)),
                sdwgroup((rhs, d, w), (~rhs, d, w)),
                sdwgroup((~lhs, not d, w), (~rhs, not d, w)),
                sdwgroup((lhs, not d, w), (rhs, not d, w)))

    class ConditionalDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            sn = ~+s.lhs | +s.rhs
            # keep negated neutral for inheritance below
            if self.negated:
                sn = ~sn
            # keep designation neutral for inheritance below
            yield adds(sdwgroup((sn, d, w)))

    class ConditionalNegatedDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            # Keep designation fixed for inheritance below.
            yield adds(sdwgroup(
                (s.lhs, True, w),
                (s.rhs, False, w)))

    class BiconditionalDesignated(rules.OperatorNodeRule):

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

    class BiconditionalNegatedUndesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup((lhs, d, w), (rhs, d, w)),
                sdwgroup((lhs, not d, w), (rhs, not d, w)))


    class AssertionNegatedDesignated(rules.FlippingOperandsRule): pass
    class AssertionNegatedUndesignated(rules.FlippingOperandsRule): pass
    class ConditionalUndesignated(ConditionalNegatedDesignated): pass
    class ConditionalNegatedUndesignated(ConditionalDesignated): pass
    class BiconditionalNegatedDesignated(BiconditionalDesignated): pass
    class BiconditionalUndesignated(BiconditionalDesignated): pass

    nonbranching_groups = group(
        group(
            K3.Rules.AssertionDesignated,
            K3.Rules.AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,
            K3.Rules.ConjunctionDesignated,
            K3.Rules.DisjunctionNegatedDesignated,
            ConditionalNegatedDesignated,
            ConditionalUndesignated,
            K3.Rules.DoubleNegationDesignated,
            K3.Rules.DoubleNegationUndesignated,
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
            BiconditionalNegatedDesignated))

    branching_groups = group(
        group(
            # two-branching rules
            K3.Rules.ConjunctionUndesignated,
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
            MaterialBiconditionalNegatedUndesignated))
    
    groups = (
        *nonbranching_groups,
        *branching_groups,
        *K3.Rules.unquantifying_groups)

    @staticmethod
    def _check_groups():
        cls = __class__
        for branching, group in zip(range(4), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'
