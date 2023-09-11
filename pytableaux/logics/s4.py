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

from ..lang import Marking
from ..proof import AccessNode, adds, anode, filters, rules
from ..proof.helpers import FilterHelper, MaxWorlds, WorldIndex
from ..tools import group
from . import k as K
from . import t as T


class Meta(T.Meta):
    name = 'S4'
    title = 'S4 Normal Modal Logic'
    description = (
        'Normal modal logic with a reflexive and '
        'transitive access relation')
    category_order = 4
    extension_of = (
        'S4B3E',
        'S4G3',
        'S4GO',
        'S4K3',
        'S4K3W',
        'S4L3',
        'S4LP',
        'S4RM3',
        'T')

class Model(T.Model):

    def finish(self):
        self._check_not_finished()
        self._ensure_reflexive_transitive()
        return super().finish()

    def _ensure_reflexive_transitive(self):
        self._check_not_finished()
        R = self.R
        while True:
            self._ensure_reflexive()
            to_add = set()
            add = to_add.add
            for w1 in self.frames:
                for w2 in R[w1]:
                    for w3 in R[w2]:
                        if w3 not in R[w1]:
                            add((w1, w3))
            if not to_add:
                break
            for _ in map(R.add, to_add): pass

class System(K.System): pass

class Rules(T.Rules):

    class Transitive(rules.GetNodeTargetsRule):
        """
        .. _transitive-rule:

        For any world *w* appearing on a branch *b*, for each world *w'* and for each
        world *w''* on *b*, if *wRw'* and *wRw''* appear on *b*, but *wRw''* does not
        appear on *b*, then add *wRw''* to *b*.
        """
        Helpers = (MaxWorlds, WorldIndex)
        NodeFilters = group(filters.NodeType)
        NodeType = AccessNode
        ticking = False
        marklegend = [(Marking.tableau, ('access', 'transitive'))]

        def _get_node_targets(self, node: AccessNode, branch, /):
            if self[MaxWorlds].is_reached(branch):
                self[FilterHelper].release(node, branch)
                return
            w1, w2 = pair = node.pair()
            for w3 in self[WorldIndex].intransitives(branch, pair):
                nnode = anode(w1, w3)
                yield adds(group(nnode),
                    nodes=(node, branch.find(anode(w2, w3))),
                    **nnode)

        def score_candidate(self, target, /):
            # Rank the highest world
            return float(target.world2)

        def example_nodes(self):
            yield anode(0, 1)
            yield anode(1, 2)

    groups = (
        *K.Rules.nonbranching_groups,
        group(Transitive),
        *K.Rules.unmodal_groups,
        group(T.Rules.Reflexive),
        *K.Rules.branching_groups,
        *K.Rules.unquantifying_groups)
