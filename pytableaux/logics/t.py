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

from ..lang import Atomic, Marking
from ..proof import WorldPair, adds, swnode
from ..proof.helpers import FilterHelper, MaxWorlds, WorldIndex
from ..tools import group
from . import k as K


class Meta(K.Meta):
    name = 'T'
    title = 'Reflexive Normal Modal Logic'
    description = 'Normal modal logic with a reflexive access relation'
    category_order = 3

class Model(K.Model):

    def finish(self):
        for w in self.frames:
            self.R[w].add(w)
        super().finish()

class System(K.System):
    pass

class Rules(K.Rules):

    class Reflexive(K.DefaultNodeRule):
        """
        .. _reflexive-rule:

        The Reflexive rule applies to an open branch *b* when there is a node *n*
        on *b* with a world *w* but there is not a node where *w* accesses *w* (itself).

        For a node *n* on an open branch *b* on which appears a world *w* for which there is
        no node such that world1 and world2 is *w*, add a node to *b* where world1 and world2
        is *w*.
        """
        Helpers = (MaxWorlds, WorldIndex)
        ignore_ticked = False
        ticking = False
        marklegend = group((Marking.tableau, ('access', 'reflexive')))

        _defaults = dict(is_rank_optim = False)

        def _get_node_targets(self, node, branch, /):
            if self[MaxWorlds].is_exceeded(branch):
                self[FilterHelper].release(node, branch)
                return
            for w in node.worlds():
                access = WorldPair(w, w)
                if self[WorldIndex].has(branch, access):
                    self[FilterHelper].release(node, branch)
                    continue
                yield adds(group(access.tonode()), world = w)

        def example_nodes(self):
            yield swnode(Atomic.first(), 0)

    groups = (
        group(
            # non-branching rules
            K.Rules.IdentityIndiscernability,
            K.Rules.Assertion,
            K.Rules.AssertionNegated,
            K.Rules.Conjunction, 
            K.Rules.DisjunctionNegated, 
            K.Rules.MaterialConditionalNegated,
            K.Rules.ConditionalNegated,
            K.Rules.DoubleNegation,
            K.Rules.PossibilityNegated,
            K.Rules.NecessityNegated,
            K.Rules.ExistentialNegated,
            K.Rules.UniversalNegated),
        group(
            # modal rules
            K.Rules.Necessity,
            K.Rules.Possibility),
        group(
            Reflexive),
        group(
            # branching rules
            K.Rules.ConjunctionNegated,
            K.Rules.Disjunction, 
            K.Rules.MaterialConditional, 
            K.Rules.MaterialBiconditional,
            K.Rules.MaterialBiconditionalNegated,
            K.Rules.Conditional,
            K.Rules.Biconditional,
            K.Rules.BiconditionalNegated),
        group(
            K.Rules.Existential,
            K.Rules.Universal))
