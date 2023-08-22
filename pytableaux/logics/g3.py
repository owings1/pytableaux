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

from ..proof import adds, sdnode
from ..tools import group
from . import fde as FDE
from . import k3 as K3
from . import l3 as L3
from . import LogicType

class Meta(L3.Meta):
    name = 'G3'
    title = 'Gödel 3-valued Logic'
    description = (
        'Three-valued logic (T, F, N) with alternate '
        'negation and conditional')
    category_order = 90

class Model(FDE.Model):

    class TruthFunction(L3.Model.TruthFunction):

        def Negation(self, a, /):
            if a == self.values.N:
                return self.values.F
            return super().Negation(a)

class System(FDE.System): pass

class Rules(LogicType.Rules):

    closure = K3.Rules.closure

    class DoubleNegationDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated double-negation node `n` on a branch `b`,
        add an undesignated node with the negatum of `n`. Then tick `n`.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s, not d)))

    class DoubleNegationUndesignated(DoubleNegationDesignated): pass

    class ConditionalNegatedDesignated(System.OperatorNodeRule):
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

    class ConditionalNegatedUndesignated(System.OperatorNodeRule):
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

    class BiconditionalDesignated(System.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedDesignated(System.ConditionalConjunctsReducingRule): pass
    class BiconditionalUndesignated(System.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedUndesignated(System.ConditionalConjunctsReducingRule): pass
    class MaterialConditionalDesignated(System.MaterialConditionalReducingRule): pass
    class MaterialConditionalNegatedDesignated(System.MaterialConditionalReducingRule): pass
    class MaterialConditionalUndesignated(System.MaterialConditionalReducingRule): pass
    class MaterialConditionalNegatedUndesignated(System.MaterialConditionalReducingRule): pass
    class MaterialBiconditionalDesignated(System.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedDesignated(System.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalUndesignated(System.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedUndesignated(System.MaterialConditionalConjunctsReducingRule): pass


    groups = (
        group(
            # non-branching rules
            FDE.Rules.AssertionDesignated,
            FDE.Rules.AssertionUndesignated,
            FDE.Rules.AssertionNegatedDesignated,
            FDE.Rules.AssertionNegatedUndesignated,
            FDE.Rules.ConjunctionDesignated,
            FDE.Rules.ConjunctionNegatedUndesignated,
            FDE.Rules.DisjunctionNegatedDesignated,
            FDE.Rules.DisjunctionUndesignated,

            FDE.Rules.ExistentialNegatedDesignated,
            FDE.Rules.ExistentialNegatedUndesignated,
            FDE.Rules.UniversalNegatedDesignated,
            FDE.Rules.UniversalNegatedUndesignated,

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
            BiconditionalNegatedDesignated),
        group(
            # branching rules
            FDE.Rules.ConjunctionNegatedDesignated,
            FDE.Rules.ConjunctionUndesignated,
            FDE.Rules.DisjunctionDesignated,
            FDE.Rules.DisjunctionNegatedUndesignated,

            L3.Rules.ConditionalDesignated,
            L3.Rules.ConditionalUndesignated,
            ConditionalNegatedUndesignated,
            ConditionalNegatedDesignated),
        group(
            FDE.Rules.ExistentialDesignated,
            FDE.Rules.ExistentialUndesignated),
        group(
            FDE.Rules.UniversalDesignated,
            FDE.Rules.UniversalUndesignated))

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(2), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'