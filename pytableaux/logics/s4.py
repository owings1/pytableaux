# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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

from typing import Generator

import pytableaux.logics.k as K
import pytableaux.logics.t as T
from pytableaux.proof import Access, Branch, Node, Target, adds, anode, group
from pytableaux.proof.helpers import FilterHelper, MaxWorlds, WorldIndex

name = 'S4'

class Meta(K.Meta):
    title       = 'S4 Normal Modal Logic'
    description = 'Normal modal logic with a reflexive and transitive access relation'
    category_order = 4

class Model(T.Model):

    def finish(self):
        finish = super().finish
        vis = self.visibles
        while True:
            finish()
            to_add = set()
            for w1 in self.frames:
                for w2 in vis(w1):
                    for w3 in vis(w2):
                        a = (w1, w3)
                        if a not in self.access:
                            to_add.add(a)
            if len(to_add) == 0:
                return
            self.access.update(to_add)

class TableauxSystem(K.TableauxSystem):
    pass

@TableauxSystem.initialize
class TabRules(T.TabRules):

    class Transitive(K.DefaultNodeRule):
        """
        .. _transitive-rule:

        For any world *w* appearing on a branch *b*, for each world *w'* and for each
        world *w''* on *b*, if *wRw'* and *wRw''* appear on *b*, but *wRw''* does not
        appear on *b*, then add *wRw''* to *b*.
        """
        Helpers = MaxWorlds, WorldIndex,
        access = True
        ticking = False
        modal_operators = Model.modal_operators

        def _get_node_targets(self, node: Node, branch: Branch,/) -> Generator[dict, None, None]:

            if self[MaxWorlds].is_reached(branch):
                self[FilterHelper].release(node, branch)
                return

            w1, w2 = Access.fornode(node)

            return (
                adds(
                    group(anode(w1, w3)),
                    ** anode(w1, w3),
                    nodes = {
                        node, branch.find(anode(w2, w3))
                    },
                )
                for w3 in self[WorldIndex].intransitives(branch, w1, w2)
            )

        def score_candidate(self, target: Target, /) -> float:
            # Rank the highest world
            return float(target.world2)

        @staticmethod
        def example_nodes() -> tuple[dict, dict]:
            w1, w2, w3 = range(3)
            return anode(w1, w2), anode(w2, w3)

    rule_groups = (
        (
            # non-branching rules
            K.TabRules.IdentityIndiscernability,
            K.TabRules.Assertion,
            K.TabRules.AssertionNegated,
            K.TabRules.Conjunction, 
            K.TabRules.DisjunctionNegated, 
            K.TabRules.MaterialConditionalNegated,
            K.TabRules.ConditionalNegated,
            K.TabRules.DoubleNegation,
            K.TabRules.PossibilityNegated,
            K.TabRules.NecessityNegated,
            K.TabRules.ExistentialNegated,
            K.TabRules.UniversalNegated,
        ),
        # Things seem to work better with the Transitive rule before
        # the modal operator rules, and the other access rules after.
        # However, if we put the Transitive after, then some trees
        # fail to close. It is so far an open question whether this
        # is a good idea.
        (
            Transitive,
        ),
        (
            # modal operator rules
            K.TabRules.Necessity,
            K.TabRules.Possibility,
        ),
        (
            T.TabRules.Reflexive,
        ),
        (
            # branching rules
            K.TabRules.ConjunctionNegated,
            K.TabRules.Disjunction, 
            K.TabRules.MaterialConditional, 
            K.TabRules.MaterialBiconditional,
            K.TabRules.MaterialBiconditionalNegated,
            K.TabRules.Conditional,
            K.TabRules.Biconditional,
            K.TabRules.BiconditionalNegated,
        ),
        (
            K.TabRules.Existential,
            K.TabRules.Universal,
        ),
    )
