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

class Meta(object):

    title    = 'Deontic Normal Modal Logic'
    category = 'Bivalent Modal'

    description = 'Normal modal logic with a serial access relation'

    tags = ['bivalent', 'modal', 'first-order']

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

    class Serial(k.IsModal, logic.TableauxSystem.PotentialNodeRule):
        """
        The Serial rule applies to a an open branch *b* when there is a world *w* that
        appears on *b*, but there is no world *w'* such that *w* accesses *w'*. The exception
        to this is when the Serial rule was the last rule to apply to the branch. This
        prevents infinite repetition of the Serial rule for open branches that are otherwise
        finished. For this reason, the Serial rule is ordered
        last in the rules, so that all other rules are checked before it.

        For a node *n* on an open branch *b* on which appears a world *w* for which there is
        no world *w'* on *b* such that *w* accesses *w'*, add a node to *b* with *w* as world1,
        and *w1* as world2, where *w1* does not yet appear on *b*.
        """

        def __init__(self, *args, **opts):
            super(TableauxRules.Serial, self).__init__(*args, **opts)
            self.safeprop('unserial_worlds', {})
            self.safeprop('max_worlds_tracker', k.MaxWorldsTracker(self))

        def after_trunk_build(self, branches):
            super(TableauxRules.Serial, self).after_trunk_build(branches)
            self.max_worlds_tracker.after_trunk_build(branches)

        # Cache

        def register_branch(self, branch, parent):
            super(TableauxRules.Serial, self).register_branch(branch, parent)
            if parent != None and parent.id in self.unserial_worlds:
                self.unserial_worlds[branch.id] = set(self.unserial_worlds[parent.id])
            else:
                self.unserial_worlds[branch.id] = set()

        def register_node(self, node, branch):
            super(TableauxRules.Serial, self).register_node(node, branch)
            for w in node.worlds():
                if branch.has({'world1': w}):
                    self.unserial_worlds[branch.id].discard(w)
                else:
                    self.unserial_worlds[branch.id].add(w)

        # Implementation

        def is_potential_node(self, node, branch):
            return len(node.worlds()) > 0

        def get_targets_for_node(self, node, branch):

            if not len(self.unserial_worlds[branch.id]):
                return

            if self.should_stop(branch):
                return

            return [{'world': w} for w in self.unserial_worlds[branch.id]]

        def apply_to_target(self, target):
            target['branch'].add({ 
                'world1': target['world'], 
                'world2': target['branch'].new_world(),
            })

        def example(self):
            self.branch().add({ 'sentence' : atomic(0, 0), 'world' : 0 })

        # Util

        def should_stop(self, branch):

            # TODO: Shouldn't this check the history only relative to the branch?
            #       Waiting to come up with a test case before fixing it.

            # This tends to stop modal explosion better than the max worlds check,
            # at least in its current form (all modal operators + worlds + 1).
            if len(self.tableau.history) and self.tableau.history[-1]['rule'] == self:
                return True

            # As above, this is unnecessary
            if self.max_worlds_tracker.max_worlds_exceeded(branch):
                return True

            return False

    # NB: Since we have redesigned the modal rules, it is not obvious that we need this
    #     alternate rule. So far I have not been able to think of a way to break it. I
    #     am leaving it here just in case
    #
    #class IdentityIndiscernability(k.TableauxRules.IdentityIndiscernability):
    #    """
    #    The rule for identity indiscernability is the same as for `K`_, with the exception that
    #    the rule does not apply if the Serial rule was the last rule to apply to the branch.
    #    This prevents infinite repetition (back and forth) of the Serial and IdentityIndiscernability
    #    rules.
    #    """
    #
    #    
    #
    #    def get_targets_for_node(self, node, branch):
    #        if len(self.tableau.history) and isinstance(self.tableau.history[-1]['rule'], TableauxRules.Serial):
    #            return False
    #        return super(TableauxRules.IdentityIndiscernability, self).get_targets_for_node(node, branch)

    closure_rules = list(k.TableauxRules.closure_rules)

    rule_groups = [
        [
            # non-branching rules
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
            # See comment on rule above -- using K rule now
            ## special ordering of serial rule
            #IdentityIndiscernability,
            k.TableauxRules.IdentityIndiscernability,
        ],
        [
            # special ordering of serial rule
            Serial,
        ],
    ]