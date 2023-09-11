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


class Meta(K3.Meta):
    name = 'K3W'
    title = 'Weak Kleene Logic'
    description = 'Three-valued logic with values T, F, and N'
    category_order = 7

class Model(K3.Model):

    class TruthFunction(K3.Model.TruthFunction):

        def Conjunction(self, a: Meta.values, b: Meta.values) -> Meta.values:
            if a == 'N' or b == 'N':
                return self.values.N
            return super().Conjunction(a, b)

        def Disjunction(self, a: Meta.values, b: Meta.values) -> Meta.values:
            if a == 'N' or b == 'N':
                return self.values.N
            return super().Disjunction(a, b)

class System(K3.System): pass

class Rules(K3.Rules):

    class ConjunctionNegatedDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup(( lhs, True, w), (~rhs, True, w)),
                sdwgroup((~lhs, True, w), ( rhs, True, w)),
                sdwgroup((~lhs, True, w), (~rhs, True, w)))

    class ConjunctionNegatedUndesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup((lhs, False, w), (~lhs, False, w)),
                sdwgroup((rhs, False, w), (~rhs, False, w)),
                sdwgroup((lhs, True, w),  ( rhs, True, w)))

    class DisjunctionDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup(( lhs, True, w), (~rhs, True, w)),
                sdwgroup((~lhs, True, w), ( rhs, True, w)),
                sdwgroup(( lhs, True, w), ( rhs, True, w)))
            
    class DisjunctionUndesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup(( lhs, False, w), (~lhs, False, w)),
                sdwgroup(( rhs, False, w), (~rhs, False, w)),
                sdwgroup((~lhs, True, w),  (~rhs, True, w)))

    class DisjunctionNegatedUndesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                sdwgroup((s, True, w)),
                sdwgroup((s.lhs, False, w), (~s.lhs, False, w)),
                sdwgroup((s.rhs, False, w), (~s.rhs, False, w)))

    class MaterialConditionalDesignated(rules.MaterialConditionalReducingRule): pass
    class MaterialConditionalNegatedDesignated(rules.MaterialConditionalReducingRule): pass
    class MaterialConditionalUndesignated(rules.MaterialConditionalReducingRule): pass
    class MaterialConditionalNegatedUndesignated(rules.MaterialConditionalReducingRule): pass
    class MaterialBiconditionalDesignated(rules.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedDesignated(rules.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalUndesignated(rules.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedUndesignated(rules.MaterialConditionalConjunctsReducingRule): pass
    class ConditionalDesignated(rules.MaterialConditionalReducingRule): pass
    class ConditionalNegatedDesignated(rules.MaterialConditionalReducingRule): pass
    class ConditionalUndesignated(rules.MaterialConditionalReducingRule): pass
    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated): pass
    class BiconditionalDesignated(rules.MaterialConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedDesignated(rules.MaterialConditionalConjunctsReducingRule): pass
    class BiconditionalUndesignated(rules.MaterialConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedUndesignated(rules.MaterialConditionalConjunctsReducingRule): pass

    nonbranching_groups = group(
        group(
            K3.Rules.AssertionDesignated,
            K3.Rules.AssertionUndesignated,
            K3.Rules.AssertionNegatedDesignated,
            K3.Rules.AssertionNegatedUndesignated,
            K3.Rules.ConjunctionDesignated, 
            K3.Rules.DisjunctionNegatedDesignated,
            K3.Rules.DoubleNegationDesignated,
            K3.Rules.DoubleNegationUndesignated,
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
            BiconditionalNegatedUndesignated))

    branching_groups = group(
        group(
            # two-branching rules
            K3.Rules.ConjunctionUndesignated),
        group(
            # three-branching rules
            DisjunctionDesignated,
            DisjunctionUndesignated,
            ConjunctionNegatedDesignated,
            ConjunctionNegatedUndesignated,
            # five-branching rules (formerly)
            DisjunctionNegatedUndesignated))

    groups = (
        *nonbranching_groups,
        *branching_groups,
        *K3.Rules.unquantifying_groups)
