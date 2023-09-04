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

from ..lang import Operated, Operator
from ..proof import WorldPair, adds, anode, sdwnode
from ..proof.helpers import (AdzHelper, AplSentCount, FilterHelper, MaxWorlds,
                             NodeCount, NodesWorlds, QuitFlag, WorldIndex)
from ..tools import EMPTY_SET, group, maxceil, minfloor
from . import LogicType
from . import fde as FDE


class Meta(FDE.Meta):
    name = 'KFDE'
    title = 'FDE with K modal'
    modal = True
    description = 'Modal version of FDE based on K normal modal logic'
    native_operators = FDE.Meta.native_operators | LogicType.Meta.modal_operators
    category_order = 10
    extension_of = ('FDE')

class Model(FDE.Model):

    def value_of_operated(self, s: Operated, /, *, world: int = 0):
        self._check_finished()
        oper = s.operator
        if self.Meta.modal and oper in self.Meta.modal_operators:
            it = map(lambda w: self.value_of(s.lhs, world=w), self.R[world])
            if oper is Operator.Possibility:
                return maxceil(self.maxval, it, self.minval)
            if oper is Operator.Necessity:
                return minfloor(self.minval, it, self.maxval)
            raise NotImplementedError from ValueError(s.operator)
        return super().value_of_operated(s, world=world)

class System(FDE.System): pass

class Rules(LogicType.Rules):

    closure = FDE.Rules.closure

    class PossibilityDesignated(System.OperatorNodeRule):

        Helpers = (QuitFlag, MaxWorlds, AplSentCount)

        def _get_node_targets(self, node, branch, /):

            # Check for max worlds reached
            if self[MaxWorlds].is_exceeded(branch):
                self[FilterHelper].release(node, branch)
                if not self[QuitFlag].get(branch):
                    fnode = self[MaxWorlds].quit_flag(branch)
                    yield adds(group(fnode), flag=fnode['flag'])
                return

            si = self.sentence(node).lhs
            d = self.designation
            w1 = node['world']
            w2 = branch.new_world()
            yield adds(
                group(sdwnode(si, d, w2), anode(w1, w2)),
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
            # Don't bother checking for closure since we will always have a new world
            track_count = self[AplSentCount][target.branch][si]
            if track_count == 0:
                return 1.0
            return -1.0 * self[MaxWorlds].modals[s] * track_count

        def group_score(self, target, /) -> float:
            if target['candidate_score'] > 0:
                return 1.0
            s = self.sentence(target.node)
            si = s.lhs
            return -1.0 * self[AplSentCount][target.branch][si]

    class PossibilityNegatedDesignated(System.OperatorNodeRule):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(group(sdwnode(self.operator.other(~s.lhs), d, w)))

    class PossibilityUndesignated(System.OperatorNodeRule):

        ticking = False
        Helpers = (QuitFlag, MaxWorlds, NodeCount, NodesWorlds, WorldIndex)

        def _get_node_targets(self, node, branch, /):

            # Check for max worlds reached
            if self[MaxWorlds].is_exceeded(branch):
                self[FilterHelper].release(node, branch)
                if not self[QuitFlag].get(branch):
                    fnode = self[MaxWorlds].quit_flag(branch)
                    yield adds(group(fnode), flag = fnode['flag'])
                return

            # Only count least-applied-to nodes
            if not self[NodeCount].isleast(node, branch):
                return

            s = self.sentence(node)
            d = self.designation
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
            s = Operated.first(self.operator)
            a = WorldPair(0, 1)
            d = self.designation
            yield sdwnode(s, d, a.world1)
            yield a.tonode()

    class PossibilityNegatedUndesignated(PossibilityNegatedDesignated): pass
    class NecessityDesignated(PossibilityUndesignated): pass
    class NecessityNegatedDesignated(PossibilityNegatedDesignated): pass
    class NecessityUndesignated(PossibilityDesignated): pass
    class NecessityNegatedUndesignated(PossibilityNegatedDesignated): pass

    groups = (
        FDE.Rules.groups[0] + group(
            # non-branching rules
            PossibilityNegatedDesignated,
            PossibilityNegatedUndesignated,
            NecessityNegatedDesignated,
            NecessityNegatedUndesignated),
        # branching rules
        FDE.Rules.groups[1],
        group(
            NecessityDesignated,
            PossibilityUndesignated),
        group(
            NecessityUndesignated,
            PossibilityDesignated),
        # quantifier rules
        FDE.Rules.groups[-2],
        FDE.Rules.groups[-1])

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(2), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'