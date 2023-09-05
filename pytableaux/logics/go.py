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

from ..lang import Operator, Quantified, Quantifier
from ..proof import adds, rules, sdwnode
from ..tools import group, maxceil, minfloor
from . import LogicType
from . import b3e as B3E
from . import fde as FDE
from . import k3 as K3


class Meta(K3.Meta):
    name = 'GO'
    title = 'Gappy Object 3-valued Logic'
    description = (
        'Three-valued logic (True, False, Neither) with '
        'classical-like binary operators')
    category_order = 13
    native_operators = FDE.Meta.native_operators | [
        Operator.Assertion,
        Operator.Conditional,
        Operator.Biconditional]

class Model(FDE.Model):

    class TruthFunction(B3E.Model.TruthFunction):

        def Disjunction(self, *args):
            return max(map(self.Assertion, args))

        def Conjunction(self, *args):
            return min(map(self.Assertion, args))

        def Conditional(self, a, b, /):
            if a == b:
                return self.values.T
            return self.MaterialConditional(a, b)

    def value_of_quantified(self, s: Quantified, /, *, world: int = 0):
        it = map(self.truth_function.Assertion, self._unquantify_values(s, world=world))
        if s.quantifier is Quantifier.Existential:
            return maxceil(self.maxval, it, self.minval)
        if s.quantifier is Quantifier.Universal:
            return minfloor(self.minval, it, self.maxval)
        raise NotImplementedError from ValueError(s.quantifier)

class System(FDE.System): pass

