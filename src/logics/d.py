# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2020 Doug Owings.
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
# pytableaux - Deonitic Normal Modal Logic
name = 'D'
title = 'Deontic Normal Modal Logic'
description = 'Normal modal logic with a serial access relation'
tags_list = ['bivalent', 'modal', 'first-order']
tags = set(tags_list)
category = 'Bivalent Modal'
category_display_order = 2

import logic
from logic import atomic
from . import k

class Model(k.Model):
    """
    A D model is just like a `K model`_ with a *serial* restriction on the access
    relation.

    * **Seriality**: For each world *w*, there is some world *w'* such that `<w,w'>`
      is in the access relation.

    .. _K model: k.html#logics.k.Model
    """

    def finish(self):
        needs_world = set()
        for world in self.frames:
            if len(self.visibles(world)) == 0:
                needs_world.add(world)
        if len(needs_world) > 0:
            # only add one extra world
            w2 = max(self.frames.keys()) + 1
            for w1 in needs_world:
                self.add_access(w1, w2)
            self.add_access(w2, w2)
        super(Model, self).finish()

class TableauxSystem(k.TableauxSystem):
    """
    D's Tableaux System inherits directly inherits directly from the `K system`_.

    .. _K system: k.html#logics.k.TableauxSystem
    """
    pass

class TableauxRules:
    """
    The Tableaux Rules for D contain the rules for `K`_, as well as an additional
    Serial rule, which operates on the accessibility relation for worlds.

    .. _K: k.html
    """

    class Serial(logic.TableauxSystem.BranchRule):
        """
        The Serial rule applies to a an open branch *b* when there is a world *w* that
        appears on *b*, but there is no world *w'* such that *w* accesses *w'*. The exception
        to this is when the Serial rule was the last rule to apply to the branch. This
        prevents infinite repetition of the Serial rule for open branches that are otherwise
        finished. For this reason, even though the Serial rule is non-branching, it is ordered
        last in the rules, so that all other rules are checked before it.

        For a node *n* on an open branch *b* on which appears a world *w* for which there is
        no world *w'* on *b* such that *w* accesses *w'*, add a node to *b* with *w* as world1,
        and *w1* as world2, where *w1* does not yet appear on *b*.
        """

        def applies_to_branch(self, branch):
            if len(self.tableau.history) and self.tableau.history[-1]['rule'] == self:
                return False
            serial_worlds = {node.props['world1'] for node in branch.get_nodes() if 'world1' in node.props}
            worlds = branch.worlds() - serial_worlds
            if len(worlds):
                world = worlds.pop()
                return { 'branch' : branch, 'world' : world, 'node' : branch.find({ 'world1' : world }) }
            return False

        def apply(self, target):
            target['branch'].add({ 
                'world1': target['world'], 
                'world2': target['branch'].new_world()
            })

        def example(self):
            self.tableau.branch().add({ 'sentence' : atomic(0, 0), 'world' : 0 })

    class IdentityIndiscernability(k.TableauxRules.IdentityIndiscernability):
        """
        The rule for identity indiscernability is the same as for `K`_, with the exception that
        the rule does not apply if the Serial rule was the last rule to apply to the branch.
        This prevents infinite repetition (back and forth) of the Serial and IdentityIndiscernability
        rules.
        """

        def applies_to_branch(self, branch):
            if len(self.tableau.history) and isinstance(self.tableau.history[-1]['rule'], TableauxRules.Serial):
                return False
            return super(TableauxRules.IdentityIndiscernability, self).applies_to_branch(branch)
        
    rules = [

        k.TableauxRules.Closure,
        k.TableauxRules.SelfIdentityClosure,

        # non-branching rules
        k.TableauxRules.Conjunction, 
        k.TableauxRules.DisjunctionNegated, 
        k.TableauxRules.MaterialConditionalNegated,
        k.TableauxRules.ConditionalNegated,
        k.TableauxRules.Existential,
        k.TableauxRules.ExistentialNegated,
        k.TableauxRules.Universal,
        k.TableauxRules.UniversalNegated,
        k.TableauxRules.DoubleNegation,
        k.TableauxRules.PossibilityNegated,
        k.TableauxRules.NecessityNegated,

        # branching rules
        k.TableauxRules.ConjunctionNegated,
        k.TableauxRules.Disjunction, 
        k.TableauxRules.MaterialConditional, 
        k.TableauxRules.MaterialBiconditional,
        k.TableauxRules.MaterialBiconditionalNegated,
        k.TableauxRules.Conditional,
        k.TableauxRules.Biconditional,
        k.TableauxRules.BiconditionalNegated,

        # world creation rules
        k.TableauxRules.Possibility,
        k.TableauxRules.Necessity,

        # special ordering of serial rule
        IdentityIndiscernability,
        Serial
    ]