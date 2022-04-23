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
# pytableaux - Reflexive Normal Modal Logic
from __future__ import annotations

name = 'T'

class Meta:
    title    = 'Reflexive Normal Modal Logic'
    category = 'Bivalent Modal'
    description = 'Normal modal logic with a reflexive access relation'
    tags = ['bivalent', 'modal', 'first-order']
    category_order = 3

from pytableaux.lexicals import Atomic
from pytableaux.proof.baserules import adds, group
from pytableaux.proof.common import Access, Branch, Node
from pytableaux.proof.helpers import FilterHelper, MaxWorlds, WorldIndex
from pytableaux.logics import k as K
from pytableaux.logics.k import swnode

class Model(K.Model):
    """
    A T model is just like a :ref:`K model <k-model>` with a *reflexive*
    restriction on the access relation.
    """

    def finish(self):
        for w in self.frames:
            self.add_access(w, w)
        super().finish()

class TableauxSystem(K.TableauxSystem):
    """
    T's Tableaux System inherits directly inherits directly from K.
    """
    pass

class TabRules:
    """
    The Tableaux Rules for T contain the rules for :ref:`K <K>`, as well as an additional
    Reflexive rule, which operates on the accessibility relation for worlds.
    """

    class Reflexive(K.DefaultNodeRule):
        """
        .. _reflexive-rule:

        The Reflexive rule applies to an open branch *b* when there is a node *n*
        on *b* with a world *w* but there is not a node where *w* accesses *w* (itself).

        For a node *n* on an open branch *b* on which appears a world *w* for which there is
        no node such that world1 and world2 is *w*, add a node to *b* where world1 and world2
        is *w*.
        """
        Helpers = MaxWorlds, WorldIndex,

        ignore_ticked = False
        ticking = False

        _defaults = dict(is_rank_optim = False)

        def _get_node_targets(self, node: Node, branch: Branch,/):
            if self[MaxWorlds].max_worlds_exceeded(branch):
                self[FilterHelper].release(node, branch)
                return

            for w in node.worlds:
                access = Access(w, w)
                if not self[WorldIndex].has(branch, access):
                    return adds(group(access._asdict()), world = w)

        @staticmethod
        def example_nodes():
            return swnode(Atomic.first(), 0),

    closure_rules = K.TabRules.closure_rules

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
        (
            # modal rules
            K.TabRules.Necessity,
            K.TabRules.Possibility,
        ),
        (
            Reflexive,
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
