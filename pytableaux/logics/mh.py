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
from . import LogicType

class Meta(K3.Meta):
    name = 'MH'
    title = 'Paracomplete Hybrid Logic'
    quantified = False
    description = (
        'Three-valued logic (True, False, Neither) with non-standard disjunction, '
        'and a classical-like conditional')
    category_order = 70
    tags = ( # remove first-order
        'many-valued',
        'gappy',
        'non-modal')
    native_operators = FDE.Meta.native_operators | (
        Operator.Conditional,
        Operator.Biconditional)

class Model(FDE.Model):

    class TruthFunction(K3.Model.TruthFunction):

        def Disjunction(self, a, b):
            if a == self.values.N and b == self.values.N:
                return self.values.F
            return super().Disjunction(a, b)

        def Conditional(self, a, b):
            if a == self.values.T and b != self.values.T:
                return self.values.F
            return self.values.T

class System(FDE.System): pass

class Rules(LogicType.Rules):

    closure = K3.Rules.closure

    class DisjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, designated disjunction node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'* add four undesignated
        nodes, one for each disjunct and its negation. On *b''* add two designated
        nodes, one for the negation of each disjunct. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(
                    sdnode( lhs, not d),
                    sdnode(~lhs, not d),
                    sdnode( rhs, not d),
                    sdnode(~rhs, not d)),
                group(
                    sdnode(~lhs, d),
                    sdnode(~rhs, d)))

    class DisjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, undesignated disjunction node *n* on a branch
        *b*, make four branches from *b*: *b'*, *b''*, *b'''*, and *b''''*. On *b'*,
        add a designated node with the first disjunct, and on *b''*, add a designated
        node with the second disjunct.

        On *b'''* add three nodes:

        - An undesignated node with the first disjunct.
        - An undesignated node with the negation of the first disjunct.
        - A designated node with the negation of the second disjunct.

        On *b''''* add three nodes:

        - An undesignated node with the second disjunct.
        - An undesignated node with the negation of the second disjunct.
        - A designated node with the negation of the first disjunct.

        Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(
                    sdnode(lhs, not d)),
                group(
                    sdnode(rhs, not d)),
                group(
                    sdnode(lhs, d), sdnode(~lhs, d), sdnode(~rhs, not d)),
                group(
                    sdnode(rhs, d), sdnode(~rhs, d), sdnode(~lhs, not d)))

    class MaterialConditionalNegatedDesignated(FDE.OperatorNodeRule):

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(
                    sdnode( lhs, not d),
                    sdnode(~lhs, not d),
                    sdnode( rhs, not d),
                    sdnode(~rhs, not d)),
                group(
                    sdnode(lhs, d),
                    sdnode(~rhs, d)))

    class MaterialConditionalNegatedUndesignated(FDE.MaterialConditionalReducingRule): pass
    class MaterialBiconditionalDesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedDesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalUndesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedUndesignated(FDE.MaterialConditionalConjunctsReducingRule): pass

    class ConditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add an undesignated node
        with the antecedent, and on *b''* add a designated node with the consequent.
        Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            # Keep designation fixed for inheritance below.
            yield adds(
                group(sdnode(s.lhs, False)),
                group(sdnode(s.rhs, True)))

    class ConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, desigated conditional node *n* on a branch *b*,
        add two nodes to *b*:

        - A designated node with the antecedent.
        - An undesignated node with the consequent.

        Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            # Keep designation fixed for inheritance below.
            yield adds(group(sdnode(s.lhs, True), sdnode(s.rhs, False)))

    class ConditionalUndesignated(ConditionalNegatedDesignated): pass
    class ConditionalNegatedUndesignated(ConditionalDesignated): pass
    class BiconditionalDesignated(FDE.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedDesignated(FDE.ConditionalConjunctsReducingRule): pass
    class BiconditionalUndesignated(FDE.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedUndesignated(FDE.ConditionalConjunctsReducingRule): pass


    groups = (
        # Non-branching rules.
        group(
            FDE.Rules.AssertionDesignated,
            FDE.Rules.AssertionUndesignated,
            FDE.Rules.AssertionNegatedDesignated,
            FDE.Rules.AssertionNegatedUndesignated,
            FDE.Rules.ConjunctionDesignated,
            FDE.Rules.ConjunctionNegatedUndesignated,
            FDE.Rules.DisjunctionUndesignated,
            FDE.Rules.MaterialConditionalUndesignated,
            MaterialConditionalNegatedUndesignated,
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
            FDE.Rules.DoubleNegationDesignated,
            FDE.Rules.DoubleNegationUndesignated),
        # 1-branching rules.
        group(
            FDE.Rules.ConjunctionUndesignated,
            FDE.Rules.ConjunctionNegatedDesignated,
            FDE.Rules.DisjunctionDesignated,
            DisjunctionNegatedDesignated,
            FDE.Rules.MaterialConditionalDesignated,
            MaterialConditionalNegatedDesignated,
            ConditionalDesignated,
            ConditionalNegatedUndesignated),
        # 3-branching rules.
        group(
            DisjunctionNegatedUndesignated))

    @classmethod
    def _check_groups(cls):
        for branching, group in zip((0, 1, 3), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'