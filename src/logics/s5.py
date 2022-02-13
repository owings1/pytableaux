# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
# pytableaux - S5 Normal Modal Logic
name = 'S5'

class Meta:
    title = 'S5 Normal Modal Logic'
    description = 'Normal modal logic with a reflexive, symmetric, and transitive access relation'
    tags = ['bivalent', 'modal', 'first-order']
    category = 'Bivalent Modal'
    category_display_order = 5

from proof.baserules import adds, group
from proof.common import Access, Branch, Node
from proof.helpers import FilterHelper, MaxWorlds, WorldIndex
from . import k as K, t as T, s4 as S4

# TODO:
# Some problematic arguments for S5:
#
#   VxLUFxMSyLGy |- b       or   ∀x◻(Fx → ◇∃y◻Gy) |- B  (also bad for S4)

class Model(S4.Model):
    """
    An S5 model is just like an :ref:`S4 model <s4-model>` with an additional
    *symmetric* restriction on the access relation.
    """
    def finish(self):
        while True:
            super().finish()
            to_add = set()
            for w1 in self.frames:
                for w2 in self.visibles(w1):
                    a = (w2, w1)
                    if a not in self.access:
                        to_add.add(a)
            if len(to_add) == 0:
                return
            self.access.update(to_add)

class TableauxSystem(K.TableauxSystem):
    """
    S5's Tableaux System inherits directly inherits directly from K.
    """
    pass

class TabRules:
    """
    The Tableaux Rules for S5 contain the rules for :ref:`S4 <S4>`, as well
    as an additional Symmetric rule, which operates on the accessibility
    relation for worlds.
    """
    
    class Symmetric(K.DefaultNodeRule):
        """
        .. _symmetric-rule:

        For any world *w* appearing on a branch *b*, for each world *w'* on *b*,
        if *wRw'* appears on *b*, but *w'Rw* does not appear on *b*, then add *w'Rw* to *b*.
        """
        Helpers = MaxWorlds, WorldIndex,
        access = True
        _defaults = dict(is_rank_optim = False)

        def _get_node_targets(self, node: Node, branch: Branch):
            if not self[MaxWorlds].max_worlds_exceeded(branch):
                access = Access.fornode(node).reverse()
                if not self[WorldIndex].has(branch, access):
                    anode = access.todict()
                    return adds(group(anode), **anode)
            self[FilterHelper].release(node, branch)

        @staticmethod
        def example_nodes():
            return Access(0, 1).todict(),

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
        # Things seem to work better with the Transitive rule before
        # the modal operator rules, and the other access rules after.
        # However, if we put the Transitive after, then some trees
        # fail to close. It is so far an open question whether this
        # is a good idea.
        (
            S4.TabRules.Transitive,
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
        (
            Symmetric,
        ),
    )
