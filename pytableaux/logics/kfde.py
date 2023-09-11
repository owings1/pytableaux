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

from ..proof import Branch, Node, adds, anode, rules, sdwgroup, sdwnode
from ..proof.helpers import (AdzHelper, AplSentCount, MaxWorlds, NodeCount,
                             NodesWorlds, WorldIndex)
from ..tools import EMPTY_SET, group
from . import LogicType
from . import fde as FDE


class Meta(FDE.Meta):
    name = 'KFDE'
    title = 'FDE with K modal'
    modal = True
    description = 'Modal version of FDE based on K normal modal logic'
    native_operators = FDE.Meta.native_operators | LogicType.Meta.modal_operators
    category_order = 1
    extension_of = ('FDE')

class Model(FDE.Model): pass
class System(FDE.System): pass

class Rules(FDE.Rules):

    class PossibilityDesignated(rules.ModalOperatorRule):

        Helpers = (AplSentCount)

        def _get_node_targets(self, node: Node, branch: Branch, /):
            si = self.sentence(node).lhs
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

        def score_candidate(self, target, /) -> float:
            """
            Overrides `AdzHelper` closure score
            """
            if target.get('flag'):
                return 1.0
            # override
            s = self.sentence(target.node)
            si = s.lhs
            d = self.designation
            if d is not None:
                d = self.new_designation(d)
            # Don't bother checking for closure since we will always have a new world
            track_count = self[AplSentCount][target.branch][si, d]
            if track_count == 0:
                return 1.0
            return -1.0 * self[MaxWorlds].modals[s] * track_count

        def group_score(self, target, /) -> float:
            if target['candidate_score'] > 0:
                return 1.0
            s = self.sentence(target.node)
            si = s.lhs
            d = self.designation
            if d is not None:
                d = self.new_designation(d)
            return -1.0 * self[AplSentCount][target.branch][si, d]

    class PossibilityNegatedDesignated(rules.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(sdwgroup((self.operator.other(~s.lhs), d, w)))

    class NecessityDesignated(rules.ModalOperatorRule):

        ticking = False
        Helpers = (NodeCount, NodesWorlds, WorldIndex)

        def _get_node_targets(self, node, branch, /):
            # Only count least-applied-to nodes
            if not self[NodeCount].isleast(node, branch):
                return

            s = self.sentence(node)
            d = self.designation
            if d is not None:
                d = self.new_designation(d)
            si = s.lhs
            w1 = node['world']

            for w2 in self[WorldIndex][branch].get(w1, EMPTY_SET):
                if (node, w2) in self[NodesWorlds][branch]:
                    continue
                add = sdwnode(si, d, w2)
                if branch.has(add):
                    continue
                nodes = (node, branch.find(anode(w1, w2)))
                yield adds(group(add),
                    sentence=si,
                    world=w2,
                    nodes=nodes)

        def score_candidate(self, target, /) -> float:
            if target.get('flag'):
                return 1.0
            # We are already restricted to least-applied-to nodes by
            # ``_get_node_targets()``
            # Check for closure
            if self[AdzHelper].closure_score(target) == 1:
                return 1.0
            # Not applied to yet
            apcount = self[NodeCount][target.branch][target.node]
            if apcount == 0:
                return 1.0
            # Pick the least branching complexity
            return -1.0 * self.tableau.branching_complexity(target.node)

        def group_score(self, target, /) -> float:
            if self.score_candidate(target) > 0:
                return 1.0
            return -1.0 * self[NodeCount][target.branch][target.node]

        def example_nodes(self):
            yield from super().example_nodes()
            yield anode(0, 1)

    class PossibilityNegatedUndesignated(PossibilityNegatedDesignated): pass
    class PossibilityUndesignated(NecessityDesignated): pass
    class NecessityNegatedDesignated(PossibilityNegatedDesignated): pass
    class NecessityUndesignated(PossibilityDesignated): pass
    class NecessityNegatedUndesignated(PossibilityNegatedDesignated): pass

    unmodal_groups = (
        group(
            NecessityDesignated,
            PossibilityUndesignated),
        group(
            NecessityUndesignated,
            PossibilityDesignated))

    groups = (
        FDE.Rules.groups[0] + group(
            # non-branching rules
            PossibilityNegatedDesignated,
            PossibilityNegatedUndesignated,
            NecessityNegatedDesignated,
            NecessityNegatedUndesignated),
        # branching rules
        FDE.Rules.groups[1],
        # modal operator rules
        *unmodal_groups,
        # quantifier rules
        *FDE.Rules.unquantifying_groups)

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(2), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'