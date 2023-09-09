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

from ..lang import Operator, Quantified
from ..proof import adds, sdwgroup
from ..tools import group
from . import LogicType
from . import b3e as B3E
from . import fde as FDE
from . import k3 as K3
from . import l3 as L3


class Meta(K3.Meta):
    name = 'GO'
    title = 'Gappy Object Logic'
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

    def _unquantify_values(self, s: Quantified, /, **kw):
        return map(self.truth_function.Assertion, super()._unquantify_values(s, **kw))

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
                sdwgroup((s.lhs, not d, w)),
                sdwgroup((s.rhs, not d, w)))

    class MaterialConditionalNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated, negated material conditional node *n* on a branch
        *b*, add an undesignated node with the negation of the antecedent, and an
        undesignated node with the consequent to *b*, then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(sdwgroup((~s.lhs, not d, w), (s.rhs, not d, w)))

    class MaterialBiconditionalNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated, negated, material biconditional node *n* on a branch
        *b*, make two branches *b'* and *b''* from *b*. On *b'* add undesignated nodes for
        the negation of the antecent, and for the consequent. On *b''* add undesignated
        nodes for the antecedent, and for the negation of the consequent. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                sdwgroup((~s.lhs, not d, w), ( s.rhs, not d, w)),
                sdwgroup(( s.lhs, not d, w), (~s.rhs, not d, w)))

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
                sdwgroup(( s.lhs, d, w), (s.rhs, not d, w)),
                sdwgroup((~s.lhs, not d, w), (~s.rhs, d, w)))

    class BiconditionalDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated biconditional node *n* on a branch *b*, add two
        designated conditional nodes to *b*, one with the operands of the biconditional,
        and the other with the reversed operands. Then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            convert = self.operator.other
            yield adds(sdwgroup(
                (convert(s.operands), d, w),
                (convert(reversed(s)), d, w)))

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
                sdwgroup((~convert(s.operands), d, w)),
                sdwgroup((~convert(reversed(s)), d, w)))

    class ExistentialNegatedDesignated(System.QuantifierNodeRule):
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
            yield adds(sdwgroup((sq, d, w)))

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
                sdwgroup((self.quantifier.other(v, ~si), d, w)),
                sdwgroup((r, not d, w), (~r, not d, w)))

    class DisjunctionNegatedDesignated(System.FlippingOperandsRule): pass

    class ConjunctionUndesignated(System.NegatingFlippingRule): pass
    class DisjunctionUndesignated(System.NegatingFlippingRule): pass
    class MaterialConditionalUndesignated(System.NegatingFlippingRule): pass
    class MaterialBiconditionalUndesignated(System.NegatingFlippingRule): pass
    class ConditionalUndesignated(System.NegatingFlippingRule): pass
    class BiconditionalUndesignated(System.NegatingFlippingRule): pass
    class ExistentialUndesignated(System.NegatingFlippingRule): pass
    class UniversalUndesignated(System.NegatingFlippingRule): pass

    class ConjunctionNegatedUndesignated(System.FlippingRule): pass
    class DisjunctionNegatedUndesignated(System.FlippingRule): pass
    class MaterialConditionalNegatedUndesignated(System.FlippingRule): pass
    class MaterialBiconditionalNegatedUndesignated(System.FlippingRule): pass
    class ConditionalNegatedUndesignated(System.FlippingRule): pass
    class BiconditionalNegatedUndesignated(System.FlippingRule): pass
    class ExistentialNegatedUndesignated(System.FlippingRule): pass
    class UniversalNegatedUndesignated(System.FlippingRule): pass

    unquantifying_rules = (
        FDE.Rules.ExistentialDesignated, # skinny
        UniversalNegatedDesignated, # skinny + branching
        FDE.Rules.UniversalDesignated) # fat
    unquantifying_groups = tuple(map(group, unquantifying_rules))

    groups = (
        group(
            # non-branching rules
            FDE.Rules.AssertionDesignated,
            FDE.Rules.AssertionUndesignated,
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
            L3.Rules.ConditionalDesignated,
            ConditionalNegatedDesignated,
            BiconditionalNegatedDesignated,
            UniversalNegatedDesignated))

    @classmethod
    def _check_groups(cls):
        for branching, group in enumerate(cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'