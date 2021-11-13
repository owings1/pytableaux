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
# pytableaux - S4 Normal Modal Logic
name = 'S4'

class Meta(object):
    title    = 'S4 Normal Modal Logic'
    category = 'Bivalent Modal'
    description = 'Normal modal logic with a reflexive and transitive access relation'
    tags = ['bivalent', 'modal', 'first-order']
    category_display_order = 4

from proof.helpers import MaxWorldsTracker, VisibleWorldsIndex, clshelpers

from . import k, t

class Model(t.Model):
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

class TableauxSystem(k.TableauxSystem):
    """
    S4's Tableaux System inherits directly inherits directly from K.
    """
    pass

class TableauxRules(object):
    """
    The Tableaux Rules for S4 contain the rules for :ref:`T <T>`, as well as an additional
    Transitive rule, which operates on the accessibility relation for worlds.
    """
    
    @clshelpers(
        maxw = MaxWorldsTracker,
        vwidx = VisibleWorldsIndex,
    )
    class Transitive(k.GetNodeTargets, k.DefaultRule):
        """
        .. _transitive-rule:

        For any world *w* appearing on a branch *b*, for each world *w'* and for each
        world *w''* on *b*, if *wRw'* and *wRw''* appear on *b*, but *wRw''* does not
        appear on *b*, then add *wRw''* to *b*.
        """
        access = True
        # rule implmentation

        def _get_node_targets(self, node, branch):
            if self.maxw.max_worlds_reached(branch):
                return
            w1 = node['world1']
            w2 = node['world2']
            return (
                {
                    'world1': w1,
                    'world2': w3,
                    'branch': branch,
                    'nodes' : {node, branch.find({'world1': w2, 'world2': w3})},
                } for w3 in self.vwidx.intransitives(branch, w1, w2)
            )
            # targets = list()
            # intransitives = self.vwidx.intransitives(branch, w1, w2)
            # for w3 in intransitives:
            #     # sanity check
            #     if not branch.has_access(w1, w3):
            #         targets.append({
            #             'world1': w1,
            #             'world2': w3,
            #             'branch': branch,
            #             'nodes' : set([node, branch.find({'world1': w2, 'world2': w3})]),
            #         })
            # return targets

        def _apply(self, target):
            target.branch.add({
                'world1': target['world1'],
                'world2': target['world2'],
            })

        def score_candidate(self, target):
            # Rank the highest world
            return target['world2']

        def example_nodes(self, branch = None):
            w1, w2, w3 = range(3)
            return [
                {'world1': w1, 'world2': w2},
                {'world1': w2, 'world2': w3},
            ]

    closure_rules = list(k.TableauxRules.closure_rules)

    rule_groups = [
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
        # Things seem to work better with the Transitive rule before
        # the modal operator rules, and the other access rules after.
        # However, if we put the Transitive after, then some trees
        # fail to close. It is so far an open question whether this
        # is a good idea.
        [
            Transitive,
        ],
        [
            # modal operator rules
            k.TableauxRules.Necessity,
            k.TableauxRules.Possibility,
        ],
        [
            t.TableauxRules.Reflexive,
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
            k.TableauxRules.Existential,
            k.TableauxRules.Universal,
        ],
    ]