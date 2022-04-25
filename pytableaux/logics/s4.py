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
#
# ------------------
#
# pytableaux - S4 Normal Modal Logic
from __future__ import annotations

from typing import Generator

from pytableaux.logics import k as K
from pytableaux.logics import t as T
from pytableaux.logics.k import adds, anode, group
from pytableaux.proof.common import Branch, Node, Target
from pytableaux.proof.helpers import FilterHelper, MaxWorlds, WorldIndex
from pytableaux.proof.util import Access

name = 'S4'

class Meta:
    title    = 'S4 Normal Modal Logic'
    category = 'Bivalent Modal'
    description = 'Normal modal logic with a reflexive and transitive access relation'
    tags = 'bivalent', 'modal', 'first-order'
    category_order = 4

class Model(T.Model):
    """
    An S4 model is just like a :ref:`T model <T>` with an additional *transitive*
    restriction on the access relation.
    """
    def finish(self):
        while True:
            super().finish()
            to_add = set()
            for w1 in self.frames:
                for w2 in self.visibles(w1):
                    for w3 in self.visibles(w2):
                        a = (w1, w3)
                        if a not in self.access:
                            to_add.add(a)
            if len(to_add) == 0:
                return
            self.access.update(to_add)

class TableauxSystem(K.TableauxSystem):
    """
    S4's Tableaux System inherits directly inherits directly from K.
    """
    pass

class TabRules:
    """
    The Tableaux Rules for S4 contain the rules for :ref:`T <T>`, as well as an additional
    Transitive rule, which operates on the accessibility relation for worlds.
    """

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

    closure_rules = tuple(K.TabRules.closure_rules)

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
