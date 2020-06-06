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
# pytableaux - S4 Normal Modal Logic
name = 'S4'
title = 'S4 Normal Modal Logic'
description = 'Normal modal logic with a reflexive and transitive access relation'
tags_list = ['bivalent', 'modal', 'first-order']
tags = set(tags_list)
category = 'Bivalent Modal'
category_display_order = 4

import logic
from . import k, t

class Model(t.Model):
    """
    An S4 model is just like a `T model`_ with an additional *transitive*
    restriction on the access relation.

    * **Transitivity**: For each world *w* and each world *w'*, for any world
      *w''* such that `<w,w'>` and `<w',w''>` are in the access relation, then
      `<w,w''>` is in the access relation.

    .. _T model: t.html#logics.t.Model
    """

    def finish(self):
        while True:
            super(Model, self).finish()
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

class TableauxSystem(k.TableauxSystem):
    """
    S4's Tableaux System inherits directly inherits directly from the `K system`_.

    .. _K system: k.html#logics.k.TableauxSystem
    """
    pass

class TableauxRules(object):
    """
    The Tableaux Rules for S4 contain the rules for `T`_, as well as an additional
    Transitive rule, which operates on the accessibility relation for worlds.

    .. _T: t.html
    """
    
    class Transitive(logic.TableauxSystem.BranchRule):
        """
        For any world *w* appearing on a branch *b*, for each world *w'* and for each
        world *w''* on *b*, if *wRw'* and *wRw''* appear on *b*, but *wRw''* does not
        appear on *b*, then add *wRw''* to *b*.
        """
        
        def get_candidate_targets(self, branch):
            nodes = {node for node in branch.get_nodes() if node.has('world1')}
            cands = list()
            for node in nodes:
                for other_node in nodes:
                    if node.props['world2'] == other_node.props['world1']:
                        n = branch.find({ 
                            'world1': node.props['world1'], 
                            'world2': other_node.props['world2'],
                        })
                        if n == None:
                            target = { 
                                'world1': node.props['world1'],
                                'world2': other_node.props['world2'],
                                'branch': branch,
                                'nodes' : set([node, other_node]),
                                'type'  : 'Nodes',
                            }
                            cands.append(target)
            return cands

        def select_best_target(self, targets, branch):
            return targets[0]

        def apply(self, target):
            target['branch'].add({
                'world1': target['world1'],
                'world2': target['world2'],
            })

        def example(self):
            self.branch().update([
                {'world1': 0, 'world2': 1},
                {'world1': 1, 'world2': 2},
            ])

    closure_rules = list(k.TableauxRules.closure_rules)

    rule_groups = [
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
            Transitive,
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