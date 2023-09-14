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

from ..lang import Operated, Sentence
from ..proof import anode, rules
from ..tools import group
from . import k3wq as K3WQ
from . import kfde as KFDE


class Meta(K3WQ.Meta, KFDE.Meta):
    name = 'KK3WQ'
    title = 'K3WQ with K modal'
    description = 'Modal version of K3WQ based on K normal modal logic'
    category_order = 30.1
    extension_of = ('K3WQ')

class Model(K3WQ.Model, KFDE.Model):

    def value_of_operated(self, s, w, /):
        o = s.operator
        if o not in self.Meta.modal_operators:
            return super().value_of_operated(s, w)
        it = self.unmodal_values(s, w)
        initial = self.valseq[-(o is o.Necessity)]
        return self.truth_function.generalize(o, it, initial)

class System(K3WQ.System, KFDE.System):

    class GeneralModalRule(rules.ModalOperatorRule, K3WQ.System.ReduceResolveBase[Operated], intermediate=True):

        def _get_node_targets(self, node, branch    , /):
            yield from self._redres_targets(node, branch)

        def _resolved(self, s, node, branch) -> Sentence:
            return super()._resolved(s.inner, node, branch)

        def _new_world(self, node, branch):
            return branch.new_world()

        def _makenodes(self, s, node, branch):
            for n in super()._makenodes(s, node, branch):
                yield n
            yield anode(node['world'], n['world'])

        def _reduced(self, s, node, branch):
            return s.operator.Necessity(super()._reduced(s, node, branch))

class Rules(K3WQ.Rules, KFDE.Rules):

    class PossibilityDesignated(System.GeneralModalRule, System.GeneralDisjunctionDesignated): pass
    class PossibilityUndesignated(System.GeneralModalRule, System.GeneralDisjunctionUndesignated): pass
    class PossibilityNegatedUndesignated(System.GeneralModalRule, System.GeneralDisjunctionNegatedUndesignated): pass
    class NecessityNegatedDesignated(PossibilityDesignated): pass
    class NecessityNegatedUndesignated(PossibilityUndesignated): pass

    unmodal_groups = (
        group(
            KFDE.Rules.NecessityDesignated,
            KFDE.Rules.PossibilityNegatedDesignated),
        group(
            KFDE.Rules.NecessityUndesignated,
            PossibilityDesignated,
            PossibilityNegatedUndesignated,
            NecessityNegatedDesignated),
        group(
            PossibilityUndesignated,
            NecessityNegatedUndesignated))

    groups = (
        *K3WQ.Rules.nonbranching_groups,
        *K3WQ.Rules.branching_groups,
        *unmodal_groups,
        *K3WQ.Rules.unquantifying_groups)
