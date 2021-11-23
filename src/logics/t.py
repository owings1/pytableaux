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
from proof.common import Branch, Node, Target
from proof.rules import PotentialNodeRule
from proof.helpers import MaxWorldsTracker, clshelpers

from . import k

class Model(k.Model):
    """
    A T model is just like a :ref:`K model <k-model>` with a *reflexive*
    restriction on the access relation.
    """

    def finish(self):
        for w in self.frames:
            self.add_access(w, w)
        super().finish()

class TableauxSystem(k.TableauxSystem):
    """
    T's Tableaux System inherits directly inherits directly from K.
    """
    pass

class TableauxRules(object):
    """
    The Tableaux Rules for T contain the rules for :ref:`K <K>`, as well as an additional
    Reflexive rule, which operates on the accessibility relation for worlds.
    """

    class Reflexive(PotentialNodeRule):
        """
        .. _reflexive-rule:

        The Reflexive rule applies to an open branch *b* when there is a node *n*
        on *b* with a world *w* but there is not a node where *w* accesses *w* (itself).

        For a node *n* on an open branch *b* on which appears a world *w* for which there is
        no node such that world1 and world2 is *w*, add a node to *b* where world1 and world2
        is *w*.
        """
        Helpers = (
            *PotentialNodeRule.Helpers,
            ('max_worlds_tracker', MaxWorldsTracker),
        )
        Timers = (
            *PotentialNodeRule.Timers,
            'is_potential_node',
        )
        modal = True

        def __init__(self, *args, **opts):
            super().__init__(*args, **opts)
            self.opts['is_rank_optim'] = False

        # rule implementation

        def is_potential_node(self, node, branch):
            ret = None
            with self.timers['is_potential_node']:
                for w in node.worlds:
                    if not branch.has_access(w, w):
                        ret = True
                        break
            return ret

        def get_target_for_node(self, node, branch):
            # why apply when necessity will not apply
            if not self.__should_apply(branch):
                return
            for world in node.worlds:
                if not branch.has_access(world, world):
                    return {'world': world}
            return False
            
        def apply_to_node_target(self, node, branch, target):
            branch.add({'world1': target['world'], 'world2': target['world']})

        def example_nodes(self, branch = None):
            return ({'sentence': Atomic.first(), 'world': 0},)

        # private util

        def __should_apply(self, branch):
            # why apply when necessity will not apply
            return not self.max_worlds_tracker.max_worlds_exceeded(branch)

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
        #[
        #    
        #],
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
        [
            k.TableauxRules.Existential,
            k.TableauxRules.Universal,
        ],
    ]