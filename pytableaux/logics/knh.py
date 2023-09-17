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
from . import nh as NH


class Meta(NH.Meta, KFDE.Meta):
    name = 'KNH'
    title = 'NH with K modal'
    description = 'Modal version of NH based on K normal modal logic'
    category_order = 51
    extension_of = ('NH')

class Model(NH.Model, KFDE.Model):

    def value_of_operated(self, s, w, /):
        o = s.operator
        if o is not o.Necessity:
            return super().value_of_operated(s, w)
        valset = set(self.unmodal_values(s, w))
        values = self.values
        if values.F in valset:
            return values.F
        if len(valset) > 1:
            return values.B
        return values.T

class System(NH.System, KFDE.System): pass

class Rules(NH.Rules, KFDE.Rules):


    class NecessityNegatedDesignated(rules.PossibilityRule):
        pass
        """
                  ¬◻A w0 +
               ______|_______
              |              |
            w0Rw1           w0Rw1
           A w1 -          ¬A w1 -
                        ◇(A ∧ ¬A) w0 +
        """

        def new_designation(self, d: bool) -> bool:
            return not d

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            con = s.connective.other
            inner = s.inner
            resolved = inner
            joined = inner & ~inner
            reduced = con(joined)
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
                    sdwnode(reduced, not d, w)),
                sentence=inner,
                designated=self.designation)

    class NecessityNegatedUndesignated(rules.OperatorNodeRule):
        pass
        """
                  ¬◻A w -
               ______|_______
              |              |
          ◇¬A w -       ◻(A ∧ ¬A) w +
        """
        def _get_sdw_targets(self, s, d, w, /):
            con = s.connective
            inner = s.inner
            joined = inner & ~inner
            yield adds(
                sdwgroup((con.other(~inner), d, w)),
                sdwgroup((con(joined), not d, w)))

    branching_groups = (
        group(
            *NH.Rules.branching_groups[0],
            NecessityNegatedUndesignated),
        *NH.Rules.branching_groups[1:])

    unmodal_groups = (
        group(
            KFDE.Rules.NecessityDesignated,
            KFDE.Rules.PossibilityNegatedDesignated,
            KFDE.Rules.PossibilityUndesignated),
        group(NecessityNegatedDesignated),
        group(
            KFDE.Rules.PossibilityDesignated,
            KFDE.Rules.PossibilityNegatedUndesignated,
            KFDE.Rules.NecessityUndesignated))

    groups = (
        *NH.Rules.nonbranching_groups,
        *branching_groups,
        *unmodal_groups,
        *NH.Rules.unquantifying_groups)
