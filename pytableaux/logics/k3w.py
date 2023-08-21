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

class Meta(K3.Meta):
    name = 'K3W'
    title = 'Weak Kleene Logic'
    description = 'Three-valued logic with values T, F, and N'
    category_order = 30

class Model(FDE.Model):

    class TruthFunction(FDE.Model.TruthFunction):

        def Conjunction(self, a, b, /):
            if self.values.N in (a, b):
                return self.values.N
            return super().Conjunction(a, b)

        def Disjunction(self, a, b, /):
            if self.values.N in (a, b):
                return self.values.N
            return super().Disjunction(a, b)

        def Conditional(self, a, b, /):
            if self.values.N in (a, b):
                return self.values.N
            return super().Conditional(a, b)

class System(FDE.System): pass

class Rules(K3.Rules):

    class ConjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated conjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add a designated
        node with the first conjunct, and a designated node with the negation of the
        second conjunct. On *b''* add a designated node with the negation of the first
        conjunct, and a designated node with the second conjunct. On *b'''* add
        designated nodes with the negation of each conjunct. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode( lhs, True), sdnode(~rhs, True)),
                group(sdnode(~lhs, True), sdnode( rhs, True)),
                group(sdnode(~lhs, True), sdnode(~rhs, True)))

    class ConjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, negated conjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add undesignated nodes
        for the first conjunct and its negation. On *b''* add undesignated nodes for the
        second conjunct and its negation. On *b'''* add a designated node for each conjunct.
        Then tick *n*. 
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode(lhs, False), sdnode(~lhs, False)),
                group(sdnode(rhs, False), sdnode(~rhs, False)),
                group(sdnode(lhs, True),  sdnode( rhs, True)))

    class DisjunctionDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, disjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add a designated
        node with the first disjunct, and a designated node with the negation of the
        second disjunct. On *b''* add a designated node with the negation of the first
        disjunct, and a designated node with the second disjunct. On *b'''* add a
        designated node with each disjunct. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode( lhs, True), sdnode(~rhs, True)),
                group(sdnode(~lhs, True), sdnode( rhs, True)),
                group(sdnode( lhs, True), sdnode( rhs, True)))
            
    class DisjunctionUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated disjunction node *n* on a branch *b*, make three
        new branches *b'*, *b''*, and *b'''* from b. On *b'* add undesignated nodes for
        the first disjunct and its negation. On *b''* add undesignated nodes for the
        second disjunct and its negation. On *b'''* add designated nodes for the negation
        of each disjunct. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode( lhs, False), sdnode(~lhs, False)),
                group(sdnode( rhs, False), sdnode(~rhs, False)),
                group(sdnode(~lhs, True),  sdnode(~rhs, True)))

    class DisjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        Either the disjunction is designated, or at least one of the disjuncts
        has the value V{N}. So, from an unticked, undesignated, negated
        disjunction node *n* on a branch *b*, make three branches *b'*, *b''*,
        and *b'''* from *b*. On *b'* add a designated node with the disjunction.
        On *b''* add two undesignated nodes with the first disjunct and its
        negation, respectively. On *b'''* add undesignated nodes with the second
        disjunct and its negation, respectively. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(s, True)),
                group(sdnode(s.lhs, False), sdnode(~s.lhs, False)),
                group(sdnode(s.rhs, False), sdnode(~s.rhs, False)))

    class MaterialConditionalDesignated(FDE.MaterialConditionalReducingRule): pass
    class MaterialConditionalNegatedDesignated(FDE.MaterialConditionalReducingRule): pass
    class MaterialConditionalUndesignated(FDE.MaterialConditionalReducingRule): pass
    class MaterialConditionalNegatedUndesignated(FDE.MaterialConditionalReducingRule): pass
    class MaterialBiconditionalDesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedDesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalUndesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedUndesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class ConditionalDesignated(FDE.MaterialConditionalReducingRule): pass
    class ConditionalNegatedDesignated(FDE.MaterialConditionalReducingRule): pass
    class ConditionalUndesignated(FDE.MaterialConditionalReducingRule): pass
    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated): pass
    class BiconditionalDesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedDesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class BiconditionalUndesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedUndesignated(FDE.MaterialConditionalConjunctsReducingRule): pass

    groups = (
        group(
            # non-branching rules
            FDE.Rules.AssertionDesignated,
            FDE.Rules.AssertionUndesignated,
            FDE.Rules.AssertionNegatedDesignated,
            FDE.Rules.AssertionNegatedUndesignated,
            FDE.Rules.ConjunctionDesignated, 
            FDE.Rules.DisjunctionNegatedDesignated,
            FDE.Rules.ExistentialNegatedDesignated,
            FDE.Rules.ExistentialNegatedUndesignated,
            FDE.Rules.UniversalNegatedDesignated,
            FDE.Rules.UniversalNegatedUndesignated,
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
        group(
            FDE.Rules.ExistentialDesignated,
            FDE.Rules.ExistentialUndesignated),
        group(
            FDE.Rules.UniversalDesignated,
            FDE.Rules.UniversalUndesignated))


