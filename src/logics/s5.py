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

class Meta(object):
    title = 'S5 Normal Modal Logic'
    description = 'Normal modal logic with a reflexive, symmetric, and transitive access relation'
    tags = ['bivalent', 'modal', 'first-order']
    category = 'Bivalent Modal'
    category_display_order = 5

from proof.rules import PotentialNodeRule
from proof.helpers import MaxWorldsTracker

from . import k, t, s4

# TODO:
# Some problematic arguments for S5:
#
#   VxLUFxMSyLGy |- b       or   ∀x◻(Fx → ◇∃y◻Gy) |- B  (also bad for S4)

class Model(s4.Model):
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

class TableauxSystem(k.TableauxSystem):
    """
    S5's Tableaux System inherits directly inherits directly from K.
    """
    pass

class TableauxRules(object):
    """
    The Tableaux Rules for S5 contain the rules for :ref:`S4 <S4>`, as well
    as an additional Symmetric rule, which operates on the accessibility
    relation for worlds.
    """
    
    class Symmetric(PotentialNodeRule):
        """
        .. _symmetric-rule:

        For any world *w* appearing on a branch *b*, for each world *w'* on *b*,
        if *wRw'* appears on *b*, but *w'Rw* does not appear on *b*, then add *w'Rw* to *b*.
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
        ticked = None

        def __init__(self, *args, **opts):
            super().__init__(*args, **opts)
            self.opts['is_rank_optim'] = False

        # rule implementation

        def is_potential_node(self, node, branch):
            ret = None
            with self.timers['is_potential_node']:
                if node.has('world1') and node.has('world2'):
                    w1 = node['world1']
                    w2 = node['world2']
                    ret = not branch.has_access(w2, w1)
            return ret

        def get_target_for_node(self, node, branch):
            if not self.__should_apply(branch):
                return
            if not branch.has({'world1': node['world2'], 'world2': node['world1']}):
                return {
                    'world1' : node['world2'],
                    'world2' : node['world1'],
                }

        def apply_to_node_target(self, node, branch, target):
            branch.add({
                'world1': target['world1'],
                'world2': target['world2'],
            })

        def example_nodes(self, branch = None):
            return ({'world1': 0, 'world2': 1},)

        def __should_apply(self, branch):
            # why apply when necessity will not apply
            return not self.max_worlds_tracker.max_worlds_reached(branch)

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
            s4.TableauxRules.Transitive,
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
        [
            Symmetric,
        ],
    ]