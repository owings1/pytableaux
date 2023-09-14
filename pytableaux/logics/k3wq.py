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

from typing import TypeVar

from ..lang import Operated, Operator, Quantified, Sentence
from ..proof import Branch, Node, adds, rules, sdwgroup, sdwnode
from ..tools import EMPTY_SET, group
from . import k3w as K3W

_ST = TypeVar('_ST', bound=Quantified|Operated)

class Meta(K3W.Meta):
    name = 'K3WQ'
    title = 'Weak Kleene alt-Q Logic'
    description = 'Weak Kleene logic with alternate quantification'
    category_order = 8
    extension_of = ('K3W') # proof?

class Model(K3W.Model):

    def value_of_quantified(self, s, w, /):
        q = s.quantifier
        it = self.unquantify_values(s, w)
        initial = self.valseq[-(q is q.Universal)]
        return self.truth_function.generalize(q, it, initial)

class System(K3W.System):

    class ReduceResolveBase(rules.BaseSentenceRule[_ST], intermediate=True):

        def _redres_targets(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            yield adds(
                *self._makegroups(s, node, branch),
                designated=self.designation,
                sentence=s.inner)

        def _makegroups(self, s: _ST, node: Node, branch: Branch):
            yield group(*self._makenodes(s, node, branch))

        def _makenodes(self, s: _ST, node: Node, branch: Branch):
            yield from EMPTY_SET

        def _resolved(self, s: _ST, node: Node, branch: Branch) -> Sentence:
            resolved = s
            if self.negated:
                resolved = ~resolved
            return resolved

        def _new_world(self, node: Node, branch: Branch) -> int|None:
            return node.get('world')

        def _reduced(self, s: _ST, node: Node, branch: Branch) -> _ST:
            return s

    class GeneralDisjunctionNegatedUndesignated(ReduceResolveBase[_ST], intermediate=True):

        def _makenodes(self, s: _ST, node: Node, branch: Branch):
            d = self.designation
            yield sdwnode(self._resolved(s, node, branch), d, self._new_world(node, branch))

    class GeneralDisjunctionDesignated(GeneralDisjunctionNegatedUndesignated[_ST], intermediate=True):

        def _makenodes(self, s: _ST, node: Node, branch: Branch):
            w = node.get('world')
            d = self.designation
            yield sdwnode(self._reduced(s, node, branch), d, w)
            yield from super()._makenodes(s, node, branch)

        def _reduced(self, s: _ST, node: Node, branch: Branch) -> Operated:
            inner = s.inner
            ops = inner, ~inner
            if self.negated:
                ops = reversed(ops)
            return Operator.Disjunction(ops)

    class GeneralDisjunctionUndesignated(ReduceResolveBase[_ST], intermediate=True):

        def _makegroups(self, s: _ST, node: Node, branch: Branch):
            w = node.get('world')
            d = self.designation
            yield from super()._makegroups(s, node, branch)
            yield sdwgroup((self._reduced(s, node, branch), not d, w))

        def _makenodes(self, s:_ST, node: Node, branch: Branch):
            d = self.designation
            w = self._new_world(node, branch)
            resolved = self._resolved(s, node, branch)
            yield sdwnode(resolved, d, w)
            yield sdwnode(~resolved, d, w)

        def _reduced(self, s: _ST, node: Node, branch: Branch) -> Operated:
            inner = s.inner
            if not self.negated:
                inner = ~inner
            return inner

    class QuantifierRule(rules.QuantifierSkinnyRule, ReduceResolveBase[Quantified], intermediate=True):

        def _get_node_targets(self, node: Node, branch: Branch, /):
            yield from self._redres_targets(node, branch)

        def _resolved(self, s, node, branch) -> Sentence:
            return super()._resolved(branch.new_constant() >> s, node, branch)

        def _reduced(self, s, node, branch):
            return s.quantifier.Universal(s.variable, super()._reduced(s, node, branch))


class Rules(K3W.Rules):

    class ExistentialDesignated(System.QuantifierRule, System.GeneralDisjunctionDesignated): pass
    class ExistentialUndesignated(System.QuantifierRule, System.GeneralDisjunctionUndesignated): pass
    class ExistentialNegatedUndesignated(System.QuantifierRule, System.GeneralDisjunctionNegatedUndesignated): pass
    class UniversalNegatedDesignated(ExistentialDesignated): pass
    class UniversalNegatedUndesignated(ExistentialUndesignated): pass

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
        *unquantifying_groups,
        *K3W.Rules.branching_groups)
