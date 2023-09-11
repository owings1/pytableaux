# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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
from __future__ import annotations

from ..lang import Atomic, Marking
from ..proof import Branch, Target, adds, anode, rules, swnode
from ..proof.helpers import MaxWorlds, UnserialWorlds
from ..tools import group
from . import k as K


class Meta(K.Meta):
    name = 'D'
    title = 'Deontic Normal Modal Logic'
    description = 'Normal modal logic with a serial access relation'
    category_order = 2
    extension_of = ('K')

class Model(K.Model):

    def finish(self):
        self._check_not_finished()
        R = self.R
        add = R.add
        needs_world = {w for w in self.frames if not R[w]}
        if needs_world:
            # only add one extra world
            w2 = max(self.frames) + 1
            for w1 in needs_world:
                add((w1, w2))
            add((w2, w2))
        return super().finish()

class System(K.System): pass

class Rules(K.Rules):

    class Serial(rules.BaseSimpleRule):
        """
        .. _serial-rule:

        The Serial rule applies to a an open branch *b* when there is a world *w*
        that appears on *b*, but there is no world *w'* such that *w* accesses *w'*.

        The exception to this is when the Serial rule was the last rule to apply to
        the branch. This prevents infinite repetition of the Serial rule for open
        branches that are otherwise finished. For this reason, the Serial rule is
        ordered last in the rules, so that all other rules are checked before it.

        For a node *n* on an open branch *b* on which appears a world *w* for
        which there is no world *w'* on *b* such that *w* accesses *w'*, add a
        node to *b* with *w* as world1, and *w1* as world2, where *w1* does not
        yet appear on *b*.
        """
        Helpers = (MaxWorlds, UnserialWorlds)
        ignore_ticked = False
        ticking = False
        marklegend = [(Marking.tableau, ('access', 'serial'))]

        def _get_targets(self, branch: Branch, /):
            if not self._should_apply(branch):
                return
            for w in self[UnserialWorlds][branch]:
                yield Target(adds(
                    group(anode(w, branch.new_world())),
                    world=w,
                    branch=branch))

        def _should_apply(self, branch: Branch,/):
            try:
                entry = next(reversed(self.tableau.history))
            except StopIteration:
                pass
            else:
                # This tends to stop modal explosion better than the max worlds check,
                # at least in its current form (all modal operators + worlds + 1).
                if entry.rule == self and entry.target.branch == branch:
                    return False
            # As above, this is unnecessary
            if self[MaxWorlds].is_exceeded(branch):
                return False
            return True

        def example_nodes(self):
            yield swnode(Atomic.first(), 0)

    groups = (
        # non-branching rules
        K.Rules.groups[0],
        *K.Rules.unmodal_groups,
        # branching rules
        K.Rules.groups[1],
        *K.Rules.unquantifying_groups,
        group(Serial))

    @staticmethod
    def _check_groups():
        cls = __class__
        for branching, i in zip(range(2), (0, 2)):
            for rulecls in cls.groups[i]:
                assert rulecls.branching == branching, f'{rulecls}'

    # NB: Since we have redesigned the modal rules, it is not obvious that we need this
    #     alternate rule. So far I have not been able to think of a way to break it. I
    #     am leaving it here just in case
    #
    #class IdentityIndiscernability(K.Rules.IdentityIndiscernability):
    #    """
    #    The rule for identity indiscernability is the same as for :ref:`K <K>`, with the exception that
    #    the rule does not apply if the Serial rule was the last rule to apply to the branch.
    #    This prevents infinite repetition (back and forth) of the Serial and IdentityIndiscernability
    #    rules.
    #    """
    #
    #    
    #
    #    def get_targets_for_node(self, node, branch):
    #        if len(self.tableau.history) and isinstance(self.tableau.history[-1]['rule'], Rules.Serial):
    #            return False
    #        return super(Rules.IdentityIndiscernability, self).get_targets_for_node(node, branch)
