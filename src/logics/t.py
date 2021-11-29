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
# pytableaux - Reflexive Normal Modal Logic
name = 'T'

class Meta(object):
    title    = 'Reflexive Normal Modal Logic'
    category = 'Bivalent Modal'
    description = 'Normal modal logic with a reflexive access relation'
    tags = ['bivalent', 'modal', 'first-order']
    category_display_order = 3

from lexicals import Atomic
from proof.common import Access, Annotate, Branch, Node
from proof.helpers import VisibleWorldsIndex
from . import k as K

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

class TabRules(object):
    """
    The Tableaux Rules for T contain the rules for :ref:`K <K>`, as well as an additional
    Reflexive rule, which operates on the accessibility relation for worlds.
    """

    class Reflexive(K.ModalNodeRule):
        """
        .. _reflexive-rule:

        The Reflexive rule applies to an open branch *b* when there is a node *n*
        on *b* with a world *w* but there is not a node where *w* accesses *w* (itself).

        For a node *n* on an open branch *b* on which appears a world *w* for which there is
        no node such that world1 and world2 is *w*, add a node to *b* where world1 and world2
        is *w*.
        """
        Helpers = (VisibleWorldsIndex,)
        visw: VisibleWorldsIndex = Annotate.HelperAttr

        ignore_ticked = False
        ticking = False

        opts = {'is_rank_optim': False}

        def _get_node_targets(self, node: Node, branch: Branch):
            if not self.maxw.max_worlds_exceeded(branch):
                for w in node.worlds:
                    access = Access(w, w)
                    if not self.visw.has(branch, access):
                        return {
                            'world': w,
                            'adds': ((access.todict(),),),
                        }
            self.nf.release(node, branch)

        def example_nodes(self):
            return ({'sentence': Atomic.first(), 'world': 0},)

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
TableauxRules = TabRules