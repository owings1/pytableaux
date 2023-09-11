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

from ..proof import adds, rules, sdnode
from ..tools import group
from . import lp as LP
from . import mh as MH

class Meta(LP.Meta):
    name = 'NH'
    title = 'Paraconsistent Hybrid Logic'
    quantified = False
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

class System(LP.System): pass

class Rules(LP.Rules):

    class ConjunctionNegatedDesignated(rules.OperatorNodeRule):

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode(lhs, False)),
                group(sdnode(rhs, False)),
                group(
                    sdnode(lhs, True),
                    sdnode(~lhs, True),
                    sdnode(~rhs, False)),
                group(
                    sdnode(rhs, True),
                    sdnode(~rhs, True),
                    sdnode(~lhs, False)))

    class ConjunctionNegatedUndesignated(rules.OperatorNodeRule):

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(
                    sdnode(~lhs, False),
                    sdnode(~rhs, False)),
                group(
                    sdnode( lhs, True),
                    sdnode(~lhs, True),
                    sdnode( rhs, True),
                    sdnode(~rhs, True)))

    class MaterialConditionalNegatedDesignated(rules.OperatorNodeRule):

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s.lhs, d), sdnode(~s.rhs, d)))

    class MaterialConditionalNegatedUndesignated(rules.OperatorNodeRule):

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(s.lhs, d)),
                group(sdnode(~s.rhs, d)))

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
            ConditionalNegatedUndesignated),
        # 3-branching rules.
        group(
            ConjunctionNegatedDesignated))

    unquantifying_groups = ()

    groups = (
        *nonbranching_groups,
        *branching_groups)
