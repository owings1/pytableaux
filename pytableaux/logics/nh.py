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
from . import lp as LP
from . import mh as MH
from . import LogicType

class Meta(LP.Meta):
    name = 'NH'
    title = 'Paraconsistent Hybrid Logic'
    quantified = False
    description = (
        'Three-valued logic (True, False, Both) with non-standard conjunction, '
        'and a classical-like conditional')
    category_order = 110
    native_operators = MH.Meta.native_operators

class Model(LP.Model):

    class TruthFunction(LP.Model.TruthFunction):

        def Conjunction(self, a, b):
            if a == self.values.B and b == self.values.B:
                return self.values.T
            return super().Conjunction(a, b)

        def Conditional(self, a, b):
            if a != self.values.F and b == self.values.F:
                return self.values.F
            return self.values.T

class System(FDE.System): pass

class Rules(LogicType.Rules):

    closure = LP.Rules.closure

    class ConjunctionNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked, negated, designated conjunction node *n* on a branch *b*,
        make four new branches from *b*: *b'*, *b''*, *b'''*, *b''''*. On *b'*, add
        an undesignated node with the first conjunct. On *b''*, add an undesignated
        node with the second conjunct.

        On *b'''*, add three nodes:

        - A designated node with the first conjunct.
        - A designated node with the negation of the first conjunct.
        - An undesignated node with the negation of the second conjunct.

        On *b''''*, add three nodes:

        - A designated node with the second conjunct.
        - A designated node with the negation of the second conjunct.
        - An undesignated node with the negation of the first conjunct.

        Then, tick *n*.
        """

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

    class ConjunctionNegatedUndesignated(System.OperatorNodeRule):
        """
        From an unticked, negated, undesignated conjunction node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'*, add two undesignated nodes,
        one for the negation of each conjunct. On *b''*, add four designated nodes, one
        for each of the conjuncts and its negation. Then tick *n*.
        """

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

    class MaterialConditionalNegatedDesignated(System.OperatorNodeRule):

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s.lhs, d), sdnode(~s.rhs, d)))

    class MaterialConditionalNegatedUndesignated(System.OperatorNodeRule):

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(s.lhs, d)),
                group(sdnode(~s.rhs, d)))

    groups = (
        # Non-branching rules.
        group(
            FDE.Rules.AssertionDesignated,
            FDE.Rules.AssertionUndesignated,
            FDE.Rules.AssertionNegatedDesignated,
            FDE.Rules.AssertionNegatedUndesignated,
            FDE.Rules.ConjunctionDesignated,
            FDE.Rules.DisjunctionUndesignated,
            FDE.Rules.DisjunctionNegatedDesignated,
            MaterialConditionalNegatedDesignated,
            FDE.Rules.MaterialConditionalUndesignated,
            MH.Rules.MaterialBiconditionalDesignated,
            MH.Rules.MaterialBiconditionalNegatedDesignated,
            MH.Rules.MaterialBiconditionalUndesignated,
            MH.Rules.MaterialBiconditionalNegatedUndesignated,
            MH.Rules.ConditionalUndesignated,
            MH.Rules.ConditionalNegatedDesignated,
            MH.Rules.BiconditionalDesignated,
            MH.Rules.BiconditionalNegatedDesignated,
            MH.Rules.BiconditionalUndesignated,
            MH.Rules.BiconditionalNegatedUndesignated,
            FDE.Rules.DoubleNegationDesignated,
            FDE.Rules.DoubleNegationUndesignated),
        # 1-branching rules.
        group(
            FDE.Rules.ConjunctionUndesignated,
            ConjunctionNegatedUndesignated,
            FDE.Rules.DisjunctionDesignated,
            FDE.Rules.DisjunctionNegatedUndesignated,
            FDE.Rules.MaterialConditionalDesignated,
            MaterialConditionalNegatedUndesignated,
            MH.Rules.ConditionalDesignated,
            MH.Rules.ConditionalNegatedUndesignated),
        # 3-branching rules.
        group(
            ConjunctionNegatedDesignated))

    @classmethod
    def _check_groups(cls):
        for branching, group in zip((0, 1, 3), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'