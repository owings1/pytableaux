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

from ..proof import adds, anode, rules, sdwgroup, sdwnode
from ..tools import group
from . import kfde as KFDE
from . import mh as MH


class Meta(MH.Meta, KFDE.Meta):
    name = 'KMH'
    title = 'MH with K modal'
    description = 'Modal version of MH based on K normal modal logic'
    category_order = 46
    extension_of = ('MH')

class Model(MH.Model, KFDE.Model):

    def value_of_operated(self, s, w, /):
        o = s.operator
        if o is not o.Possibility:
            return super().value_of_operated(s, w)
        valset = set(self.unmodal_values(s, w))
        values = self.values
        if values.T in valset:
            return values.T
        if len(valset) > 1:
            return values.N
        return values.F

class System(MH.System, KFDE.System): pass

class Rules(MH.Rules, KFDE.Rules):


    class PossibilityNegatedDesignated(rules.OperatorNodeRule):
        pass
        """
                   ¬◇A w +
               ______|_______
              |              |
           ◻¬A w +     ◻¬(A ∨ ¬A) w +
        """
        def _get_sdw_targets(self, s, d, w, /):
            con = s.connective.other
            inner = s.inner
            joined = inner | ~inner
            yield adds(
                sdwgroup((con(~inner), d, w)),
                sdwgroup((con(~joined), d, w)))

    class PossibilityNegatedUndesignated(rules.PossibilityRule):
        pass
        """
                  ¬◇A w0 -
               ______|_______
              |              |
            w0Rw1           w0Rw1
             A w1 +        ¬A w1 +
                        ◇¬(A ∨ ¬A) w0 +
        """

        def new_designation(self, d: bool) -> bool:
            return not d

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            con = s.connective
            inner = s.inner
            resolved = inner
            joined = inner | ~inner
            reduced = con(~joined)
            w = node['world']
            w2 = branch.new_world()
            d = self.designation
            if d is not None:
                d = self.new_designation(d)
            yield adds(
                group(
                    anode(w, w2),
                    sdwnode(resolved, d, w2)),
                group(
                    anode(w, w2),
                    sdwnode(~resolved, d, w2),
                    sdwnode(reduced, d, w)),
                sentence=inner,
                designated=self.designation)

    branching_groups = (
        group(
            *MH.Rules.branching_groups[0],
            PossibilityNegatedDesignated),
        *MH.Rules.branching_groups[1:])

    unmodal_groups = (
        group(
            KFDE.Rules.NecessityDesignated,
            KFDE.Rules.NecessityNegatedUndesignated,
            KFDE.Rules.PossibilityUndesignated),
        group(PossibilityNegatedUndesignated),
        group(
            KFDE.Rules.PossibilityDesignated,
            KFDE.Rules.NecessityUndesignated,
            KFDE.Rules.NecessityNegatedDesignated))

    groups = (
        *MH.Rules.nonbranching_groups,
        *branching_groups,
        *unmodal_groups,
        *MH.Rules.unquantifying_groups)
