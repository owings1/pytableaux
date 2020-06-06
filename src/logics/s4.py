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
    
    class Transitive(logic.TableauxSystem.NodeRule):
        """
        For any world *w* appearing on a branch *b*, for each world *w'* and for each
        world *w''* on *b*, if *wRw'* and *wRw''* appear on *b*, but *wRw''* does not
        appear on *b*, then add *wRw''* to *b*.
        """

        def __init__(self, *args, **opts):
            super(TableauxRules.Transitive, self).__init__(*args, **opts)
            self.access = {}

        def is_potential_node(self, node, branch):
            return node.has('world1') and node.has('world2')

        def visibles(self, world, branch):
            if branch.id in self.access:
                access = self.access[branch.id]
                if world in access:
                    return access[world]
            return set()

        def track_access(self, w1, w2, branch):
            if branch.id not in self.access:
                self.access[branch.id] = {}
            access = self.access[branch.id]
            if w1 not in access:
                access[w1] = set()
            access[w1].add(w2)

        def track_access_node(self, node, branch):
            w1 = node.props['world1']
            w2 = node.props['world2']
            self.track_access(w1, w2, branch)

        def after_node_add(self, branch, node):
            super(TableauxRules.Transitive, self).after_node_add(branch, node)
            if self.is_potential_node(node, branch):
                self.track_access_node(node, branch)

        def get_targets_for_node(self, node, branch):
            w1 = node.props['world1']
            w2 = node.props['world2']
            targets = list()
            for w3 in self.visibles(w2, branch).difference(self.visibles(w1, branch)):
                if not branch.has({'world1': w1, 'world2': w3}):
                    targets.append({
                        'world1': w1,
                        'world2': w3,
                        'branch': branch,
                        'nodes' : set([node, branch.find({'world1': w2, 'world2': w3})]),
                        'type'  : 'Nodes',
                    })
            return targets

        def score_candidate(self, target):
            # Rank the highest world
            return target['world2']

        def apply_to_target(self, target):
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
            k.TableauxRules.Existential,
        ],
        [
            k.TableauxRules.Universal,
        ],
        [
            Transitive,
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