class Rules(LogicType.Rules):

    closure = K3.Rules.closure

    class ConjunctionNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated, negated conjunction node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add an undesignated node to
        *b'* with one conjunct, and an undesignated node to *b''* with the other
        conjunct, then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                group(sdwnode(s.lhs, not d, w)),
                group(sdwnode(s.rhs, not d, w)))

    class ConjunctionUndesignated(System.OperatorNodeRule):
        """
        From an unticked, undesignated conjunction node *n* on a branch *b*, add a
        designated node to *b* with the negation of the conjunction, then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(group(sdwnode(~s, not d, w)))

    class ConjunctionNegatedUndesignated(System.OperatorNodeRule):
        """
        From an unticked, undesignated, negated conjunction node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) conjuction, then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(group(sdwnode(s, not d, w)))
        
    class DisjunctionNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated, negated disjunction node *n* on a branch *b*,
        add an undesignated node to *b* for each disjunct, then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(group(sdwnode(s.lhs, not d, w), sdwnode(s.rhs, not d, w)))

    class DisjunctionUndesignated(ConjunctionUndesignated): pass
    class DisjunctionNegatedUndesignated(ConjunctionNegatedUndesignated): pass

    class MaterialConditionalNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated, negated material conditional node *n* on a branch
        *b*, add an undesignated node with the negation of the antecedent, and an
        undesignated node with the consequent to *b*, then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(group(sdwnode(~s.lhs, not d, w), sdwnode(s.rhs, not d, w)))

    class MaterialConditionalUndesignated(ConjunctionUndesignated): pass
    class MaterialConditionalNegatedUndesignated(ConjunctionNegatedUndesignated): pass

    class MaterialBiconditionalNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated, negated, material biconditional node *n* on a branch
        *b*, make two branches *b'* and *b''* from *b*. On *b'* add undesignated nodes for
        the negation of the antecent, and for the consequent. On *b''* add undesignated
        nodes for the antecedent, and for the negation of the consequent. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                group(sdwnode(~s.lhs, not d, w), sdwnode( s.rhs, not d, w)),
                group(sdwnode( s.lhs, not d, w), sdwnode(~s.rhs, not d, w)))

    class MaterialBiconditionalUndesignated(ConjunctionUndesignated): pass
    class MaterialBiconditionalNegatedUndesignated(ConjunctionNegatedUndesignated): pass

    class ConditionalDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated, conditional node *n* on a branch *b*, make two branches
        *b'* and *b''* from *b*. On *b'* add a designated node with a disjunction of the
        negated antecedent and the consequent. On *b''* add undesignated nodes for the
        antecedent, consequent, and their negations. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            lhs, rhs = s
            yield adds(
                group(
                    sdwnode(~lhs | rhs, d, w)),
                group(
                    sdwnode( lhs, not d, w),
                    sdwnode( rhs, not d, w),
                    sdwnode(~lhs, not d, w),
                    sdwnode(~rhs, not d, w)))

    class ConditionalNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated, negated conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add a designated node with the
        antecedent, and an undesignated node with the consequent. On *b''* add an
        undesignated node with the negation of the antencedent, and a designated node
        with the negation of the consequent. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                group(sdwnode( s.lhs, d, w), sdwnode(s.rhs, not d, w)),
                group(sdwnode(~s.lhs, not d, w), sdwnode(~s.rhs, d, w)))

    class ConditionalUndesignated(ConjunctionUndesignated): pass
    class ConditionalNegatedUndesignated(ConjunctionNegatedUndesignated): pass

    class BiconditionalDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated biconditional node *n* on a branch *b*, add two
        designated conditional nodes to *b*, one with the operands of the biconditional,
        and the other with the reversed operands. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            convert = self.operator.other
            yield adds(group(
                sdwnode(convert(s.operands), d, w),
                sdwnode(convert(reversed(s)), d, w)))

    class BiconditionalNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated, negated biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add a designated negated conditional
        node with the operands of the biconditional. On *b''* add a designated negated
        conditional node with the reversed operands of the biconditional. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            convert = self.operator.other
            yield adds(
                group(sdwnode(~convert(s.operands), d, w)),
                group(sdwnode(~convert(reversed(s)), d, w)))

    class BiconditionalUndesignated(ConjunctionUndesignated): pass
    class BiconditionalNegatedUndesignated(ConjunctionNegatedUndesignated): pass

    class ExistentialNegatedDesignated(System.DefaultNodeRule, rules.QuantifiedSentenceRule):
        """
        From an unticked, designated negated existential node *n* on a branch *b*,
        add a designated node *n'* to *b* with a universal sentence consisting of
        disjunction, whose first disjunct is the negated inner sentence of *n*,
        and whose second disjunct is the negation of a disjunction *d*, where the
        first disjunct of *d* is the inner sentence of *n*, and the second disjunct
        of *d* is the negation of the inner sentence of *n*. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            v, si = s[1:]
            sq = self.quantifier.other(v, ~si | ~(si | ~si))
            yield adds(
                group(sdwnode(sq, d, w)))

    class ExistentialUndesignated(ConjunctionUndesignated): pass
    class ExistentialNegatedUndesignated(ConjunctionNegatedUndesignated): pass

    class UniversalNegatedDesignated(System.QuantifierSkinnyRule):
        """
        From an unticked, designated universal existential node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'*, add a designtated node
        with the standard translation of the sentence on *b*. For *b''*, substitute
        a new constant *c* for the quantified variable, and add two undesignated
        nodes to *b''*, one with the substituted inner sentence, and one with its
        negation, then tick *n*.
        """

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = branch.new_constant() >> s
            d = self.designation
            w = node.get('world')
            yield adds(
                group(sdwnode(self.quantifier.other(v, ~si), d, w)),
                group(sdwnode(r, not d, w), sdwnode(~r, not d, w)))

    class UniversalUndesignated(ExistentialUndesignated): pass
    class UniversalNegatedUndesignated(ExistentialNegatedUndesignated): pass

    groups = (
        group(
            # non-branching rules
            FDE.Rules.AssertionDesignated,
            B3E.Rules.AssertionUndesignated,
            B3E.Rules.AssertionNegatedDesignated,
            B3E.Rules.AssertionNegatedUndesignated,
            FDE.Rules.ConjunctionDesignated,
            ConjunctionUndesignated,
            ConjunctionNegatedUndesignated,
            DisjunctionNegatedDesignated,
            DisjunctionUndesignated,
            DisjunctionNegatedUndesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalUndesignated,
            MaterialConditionalNegatedUndesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedUndesignated,
            ConditionalUndesignated,
            ConditionalNegatedUndesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated,
            BiconditionalDesignated,
            FDE.Rules.ExistentialDesignated,
            ExistentialNegatedDesignated,
            ExistentialUndesignated,
            ExistentialNegatedUndesignated,
            FDE.Rules.UniversalDesignated,
            UniversalUndesignated,
            UniversalNegatedUndesignated,
            FDE.Rules.DoubleNegationDesignated,
            FDE.Rules.DoubleNegationUndesignated),
        group(
            # branching rules
            FDE.Rules.DisjunctionDesignated,
            ConjunctionNegatedDesignated,
            FDE.Rules.MaterialConditionalDesignated,
            FDE.Rules.MaterialBiconditionalDesignated,
            MaterialBiconditionalNegatedDesignated,
            ConditionalDesignated,
            ConditionalNegatedDesignated,
            BiconditionalNegatedDesignated,
            UniversalNegatedDesignated))

    @classmethod
    def _check_groups(cls):
        for branching, group in enumerate(cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'