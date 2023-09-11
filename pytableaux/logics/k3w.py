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
from . import fde as FDE
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
        """
        From an unticked, designated, negated conjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add a designated
        node with the first conjunct, and a designated node with the negation of the
        second conjunct. On *b''* add a designated node with the negation of the first
        conjunct, and a designated node with the second conjunct. On *b'''* add
        designated nodes with the negation of each conjunct. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup(( lhs, True, w), (~rhs, True, w)),
                sdwgroup((~lhs, True, w), ( rhs, True, w)),
                sdwgroup((~lhs, True, w), (~rhs, True, w)))

    class ConjunctionNegatedUndesignated(rules.OperatorNodeRule):
        """
        From an unticked, undesignated, negated conjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add undesignated nodes
        for the first conjunct and its negation. On *b''* add undesignated nodes for the
        second conjunct and its negation. On *b'''* add a designated node for each conjunct.
        Then tick *n*. 
        """

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup((lhs, False, w), (~lhs, False, w)),
                sdwgroup((rhs, False, w), (~rhs, False, w)),
                sdwgroup((lhs, True, w),  ( rhs, True, w)))

    class DisjunctionDesignated(rules.OperatorNodeRule):
        """
        From an unticked, designated, disjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add a designated
        node with the first disjunct, and a designated node with the negation of the
        second disjunct. On *b''* add a designated node with the negation of the first
        disjunct, and a designated node with the second disjunct. On *b'''* add a
        designated node with each disjunct. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup(( lhs, True, w), (~rhs, True, w)),
                sdwgroup((~lhs, True, w), ( rhs, True, w)),
                sdwgroup(( lhs, True, w), ( rhs, True, w)))
            
    class DisjunctionUndesignated(rules.OperatorNodeRule):
        """
        From an unticked, undesignated disjunction node *n* on a branch *b*, make three
        new branches *b'*, *b''*, and *b'''* from b. On *b'* add undesignated nodes for
        the first disjunct and its negation. On *b''* add undesignated nodes for the
        second disjunct and its negation. On *b'''* add designated nodes for the negation
        of each disjunct. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                sdwgroup(( lhs, False, w), (~lhs, False, w)),
                sdwgroup(( rhs, False, w), (~rhs, False, w)),
                sdwgroup((~lhs, True, w),  (~rhs, True, w)))

    class DisjunctionNegatedUndesignated(rules.OperatorNodeRule):
        """
        Either the disjunction is designated, or at least one of the disjuncts
        has the value V{N}. So, from an unticked, undesignated, negated
        disjunction node *n* on a branch *b*, make three branches *b'*, *b''*,
        and *b'''* from *b*. On *b'* add a designated node with the disjunction.
        On *b''* add two undesignated nodes with the first disjunct and its
        negation, respectively. On *b'''* add undesignated nodes with the second
        disjunct and its negation, respectively. Then tick *n*.
        """

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

    groups = (
        group(
            # non-branching rules
            FDE.Rules.AssertionDesignated,
            FDE.Rules.AssertionUndesignated,
            FDE.Rules.AssertionNegatedDesignated,
            FDE.Rules.AssertionNegatedUndesignated,
            FDE.Rules.ConjunctionDesignated, 
            FDE.Rules.DisjunctionNegatedDesignated,
            FDE.Rules.DoubleNegationDesignated,
            FDE.Rules.DoubleNegationUndesignated,
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
            BiconditionalNegatedUndesignated),
        group(
            # two-branching rules
            FDE.Rules.ConjunctionUndesignated),
        group(
            # three-branching rules
            DisjunctionDesignated,
            DisjunctionUndesignated,
            ConjunctionNegatedDesignated,
            ConjunctionNegatedUndesignated,
            # five-branching rules (formerly)
            DisjunctionNegatedUndesignated),
        *K3.Rules.unquantifying_groups)

    @staticmethod
    def _check_groups():
        cls = __class__
        for branching, group in zip(range(3), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'
