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

from types import MappingProxyType as MapProxy

from ..lang import Operator, Quantified, Quantifier
from ..proof import adds, sdnode
from ..tools import group
from . import fde as FDE
from . import k3 as K3
from . import k3w as K3W
from . import LogicType


class Meta(K3.Meta):
    name = 'K3WQ'
    title = 'Weak Kleene alt-Q Logic'
    description = (
        'Three-valued logic with values T, F, and N, '
        'with alternate quantification')
    category_order = 40

class Model(FDE.Model):

    class TruthFunction(K3W.Model.TruthFunction):

        generalizing_operators = MapProxy({
            Operator.Disjunction: 'max',
            Operator.Conjunction: 'min'})
        generalized_orderings = MapProxy(dict(
            max = tuple(map(Meta.values, 'FTN')),
            min = tuple(map(Meta.values, 'NFT'))))

    def value_of_quantified(self, s: Quantified, /, *, world: int = 0):
        """
        An existential sentence is interpreted in terms of `generalized disjunction`.
        If we order the values least to greatest as V{N}, V{T}, V{F}, then we
        can define the value of an existential in terms of the `maximum` value of
        the set of values for the substitution of each constant in the model for
        the variable.

        A universal sentence is interpreted in terms of `generalized conjunction`.
        If we order the values least to greatest as V{N}, V{F}, V{T}, then we
        can define the value of a universal in terms of the `minimum` value of
        the set of values for the substitution of each constant in the model for
        the variable.
        """
        if s.quantifier is Quantifier.Existential:
            oper = Operator.Disjunction
        elif s.quantifier is Quantifier.Universal:
            oper = Operator.Conjunction
        else:
            raise NotImplementedError from ValueError(s.quantifier) # pragma: no cover
        return self.truth_function.generalize(oper, self._unquantify_values(s, world=world))

class System(FDE.System): pass

class Rules(LogicType.Rules):

    closure = K3.Rules.closure

    class ExistentialDesignated(System.QuantifierSkinnyRule):
        """
        From an unticked, designated existential node `n` on a branch `b`, add
        two designated nodes to `b`. One node is the result of universally
        quantifying over the disjunction of the inner sentence with its negation.
        The other node is a substitution of a constant new to `b`. Then tick `n`.
        """

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            d = self.designation
            yield adds(
                group(
                    sdnode(self.quantifier.other(v, si | ~si), d),
                    sdnode(branch.new_constant() >> s, d)))

    class ExistentialUndesignated(System.QuantifierSkinnyRule):
        """
        From an unticked, undesignated existential node `n` on a branch `b`, make
        two branches `b'` and `b''` from `b`. On `b'` add two undesignated nodes,
        one with the substituion of a constant new to `b` for the inner sentence,
        and the other with the negation of that sentence. On `b''` add a designated
        node with universal quantifier over the negation of the inner sentence.
        Then tick `n`.
        """

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = branch.new_constant() >> s
            d = self.designation
            yield adds(
                group(sdnode(r, d), sdnode(~r, d)),
                group(sdnode(self.quantifier.other(v, ~si), not d)))

    class ExistentialNegatedUndesignated(System.QuantifierSkinnyRule):
        """"
        From an unticked, undesignated, negated existential node `n` on a branch
        `b`, add an undesignated node to `b` with the negation of the inner
        sentence, substituting a constant new to `b` for the variable. Then
        tick `n`.
        """

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            yield adds(
                group(sdnode(~(branch.new_constant() >> s), self.designation)))

    class UniversalNegatedDesignated(System.QuantifierSkinnyRule):
        """
        From an unticked, designated, negated universal node `n` on a branch `b`,
        add two designated nodes to `b`. The first node is a universally quantified
        disjunction of the inner sentence and its negation. The second node is the
        negation of the inner sentence, substituting a constant new to `b` for the
        variable. Then tick `n`.
        """

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            d = self.designation
            yield adds(
                group(
                    sdnode(self.quantifier(v, si | ~si), d),
                    sdnode(~(branch.new_constant() >> s), d)))

    class UniversalNegatedUndesignated(System.QuantifierSkinnyRule):
        """
        From an unticked, undesignated, negated universal node `n` on a branch `b`,
        make two branches `b'` and `b''` from `b`. On `b'` add two undesignated nodes,
        one with the substitution of a constant new to `b` for the inner sentence
        of `n`, and the other with the negation of that sentence. On `b''`, add
        a designated node with the negatum of `n`. Then tick `n`.
        """

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = branch.new_constant() >> s
            d = self.designation
            yield adds(
                group(sdnode(r, d), sdnode(~r, d)),
                group(sdnode(self.quantifier(v, si), not d)))

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
            FDE.Rules.DoubleNegationDesignated,
            FDE.Rules.DoubleNegationUndesignated,
            # reduction rules (thus, non-branching)
            K3W.Rules.MaterialConditionalDesignated,
            K3W.Rules.MaterialConditionalUndesignated,
            K3W.Rules.MaterialConditionalNegatedDesignated,
            K3W.Rules.MaterialConditionalNegatedUndesignated,
            K3W.Rules.ConditionalDesignated,
            K3W.Rules.ConditionalUndesignated,
            K3W.Rules.ConditionalNegatedDesignated,
            K3W.Rules.ConditionalNegatedUndesignated,
            K3W.Rules.MaterialBiconditionalDesignated,
            K3W.Rules.MaterialBiconditionalUndesignated,
            K3W.Rules.MaterialBiconditionalNegatedDesignated,
            K3W.Rules.MaterialBiconditionalNegatedUndesignated,
            K3W.Rules.BiconditionalDesignated,
            K3W.Rules.BiconditionalUndesignated,
            K3W.Rules.BiconditionalNegatedDesignated,
            K3W.Rules.BiconditionalNegatedUndesignated),
        group(
            # two-branching rules
            FDE.Rules.ConjunctionUndesignated),
        group(
            # three-branching rules
            K3W.Rules.DisjunctionDesignated,
            K3W.Rules.DisjunctionUndesignated,
            K3W.Rules.ConjunctionNegatedDesignated,
            K3W.Rules.ConjunctionNegatedUndesignated,
            # five-branching rules (formerly)
            K3W.Rules.DisjunctionNegatedUndesignated),
        group(
            ExistentialDesignated,
            ExistentialNegatedUndesignated,
            ExistentialUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated),
        group(
            FDE.Rules.UniversalDesignated,
            FDE.Rules.UniversalUndesignated))

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(3), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'