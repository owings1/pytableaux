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

from ..proof import Branch, Node, adds, anode, rules, sdwnode
from ..proof.helpers import WorldIndex
from ..tools import group
from . import fde as FDE


class Meta(FDE.Meta):
    name = 'KFDE'
    title = 'FDE with K modal'
    modal = True
    description = 'Modal version of FDE based on K normal modal logic'
    category_order = FDE.Meta.category_order
    extension_of = ('FDE')

class Model(FDE.Model): pass
class System(FDE.System): pass

class Rules(FDE.Rules):

    class PossibilityDesignated(rules.PossibilityRule):

        def _get_node_targets(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            si = s.lhs
            if self.new_negated(self.negated):
                si = ~si
            d = self.designation
            # Allow override for S4GO
            if d is not None:
                d = self.new_designation(d)
            w1 = node['world']
            w2 = branch.new_world()
            yield adds(
                group(sdwnode(si, d, w2), anode(w1, w2)),
                designated=d,
                sentence=si)

    class NecessityDesignated(rules.NecessityRule):

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            si = s.lhs
            if self.new_negated(self.negated):
                si = ~si
            d = self.designation
            if d is not None:
                d = self.new_designation(d)
            w1 = node['world']

            for w2 in self[WorldIndex][branch][w1]:
                add = sdwnode(si, d, w2)
                if branch.has(add):
                    continue
                nodes = (node, branch.find(anode(w1, w2)))
                yield adds(group(add),
                    sentence=si,
                    world=w2,
                    nodes=nodes)

    class NecessityNegatedUndesignated(NecessityDesignated): pass
    class PossibilityUndesignated(NecessityDesignated): pass
    class PossibilityNegatedDesignated(NecessityDesignated): pass

    class PossibilityNegatedUndesignated(PossibilityDesignated): pass
    class NecessityUndesignated(PossibilityDesignated): pass
    class NecessityNegatedDesignated(PossibilityDesignated): pass

    unmodal_groups = (
        group(
            NecessityDesignated,
            PossibilityUndesignated,
            PossibilityNegatedDesignated,
            NecessityNegatedUndesignated),
        group(
            NecessityUndesignated,
            PossibilityDesignated,
            PossibilityNegatedUndesignated,
            NecessityNegatedDesignated))

    groups = (
        *FDE.Rules.nonbranching_groups,
        *FDE.Rules.branching_groups,
        *unmodal_groups,
        *FDE.Rules.unquantifying_groups)
