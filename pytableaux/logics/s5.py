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

from ..lang import Marking
from ..proof import AccessNode, Branch, adds, anode
from ..proof.helpers import FilterHelper, MaxWorlds, WorldIndex
from ..tools import group
from . import k as K
from . import s4 as S4
from . import t as T


class Meta(K.Meta):
    name = 'S5'
    title = 'S5 Normal Modal Logic'
    description = (
        'Normal modal logic with a reflexive, symmetric, and transitive '
        'access relation')
    category_order = 5


# TODO:
# Some problematic arguments for S5:
#
#   VxLUFxMSyLGy |- b       or   ∀x◻(Fx → ◇∃y◻Gy) |- B  (also bad for S4)

class Model(S4.Model):

    def finish(self):
        while True:
            super().finish()
            to_add = set()
            for w1 in self.frames:
                for w2 in self.R[w1]:
                    if w1 not in self.R[w2]:
                        to_add.add((w2, w1))
            if not to_add:
                return
            for w1, w2 in to_add:
                self.R[w1].add(w2)

class System(K.System):
    pass

class Rules(S4.Rules):
    
    class Symmetric(K.DefaultNodeRule):
        """
        .. _symmetric-rule:

        For any world *w* appearing on a branch *b*, for each world *w'* on *b*,
        if *wRw'* appears on *b*, but *w'Rw* does not appear on *b*, then add
        *w'Rw* to *b*.
        """
        Helpers = (MaxWorlds, WorldIndex)
        NodeType = AccessNode
        ticking = False
        marklegend = [(Marking.tableau, ('access', 'symmetric'))]
        _defaults = dict(is_rank_optim = False)

        def _get_node_targets(self, node: AccessNode, branch: Branch,/):
            if self[MaxWorlds].is_exceeded(branch):
                self[FilterHelper].release(node, branch)
                return
            access = node.pair().reversed()
            if self[WorldIndex].has(branch, access):
                self[FilterHelper].release(node, branch)
                return
            yield adds(group(a := access.tonode()), **a)

    rule_groups = (
        (
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
            K.Rules.UniversalNegated,
        ),
        # Things seem to work better with the Transitive rule before
        # the modal operator rules, and the other access rules after.
        # However, if we put the Transitive after, then some trees
        # fail to close. It is so far an open question whether this
        # is a good idea.
        (
            S4.Rules.Transitive,
        ),
        (
            # modal operator rules
            K.Rules.Necessity,
            K.Rules.Possibility,
        ),
        (
            T.Rules.Reflexive,
        ),
        (
            # branching rules
            K.Rules.ConjunctionNegated,
            K.Rules.Disjunction, 
            K.Rules.MaterialConditional, 
            K.Rules.MaterialBiconditional,
            K.Rules.MaterialBiconditionalNegated,
            K.Rules.Conditional,
            K.Rules.Biconditional,
            K.Rules.BiconditionalNegated,
        ),
        (
            K.Rules.Existential,
            K.Rules.Universal,
        ),
        (
            Symmetric,
        ),
    )
