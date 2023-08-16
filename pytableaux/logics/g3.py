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
from ..proof import adds, sdnode
from ..tools import group
from . import fde as FDE
from . import k3 as K3
from . import l3 as L3

class Meta(L3.Meta):
    name = 'G3'
    title = 'Gödel 3-valued Logic'
    description = 'Three-valued logic (T, F, N) with alternate negation and conditional'
    category_order = 90

class Model(L3.Model):

    def truth_function(self, operator, a, b = None, /):
        if operator == Operator.Negation:
            if a == self.Value.N:
                return self.Value.F
        return super().truth_function(operator, a, b)

class System(K3.System):

    branchables = FDE.System.branchables | {
        Operator.Conditional: ((1, 1), (1, 1)),
        Operator.Biconditional: ((0, 0), (0, 0))}


class Rules(L3.Rules):

    class DoubleNegationDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated double-negation node `n` on a branch `b`,
        add an undesignated node with the negatum of `n`. Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s, not d)))

    class DoubleNegationUndesignated(DoubleNegationDesignated):
        """
        From an unticked, undesignated double-negation node `n` on a branch `b`,
        add a designated node with the negatum of `n`. Then tick `n`.
        """

    class ConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated conditional node `n` on a branch
        `b`, make two branches `b'` and `b''` from `b`. On `b'` add two designated
        nodes, one with the antecedent, and one with the negation of the consequent.
        On `b''` add two undesignated nodes, one with the antecedent, and one with
        the negation of the antecedent, and one designated node with the negation
        of the consequent. Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(
                    sdnode( lhs, d),
                    sdnode(~rhs, d)),
                group(
                    sdnode( lhs, not d),
                    sdnode(~lhs, not d),
                    sdnode(~rhs, d)))
    
    class ConditionalNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, negated conditional node `n` on a branch
        `b`, make two branches `b'` and `b''` from `b`. On `b'` add a designated
        node with the negation of the antecedent. On `b''` add an undesignated
        node with the negation of the consequent. Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(~s.lhs, not d)),
                group(sdnode(~s.rhs, d)))

    class BiconditionalDesignated(FDE.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedDesignated(FDE.ConditionalConjunctsReducingRule): pass
    class BiconditionalUndesignated(FDE.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedUndesignated(FDE.ConditionalConjunctsReducingRule): pass

    groups = (
        (
            # non-branching rules
            FDE.Rules.AssertionDesignated,
            FDE.Rules.AssertionUndesignated,
            FDE.Rules.AssertionNegatedDesignated,
            FDE.Rules.AssertionNegatedUndesignated,
            FDE.Rules.ConjunctionDesignated,
            FDE.Rules.DisjunctionNegatedDesignated,
            FDE.Rules.DisjunctionUndesignated,
            FDE.Rules.DisjunctionNegatedUndesignated,
            FDE.Rules.MaterialConditionalNegatedDesignated,
            FDE.Rules.MaterialConditionalUndesignated,

            BiconditionalDesignated,
            BiconditionalNegatedUndesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedDesignated,

            FDE.Rules.ExistentialNegatedDesignated,
            FDE.Rules.ExistentialNegatedUndesignated,
            FDE.Rules.UniversalNegatedDesignated,
            FDE.Rules.UniversalNegatedUndesignated,

            DoubleNegationDesignated,
            DoubleNegationUndesignated,
        ),
        (
            # branching rules
            FDE.Rules.ConjunctionNegatedDesignated,
            FDE.Rules.ConjunctionUndesignated,
            FDE.Rules.ConjunctionNegatedUndesignated,
            FDE.Rules.DisjunctionDesignated,
            FDE.Rules.MaterialConditionalDesignated,
            FDE.Rules.MaterialConditionalNegatedUndesignated,
            FDE.Rules.MaterialBiconditionalDesignated,
            FDE.Rules.MaterialBiconditionalNegatedDesignated,
            FDE.Rules.MaterialBiconditionalUndesignated,
            FDE.Rules.MaterialBiconditionalNegatedUndesignated,

            L3.Rules.ConditionalDesignated,
            L3.Rules.ConditionalUndesignated,
            ConditionalNegatedUndesignated,
            ConditionalNegatedDesignated,
        ),
        (
            FDE.Rules.ExistentialDesignated,
            FDE.Rules.ExistentialUndesignated,
        ),
        (
            FDE.Rules.UniversalDesignated,
            FDE.Rules.UniversalUndesignated,
        ),
    )
