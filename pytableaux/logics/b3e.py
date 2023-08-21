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

from ..lang import Operator as Operator
from ..proof import adds, sdnode
from ..tools import group
from . import fde as FDE
from . import k3 as K3
from . import k3w as K3W

class Meta(K3.Meta):
    name = 'B3E'
    title = 'Bochvar 3 External Logic'
    description = 'Three-valued logic (True, False, Neither) with assertion operator'
    category_order = 50
    native_operators = tuple(
        sorted(FDE.Meta.native_operators + group(Operator.Assertion)))

class Model(K3W.Model):

    class TruthFunction(K3W.Model.TruthFunction):

        def gap(self, v, /):
            return self.values[min(v, 1 - v)]

        def crunch(self, v, /):
            return self.values[v - self.gap(v)]
        
        Assertion = crunch

        def Conditional(self, a, b, /):
            return self.Disjunction(
                self.Negation(self.Assertion(a)),
                self.Assertion(b))

class Rules(K3W.Rules):
    """
    The closure rules for L{B3E} are the L{FDE} closure rule, and the {@K3} closure rule.
    The operator rules are mostly a mix of L{FDE} and {@K3W}
    rules, but with different rules for the assertion, conditional and
    biconditional operators.
    """

    class AssertionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated assertion node *n* on a branch *b*,
        add an undesignated node to *b* with the assertion of *n*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            # Keep designation fixed to False for inheritance below
            yield adds(group(sdnode(s.lhs, False)))

    class AssertionUndesignated(AssertionNegatedDesignated): pass

    class AssertionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, negated assertion node *n* on a branch *b*, add
        a designated node to *b* with the assertion of *n*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s.lhs, not d)))

    class ConditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*,
        add a designated node to *b* with a disjunction, where the
        first disjunction is the negation of the assertion of the antecedent,
        and the second disjunct is the assertion of the consequent. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            sn = ~+s.lhs | +s.rhs
            # keep negated neutral for inheritance below
            if self.negated:
                sn = ~sn
            # keep designation neutral for inheritance below
            yield adds(group(sdnode(sn, d)))

    class ConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated negated conditional node *n* on a branch *b*,
        add a designated node with the antecedent, and an undesigntated node
        with the consequent to *b*. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            # Keep designation fixed for inheritance below.
            yield adds(group(sdnode(s.lhs, True), sdnode(s.rhs, False)))

    class ConditionalUndesignated(ConditionalNegatedDesignated): pass
    class ConditionalNegatedUndesignated(ConditionalDesignated): pass

    class BiconditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated biconditional node *n* on a branch *b*, add
        two designated nodes to *b*, one with a disjunction, where the first
        disjunct is the negated asserted antecedent, and the second disjunct is
        the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhsa = +s.lhs
            rhsa = +s.rhs
            sn1 = ~lhsa | rhsa
            sn2 = ~rhsa | lhsa
            # Keep negated neutral for inheritance below.
            if self.negated:
                sn1 = ~sn1
                sn2 = ~sn2
            # Keep designation neutral for inheritance below.
            yield adds(group(sdnode(sn1, d), sdnode(sn2, d)))

    class BiconditionalNegatedDesignated(BiconditionalDesignated): pass
    class BiconditionalUndesignated(BiconditionalDesignated): pass
    class BiconditionalNegatedUndesignated(BiconditionalUndesignated): pass

    groups = (
        group(
            FDE.Rules.AssertionDesignated,
            AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,
            FDE.Rules.ConjunctionDesignated,
            FDE.Rules.DisjunctionNegatedDesignated,
            ConditionalNegatedDesignated,
            ConditionalUndesignated,
            FDE.Rules.ExistentialNegatedDesignated,
            FDE.Rules.ExistentialNegatedUndesignated,
            FDE.Rules.UniversalNegatedDesignated,
            FDE.Rules.UniversalNegatedUndesignated,
            FDE.Rules.DoubleNegationDesignated,
            FDE.Rules.DoubleNegationUndesignated,
            # reduction rules (thus, non-branching)
            K3W.Rules.MaterialConditionalDesignated,
            K3W.Rules.MaterialConditionalUndesignated,
            K3W.Rules.MaterialConditionalNegatedDesignated,
            K3W.Rules.MaterialConditionalNegatedUndesignated,
            ConditionalDesignated,
            ConditionalNegatedUndesignated,
            K3W.Rules.MaterialBiconditionalDesignated,
            K3W.Rules.MaterialBiconditionalUndesignated,
            K3W.Rules.MaterialBiconditionalNegatedDesignated,
            K3W.Rules.MaterialBiconditionalNegatedUndesignated,
            BiconditionalDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedDesignated,
            BiconditionalNegatedUndesignated),
        group(
            # two-branching rules
            FDE.Rules.ConjunctionUndesignated),
        group(
            # three-branching rules
            K3W.Rules.DisjunctionDesignated,
            K3W.Rules.DisjunctionUndesignated,
            K3W.Rules.ConjunctionNegatedDesignated,
            K3W.Rules.ConjunctionNegatedUndesignated,
            # (formerly) four-branching rules
            K3W.Rules.DisjunctionNegatedUndesignated),
        group(
            FDE.Rules.ExistentialDesignated,
            FDE.Rules.ExistentialUndesignated),
        group(
            FDE.Rules.UniversalDesignated,
            FDE.Rules.UniversalUndesignated))


class System(K3.System):

    # operator => negated => designated
    branchables = K3W.System.branchables | {
        # reduction
        Operator.Conditional: ((0, 0), (0, 0)),
        # reduction
        Operator.Biconditional: ((0, 0), (0, 0)),}