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
# pytableaux - S5 Normal Modal Logic
name = 'S5'
title = 'S5 Normal Modal Logic'
description = 'Normal modal logic with a reflexive, symmetric, and transitive access relation'
tags_list = ['bivalent', 'modal', 'first-order']
tags = set(tags_list)
category = 'Bivalent Modal'
category_display_order = 5

import logic
from . import k, t, s4

class Model(s4.Model):
    """
    An S5 model is just like an `S4 model`_ with an additional *symmetric*
    restriction on the access relation.

    * **Symmetry**: For each world *w* and each world *w'*, if `<w,w'>` is
      in the access relation, then so is `<w',w>`.

    .. _S4 model: s4.html#logics.s4.Model
    """

    def finish(self):
        while True:
            super(Model, self).finish()
            to_add = set()
            for w1 in self.frames:
                for w2 in self.visibles(w1):
                    a = (w2, w1)
                    if a not in self.access:
                        to_add.add(a)
            if len(to_add) == 0:
                return
            self.access.update(to_add)

class TableauxSystem(k.TableauxSystem):
    """
    S5's Tableaux System inherits directly inherits directly from the `K system`_.

    .. _K system: k.html#logics.k.TableauxSystem
    """
    pass

class TableauxRules(object):
    """
    The Tableaux Rules for S5 contain the rules for `S4`_, as well as an additional
    Symmetric rule, which operates on the accessibility relation for worlds.

    .. _S4: s4.html
    """
    
    class Symmetric(logic.TableauxSystem.BranchRule):
        """
        For any world *w* appearing on a branch *b*, for each world *w'* on *b*,
        if *wRw'* appears on *b*, but *w'Rw* does not appear on *b*, then add *w'Rw* to *b*.
        """
        
        def applies_to_branch(self, branch):
            nodes = {node for node in branch.get_nodes() if node.has('world1')}
            for node in nodes:
                n = branch.find({
                    'world1': node.props['world2'],
                    'world2': node.props['world1'],
                })
                if n == None:
                    return { 
                        'world1': node.props['world2'],
                        'world2': node.props['world1'],
                        'branch': branch,
                        'node'  : node,
                    }
                        
            return False

        def apply(self, target):
            target['branch'].add({
                'world1': target['world1'],
                'world2': target['world2'],
            })

        def example(self):
            self.branch().update([
                {'world1': 0, 'world2': 1},
            ])

    closure_rules = list(k.TableauxRules.closure_rules)

    rule_groups = [
        [
            Symmetric,
            s4.TableauxRules.Transitive,
        ],
        [
            t.TableauxRules.Reflexive,
        ],
        [
            # non-branching rules
            k.TableauxRules.IdentityIndiscernability,
            k.TableauxRules.Assertion,
            k.TableauxRules.AssertionNegated,
            k.TableauxRules.Conjunction, 
            k.TableauxRules.DisjunctionNegated, 
            k.TableauxRules.MaterialConditionalNegated,
            k.TableauxRules.ConditionalNegated,
            k.TableauxRules.DoubleNegation,
            k.TableauxRules.PossibilityNegated,
            k.TableauxRules.NecessityNegated,
            k.TableauxRules.ExistentialNegated,
            k.TableauxRules.UniversalNegated,
        ],
        [
            k.TableauxRules.Existential,
        ],
        [
            k.TableauxRules.Universal,
        ],
        [
            # branching rules
            k.TableauxRules.ConjunctionNegated,
            k.TableauxRules.Disjunction, 
            k.TableauxRules.MaterialConditional, 
            k.TableauxRules.MaterialBiconditional,
            k.TableauxRules.MaterialBiconditionalNegated,
            k.TableauxRules.Conditional,
            k.TableauxRules.Biconditional,
            k.TableauxRules.BiconditionalNegated,
        ],
        [
            # world creation rules 2
            k.TableauxRules.Necessity,
        #],
        #[
            # world creation rules 1
            k.TableauxRules.Possibility,
        ],
    ]