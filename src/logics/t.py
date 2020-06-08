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
# pytableaux - Reflexive Normal Modal Logic
name = 'T'

class Meta(object):

    title    = 'Reflexive Normal Modal Logic'
    category = 'Bivalent Modal'

    description = 'Normal modal logic with a reflexive access relation'

    tags = ['bivalent', 'modal', 'first-order']

    category_display_order = 3

import logic
from . import k

class Model(k.Model):
    """
    A T model is just like a `K model`_ with a *reflexive* restriction on the access
    relation.

    * **Reflexivity**: For each world *w*, `<w,w>` is in the access relation.

    .. _K model: k.html#logics.k.Model
    """

    def finish(self):
        for w in self.frames:
            self.add_access(w, w)
        super(Model, self).finish()

class TableauxSystem(k.TableauxSystem):
    """
    T's Tableaux System inherits directly inherits directly from the `K system`_.

    .. _K system: k.html#logics.k.TableauxSystem
    """
    pass

class TableauxRules(object):
    """
    The Tableaux Rules for T contain the rules for `K`_, as well as an additional
    Reflexive rule, which operates on the accessibility relation for worlds.

    .. _K: k.html
    """

    class Reflexive(k.MaxWorldTrackingFilterRule):
        """
        The Reflexive rule applies to an open branch *b* when there is a node *n*
        on *b* with a world *w* but there is not a node where *w* accesses *w* (itself).

        For a node *n* on an open branch *b* on which appears a world *w* for which there is
        no node such that world1 and world2 is *w*, add a node to *b* where world1 and world2
        is *w*.
        """

        ticked = None

        def __init__(self, *args, **opts):
            super(TableauxRules.Reflexive, self).__init__(*args, **opts)
            self.opts['is_rank_optim'] = False

        def is_potential_node(self, node, branch):
            # TODO: caching filter
            return True

        def get_target_for_node(self, node, branch):
            # why apply when necessity will not apply
            if self.should_stop(branch):
                return
            for world in node.worlds():
                if not branch.has({'world1': world, 'world2': world}):
                    return {'world': world}
            return False
            
        def apply_to_node_target(self, node, branch, target):
            branch.add({'world1': target['world'], 'world2': target['world']})

        def should_stop(self, branch):
            return self.max_worlds_reached(branch)

        def example(self):
            s = logic.atomic(0, 0)
            self.branch().add({'sentence': s, 'world': 0})

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
        [
            k.TableauxRules.Existential,
        ],
        [
            k.TableauxRules.Universal,
        ],
        [
            # modal rules
            k.TableauxRules.Necessity,
            k.TableauxRules.Possibility,
        ],
        [
            Reflexive,
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
    ]