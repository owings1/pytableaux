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
from . import lp as LP
from . import mh as MH

class Meta(LP.Meta):
    name = 'NH'
    title = 'Paraconsistent Hybrid Logic'
    description = (
        'Three-valued logic (True, False, Both) with non-standard conjunction, '
        'and a classical-like conditional')
    category_order = 12
    native_operators = MH.Meta.native_operators

class Model(LP.Model):

    class TruthFunction(LP.Model.TruthFunction):

        def Conjunction(self, a, b):
            if a == b == self.values.B:
                return self.values.T
            return super().Conjunction(a, b)

        def Conditional(self, a, b):
            if a != self.values.F and b == self.values.F:
                return self.values.F
            return self.values.T

    def value_of_quantified(self, s, w, /):
        self._check_finished()
        q = s.quantifier
        if q is not q.Universal:
            return super().value_of_quantified(s, w)
        valset = set(self.unquantify_values(s, w))
        values = self.values
        if values.F in valset:
            return values.F
        if len(valset) > 1:
            return values.B
        return values.T


class System(LP.System): pass

class Rules(LP.Rules):

    class ConjunctionNegatedDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup((lhs, False, w)),
                sdwgroup((rhs, False, w)),
                sdwgroup(
                    (lhs, True, w),
                    (~lhs, True, w),
                    (~rhs, False, w)),
                sdwgroup(
                    (rhs, True, w),
                    (~rhs, True, w),
                    (~lhs, False, w)))

    class ConjunctionNegatedUndesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup(
                    (~lhs, False, w),
                    (~rhs, False, w)),
                sdwgroup(
                    ( lhs, True, w),
                    (~lhs, True, w),
                    ( rhs, True, w),
                    (~rhs, True, w)))

    class MaterialConditionalNegatedDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(sdwgroup((s.lhs, d, w), (~s.rhs, d, w)))

    class MaterialConditionalNegatedUndesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                sdwgroup((s.lhs, d, w)),
                sdwgroup((~s.rhs, d, w)))

    class UniversalNegatedDesignated(rules.QuantifierSkinnyRule):
        pass
        """
                  ¬∀xFx +
               ______|_______
              |              |
             Fa -          ¬Fa -
                        ∃x(Fx ∧ ¬Fx) +

                          
        if ¬∀xFx +, then either
            - At least one is F, or
            - At least one is B and at least one is T
        """

        def _get_node_targets(self, node, branch, /):
            c = branch.new_constant()
            s = self.sentence(node)
            v = s.variable
            sc = c >> s
            q = self.quantifier
            si = s.sentence
            w = node.get('world')
            d = self.designation
            yield adds(
                sdwgroup((sc, not d, w)),
                sdwgroup((~sc, not d, w), (q.other(v, si & ~si), d, w)))

    class UniversalNegatedUndesignated(rules.QuantifierNodeRule):
        pass
        """
                  ¬∀xFx -
               ______|_______
              |              |
           ∃x¬Fx -      ∀x(Fx ∧ ¬Fx) +


        if ¬∀xFx -, then either
            - All are T, or
            - All are B
        """
        def _get_sdw_targets(self, s, d, w, /):
            q = self.quantifier
            v = s.variable
            s = s.sentence
            yield adds(
                sdwgroup((q.other(v, ~s), d, w)),
                sdwgroup((q(v, s & ~s), not d, w)))

    MaterialBiconditionalDesignated = MH.Rules.MaterialBiconditionalDesignated
    MaterialBiconditionalNegatedDesignated = MH.Rules.MaterialBiconditionalNegatedDesignated
    MaterialBiconditionalUndesignated = MH.Rules.MaterialBiconditionalUndesignated
    MaterialBiconditionalNegatedUndesignated = MH.Rules.MaterialBiconditionalNegatedUndesignated
    ConditionalUndesignated = MH.Rules.ConditionalUndesignated
    ConditionalNegatedDesignated = MH.Rules.ConditionalNegatedDesignated
    BiconditionalDesignated = MH.Rules.BiconditionalDesignated
    BiconditionalNegatedDesignated = MH.Rules.BiconditionalNegatedDesignated
    BiconditionalUndesignated = MH.Rules.BiconditionalUndesignated
    BiconditionalNegatedUndesignated = MH.Rules.BiconditionalNegatedUndesignated
    ConditionalDesignated = MH.Rules.ConditionalDesignated
    ConditionalNegatedUndesignated = MH.Rules.ConditionalNegatedUndesignated

    nonbranching_groups = group(
        group(
            LP.Rules.AssertionDesignated,
            LP.Rules.AssertionUndesignated,
            LP.Rules.AssertionNegatedDesignated,
            LP.Rules.AssertionNegatedUndesignated,
            LP.Rules.ConjunctionDesignated,
            LP.Rules.DisjunctionUndesignated,
            LP.Rules.DisjunctionNegatedDesignated,
            MaterialConditionalNegatedDesignated,
            LP.Rules.MaterialConditionalUndesignated,
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
            LP.Rules.DoubleNegationDesignated,
            LP.Rules.DoubleNegationUndesignated))

    branching_groups = group(
        group(
            LP.Rules.ConjunctionUndesignated,
            ConjunctionNegatedUndesignated,
            LP.Rules.DisjunctionDesignated,
            LP.Rules.DisjunctionNegatedUndesignated,
            LP.Rules.MaterialConditionalDesignated,
            MaterialConditionalNegatedUndesignated,
            ConditionalDesignated,
            ConditionalNegatedUndesignated,
            UniversalNegatedUndesignated),
        # 3-branching rules.
        group(
            ConjunctionNegatedDesignated))

    unquantifying_groups = group(
        group(
            LP.Rules.UniversalDesignated,
            LP.Rules.ExistentialNegatedDesignated,
            LP.Rules.ExistentialUndesignated),
        group(
            LP.Rules.ExistentialDesignated,
            LP.Rules.ExistentialNegatedUndesignated,
            LP.Rules.UniversalUndesignated),
        group(
            UniversalNegatedDesignated))

    groups = (
        *nonbranching_groups,
        *branching_groups,
        *unquantifying_groups)
