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


class Meta(K3.Meta):
    name = 'MH'
    title = 'Paracomplete Hybrid Logic'
    description = (
        'Three-valued logic (T, F, N) with non-standard disjunction, '
        'and a classical-like conditional')
    category_order = K3.Meta.category_order + 8
    native_operators = [Operator.Conditional, Operator.Biconditional]

class Model(K3.Model):

    class TruthFunction(K3.Model.TruthFunction):

        def Disjunction(self, a, b):
            if a == b == self.values.N:
                return self.values.F
            return super().Disjunction(a, b)

        def Conditional(self, a, b):
            if a == self.values.T and b != self.values.T:
                return self.values.F
            return self.values.T

    def value_of_quantified(self, s, w, /):
        q = s.quantifier
        if q is not q.Existential:
            return super().value_of_quantified(s, w)
        valset = set(self.unquantify_values(s, w))
        values = self.values
        if values.T in valset:
            return values.T
        if len(valset) > 1:
            return values.N
        return values.F

class System(K3.System): pass

class Rules(K3.Rules):

    class DisjunctionNegatedDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup(
                    ( lhs, not d, w),
                    (~lhs, not d, w),
                    ( rhs, not d, w),
                    (~rhs, not d, w)),
                sdwgroup(
                    (~lhs, d, w),
                    (~rhs, d, w)))

    class DisjunctionNegatedUndesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup((lhs, not d, w)),
                sdwgroup((rhs, not d, w)),
                sdwgroup(
                    (lhs, d, w),
                    (~lhs, d, w),
                    (~rhs, not d, w)),
                sdwgroup(
                    (rhs, d, w),
                    (~rhs, d, w),
                    (~lhs, not d, w)))

    class MaterialConditionalNegatedDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup(
                    ( lhs, not d, w),
                    (~lhs, not d, w),
                    ( rhs, not d, w),
                    (~rhs, not d, w)),
                sdwgroup(
                    (lhs, d, w),
                    (~rhs, d, w)))

    class MaterialConditionalNegatedUndesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup((~lhs, not d, w)),
                sdwgroup((rhs, not d, w)),
                sdwgroup(
                    (lhs, d, w),
                    (~lhs, d, w),
                    (~rhs, not d, w)),
                sdwgroup(
                    (rhs, d, w),
                    (~rhs, d, w),
                    (lhs, not d, w)))

    class ConditionalDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            # Keep designation fixed for inheritance below.
            yield adds(
                sdwgroup((s.lhs, False, w)),
                sdwgroup((s.rhs, True, w)))

    class ConditionalNegatedDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            # Keep designation fixed for inheritance below.
            yield adds(sdwgroup((s.lhs, True, w), (s.rhs, False, w)))

    class ExistentialNegatedDesignated(rules.QuantifierNodeRule):
        pass
        """
                  ¬∃xFx +
               ______|_______
              |              |
            ∀x¬Fx +    ∀x¬(Fx ∨ ¬Fx) +
        """
        def _get_sdw_targets(self, s, d, w, /):
            con = s.connective.other
            v = s.variable
            inner = s.inner
            joined = inner | ~inner
            yield adds(
                sdwgroup((con(v, ~inner), d, w)),
                sdwgroup((con(v, ~joined), d, w)))
    
    class ExistentialNegatedUndesignated(rules.ExistentialQuantifierRule):
        pass
        """
                  ¬∃xFx -
               ______|_______
              |              |
             Fa +           ¬Fa +
                       ∃x¬(Fx ∨ ¬Fx) +
        """

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            con = s.connective
            v = s.variable
            inner = s.inner
            resolved = branch.new_constant() >> s
            joined = inner | ~inner
            reduced = con(v, ~joined)
            w = node.get('world')
            d = self.designation
            if d is not None:
                d = not d
            yield adds(
                sdwgroup((resolved, d, w)),
                sdwgroup((~resolved, d, w), (reduced, d, w)))

    class MaterialBiconditionalDesignated(rules.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedDesignated(rules.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalUndesignated(rules.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedUndesignated(rules.MaterialConditionalConjunctsReducingRule): pass
    class ConditionalUndesignated(ConditionalNegatedDesignated): pass
    class ConditionalNegatedUndesignated(ConditionalDesignated): pass
    class BiconditionalDesignated(rules.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedDesignated(rules.ConditionalConjunctsReducingRule): pass
    class BiconditionalUndesignated(rules.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedUndesignated(rules.ConditionalConjunctsReducingRule): pass

    nonbranching_groups = group(
        group(
            K3.Rules.AssertionDesignated,
            K3.Rules.AssertionUndesignated,
            K3.Rules.AssertionNegatedDesignated,
            K3.Rules.AssertionNegatedUndesignated,
            K3.Rules.ConjunctionDesignated,
            K3.Rules.ConjunctionNegatedUndesignated,
            K3.Rules.DisjunctionUndesignated,
            K3.Rules.MaterialConditionalUndesignated,
            MaterialBiconditionalDesignated,
            MaterialBiconditionalNegatedDesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedUndesignated,
            ConditionalUndesignated,
            ConditionalNegatedDesignated,
            BiconditionalDesignated,
            BiconditionalNegatedDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated,
            K3.Rules.DoubleNegationDesignated,
            K3.Rules.DoubleNegationUndesignated))

    branching_groups = group(
        group(
            K3.Rules.ConjunctionUndesignated,
            K3.Rules.ConjunctionNegatedDesignated,
            K3.Rules.DisjunctionDesignated,
            DisjunctionNegatedDesignated,
            K3.Rules.MaterialConditionalDesignated,
            MaterialConditionalNegatedDesignated,
            ConditionalDesignated,
            ConditionalNegatedUndesignated,
            ExistentialNegatedDesignated),
        # 3-branching rules.
        group(
            MaterialConditionalNegatedUndesignated,
            DisjunctionNegatedUndesignated))

    unquantifying_groups = group(
        group(
            K3.Rules.ExistentialDesignated,
            K3.Rules.UniversalNegatedDesignated,
            K3.Rules.UniversalUndesignated),
        group(
            ExistentialNegatedUndesignated),
        group(
            K3.Rules.UniversalDesignated,
            K3.Rules.UniversalNegatedUndesignated,
            K3.Rules.ExistentialUndesignated))

    groups = (
        *nonbranching_groups,
        *branching_groups,
        *unquantifying_groups)
