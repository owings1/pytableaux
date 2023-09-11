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
from ..proof import adds, rules, sdwgroup
from ..tools import group
from . import k3w as K3W


class Meta(K3W.Meta):
    name = 'K3WQ'
    title = 'Weak Kleene alt-Q Logic'
    description = 'Weak Kleene logic with alternate quantification'
    category_order = 8
    extension_of = ('K3W') # proof?

class Model(K3W.Model):

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
            raise NotImplementedError from ValueError(s.quantifier)
        return self.truth_function.generalize(oper, self._unquantify_values(s, world=world))

class System(K3W.System): pass

class Rules(K3W.Rules):

    class ExistentialDesignated(rules.QuantifierSkinnyRule):

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            d = self.designation
            w = node.get('world')
            yield adds(
                sdwgroup(
                    (self.quantifier.other(v, si | ~si), d, w),
                    (branch.new_constant() >> s, d, w)))

    class ExistentialUndesignated(rules.QuantifierSkinnyRule):

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = branch.new_constant() >> s
            d = self.designation
            w = node.get('world')
            yield adds(
                sdwgroup((r, d, w), (~r, d, w)),
                sdwgroup((self.quantifier.other(v, ~si), not d, w)))

    class ExistentialNegatedUndesignated(rules.QuantifierSkinnyRule):

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            w = node.get('world')
            yield adds(
                sdwgroup((~(branch.new_constant() >> s), self.designation, w)))

    class UniversalNegatedDesignated(rules.QuantifierSkinnyRule):

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            d = self.designation
            w = node.get('world')
            yield adds(
                sdwgroup(
                    (self.quantifier(v, si | ~si), d, w),
                    (~(branch.new_constant() >> s), d, w)))

    class UniversalNegatedUndesignated(rules.QuantifierSkinnyRule):

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = branch.new_constant() >> s
            d = self.designation
            w = node.get('world')
            yield adds(
                sdwgroup((r, d, w), (~r, d, w)),
                sdwgroup((self.quantifier(v, si), not d, w)))

    unquantifying_groups = group(
        group(
            ExistentialDesignated,
            ExistentialNegatedUndesignated,
            ExistentialUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated),
        group(
            K3W.Rules.ExistentialNegatedDesignated,
            K3W.Rules.UniversalDesignated,
            K3W.Rules.UniversalUndesignated))

    groups = (
        *K3W.Rules.nonbranching_groups,
        *K3W.Rules.branching_groups,
        *unquantifying_groups)
