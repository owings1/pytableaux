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
from . import b3e as B3E
from . import k3 as K3
from . import l3 as L3


class Meta(L3.Meta, B3E.Meta):
    name = 'GO'
    title = 'Gappy Object Logic'
    description = (
        'Three-valued logic (T, F, N) with '
        'classical-like binary operators')
    category_order = 13

class Model(K3.Model):

    class TruthFunction(K3.Model.TruthFunction):

        Assertion = B3E.Model.TruthFunction.Assertion

        def Disjunction(self, *args):
            return max(map(self.Assertion, args))

        def Conjunction(self, *args):
            return min(map(self.Assertion, args))

        def Conditional(self, a, b):
            if a == b:
                return self.values.T
            return self.MaterialConditional(a, b)

    def unquantify_values(self, s, w, /):
        return map(self.truth_function.Assertion, super().unquantify_values(s, w))

class System(K3.System): pass

class Rules(K3.Rules):

    class ConjunctionNegatedDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                sdwgroup((s.lhs, not d, w)),
                sdwgroup((s.rhs, not d, w)))

    class MaterialConditionalNegatedDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(sdwgroup((~s.lhs, not d, w), (s.rhs, not d, w)))

    class MaterialBiconditionalNegatedDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                sdwgroup((~s.lhs, not d, w), ( s.rhs, not d, w)),
                sdwgroup(( s.lhs, not d, w), (~s.rhs, not d, w)))

    class ConditionalNegatedDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                sdwgroup(( s.lhs, d, w), (s.rhs, not d, w)),
                sdwgroup((~s.lhs, not d, w), (~s.rhs, d, w)))

    class BiconditionalDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            convert = self.operator.other
            yield adds(sdwgroup(
                (convert(s.operands), d, w),
                (convert(reversed(s)), d, w)))

    class BiconditionalNegatedDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            convert = self.operator.other
            yield adds(
                sdwgroup((~convert(s.operands), d, w)),
                sdwgroup((~convert(reversed(s)), d, w)))

    class ExistentialNegatedDesignated(rules.QuantifierNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            v, si = s[1:]
            sq = self.quantifier.other(v, ~si | ~(si | ~si))
            yield adds(sdwgroup((sq, d, w)))

    class UniversalNegatedDesignated(rules.QuantifierSkinnyRule):

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = branch.new_constant() >> s
            d = self.designation
            w = node.get('world')
            yield adds(
                sdwgroup((self.quantifier.other(v, ~si), d, w)),
                sdwgroup((r, not d, w), (~r, not d, w)))

    class DisjunctionNegatedDesignated(rules.FlippingOperandsRule): pass

    class ConjunctionUndesignated(rules.NegatingFlippingRule): pass
    class DisjunctionUndesignated(rules.NegatingFlippingRule): pass
    class MaterialConditionalUndesignated(rules.NegatingFlippingRule): pass
    class MaterialBiconditionalUndesignated(rules.NegatingFlippingRule): pass
    class ConditionalUndesignated(rules.NegatingFlippingRule): pass
    class BiconditionalUndesignated(rules.NegatingFlippingRule): pass
    class ExistentialUndesignated(rules.NegatingFlippingRule): pass
    class UniversalUndesignated(rules.NegatingFlippingRule): pass

    class ConjunctionNegatedUndesignated(rules.FlippingRule): pass
    class DisjunctionNegatedUndesignated(rules.FlippingRule): pass
    class MaterialConditionalNegatedUndesignated(rules.FlippingRule): pass
    class MaterialBiconditionalNegatedUndesignated(rules.FlippingRule): pass
    class ConditionalNegatedUndesignated(rules.FlippingRule): pass
    class BiconditionalNegatedUndesignated(rules.FlippingRule): pass
    class ExistentialNegatedUndesignated(rules.FlippingRule): pass
    class UniversalNegatedUndesignated(rules.FlippingRule): pass

    AssertionNegatedDesignated = B3E.Rules.AssertionNegatedDesignated
    AssertionNegatedUndesignated = B3E.Rules.AssertionNegatedUndesignated
    ConditionalDesignated = L3.Rules.ConditionalDesignated

    nonbranching_groups = group(
        group(
            K3.Rules.DoubleNegationDesignated,
            K3.Rules.DoubleNegationUndesignated,
            K3.Rules.AssertionDesignated,
            K3.Rules.AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,
            K3.Rules.ConjunctionDesignated,
            ConjunctionUndesignated,
            ConjunctionNegatedUndesignated,
            DisjunctionNegatedDesignated,
            DisjunctionUndesignated,
            DisjunctionNegatedUndesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalUndesignated,
            MaterialConditionalNegatedUndesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedUndesignated,
            ConditionalUndesignated,
            ConditionalNegatedUndesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated,
            BiconditionalDesignated,
            ExistentialNegatedDesignated,
            ExistentialUndesignated,
            ExistentialNegatedUndesignated,
            UniversalUndesignated,
            UniversalNegatedUndesignated))

    branching_groups = group(
        group(
            K3.Rules.DisjunctionDesignated,
            ConjunctionNegatedDesignated,
            K3.Rules.MaterialConditionalDesignated,
            K3.Rules.MaterialBiconditionalDesignated,
            MaterialBiconditionalNegatedDesignated,
            ConditionalDesignated,
            ConditionalNegatedDesignated,
            BiconditionalNegatedDesignated))

    unquantifying_groups = (
        group(K3.Rules.UniversalDesignated),
        group(K3.Rules.ExistentialDesignated),
        # existential + branching
        group(UniversalNegatedDesignated))

    groups = (
        *nonbranching_groups,
        *branching_groups,
        *unquantifying_groups)
