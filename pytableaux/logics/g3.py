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

from ..proof import adds, rules, sdwgroup
from ..tools import group
from . import k3 as K3
from . import l3 as L3


class Meta(L3.Meta):
    name = 'G3'
    title = 'Gödel 3-valued Logic'
    description = (
        'Three-valued logic (T, F, N) with alternate '
        'negation and conditional')
    category_order = L3.Meta.category_order + 5

class Model(K3.Model):

    class TruthFunction(L3.Model.TruthFunction):

        def Negation(self, a):
            if a == 'N':
                return self.values.F
            return super().Negation(a)

class System(K3.System): pass

class Rules(K3.Rules):

    class ConditionalNegatedDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup(
                    ( lhs, d, w),
                    (~rhs, d, w)),
                sdwgroup(
                    ( lhs, not d, w),
                    (~lhs, not d, w),
                    (~rhs, d, w)))

    class ConditionalNegatedUndesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                sdwgroup((~s.lhs, not d, w)),
                sdwgroup((~s.rhs, d, w)))

    class DoubleNegationDesignated(rules.FlippingRule): pass
    class DoubleNegationUndesignated(rules.FlippingRule): pass
    class BiconditionalDesignated(rules.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedDesignated(rules.ConditionalConjunctsReducingRule): pass
    class BiconditionalUndesignated(rules.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedUndesignated(rules.ConditionalConjunctsReducingRule): pass
    class MaterialConditionalDesignated(rules.MaterialConditionalReducingRule): pass
    class MaterialConditionalNegatedDesignated(rules.MaterialConditionalReducingRule): pass
    class MaterialConditionalUndesignated(rules.MaterialConditionalReducingRule): pass
    class MaterialConditionalNegatedUndesignated(rules.MaterialConditionalReducingRule): pass
    class MaterialBiconditionalDesignated(rules.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedDesignated(rules.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalUndesignated(rules.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedUndesignated(rules.MaterialConditionalConjunctsReducingRule): pass

    ConditionalDesignated = L3.Rules.ConditionalDesignated
    ConditionalUndesignated = L3.Rules.ConditionalUndesignated

    nonbranching_groups = group(
        group(
            # non-branching rules
            K3.Rules.AssertionDesignated,
            K3.Rules.AssertionUndesignated,
            K3.Rules.AssertionNegatedDesignated,
            K3.Rules.AssertionNegatedUndesignated,
            K3.Rules.ConjunctionDesignated,
            K3.Rules.ConjunctionNegatedUndesignated,
            K3.Rules.DisjunctionNegatedDesignated,
            K3.Rules.DisjunctionUndesignated,
            DoubleNegationDesignated,
            DoubleNegationUndesignated,
            # reduction rules
            MaterialConditionalNegatedDesignated,
            MaterialConditionalUndesignated,
            MaterialConditionalDesignated,
            MaterialConditionalNegatedUndesignated,
            MaterialBiconditionalDesignated,
            MaterialBiconditionalNegatedDesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedUndesignated,
            BiconditionalDesignated,
            BiconditionalNegatedUndesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedDesignated))

    branching_groups = group(
        group(
            K3.Rules.ConjunctionNegatedDesignated,
            K3.Rules.ConjunctionUndesignated,
            K3.Rules.DisjunctionDesignated,
            K3.Rules.DisjunctionNegatedUndesignated,
            ConditionalDesignated,
            ConditionalUndesignated,
            ConditionalNegatedUndesignated,
            ConditionalNegatedDesignated))

    groups = (
        *nonbranching_groups,
        *branching_groups,
        *K3.Rules.unquantifying_groups)
